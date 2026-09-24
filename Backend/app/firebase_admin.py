"""Firebase Admin init + Firestore client (named database) with mock fallback.

Architecture:
    Firebase Auth -> Firebase UID -> users/{uid} -> projects/{projectId} (userId == uid)
      -> Sources -> UCKR -> Deliverables (nested fields inside the project doc)

If service-account credentials are missing/unreachable and ALLOW_MOCK_DB=true,
we fall back to a local JSON-file store with the SAME interface so Postman
tests and frontend refresh flows still work.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from .config import get_settings

log = logging.getLogger("gen-transform")

_firebase_app = None
_firestore_client = None
_use_mock = False
_init_attempted = False
_lock = threading.Lock()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------
# Mock DB (JSON file) — same shape as Firestore: users{} projects{}
# ------------------------------------------------------------------
class MockDB:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self.data: dict[str, Any] = {"users": {}, "projects": {}}
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    if isinstance(raw, dict):
                        self.data.setdefault("users", raw.get("users", {}))
                        self.data.setdefault("projects", raw.get("projects", {}))
        except Exception as e:
            log.warning("mock_db load failed: %s", e)

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            log.warning("mock_db save failed: %s", e)

    # users
    def get_user(self, uid: str) -> Optional[dict]:
        return self.data["users"].get(uid)

    def set_user(self, uid: str, doc: dict, merge: bool = True):
        with self._lock:
            if merge and uid in self.data["users"]:
                self.data["users"][uid] = {**self.data["users"][uid], **doc}
            else:
                self.data["users"][uid] = doc
            self._save()

    # projects
    def get_project(self, pid: str) -> Optional[dict]:
        return self.data["projects"].get(pid)

    def list_projects(self, uid: str) -> list[dict]:
        return [p for p in self.data["projects"].values() if p.get("userId") == uid]

    def set_project(self, pid: str, doc: dict):
        with self._lock:
            self.data["projects"][pid] = doc
            self._save()

    def delete_project(self, pid: str):
        with self._lock:
            self.data["projects"].pop(pid, None)
            self._save()


_mock_db: Optional[MockDB] = None


def get_mock_db() -> MockDB:
    global _mock_db
    if _mock_db is None:
        _mock_db = MockDB(get_settings().MOCK_DB_PATH)
    return _mock_db


def is_mock() -> bool:
    return _use_mock


def init_firebase():
    """Init firebase_admin once. Falls back to mock DB when credentials missing."""
    global _firebase_app, _firestore_client, _use_mock, _init_attempted
    with _lock:
        if _init_attempted:
            return
        _init_attempted = True
        settings = get_settings()
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore as admin_firestore

            cred = None
            if settings.FIREBASE_SERVICE_ACCOUNT_JSON.strip():
                cred = credentials.Certificate(json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON))
            elif os.path.exists(settings.FIREBASE_SERVICE_ACCOUNT_PATH):
                cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
            else:
                # Try Application Default Credentials
                try:
                    cred = credentials.ApplicationDefault()
                except Exception:
                    cred = None

            if cred is None:
                raise RuntimeError("no credentials")

            opts = {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None
            try:
                _firebase_app = firebase_admin.get_app()
            except ValueError:
                _firebase_app = firebase_admin.initialize_app(cred, opts) if opts else firebase_admin.initialize_app(cred)

            # Named database support (firebase-admin >= 6)
            try:
                _firestore_client = admin_firestore.client(app=_firebase_app, database_id=settings.FIRESTORE_DATABASE_ID)
            except TypeError:
                # older SDK: database param named `database`
                try:
                    _firestore_client = admin_firestore.client(app=_firebase_app, database=settings.FIRESTORE_DATABASE_ID)
                except TypeError:
                    _firestore_client = admin_firestore.client(app=_firebase_app)
            log.info("Firebase Admin initialised (db=%s)", settings.FIRESTORE_DATABASE_ID)
        except Exception as e:
            log.warning("Firebase init failed (%s). Mock DB=%s", e, settings.ALLOW_MOCK_DB)
            if settings.ALLOW_MOCK_DB:
                _use_mock = True
                get_mock_db()  # ensure file exists
            else:
                raise


def get_db():
    init_firebase()
    if _use_mock or _firestore_client is None:
        return None
    return _firestore_client


# ---------------- Firestore helpers (real or mock) ----------------
def db_get_user(uid: str) -> Optional[dict]:
    if is_mock() or get_db() is None:
        return get_mock_db().get_user(uid)
    snap = get_db().collection("users").document(uid).get()
    return snap.to_dict() if snap.exists else None


def db_set_user(uid: str, doc: dict, merge: bool = True):
    doc = {**doc, "userId": uid, "updatedAt": _utcnow_iso()}
    doc.setdefault("createdAt", _utcnow_iso())
    if is_mock() or get_db() is None:
        get_mock_db().set_user(uid, doc, merge=merge)
        return doc
    get_db().collection("users").document(uid).set(doc, merge=merge)
    return doc


def db_get_project(pid: str) -> Optional[dict]:
    if is_mock() or get_db() is None:
        return get_mock_db().get_project(pid)
    snap = get_db().collection("projects").document(pid).get()
    return snap.to_dict() if snap.exists else None


def db_list_projects(uid: str, limit: int = 50) -> list[dict]:
    if is_mock() or get_db() is None:
        projs = get_mock_db().list_projects(uid)
        projs.sort(key=lambda p: p.get("updatedAt", ""), reverse=True)
        return projs[:limit]
    q = get_db().collection("projects").where("userId", "==", uid).limit(limit).stream()
    out = [d.to_dict() for d in q]
    out.sort(key=lambda p: p.get("updatedAt", ""), reverse=True)
    return out


def db_set_project(pid: str, doc: dict) -> dict:
    if is_mock() or get_db() is None:
        get_mock_db().set_project(pid, doc)
        return doc
    get_db().collection("projects").document(pid).set(doc)
    return doc


def db_delete_project(pid: str):
    if is_mock() or get_db() is None:
        get_mock_db().delete_project(pid)
        return
    get_db().collection("projects").document(pid).delete()
