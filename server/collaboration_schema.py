"""SQLite schema and versioned migrations for stable collaboration accounts."""
import hashlib
from correction_schema import SCHEMA as CORRECTION_SCHEMA
from component_reviews import SCHEMA as COMPONENT_SCHEMA
import correction_scope

HISTORICAL_REVIEWER_EMAIL = "maartenvroegindeweij@gmail.com"
HISTORICAL_REVIEWER_NAME = "Maarten Vroegindeweij"

SCHEMA = """
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS users (
    uid TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    display_name TEXT NOT NULL,
    photo_url TEXT,
    roles_json TEXT NOT NULL DEFAULT '[]',
    registered INTEGER NOT NULL DEFAULT 1,
    bootstrap INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS role_events (
    id TEXT PRIMARY KEY,
    target_uid TEXT NOT NULL,
    target_email TEXT NOT NULL,
    target_name TEXT NOT NULL,
    roles_json TEXT NOT NULL,
    actor_uid TEXT NOT NULL,
    actor_email TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS review_subjects (
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    revision TEXT NOT NULL,
    label TEXT NOT NULL,
    href TEXT NOT NULL,
    source TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (subject_type, subject_id, revision)
);
CREATE TABLE IF NOT EXISTS review_events (
    id TEXT PRIMARY KEY,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    revision TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('approved', 'revoked')),
    note TEXT NOT NULL,
    actor_kind TEXT NOT NULL CHECK(actor_kind IN ('user', 'historical-import')),
    actor_uid TEXT,
    actor_email TEXT,
    actor_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(subject_type, subject_id, revision)
      REFERENCES review_subjects(subject_type, subject_id, revision)
);
CREATE INDEX IF NOT EXISTS review_events_subject
  ON review_events(subject_type, subject_id, revision, created_at DESC);
CREATE TRIGGER IF NOT EXISTS immutable_role_events_update
  BEFORE UPDATE ON role_events BEGIN
    SELECT RAISE(ABORT, 'role_events are immutable');
  END;
CREATE TRIGGER IF NOT EXISTS immutable_role_events_delete
  BEFORE DELETE ON role_events BEGIN
    SELECT RAISE(ABORT, 'role_events are immutable');
  END;
CREATE TRIGGER IF NOT EXISTS immutable_review_events_update
  BEFORE UPDATE ON review_events BEGIN
    SELECT RAISE(ABORT, 'review_events are immutable');
  END;
CREATE TRIGGER IF NOT EXISTS immutable_review_events_delete
  BEFORE DELETE ON review_events BEGIN
    SELECT RAISE(ABORT, 'review_events are immutable');
  END;
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def initialize_database(db, bootstrap_admins, administrator_roles, timestamp):
    db.executescript(SCHEMA + CORRECTION_SCHEMA + COMPONENT_SCHEMA)
    db.execute("BEGIN IMMEDIATE")
    db.execute("INSERT OR IGNORE INTO metadata VALUES ('corrections-v1', ?)", (timestamp,))
    correction_scope.initialize(db)
    identity_version = db.execute(
        "SELECT 1 FROM metadata WHERE key='account-identity-v1'"
    ).fetchone()
    if not identity_version:
        db.execute("ALTER TABLE users ADD COLUMN firebase_uid TEXT")
        db.execute("UPDATE users SET firebase_uid=uid WHERE registered=1")
        db.execute("CREATE UNIQUE INDEX users_firebase_uid ON users(firebase_uid)")
        db.execute("INSERT INTO metadata VALUES ('account-identity-v1', ?)", (timestamp,))

    for email in sorted(bootstrap_admins | {HISTORICAL_REVIEWER_EMAIL}):
        uid = "pending:" + hashlib.sha256(email.encode()).hexdigest()[:24]
        name = HISTORICAL_REVIEWER_NAME if email == HISTORICAL_REVIEWER_EMAIL else email
        db.execute(
            """INSERT OR IGNORE INTO users
               (uid, email, display_name, roles_json, registered, bootstrap, created_at, last_seen_at)
               VALUES (?, ?, ?, ?, 0, ?, ?, ?)""",
            (uid, email, name, administrator_roles if email in bootstrap_admins else "[]",
             int(email in bootstrap_admins), timestamp, timestamp),
        )

    if db.execute("SELECT 1 FROM metadata WHERE key='historical-review-attribution-v3'").fetchone():
        return
    # Only this versioned data migration may repair old audit references. The
    # triggers are restored inside the same transaction, before any API is served.
    for table in ("role_events", "review_events"):
        db.execute(f"DROP TRIGGER immutable_{table}_update")
    db.execute(
        "UPDATE users SET display_name=? WHERE email=? AND registered=0",
        (HISTORICAL_REVIEWER_NAME, HISTORICAL_REVIEWER_EMAIL),
    )
    maarten = db.execute("SELECT * FROM users WHERE email=?", (HISTORICAL_REVIEWER_EMAIL,)).fetchone()
    db.execute(
        """UPDATE review_events SET actor_uid=?, actor_email=?, actor_name=?
           WHERE actor_kind='historical-import'""",
        (maarten["uid"], maarten["email"], HISTORICAL_REVIEWER_NAME),
    )
    # Earlier sign-in replaced placeholder user rows; repair references to those
    # deleted IDs once. From now on account IDs never change during sign-in.
    for table, prefix in (("role_events", "target"), ("role_events", "actor"), ("review_events", "actor")):
        db.execute(
            f"""UPDATE {table} SET {prefix}_uid=(
                    SELECT uid FROM users WHERE email={table}.{prefix}_email COLLATE NOCASE
                ) WHERE {prefix}_uid NOT IN (SELECT uid FROM users)"""
        )
        orphan = db.execute(
            f"""SELECT 1 FROM {table} WHERE {prefix}_uid IS NULL
                OR {prefix}_uid NOT IN (SELECT uid FROM users) LIMIT 1"""
        ).fetchone()
        if orphan:
            raise RuntimeError(f"Cannot migrate unresolved {table}.{prefix}_uid")
    for table in ("role_events", "review_events"):
        db.execute(
            f"""CREATE TRIGGER immutable_{table}_update BEFORE UPDATE ON {table} BEGIN
                  SELECT RAISE(ABORT, '{table} are immutable');
                END"""
        )
    db.execute("INSERT INTO metadata VALUES ('historical-review-attribution-v3', ?)", (timestamp,))
