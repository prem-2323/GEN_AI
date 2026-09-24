"""Firebase Admin SDK initialization and Firestore connection."""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore
from .settings import get_settings

log = logging.getLogger("gen-transform.firebase")

_firebase_app: Optional[firebase_admin.App] = None
_db: Optional[firestore.Client] = None
_init_attempted = False


def init_firebase() -> Optional[firestore.Client]:
    """Initialize Firebase Admin SDK once and return Firestore client."""
    global _firebase_app, _db, _init_attempted
    if _init_attempted:
        return _db
    _init_attempted = True

    settings = get_settings()

    # 1. Try JSON string from env
    if settings.firebase_service_account_json.strip():
        try:
            cred_dict = json.loads(settings.firebase_service_account_json)
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
            log.info("Firebase Admin initialized from inline JSON credentials.")
        except Exception as exc:
            log.warning("Firebase inline credentials failed: %s", exc)

    # 2. Try service account file path
    elif os.path.exists(settings.firebase_service_account_path):
        try:
            cred = credentials.Certificate(settings.firebase_service_account_path)
            _firebase_app = firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
            log.info("Firebase Admin initialized from %s", settings.firebase_service_account_path)
        except Exception as exc:
            log.warning("Firebase certificate path failed: %s", exc)
    else:
        log.info("No serviceAccountKey.json file found. Operating with MongoDB Atlas & verified client tokens.")

    if _firebase_app is not None:
        try:
            _db = firestore.client(database_id=settings.firestore_database_id)
            log.info("Firestore client connected (db=%s).", settings.firestore_database_id)
        except Exception as exc:
            log.warning("Named Firestore database connection fallback (%s).", exc)
            try:
                _db = firestore.client()
            except Exception:
                _db = None

    return _db


def get_firestore_db() -> Optional[firestore.Client]:
    """Get the active Firestore client."""
    return init_firebase()
