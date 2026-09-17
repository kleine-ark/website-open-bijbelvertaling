"""Correction targets and the explicit upgrade from whole-subject requests."""
import json
import uuid

from collaboration_errors import InvalidRequest
from review_content import canonical_hash, subject_payload
from review_components import component_metadata


def selection(subject, payload):
    component, custom = payload['component'], payload['customTarget']
    available = json.loads(subject['metadata_json'])['components']
    if (not isinstance(component, str) or component not in {*available, 'custom'}
            or not isinstance(custom, str) or len(custom) > 200):
        raise InvalidRequest()
    custom = custom.strip()
    if (component == 'custom') != bool(custom):
        raise InvalidRequest()
    return component, custom


def initialize(db):
    if db.execute("SELECT 1 FROM metadata WHERE key='correction-scope-columns-v1'").fetchone():
        return
    columns = {row['name'] for row in db.execute('PRAGMA table_info(corrections)')}
    if 'component' not in columns:
        db.execute("ALTER TABLE corrections ADD COLUMN component TEXT NOT NULL DEFAULT 'text'")
        db.execute("ALTER TABLE corrections ADD COLUMN custom_target TEXT NOT NULL DEFAULT ''")
        db.execute("UPDATE corrections SET component='content' WHERE subject_type NOT LIKE 'text-%'")
    db.execute('DROP INDEX IF EXISTS correction_open_subject')
    db.execute("""CREATE UNIQUE INDEX correction_open_component ON corrections(subject_type, subject_id, component)
        WHERE status NOT IN ('applied','closed')""")
    db.execute("INSERT INTO metadata VALUES ('correction-scope-columns-v1', '1')")


def _publication_links(db, task):
    published = db.execute("SELECT * FROM correction_events WHERE correction_id=? AND kind='applied'",
                           (task['id'],)).fetchone()
    if not published:
        return []
    accept = db.execute("""SELECT * FROM correction_events WHERE correction_id=? AND kind='accept'
        ORDER BY rowid DESC LIMIT 1""", (task['id'],)).fetchone()
    proposal = db.execute("""SELECT * FROM correction_proposals WHERE correction_id=?
        ORDER BY version DESC LIMIT 1""", (task['id'],)).fetchone()
    removed = []
    for file in json.loads(proposal['files_json']):
        before, after = json.loads(file['before']), json.loads(file['after'])
        rows = db.execute("""SELECT c.*,e.subject_type,e.subject_id,e.revision AS subject_revision
            FROM review_components c JOIN review_events e ON e.id=c.event_id
            JOIN review_subjects s ON s.subject_type=e.subject_type AND s.subject_id=e.subject_id AND s.revision=e.revision
            WHERE s.source=? AND e.decision='revoked' AND e.actor_uid=? AND e.created_at>=? AND e.created_at<=?
                AND e.note='Correctie gepubliceerd; de gewijzigde versie moet opnieuw worden geverifieerd.'""",
            (file['path'], accept['actor_uid'], accept['created_at'], published['created_at'])).fetchall()
        for row in rows:
            after_payload = subject_payload(row['subject_type'], row['subject_id'], after)
            if row['subject_revision'] != canonical_hash(after_payload):
                continue  # Another publication may have happened between acceptance and this publication.
            before_parts = component_metadata(row['subject_type'], subject_payload(row['subject_type'], row['subject_id'], before))
            after_parts = component_metadata(row['subject_type'], after_payload)
            key = row['component']
            if before_parts[key]['revision'] == after_parts[key]['revision']:
                removed.append({key: row[key] for key in ('event_id', 'component', 'revision', 'members_json')})
    return removed


def migrate_reviews(db, timestamp):
    """Remove only automatic, over-broad revocation links; never create approvals.

    The original immutable events stay intact. Removed component links are
    retained in an explicit task migration event, including their fingerprints.
    This runs after the whole-item → component-review migration, in its transaction.
    """
    if db.execute("SELECT 1 FROM metadata WHERE key='correction-review-scopes-v1'").fetchone():
        return
    db.execute('DROP TRIGGER immutable_components_delete')
    for task in db.execute('SELECT * FROM corrections').fetchall():
        removed = []
        requests = db.execute("""SELECT * FROM correction_events WHERE correction_id=?
            AND kind IN ('requested','rebased') ORDER BY rowid""", (task['id'],)).fetchall()
        for request in requests:
            rows = db.execute("""SELECT c.* FROM review_components c JOIN review_events e ON e.id=c.event_id
                JOIN review_subjects s ON s.subject_type=e.subject_type AND s.subject_id=e.subject_id
                    AND s.revision=e.revision
                WHERE e.decision='revoked' AND e.note=? AND e.actor_uid=?
                    AND e.created_at>=? AND e.created_at<=? AND s.source=?
                    AND (s.subject_type='text-chapter' OR ?='text-chapter'
                         OR (s.subject_type=? AND s.subject_id=?)) AND c.component!=?""",
                ('Aanpassing aangevraagd: ' + request['note'], request['actor_uid'],
                 task['created_at'], request['created_at'], task['source'], task['subject_type'],
                 task['subject_type'], task['subject_id'], task['component'])).fetchall()
            for row in rows:
                removed.append(dict(row))
                db.execute('DELETE FROM review_components WHERE event_id=? AND component=?',
                           (row['event_id'], row['component']))
        for row in _publication_links(db, task):
            removed.append(row)
            db.execute('DELETE FROM review_components WHERE event_id=? AND component=?',
                       (row['event_id'], row['component']))
        db.execute('INSERT INTO correction_events VALUES (?,?,?,?,?,?,?)',
                   (str(uuid.uuid4()), task['id'], 'scope-migrated',
                    'Aanvraag gekoppeld aan één onderdeel; onterechte intrekkingen van andere onderdelen hersteld.',
                    None, json.dumps({'component': task['component'], 'removedReviewComponents': removed}), timestamp))
    db.execute("""CREATE TRIGGER immutable_components_delete BEFORE DELETE ON review_components
        BEGIN SELECT RAISE(ABORT, 'Immutable component review'); END""")
    db.execute("INSERT INTO metadata VALUES ('correction-review-scopes-v1', '1')")
