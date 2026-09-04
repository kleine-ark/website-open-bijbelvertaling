#!/usr/bin/env python3
"""Authenticated role and review API for Open Vertaling.

Firebase supplies signed Google identities. This service verifies those tokens
and stores only the collaboration directory, roles and immutable audit events.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import math
import mimetypes
import os
import re
import sqlite3
import ssl
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

PROJECT_ID = "open-vertaling"
CERTIFICATES_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)
ALLOWED_ROLES = {"administrator", "reviewer"}
MAX_BODY_BYTES = 64 * 1024
GENERIC_ERROR = "Er is een fout opgetreden. Controleer het logboek."

LOGGER = logging.getLogger("openvertaling.collaboration")


class ApiError(Exception):
    status = 400
    public_message = "Ongeldig verzoek."


class Unauthorized(ApiError):
    status = 401
    public_message = "Inloggen is vereist."


class Forbidden(ApiError):
    status = 403
    public_message = "Geen toegang."


class NotFound(ApiError):
    status = 404
    public_message = "Niet gevonden."


class Conflict(ApiError):
    status = 409
    public_message = "De gegevens zijn intussen gewijzigd. Laad de pagina opnieuw."


class InvalidRequest(ApiError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalized_email(value: object) -> str:
    email = str(value or "").strip().casefold()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise Unauthorized()
    return email


def decode_segment(segment: str) -> bytes:
    try:
        return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
    except Exception as error:
        raise Unauthorized() from error


def validate_token_claims(payload: dict, project_id: str, now: int | None = None) -> None:
    current = int(time.time()) if now is None else now
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject or len(subject) > 128:
        raise Unauthorized()
    if payload.get("aud") != project_id:
        raise Unauthorized()
    if payload.get("iss") != f"https://securetoken.google.com/{project_id}":
        raise Unauthorized()
    for field in ("iat", "auth_time", "exp"):
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise Unauthorized()
    if payload["exp"] <= current or payload["iat"] > current or payload["auth_time"] > current:
        raise Unauthorized()
    if payload.get("email_verified") is not True:
        raise Unauthorized()
    firebase = payload.get("firebase")
    if not isinstance(firebase, dict) or firebase.get("sign_in_provider") != "google.com":
        raise Unauthorized()
    normalized_email(payload.get("email"))


class FirebaseTokenVerifier:
    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.certificates = {}
        self.expires_at = 0.0
        self.lock = threading.Lock()

    def _refresh_certificates(self) -> None:
        request = urllib.request.Request(
            CERTIFICATES_URL, headers={"User-Agent": "openvertaling-collaboration/1"}
        )
        with urllib.request.urlopen(
            request, timeout=8, context=ssl.create_default_context()
        ) as response:
            certificates = json.loads(response.read().decode("utf-8"))
            cache_control = response.headers.get("Cache-Control", "")
        if not isinstance(certificates, dict) or not certificates:
            raise Unauthorized()
        match = re.search(r"max-age=(\d+)", cache_control)
        ttl = int(match.group(1)) if match else 300
        self.certificates = certificates
        self.expires_at = time.time() + max(60, min(ttl, 86400))

    def _certificate(self, key_id: str) -> str:
        with self.lock:
            if time.time() >= self.expires_at or key_id not in self.certificates:
                self._refresh_certificates()
            certificate = self.certificates.get(key_id)
        if not certificate:
            raise Unauthorized()
        return certificate

    def verify(self, token: str) -> dict:
        try:
            header_part, payload_part, signature_part = token.split(".")
            header = json.loads(decode_segment(header_part))
            payload_data = json.loads(decode_segment(payload_part))
            signature = decode_segment(signature_part)
        except (ValueError, json.JSONDecodeError) as error:
            raise Unauthorized() from error
        if not isinstance(header, dict) or not isinstance(payload_data, dict):
            raise Unauthorized()
        if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
            raise Unauthorized()
        certificate = x509.load_pem_x509_certificate(
            self._certificate(header["kid"]).encode("ascii")
        )
        try:
            certificate.public_key().verify(
                signature,
                f"{header_part}.{payload_part}".encode("ascii"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except Exception as error:
            raise Unauthorized() from error
        validate_token_claims(payload_data, self.project_id)
        return payload_data


def serialize_roles(roles: set[str] | list[str]) -> str:
    return json.dumps(sorted(set(roles)), separators=(",", ":"))


def parse_roles(value: str) -> list[str]:
    roles = json.loads(value or "[]")
    return sorted(role for role in roles if role in ALLOWED_ROLES)


def review_catalog_revision(catalog: dict) -> str:
    payload = {key: value for key, value in catalog.items() if key != "catalogRevision"}
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ReviewStore:
    def __init__(self, database_path: Path, bootstrap_admins: set[str]):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.bootstrap_admins = {normalized_email(email) for email in bootstrap_admins}
        self.catalog_lock = threading.Lock()
        self.catalog_file_lock = threading.Lock()
        self.catalog_file_stamp = None
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
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
            )
            for email in sorted(self.bootstrap_admins):
                pending_uid = "pending:" + hashlib.sha256(email.encode()).hexdigest()[:24]
                timestamp = now_iso()
                db.execute(
                    """INSERT OR IGNORE INTO users
                       (uid, email, display_name, roles_json, registered, bootstrap,
                        created_at, last_seen_at)
                       VALUES (?, ?, ?, ?, 0, 1, ?, ?)""",
                    (
                        pending_uid, email, email,
                        serialize_roles(ALLOWED_ROLES), timestamp, timestamp,
                    ),
                )

    def _row_to_user(self, row: sqlite3.Row) -> dict:
        roles = set(parse_roles(row["roles_json"]))
        if row["email"].casefold() in self.bootstrap_admins:
            roles.update(ALLOWED_ROLES)
        return {
            "uid": row["uid"],
            "email": row["email"],
            "displayName": row["display_name"],
            "photoURL": row["photo_url"],
            "roles": sorted(roles),
            "registered": bool(row["registered"]),
            "bootstrap": bool(row["bootstrap"]),
            "createdAt": row["created_at"],
            "lastSeenAt": row["last_seen_at"],
        }

    def upsert_user(self, claims: dict) -> dict:
        uid = str(claims["sub"])
        email = normalized_email(claims.get("email"))
        display_name = str(claims.get("name") or email).strip()[:200]
        photo_url = str(claims.get("picture") or "").strip()[:2000] or None
        timestamp = now_iso()
        with self._connect() as db:
            existing_email = db.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email,)
            ).fetchone()
            roles = set(parse_roles(existing_email["roles_json"])) if existing_email else set()
            created_at = existing_email["created_at"] if existing_email else timestamp
            if email in self.bootstrap_admins:
                roles.update(ALLOWED_ROLES)
            if existing_email and existing_email["uid"] != uid:
                db.execute("DELETE FROM users WHERE uid = ?", (existing_email["uid"],))
            db.execute(
                """INSERT INTO users
                   (uid, email, display_name, photo_url, roles_json, registered,
                    bootstrap, created_at, last_seen_at)
                   VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                   ON CONFLICT(uid) DO UPDATE SET
                     email=excluded.email, display_name=excluded.display_name,
                     photo_url=excluded.photo_url, roles_json=excluded.roles_json,
                     registered=1, bootstrap=excluded.bootstrap,
                     last_seen_at=excluded.last_seen_at""",
                (
                    uid, email, display_name, photo_url, serialize_roles(roles),
                    int(email in self.bootstrap_admins), created_at, timestamp,
                ),
            )
            row = db.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
        return self._row_to_user(row)

    @staticmethod
    def _require_role(actor: dict, role: str) -> None:
        if role not in actor.get("roles", []):
            raise Forbidden()

    def list_users(
        self, actor: dict, query: str = "", offset: int = 0, limit: int = 100,
    ) -> dict:
        self._require_role(actor, "administrator")
        needle = f"%{query.strip()[:200]}%"
        limit = max(1, min(int(limit), 100))
        offset = max(0, int(offset))
        with self._connect() as db:
            total = db.execute(
                """SELECT count(*) FROM users
                   WHERE display_name LIKE ? COLLATE NOCASE OR email LIKE ? COLLATE NOCASE""",
                (needle, needle),
            ).fetchone()[0]
            rows = db.execute(
                """SELECT * FROM users
                   WHERE display_name LIKE ? COLLATE NOCASE OR email LIKE ? COLLATE NOCASE
                   ORDER BY display_name COLLATE NOCASE, email COLLATE NOCASE
                   LIMIT ? OFFSET ?""",
                (needle, needle, limit, offset),
            ).fetchall()
        return {"total": total, "items": [self._row_to_user(row) for row in rows]}

    def set_roles(self, actor: dict, target_uid: str, roles: list[str]) -> dict:
        self._require_role(actor, "administrator")
        if not isinstance(roles, list) or any(role not in ALLOWED_ROLES for role in roles):
            raise InvalidRequest()
        roles = sorted(set(roles))
        if "administrator" in roles:
            roles = sorted(set(roles) | {"reviewer"})
        with self._connect() as db:
            target = db.execute("SELECT * FROM users WHERE uid = ?", (target_uid,)).fetchone()
            if not target:
                raise NotFound()
            if target["email"].casefold() in self.bootstrap_admins:
                roles = sorted(ALLOWED_ROLES)
            db.execute(
                "UPDATE users SET roles_json = ? WHERE uid = ?",
                (serialize_roles(roles), target_uid),
            )
            db.execute(
                """INSERT INTO role_events
                   (id, target_uid, target_email, target_name, roles_json,
                    actor_uid, actor_email, actor_name, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), target_uid, target["email"],
                    target["display_name"], serialize_roles(roles),
                    actor["uid"], actor["email"], actor["displayName"], now_iso(),
                ),
            )
            updated = db.execute("SELECT * FROM users WHERE uid = ?", (target_uid,)).fetchone()
        return self._row_to_user(updated)

    def list_role_events(self, actor: dict) -> list[dict]:
        self._require_role(actor, "administrator")
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM role_events ORDER BY created_at DESC, id DESC LIMIT 250"
            ).fetchall()
        return [{
            "id": row["id"], "targetUid": row["target_uid"],
            "targetEmail": row["target_email"],
            "targetDisplayName": row["target_name"],
            "roles": parse_roles(row["roles_json"]),
            "actor": {
                "uid": row["actor_uid"], "email": row["actor_email"],
                "displayName": row["actor_name"],
            },
            "createdAt": row["created_at"],
        } for row in rows]

    def sync_catalog_file(self, path: Path) -> None:
        with self.catalog_file_lock:
            try:
                catalog_path = Path(path)
                stat = catalog_path.stat()
                stamp = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
                if stamp == self.catalog_file_stamp:
                    return
                catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                LOGGER.exception("Reviewcatalogus kon niet worden gelezen")
                raise ApiError() from None
            self.sync_catalog(catalog)
            self.catalog_file_stamp = stamp

    def sync_catalog(self, catalog: dict) -> None:
        subject_types = catalog.get("subjectTypes")
        declared_revision = catalog.get("catalogRevision")
        if (
            catalog.get("schemaVersion") != 1
            or not isinstance(declared_revision, str)
            or not re.fullmatch(r"[a-f0-9]{64}", declared_revision)
            or declared_revision != review_catalog_revision(catalog)
            or not isinstance(subject_types, dict)
            or not subject_types
            or any(
                not isinstance(key, str) or not key
                or not isinstance(label, str) or not label
                for key, label in subject_types.items()
            )
            or not isinstance(catalog.get("subjects"), list)
        ):
            raise InvalidRequest()
        revision = declared_revision
        with self.catalog_lock, self._connect() as db:
            current = db.execute(
                "SELECT value FROM metadata WHERE key = 'catalog-revision'"
            ).fetchone()
            if current and current["value"] == revision:
                return
            db.execute("UPDATE review_subjects SET active = 0")
            for item in catalog["subjects"]:
                self._validate_subject(item)
                if item["type"] not in subject_types:
                    raise InvalidRequest()
                db.execute(
                    """INSERT INTO review_subjects
                       (subject_type, subject_id, revision, label, href, source,
                        metadata_json, active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                       ON CONFLICT(subject_type, subject_id, revision) DO UPDATE SET
                         label=excluded.label, href=excluded.href, source=excluded.source,
                         metadata_json=excluded.metadata_json, active=1""",
                    (
                        item["type"], item["id"], item["revision"], item["label"],
                        item["href"], item["source"],
                        json.dumps(item.get("metadata") or {}, separators=(",", ":")),
                    ),
                )
            imported = db.execute(
                "SELECT value FROM metadata WHERE key = 'historical-review-import-v1'"
            ).fetchone()
            if not imported:
                for item in catalog["subjects"]:
                    if item.get("publishedStatus") != "approved":
                        continue
                    db.execute(
                        """INSERT INTO review_events
                           (id, subject_type, subject_id, revision, decision, note,
                            actor_kind, actor_uid, actor_email, actor_name, created_at)
                           VALUES (?, ?, ?, ?, 'approved', ?, 'historical-import',
                                   NULL, NULL, ?, ?)""",
                        (
                            str(uuid.uuid4()), item["type"], item["id"], item["revision"],
                            "Bestaande status geïmporteerd uit " + item.get(
                                "migrationSource", "onbekende bron"
                            ),
                            "Onbekend (bestaande reviewstatus)", now_iso(),
                        ),
                    )
                db.execute(
                    "INSERT INTO metadata(key, value) VALUES ('historical-review-import-v1', ?)",
                    (now_iso(),),
                )
            db.execute(
                """INSERT INTO metadata(key, value) VALUES ('catalog-revision', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (revision,),
            )
            db.execute(
                """INSERT INTO metadata(key, value) VALUES ('subject-types', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (json.dumps(subject_types, ensure_ascii=False, separators=(",", ":")),),
            )

    @staticmethod
    def _validate_subject(item: dict) -> None:
        required = ("type", "id", "revision", "label", "href", "source")
        if any(not isinstance(item.get(key), str) or not item[key] for key in required):
            raise InvalidRequest()
        if not re.fullmatch(r"[a-f0-9]{64}", item["revision"]):
            raise InvalidRequest()
        if len(item["type"]) > 80 or len(item["id"]) > 300 or len(item["label"]) > 300:
            raise InvalidRequest()

    @staticmethod
    def _event(row: sqlite3.Row | None) -> dict | None:
        if not row:
            return None
        return {
            "id": row["id"], "decision": row["decision"], "note": row["note"],
            "actor": {
                "kind": row["actor_kind"], "uid": row["actor_uid"],
                "email": row["actor_email"], "displayName": row["actor_name"],
            },
            "createdAt": row["created_at"],
        }

    def _subject(self, db: sqlite3.Connection, row: sqlite3.Row) -> dict:
        event = db.execute(
            """SELECT * FROM review_events
               WHERE subject_type=? AND subject_id=? AND revision=?
               ORDER BY created_at DESC, rowid DESC LIMIT 1""",
            (row["subject_type"], row["subject_id"], row["revision"]),
        ).fetchone()
        latest = self._event(event)
        return {
            "type": row["subject_type"], "id": row["subject_id"],
            "revision": row["revision"], "label": row["label"],
            "href": row["href"], "source": row["source"],
            "metadata": json.loads(row["metadata_json"]),
            "status": "approved" if latest and latest["decision"] == "approved" else "pending",
            "latestReview": latest,
        }

    def list_subjects(
        self, actor: dict, subject_type: str = "", status: str = "",
        query: str = "", offset: int = 0, limit: int = 100,
    ) -> dict:
        self._require_role(actor, "reviewer")
        if status not in ("", "approved", "pending"):
            raise InvalidRequest()
        limit = max(1, min(int(limit), 100))
        offset = max(0, int(offset))
        sql = "SELECT * FROM review_subjects WHERE active = 1"
        values = []
        if subject_type:
            sql += " AND subject_type = ?"
            values.append(subject_type)
        if query:
            sql += " AND (label LIKE ? COLLATE NOCASE OR subject_id LIKE ? COLLATE NOCASE)"
            needle = f"%{query[:200]}%"
            values.extend((needle, needle))
        sql += " ORDER BY subject_type, label COLLATE NOCASE, subject_id"
        with self._connect() as db:
            items = [self._subject(db, row) for row in db.execute(sql, values).fetchall()]
            type_row = db.execute(
                "SELECT value FROM metadata WHERE key = 'subject-types'"
            ).fetchone()
        type_labels = json.loads(type_row["value"])
        for item in items:
            item["typeLabel"] = type_labels[item["type"]]
        if status:
            items = [item for item in items if item["status"] == status]
        return {
            "total": len(items),
            "items": items[offset:offset + limit],
            "types": [
                {"id": type_id, "label": label}
                for type_id, label in sorted(type_labels.items(), key=lambda pair: pair[1].casefold())
            ],
        }

    def record_review(self, actor: dict, payload: dict) -> dict:
        self._require_role(actor, "reviewer")
        subject_type = str(payload.get("subjectType") or "")
        subject_id = str(payload.get("subjectId") or "")
        revision = str(payload.get("revision") or "")
        decision = str(payload.get("decision") or "")
        note = str(payload.get("note") or "").strip()
        if decision not in ("approved", "revoked") or len(note) > 2000:
            raise InvalidRequest()
        with self._connect() as db:
            row = db.execute(
                """SELECT * FROM review_subjects
                   WHERE subject_type=? AND subject_id=? AND revision=? AND active=1""",
                (subject_type, subject_id, revision),
            ).fetchone()
            if not row:
                current = db.execute(
                    """SELECT 1 FROM review_subjects
                       WHERE subject_type=? AND subject_id=? AND active=1""",
                    (subject_type, subject_id),
                ).fetchone()
                if current:
                    raise Conflict()
                raise NotFound()
            db.execute(
                """INSERT INTO review_events
                   (id, subject_type, subject_id, revision, decision, note,
                    actor_kind, actor_uid, actor_email, actor_name, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'user', ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), subject_type, subject_id, revision, decision, note,
                    actor["uid"], actor["email"], actor["displayName"], now_iso(),
                ),
            )
            row = db.execute(
                """SELECT * FROM review_subjects
                   WHERE subject_type=? AND subject_id=? AND revision=?""",
                (subject_type, subject_id, revision),
            ).fetchone()
            return self._subject(db, row)

    def list_review_events(
        self, actor: dict, offset: int = 0, limit: int = 100,
    ) -> dict:
        self._require_role(actor, "reviewer")
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
        with self._connect() as db:
            total = db.execute("SELECT count(*) FROM review_events").fetchone()[0]
            rows = db.execute(
                """SELECT e.*, s.label FROM review_events e
                   JOIN review_subjects s USING(subject_type, subject_id, revision)
                   ORDER BY e.created_at DESC, e.rowid DESC LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()
        items = [{
            "id": row["id"], "subjectType": row["subject_type"],
            "subjectId": row["subject_id"], "revision": row["revision"],
            "label": row["label"], "decision": row["decision"],
            "note": row["note"], "actor": {
                "kind": row["actor_kind"], "uid": row["actor_uid"],
            "email": row["actor_email"], "displayName": row["actor_name"],
            }, "createdAt": row["created_at"],
        } for row in rows]
        return {"total": total, "items": items}


class CollaborationHandler(BaseHTTPRequestHandler):
    server_version = "OpenVertalingCollaboration/1"
    sys_version = ""

    def log_message(self, message: str, *args: object) -> None:
        LOGGER.info("%s - %s", self.client_address[0], message % args)

    @property
    def app(self):
        return self.server.app

    def _write_json(self, status: int, value: dict | list) -> None:
        body = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise InvalidRequest() from error
        if length < 0 or length > MAX_BODY_BYTES:
            raise InvalidRequest()
        try:
            value = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as error:
            raise InvalidRequest() from error
        if not isinstance(value, dict):
            raise InvalidRequest()
        return value

    def _actor(self) -> dict:
        authorization = self.headers.get("Authorization", "")
        if not authorization.startswith("Bearer ") or len(authorization) > 20000:
            raise Unauthorized()
        claims = self.app["verifier"].verify(authorization[7:])
        return self.app["store"].upsert_user(claims)

    def _route(self) -> tuple[str, dict[str, list[str]]]:
        parsed = urllib.parse.urlsplit(self.path)
        return parsed.path.rstrip("/") or "/", urllib.parse.parse_qs(parsed.query)

    def _sync_catalog(self) -> None:
        self.app["store"].sync_catalog_file(self.app["catalog_path"])

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Allow", "GET, POST, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        if not path.startswith("/api/collaboration") and self.app.get("static_root"):
            self._serve_static(path)
            return
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def do_PATCH(self) -> None:
        self._dispatch("PATCH")

    def _dispatch(self, method: str) -> None:
        try:
            path, query = self._route()
            if method == "GET" and path == "/api/collaboration/health":
                self._write_json(200, {"ok": True})
                return
            actor = self._actor()
            store = self.app["store"]
            if method == "POST" and path == "/api/collaboration/session":
                self._write_json(200, {"user": actor})
                return
            if method == "GET" and path == "/api/collaboration/users":
                self._write_json(200, store.list_users(
                    actor,
                    self._one(query, "q"),
                    self._integer(query, "offset", 0),
                    self._integer(query, "limit", 100),
                ))
                return
            if method == "GET" and path == "/api/collaboration/role-events":
                self._write_json(200, {"events": store.list_role_events(actor)})
                return
            match = re.fullmatch(r"/api/collaboration/users/([^/]+)/roles", path)
            if method == "PATCH" and match:
                uid = urllib.parse.unquote(match.group(1))
                self._write_json(200, {"user": store.set_roles(actor, uid, self._body().get("roles"))})
                return
            if method == "GET" and path == "/api/collaboration/subjects":
                self._sync_catalog()
                self._write_json(200, store.list_subjects(
                    actor,
                    subject_type=self._one(query, "type"),
                    status=self._one(query, "status"),
                    query=self._one(query, "q"),
                    offset=self._integer(query, "offset", 0),
                    limit=self._integer(query, "limit", 100),
                ))
                return
            if method == "GET" and path == "/api/collaboration/reviews":
                self._sync_catalog()
                self._write_json(200, store.list_review_events(
                    actor,
                    self._integer(query, "offset", 0),
                    self._integer(query, "limit", 100),
                ))
                return
            if method == "POST" and path == "/api/collaboration/reviews":
                self._sync_catalog()
                self._write_json(201, {"subject": store.record_review(actor, self._body())})
                return
            raise NotFound()
        except ApiError as error:
            self._write_json(error.status, {"error": error.public_message})
        except Exception:
            LOGGER.exception("Onverwachte API-fout")
            self._write_json(500, {"error": GENERIC_ERROR})

    def _serve_static(self, request_path: str) -> None:
        try:
            root = Path(self.app["static_root"]).resolve(strict=True)
            relative = urllib.parse.unquote(request_path).lstrip("/") or "index.html"
            if ".." in Path(relative).parts:
                raise NotFound()
            target = (root / relative).resolve(strict=True)
            if not target.is_relative_to(root) or not target.is_file():
                raise NotFound()
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
        except ApiError as error:
            self._write_json(error.status, {"error": error.public_message})
        except (OSError, ValueError):
            self._write_json(404, {"error": NotFound.public_message})

    @staticmethod
    def _one(query: dict[str, list[str]], key: str) -> str:
        values = query.get(key, [])
        return values[0] if values else ""

    @classmethod
    def _integer(cls, query: dict[str, list[str]], key: str, default: int) -> int:
        value = cls._one(query, key)
        try:
            return int(value) if value else default
        except ValueError as error:
            raise InvalidRequest() from error


def configured_app() -> dict:
    database_path = Path(os.environ.get(
        "OV_COLLABORATION_DB",
        "/var/lib/openvertaling-collaboration/collaboration.sqlite3",
    ))
    catalog_path = Path(os.environ.get(
        "OV_REVIEW_CATALOG",
        "/var/www/openvertaling.nl/site/data/review-catalog.json",
    ))
    bootstrap = {
        email.strip().casefold()
        for email in os.environ.get(
            "OV_BOOTSTRAP_ADMIN_EMAILS",
            "maartenvroegindeweij@gmail.com,real.johnheikens@gmail.com",
        ).split(",")
        if email.strip()
    }
    store = ReviewStore(database_path, bootstrap)
    store.sync_catalog_file(catalog_path)
    return {
        "store": store,
        "verifier": FirebaseTokenVerifier(PROJECT_ID),
        "catalog_path": catalog_path,
        "static_root": os.environ.get("OV_STATIC_ROOT") or None,
    }


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("OV_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    host = os.environ.get("OV_COLLABORATION_HOST", "127.0.0.1")
    port = int(os.environ.get("OV_COLLABORATION_PORT", "8787"))
    server = ThreadingHTTPServer((host, port), CollaborationHandler)
    server.app = configured_app()
    LOGGER.info("Collaboration API luistert op %s:%s", host, port)
    server.serve_forever()


if __name__ == "__main__":
    main()
