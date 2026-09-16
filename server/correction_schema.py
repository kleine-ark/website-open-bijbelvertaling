"""Additive correction workflow schema, also installed on existing databases."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS corrections (
    id TEXT PRIMARY KEY,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    revision TEXT NOT NULL,
    source TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    label TEXT NOT NULL,
    href TEXT NOT NULL,
    reason TEXT NOT NULL,
    before_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('requested','proposed','accepted','applied','closed')),
    version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS correction_open_subject
    ON corrections(subject_type, subject_id) WHERE status NOT IN ('applied','closed');
CREATE INDEX IF NOT EXISTS correction_source ON corrections(source, status);
CREATE TABLE IF NOT EXISTS correction_proposals (
    id TEXT PRIMARY KEY,
    correction_id TEXT NOT NULL REFERENCES corrections(id),
    version INTEGER NOT NULL,
    summary TEXT NOT NULL,
    files_json TEXT NOT NULL,
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL,
    revision TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(correction_id, version)
);
CREATE TABLE IF NOT EXISTS correction_events (
    id TEXT PRIMARY KEY,
    correction_id TEXT NOT NULL REFERENCES corrections(id),
    kind TEXT NOT NULL,
    note TEXT NOT NULL,
    actor_uid TEXT REFERENCES users(uid),
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS correction_events_task ON correction_events(correction_id);
CREATE TRIGGER IF NOT EXISTS immutable_correction_events_update
    BEFORE UPDATE ON correction_events BEGIN SELECT RAISE(ABORT, 'Immutable correction audit'); END;
CREATE TRIGGER IF NOT EXISTS immutable_correction_events_delete
    BEFORE DELETE ON correction_events BEGIN SELECT RAISE(ABORT, 'Immutable correction audit'); END;
CREATE TRIGGER IF NOT EXISTS immutable_correction_proposals_update
    BEFORE UPDATE ON correction_proposals BEGIN SELECT RAISE(ABORT, 'Immutable proposal'); END;
CREATE TRIGGER IF NOT EXISTS immutable_correction_proposals_delete
    BEFORE DELETE ON correction_proposals BEGIN SELECT RAISE(ABORT, 'Immutable proposal'); END;
"""


def open_correction(db, subject):
    """Chapter/verse decisions overlap; different locations do not."""
    return db.execute("""SELECT id FROM corrections WHERE status NOT IN ('applied','closed')
        AND source=? AND (subject_type='text-chapter' OR ?='text-chapter'
                          OR (subject_type=? AND subject_id=?)) LIMIT 1""",
        (subject['source'], subject['subject_type'], subject['subject_type'], subject['subject_id'])).fetchone()
