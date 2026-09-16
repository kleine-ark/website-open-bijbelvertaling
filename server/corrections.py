"""Reviewer-controlled corrections; proposal production is an explicit operator action."""
import difflib
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from collaboration_errors import Conflict, InvalidRequest, NotFound
from correction_files import data_path, validate_files
from review_content import canonical_hash, subject_payload

STATES = ('requested', 'proposed', 'accepted', 'applied', 'closed')
OPEN = ('requested', 'proposed', 'accepted')


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def reason(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise InvalidRequest()
    return value.strip()


def event(db, task_id, kind, note='', actor=None, data=None):
    db.execute('INSERT INTO correction_events VALUES (?, ?, ?, ?, ?, ?, ?)',
               (str(uuid.uuid4()), task_id, kind, note, actor['uid'] if actor else None,
                encoded(data or {}), timestamp()))


class Corrections:
    def __init__(self, store, content_root):
        self.store = store
        self.root = Path(content_root)

    def _task(self, db, identifier):
        row = db.execute('SELECT * FROM corrections WHERE id=?', (identifier,)).fetchone()
        if not row:
            raise NotFound()
        return row

    def _subject(self, db, kind, identifier):
        row = db.execute('SELECT * FROM review_subjects WHERE subject_type=? AND subject_id=? AND active=1',
                         (kind, identifier)).fetchone()
        if not row:
            raise NotFound()
        return row

    def _snapshot(self, subject):
        raw = data_path(self.root, subject['source']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != json.loads(subject['metadata_json'])['sourceHash']:
            raise Conflict()
        snapshot = subject_payload(subject['subject_type'], subject['subject_id'], json.loads(raw))
        if canonical_hash(snapshot) != subject['revision']:
            raise Conflict()
        return snapshot

    def _latest(self, db, task):
        return db.execute('SELECT * FROM correction_proposals WHERE correction_id=? ORDER BY version DESC LIMIT 1',
                          (task['id'],)).fetchone()

    def _current(self, db, task):
        subject = self._subject(db, task['subject_type'], task['subject_id'])
        if subject['revision'] != task['revision']:
            raise Conflict()
        self._snapshot(subject)
        return subject

    def _revoke_affected(self, db, subject, actor, note):
        affected = db.execute('''SELECT * FROM review_subjects WHERE active=1 AND source=?
            AND (subject_type='text-chapter' OR ?='text-chapter'
                 OR (subject_type=? AND subject_id=?))''',
            (subject['source'], subject['subject_type'], subject['subject_type'], subject['subject_id'])).fetchall()
        self._revoke_rows(db, affected, actor, 'Aanpassing aangevraagd: ' + note)

    def _revoke_rows(self, db, rows, actor, note):
        for row in rows:
            latest = db.execute('''SELECT decision FROM review_events WHERE subject_type=? AND subject_id=?
                AND revision=? ORDER BY (actor_kind='user') DESC, rowid DESC LIMIT 1''',
                (row['subject_type'], row['subject_id'], row['revision'])).fetchone()
            if latest and latest['decision'] == 'approved':
                db.execute('''INSERT INTO review_events
                    (id,subject_type,subject_id,revision,decision,note,actor_kind,actor_uid,actor_email,actor_name,created_at)
                    VALUES (?,?,?,?,'revoked',?,'user',?,?,?,?)''',
                    (str(uuid.uuid4()), row['subject_type'], row['subject_id'], row['revision'],
                     note, actor['uid'], actor['email'], actor['displayName'], timestamp()))

    def create(self, actor, payload):
        self.store._require_role(actor, 'reviewer')
        if set(payload) != {'subjectType', 'subjectId', 'revision', 'sourceHash', 'reason'}:
            raise InvalidRequest()
        note = reason(payload['reason'])
        with self.store.catalog_lock, self.store._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self.store._require_role(actor, 'reviewer')
            subject = self._subject(db, payload['subjectType'], payload['subjectId'])
            if (subject['revision'] != payload['revision'] or
                    json.loads(subject['metadata_json'])['sourceHash'] != payload['sourceHash']):
                raise Conflict()
            if db.execute("SELECT 1 FROM corrections WHERE subject_type=? AND subject_id=? AND status NOT IN ('applied','closed')",
                          (payload['subjectType'], payload['subjectId'])).fetchone():
                raise Conflict()
            before = self._snapshot(subject)
            identifier, now = str(uuid.uuid4()), timestamp()
            db.execute('INSERT INTO corrections VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (identifier, subject['subject_type'], subject['subject_id'], subject['revision'],
                 subject['source'], payload['sourceHash'], subject['label'], subject['href'], note,
                 encoded(before), 'requested', 1, now, now))
            self._revoke_affected(db, subject, actor, note)
            event(db, identifier, 'requested', note, actor, {'revision': subject['revision'], 'before': before})
        return self.get(actor, identifier)

    def _present(self, db, task, actor=None, detail=True, artifact=False):
        subject = db.execute('SELECT * FROM review_subjects WHERE subject_type=? AND subject_id=? AND active=1',
                             (task['subject_type'], task['subject_id'])).fetchone()
        result = {key: task[key] for key in ('id', 'label', 'href', 'reason', 'status', 'version', 'revision', 'source')}
        result.update(subjectType=task['subject_type'], subjectId=task['subject_id'],
                      createdAt=task['created_at'], updatedAt=task['updated_at'],
                      stale=task['status'] in OPEN and (not subject or subject['revision'] != task['revision']))
        if not detail:
            return result
        result['before'] = json.loads(task['before_json'])
        result['proposals'] = []
        for proposal in db.execute('SELECT * FROM correction_proposals WHERE correction_id=? ORDER BY version', (task['id'],)):
            files = json.loads(proposal['files_json'])
            item = {key: proposal[key] for key in ('id', 'version', 'summary', 'revision')}
            item.update(before=json.loads(proposal['before_json']), after=json.loads(proposal['after_json']))
            if artifact:
                item['files'] = files
            else:
                item['diffs'] = [{
                    'path': f['path'], 'diff': '\n'.join(difflib.unified_diff(
                        json.dumps(json.loads(f['before']), ensure_ascii=False, indent=2, sort_keys=True).splitlines(),
                        json.dumps(json.loads(f['after']), ensure_ascii=False, indent=2, sort_keys=True).splitlines(),
                        fromfile='Oorspronkelijk', tofile='Voorstel', lineterm='')),
                } for f in files]
            result['proposals'].append(item)
        result['proposal'] = result['proposals'][-1] if result['proposals'] else None
        if task['status'] in ('proposed', 'accepted') and not result['stale']:
            try:
                validate_files(self.root, json.loads(self._latest(db, task)['files_json']))
            except (ValueError, OSError):
                result['stale'] = True
        result['events'] = []
        for row in db.execute('''SELECT e.*, u.display_name, u.email FROM correction_events e
                LEFT JOIN users u ON u.uid=e.actor_uid WHERE correction_id=? ORDER BY e.rowid''', (task['id'],)):
            item = {'kind': row['kind'], 'note': row['note'], 'createdAt': row['created_at']}
            if actor and 'administrator' in actor['roles'] and row['actor_uid']:
                item['actor'] = {'uid': row['actor_uid'], 'displayName': row['display_name'], 'email': row['email']}
            result['events'].append(item)
        return result

    def get(self, actor, identifier):
        actor = self.store._require_role(actor, 'reviewer')
        with self.store._connect() as db:
            return self._present(db, self._task(db, identifier), actor)

    def list(self, actor, status='', query='', offset=0, limit=50):
        actor = self.store._require_role(actor, 'reviewer')
        if status and status not in STATES:
            raise InvalidRequest()
        offset, limit = max(0, offset), min(100, max(1, limit))
        clauses, values = [], []
        if status:
            clauses.append('status=?')
            values.append(status)
        if query:
            clauses.append('(label LIKE ? OR reason LIKE ?)')
            values.extend(['%' + query[:200] + '%'] * 2)
        where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
        with self.store._connect() as db:
            total = db.execute('SELECT count(*) FROM corrections' + where, values).fetchone()[0]
            rows = db.execute('SELECT * FROM corrections' + where + ' ORDER BY rowid DESC LIMIT ? OFFSET ?',
                              values + [limit, offset]).fetchall()
            return {'total': total, 'items': [self._present(db, row, actor, detail=False) for row in rows]}

    def propose(self, payload):
        """Private CLI only; no HTTP endpoint can impersonate the proposal producer."""
        if set(payload) != {'id', 'version', 'summary', 'files'}:
            raise InvalidRequest()
        summary = reason(payload['summary'])
        with self.store.catalog_lock, self.store._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            task = self._task(db, payload['id'])
            if task['status'] != 'requested' or task['version'] != payload['version']:
                raise Conflict()
            self._current(db, task)
            files = validate_files(self.root, payload['files'])
            for file in files:
                source_subject = db.execute('SELECT subject_type FROM review_subjects WHERE source=? AND active=1 LIMIT 1',
                                            (file['path'],)).fetchone()
                if source_subject:
                    before, after = json.loads(file['before']), json.loads(file['after'])
                    if source_subject['subject_type'] == 'location':
                        identities = lambda doc: [f['properties']['id'] for f in doc['features']]
                    else:
                        identities = lambda doc: [doc['number'], [v['number'] for v in doc['verses']]]
                    if identities(before) != identities(after):
                        raise ValueError('A correction cannot add, remove or renumber review subjects')
            target = next((f for f in files if f['path'] == task['source']), None)
            if target is None:
                raise InvalidRequest()
            after = subject_payload(task['subject_type'], task['subject_id'], json.loads(target['after']))
            revision = canonical_hash(after)
            if revision == task['revision']:
                raise InvalidRequest()
            version = task['version'] + 1
            db.execute('INSERT INTO correction_proposals VALUES (?,?,?,?,?,?,?,?,?)',
                (str(uuid.uuid4()), task['id'], version, summary, encoded(files),
                 task['before_json'], encoded(after), revision, timestamp()))
            db.execute("UPDATE corrections SET status='proposed',version=?,updated_at=? WHERE id=?",
                       (version, timestamp(), task['id']))
            event(db, task['id'], 'proposed', summary)
            return self._present(db, self._task(db, task['id']))

    def decide(self, actor, identifier, payload):
        self.store._require_role(actor, 'reviewer')
        if (set(payload) != {'version', 'action', 'note'} or type(payload['version']) is not int
                or payload['action'] not in ('accept', 'return', 'rebase', 'close')):
            raise InvalidRequest()
        action = payload['action']
        note = reason(payload['note']) if action != 'accept' else ''
        with self.store.catalog_lock, self.store._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = self.store._require_role(actor, 'reviewer')
            task = self._task(db, identifier)
            if task['version'] != payload['version'] or task['status'] not in OPEN:
                raise Conflict()
            if task['status'] == 'accepted' and not self._present(db, task)['stale']:
                # Acceptance authorizes the manual publication. Only a conflicting
                # source update can invalidate it before that publication finishes.
                raise Conflict()
            if action in ('accept', 'return') and task['status'] != 'proposed':
                raise Conflict()
            if action == 'accept':
                self._current(db, task)
                try:
                    validate_files(self.root, json.loads(self._latest(db, task)['files_json']))
                except (ValueError, OSError) as error:
                    raise Conflict() from error
            if action == 'rebase':
                subject = self._subject(db, task['subject_type'], task['subject_id'])
                before = self._snapshot(subject)
                db.execute('''UPDATE corrections SET revision=?,source_hash=?,before_json=? WHERE id=?''',
                           (subject['revision'], json.loads(subject['metadata_json'])['sourceHash'], encoded(before), identifier))
                self._revoke_affected(db, subject, actor, note)
                event(db, identifier, 'rebased', note, actor, {'revision': subject['revision'], 'before': before})
            else:
                event(db, identifier, action, note, actor, {'proposalVersion': task['version']})
            state = {'accept': 'accepted', 'return': 'requested', 'close': 'closed', 'rebase': 'requested'}[action]
            db.execute('UPDATE corrections SET status=?,version=version+1,updated_at=? WHERE id=?',
                       (state, timestamp(), identifier))
        return self.get(actor, identifier)

    def export(self, status='requested', identifier=''):
        """Local operator artifact: includes data, feedback, versions, never account identities."""
        if status not in STATES:
            raise InvalidRequest()
        with self.store._connect() as db:
            rows = db.execute('SELECT * FROM corrections WHERE status=? ORDER BY rowid', (status,)).fetchall()
            if identifier and not any(row['id'] == identifier for row in rows):
                raise NotFound()
            return {'schemaVersion': 1, 'items': [self._present(db, row, artifact=True)
                    for row in rows if not identifier or row['id'] == identifier]}

    def reconcile(self):
        """Publication is only complete after every accepted file and catalog revision is live."""
        with self.store._connect() as db:
            if not db.execute("SELECT 1 FROM corrections WHERE status='accepted' LIMIT 1").fetchone():
                return
        with self.store.catalog_lock, self.store._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            rows = db.execute("SELECT * FROM corrections WHERE status='accepted'").fetchall()
            for task in rows:
                proposal = self._latest(db, task)
                current = db.execute('''SELECT revision FROM review_subjects
                    WHERE subject_type=? AND subject_id=? AND active=1''',
                    (task['subject_type'], task['subject_id'])).fetchone()
                if not current or current['revision'] != proposal['revision']:
                    continue
                try:
                    validate_files(self.root, json.loads(proposal['files_json']), expected='after')
                except (ValueError, OSError):
                    continue  # A deployment may still be copying the other accepted files.
                # Reusing a previously approved text is still a new correction
                # publication: it must not resurrect an old approval automatically.
                acceptance = db.execute("SELECT actor_uid FROM correction_events WHERE correction_id=? AND kind='accept' ORDER BY rowid DESC LIMIT 1",
                                        (task['id'],)).fetchone()
                acceptor = self.store._row_to_user(db.execute('SELECT * FROM users WHERE uid=?', (acceptance['actor_uid'],)).fetchone())
                changed = []
                for file in json.loads(proposal['files_json']):
                    before_document = json.loads(file['before'])
                    for row in db.execute('SELECT * FROM review_subjects WHERE active=1 AND source=?', (file['path'],)):
                        before_revision = canonical_hash(subject_payload(row['subject_type'], row['subject_id'], before_document))
                        if before_revision != row['revision']:
                            changed.append(row)
                self._revoke_rows(db, changed, acceptor, 'Correctie gepubliceerd; de gewijzigde versie moet opnieuw worden geverifieerd.')
                db.execute("UPDATE corrections SET status='applied',version=version+1,updated_at=? WHERE id=?",
                           (timestamp(), task['id']))
                event(db, task['id'], 'applied', data={'revision': proposal['revision']})
