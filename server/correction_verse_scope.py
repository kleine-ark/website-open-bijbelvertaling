"""One-time repair of chapter withdrawals made on behalf of individual verses.

Keep the original event, actor and ordering. Its component coverage is narrowed
to the actual verses, so later individual decisions continue to take precedence.
"""
import json
import uuid

from review_components import component_metadata
from review_content import canonical_hash, subject_payload


def _requests(db):
    result = []
    for row in db.execute("""SELECT e.*,e.rowid AS sequence,t.subject_type,t.subject_id,t.component,
        t.created_at AS requested_at FROM correction_events e JOIN corrections t ON t.id=e.correction_id
        WHERE e.kind IN ('requested','rebased') AND t.subject_type LIKE 'text-%' AND t.component!='custom'
        ORDER BY e.rowid"""):
        data = json.loads(row['data_json'])
        result.append({**dict(row), 'data': data,
                       'parts': component_metadata(row['subject_type'], data['before'])})
    return result


def _requested_coverage(row, requests):
    members = json.loads(row['members_json'])
    candidates = []
    for request in requests:
        parent = request['subject_id'] if request['subject_type'] == 'text-chapter' else request['subject_id'].rsplit('/', 1)[0]
        if parent != row['subject_id'] or request['component'] != row['component']:
            continue
        data = request['data']
        if 'reviewEventIds' in data:
            matches = row['event_id'] in data['reviewEventIds']
        else:
            matches = (row['actor_uid'] == request['actor_uid']
                       and row['note'] == 'Aanpassing aangevraagd: ' + request['note']
                       and request['requested_at'] <= row['created_at'] <= request['created_at'])
        if matches:
            candidates.append(request)
    if not candidates:
        return None  # Ordinary chapter withdrawals are not correction side effects.
    types = {request['subject_type'] for request in candidates}
    if len(types) > 1:
        raise RuntimeError('Ambiguous historical chapter/verse correction withdrawal: ' + row['event_id'])
    origin = candidates[0]
    if origin['subject_type'] == 'text-chapter':
        return None  # A deliberate chapter request really does cover the chapter.
    selected = {}
    for request in requests:
        if (request['subject_type'] != 'text-verse' or request['component'] != row['component']
                or request['subject_id'].rsplit('/', 1)[0] != row['subject_id']
                or request['sequence'] < origin['sequence']):
            continue
        number = request['subject_id'].rsplit('/', 1)[1]
        revision = request['parts'][row['component']]['revision']
        if members.get(number) == revision:
            # A later request may have recorded no new withdrawal because this
            # earlier chapter withdrawal had already made its verse pending.
            selected[number] = revision
    number = origin['subject_id'].rsplit('/', 1)[1]
    if number not in selected:
        raise RuntimeError('Correction snapshot differs from original withdrawal: ' + row['event_id'])
    return origin['correction_id'], selected


def _publications(db):
    result = []
    for task in db.execute("""SELECT t.*,e.created_at AS published_at
        FROM corrections t JOIN correction_events e ON e.correction_id=t.id WHERE e.kind='applied'"""):
        accept = db.execute("""SELECT * FROM correction_events WHERE correction_id=? AND kind='accept'
            ORDER BY rowid DESC LIMIT 1""", (task['id'],)).fetchone()
        proposal = db.execute("""SELECT * FROM correction_proposals WHERE correction_id=?
            ORDER BY version DESC LIMIT 1""", (task['id'],)).fetchone()
        for file in json.loads(proposal['files_json']):
            if file['path'].endswith('.geojson'):
                continue
            result.append({'task': dict(task), 'accept': dict(accept), 'file': file})
    return result


def _published_coverage(row, publications):
    if row['note'] != 'Correctie gepubliceerd; de gewijzigde versie moet opnieuw worden geverifieerd.':
        return None
    for publication in publications:
        task, accept, file = (publication[key] for key in ('task', 'accept', 'file'))
        if (file['path'] != row['source'] or row['actor_uid'] != accept['actor_uid']
                or not accept['created_at'] <= row['created_at'] <= task['published_at']):
            continue
        after = subject_payload('text-chapter', row['subject_id'], json.loads(file['after']))
        if canonical_hash(after) != row['subject_revision']:
            continue
        before = subject_payload('text-chapter', row['subject_id'], json.loads(file['before']))
        key = row['component']
        old = component_metadata('text-chapter', before)[key]['members']
        new = component_metadata('text-chapter', after)[key]['members']
        selected = {number: revision for number, revision in new.items() if old[number] != revision}
        if not selected:
            raise RuntimeError('Unchanged publication component survived scope migration: ' + row['event_id'])
        return task['id'], selected
    return None


def migrate(db, timestamp):
    if db.execute("SELECT 1 FROM metadata WHERE key='correction-verse-scopes-v1'").fetchone():
        return
    requests, publications = _requests(db), _publications(db)
    rows = db.execute("""SELECT c.*,e.subject_id,e.revision AS subject_revision,e.note,e.actor_uid,e.created_at,s.source
        FROM review_components c JOIN review_events e ON e.id=c.event_id
        JOIN review_subjects s ON s.subject_type=e.subject_type AND s.subject_id=e.subject_id AND s.revision=e.revision
        WHERE e.subject_type='text-chapter' AND e.decision='revoked' AND c.component!='intro' AND c.scope='subject'
        ORDER BY e.rowid""").fetchall()
    repairs = {}
    db.execute('DROP TRIGGER immutable_components_update')
    for row in rows:
        coverage = _requested_coverage(row, requests) or _published_coverage(row, publications)
        if coverage is None:
            continue
        task_id, members = coverage
        repairs.setdefault(task_id, []).append({
            'eventId': row['event_id'], 'component': row['component'],
            'before': {'scope': row['scope'], 'members': json.loads(row['members_json'])},
            'after': {'scope': 'verses', 'members': members},
        })
        db.execute("UPDATE review_components SET scope='verses',members_json=? WHERE event_id=? AND component=?",
                   (json.dumps(members), row['event_id'], row['component']))
    for task_id, changes in repairs.items():
        db.execute('INSERT INTO correction_events VALUES (?,?,?,?,?,?,?)',
            (str(uuid.uuid4()), task_id, 'verse-scope-migrated',
             'Intrekkingen beperkt tot de betrokken verzen; overige versverificaties hersteld.',
             None, json.dumps({'changes': changes}), timestamp))
    db.execute("""CREATE TRIGGER immutable_components_update BEFORE UPDATE ON review_components
        BEGIN SELECT RAISE(ABORT, 'Immutable component review'); END""")
    db.execute("INSERT INTO metadata VALUES ('correction-verse-scopes-v1', '1')")
