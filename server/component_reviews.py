"""Immutable component decisions and the one-time migration of whole-item reviews."""
import json
import re
from collaboration_errors import Conflict, InvalidRequest

SCHEMA = """
CREATE TABLE IF NOT EXISTS review_components (
    event_id TEXT NOT NULL REFERENCES review_events(id),
    component TEXT NOT NULL,
    revision TEXT NOT NULL,
    members_json TEXT NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('subject','verses')),
    PRIMARY KEY(event_id, component)
);
CREATE INDEX IF NOT EXISTS component_revision ON review_components(component, revision, event_id);
CREATE TRIGGER IF NOT EXISTS immutable_components_update
    BEFORE UPDATE ON review_components BEGIN SELECT RAISE(ABORT, 'Immutable component review'); END;
CREATE TRIGGER IF NOT EXISTS immutable_components_delete
    BEFORE DELETE ON review_components BEGIN SELECT RAISE(ABORT, 'Immutable component review'); END;
"""


def validate_components(item):
    components = item['metadata']['components']
    expected = ({'text', 'notes', 'markers', 'citations', 'layout', 'intro'} if item['type'] == 'text-chapter'
                else {'text', 'notes', 'markers', 'citations', 'layout'} if item['type'] == 'text-verse'
                else {'content'})
    if set(components) != expected or any(
            not re.fullmatch('[a-f0-9]{64}', part['revision']) or not isinstance(part['present'], bool)
            for part in components.values()):
        raise InvalidRequest()


def initialize(db):
    if db.execute("SELECT 1 FROM metadata WHERE key='review-component-scope-v1'").fetchone():
        return
    columns = {row['name'] for row in db.execute('PRAGMA table_info(review_components)')}
    if 'scope' not in columns:
        db.execute("ALTER TABLE review_components ADD COLUMN scope TEXT NOT NULL DEFAULT 'subject' CHECK(scope IN ('subject','verses'))")
    db.execute("INSERT INTO metadata VALUES ('review-component-scope-v1', '1')")


def attach(db, event_id, components, metadata):
    db.executemany("""INSERT INTO review_components
        (event_id,component,revision,members_json,scope) VALUES (?, ?, ?, ?, 'subject')""",
                   [(event_id, key, revision, json.dumps(metadata[key].get('members', {})))
                    for key, revision in components.items()])


def migrate(db, catalog):
    if db.execute("SELECT 1 FROM metadata WHERE key='component-reviews-v1'").fetchone():
        return
    known = {(i['type'], i['id'], i['revision']): i['metadata']['components']
             for i in catalog['subjects'] + catalog['historicalSubjects'] + catalog['componentHistory']}
    events = db.execute('''SELECT * FROM review_events e WHERE NOT EXISTS
        (SELECT 1 FROM review_components c WHERE c.event_id=e.id) ORDER BY rowid''').fetchall()
    for event in events:
        key = tuple(event[k] for k in ('subject_type', 'subject_id', 'revision'))
        if key not in known:
            raise RuntimeError('Missing component migration snapshot: ' + repr(key))
        attach(db, event['id'], {key: part['revision'] for key, part in known[key].items()}, known[key])
    db.execute("INSERT INTO metadata VALUES ('component-reviews-v1', '1')")


def states(db, row, present_event, administrator):
    metadata = json.loads(row['metadata_json'])
    events = db.execute('''SELECT e.*, e.rowid AS sequence, c.component, c.revision AS component_revision, c.scope, c.members_json,
        (SELECT registered FROM users WHERE uid=e.actor_uid) AS actor_registered
        FROM review_events e JOIN review_components c ON c.event_id=e.id
        WHERE e.subject_type=? AND e.subject_id=?
        ORDER BY (e.actor_kind='user') DESC, e.rowid DESC''',
        (row['subject_type'], row['subject_id'])).fetchall()
    inherited = []
    if row['subject_type'] == 'text-verse':
        parent, number = row['subject_id'].rsplit('/', 1)
        for event in db.execute('''SELECT e.*, e.rowid AS sequence, c.component, c.members_json,
            (SELECT registered FROM users WHERE uid=e.actor_uid) AS actor_registered
            FROM review_events e JOIN review_components c ON c.event_id=e.id
            WHERE e.subject_type='text-chapter' AND e.subject_id=?
            ORDER BY (e.actor_kind='user') DESC, e.rowid DESC''', (parent,)):
            members = json.loads(event['members_json'])
            if number in members:
                inherited.append({**dict(event), 'component_revision': members[number]})
    children = []
    if row['subject_type'] == 'text-chapter':
        children = db.execute('''SELECT e.*, e.rowid AS sequence, c.component, c.revision AS component_revision,
            (SELECT registered FROM users WHERE uid=e.actor_uid) AS actor_registered
            FROM review_events e JOIN review_components c ON c.event_id=e.id
            JOIN review_subjects s ON s.subject_type=e.subject_type AND s.subject_id=e.subject_id AND s.active=1
            WHERE e.subject_type='text-verse' AND e.subject_id LIKE ?
            ORDER BY (e.actor_kind='user') DESC, e.rowid DESC''', (row['subject_id'] + '/%',)).fetchall()
    rank = lambda e: (e['actor_kind'] == 'user', e['sequence'])
    if row['subject_type'] == 'text-chapter':
        # A member-scoped decision affects only its listed verses. It is not a
        # withdrawal of the chapter approval from which other verses inherit.
        children = list(children)
        for event in events:
            if event['scope'] == 'verses':
                members = json.loads(event['members_json'])
                for number in metadata['components'][event['component']]['members']:
                    if number in members:
                        children.append({**dict(event), 'subject_id': row['subject_id'] + '/' + number,
                                         'component_revision': members[number]})
        children.sort(key=rank, reverse=True)
        events = [event for event in events if event['scope'] == 'subject']
    result = {}
    for key, part in metadata['components'].items():
        relevant = sorted([e for e in [*events, *inherited] if e['component'] == key], key=rank, reverse=True)
        latest = next((e for e in relevant if e['component_revision'] == part['revision']), None)
        if latest and latest['decision'] == 'approved' and children and key != 'intro':
            seen = set()
            for child in children:
                number = child['subject_id'].rsplit('/', 1)[1]
                if (child['component'] != key or number in seen or
                        child['component_revision'] != part['members'][number]):
                    continue
                seen.add(number)
                if child['decision'] == 'revoked' and rank(child) > rank(latest):
                    latest = child
                    break
        status = 'approved' if latest and latest['decision'] == 'approved' else 'pending'
        result[key] = {**part, 'status': status,
                       'needsReverification': bool(not latest and any(e['decision'] == 'approved' for e in relevant))}
        if administrator:
            result[key]['latestReview'] = present_event(latest)
    return result


def selection(row, payload):
    available = json.loads(row['metadata_json'])['components']
    # An omitted selection is an explicit whole-item review (private clients / CLI).
    # Reader controls always send the exact visible selection.
    selected = payload.get('components', {key: part['revision'] for key, part in available.items()})
    if not isinstance(selected, dict) or not selected or set(selected) - set(available):
        raise InvalidRequest()
    if any(revision != available[key]['revision'] for key, revision in selected.items()):
        raise Conflict()
    return selected


def undecided(db, row, selected, decision, present_event):
    current = states(db, row, present_event, True)
    return {key: revision for key, revision in selected.items()
            if not current[key]['latestReview'] or current[key]['latestReview']['decision'] != decision}
