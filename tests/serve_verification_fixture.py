"""Local browser-test server: real API/storage, synthetic authenticated identities."""
import hashlib
import importlib.util
import json
import sys
import signal
import tempfile
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
spec = importlib.util.spec_from_file_location("api", ROOT / "server/collaboration_api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class Verifier:
    def verify(self, token):
        if token == "maarten":
            return {"sub": "google-maarten", "email": "maartenvroegindeweij@gmail.com",
                    "email_verified": True, "name": "Maarten Vroegindeweij"}
        if token not in ("admin", "reviewer", "reader"):
            raise api.Unauthorized()
        return {"sub": token, "email": token + "@example.test",
                "email_verified": True, "name": token.title()}


signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

with tempfile.TemporaryDirectory(prefix="ov-verification-test-") as temporary:
    root = Path(temporary)
    subjects = []
    for chapter in (1, 2, 3):
        path = ROOT / f"data/genesis/{chapter}.json"
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        content = json.loads(path.read_text())
        for verse in [None] + [v["number"] for v in content["verses"]]:
            subject_type = "text-chapter" if verse is None else "text-verse"
            identifier = f"genesis/{chapter}" + (f"/{verse}" if verse else "")
            subjects.append({
                "type": subject_type, "id": identifier, "revision": source_hash,
                "label": f"Genesis {chapter}" + (f":{verse}" if verse else ""),
                "href": "index.html#" + identifier, "source": f"data/genesis/{chapter}.json",
                "metadata": {"sourceHash": source_hash},
            })
    location_path = ROOT / "data/geografie-runtime.geojson"
    location = json.loads(location_path.read_text())["features"][0]["properties"]
    location_hash = hashlib.sha256(location_path.read_bytes()).hexdigest()
    subjects.append({
        "type": "location", "id": location["id"], "revision": location_hash,
        "label": location["naam"], "href": "plaats.html?plaats=" + location["id"],
        "source": "data/geografie-runtime.geojson", "metadata": {"sourceHash": location_hash},
    })
    history = [dict(item, migrationSource="test historical review") for item in subjects
               if item["type"] == "text-chapter" and item["id"] == "genesis/3"]
    catalog = {"schemaVersion": 2, "historicalSubjects": history, "subjectTypes": {
        "text-chapter": "Hoofdstuk", "text-verse": "Vers", "location": "Plaats",
    }, "subjects": subjects}
    catalog["catalogRevision"] = api.review_catalog_revision(catalog)
    catalog_path = root / "catalog.json"
    catalog_path.write_text(json.dumps(catalog))
    store = api.ReviewStore(root / "reviews.sqlite3", {"admin@example.test", "maartenvroegindeweij@gmail.com"})
    admin = store.upsert_user(Verifier().verify("admin"))
    store.upsert_user(Verifier().verify("reviewer"))
    store.upsert_user(Verifier().verify("reader"))
    store.set_roles(admin, "reviewer", ["reviewer"])
    server = ThreadingHTTPServer(("127.0.0.1", 0), api.CollaborationHandler)
    server.app = {"store": store, "verifier": Verifier(), "catalog_path": catalog_path,
                  "static_root": str(ROOT)}
    print(json.dumps({"port": server.server_port, "location": location["id"]}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
