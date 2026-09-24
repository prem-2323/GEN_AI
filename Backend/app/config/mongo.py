"""MongoDB Atlas client, collection management, and 30-min temp scheduler."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .settings import get_settings

log = logging.getLogger("gen-transform.mongo")

_client: Optional[MongoClient] = None
_scheduler: Optional[BackgroundScheduler] = None


def get_mongo_client() -> MongoClient:
    """Get singleton MongoDB client."""
    global _client
    if _client is None:
        settings = get_settings()
        uri = settings.mongo_connection_string()
        if not uri:
            raise ValueError("MONGODB_URI is not set in environment or settings.")
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_mongo_db() -> Database:
    """Get the active MongoDB database."""
    settings = get_settings()
    client = get_mongo_client()
    return client[settings.mongodb_db_name]


def get_temp_collection() -> Collection:
    """Get the `temp` collection and verify 24h TTL index."""
    db = get_mongo_db()
    temp_col = db["temp"]
    ensure_temp_ttl_index(temp_col)
    return temp_col


def ensure_temp_ttl_index(col: Optional[Collection] = None) -> None:
    """Ensure MongoDB TTL index on `createdAt` (expires after 24 hours)."""
    try:
        settings = get_settings()
        if col is None:
            col = get_mongo_db()["temp"]

        ttl_seconds = settings.temp_ttl_hours * 3600
        col.create_index(
            [("createdAt", ASCENDING)],
            expireAfterSeconds=ttl_seconds,
            name="temp_created_at_ttl_idx",
            background=True,
        )
    except Exception as exc:
        log.warning("Could not verify MongoDB TTL index: %s", exc)


def log_temp_timestamp() -> Dict[str, Any]:
    """Insert current date and time into the `temp` collection."""
    try:
        col = get_temp_collection()
        now = datetime.now(timezone.utc)
        doc = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "iso": now.isoformat(),
            "timestamp": now.timestamp(),
            "createdAt": now,
        }
        res = col.insert_one(doc)
        log.info("Logged timestamp to temp collection: id=%s date=%s time=%s (UTC)", res.inserted_id, doc["date"], doc["time"])
        return {
            "id": str(res.inserted_id),
            "date": doc["date"],
            "time": doc["time"],
            "iso": doc["iso"],
            "createdAt": doc["createdAt"].isoformat(),
        }
    except Exception as exc:
        log.error("Failed to log timestamp into temp collection: %s", exc)
        return {"error": str(exc)}


def get_recent_temp_records(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent records from `temp` collection."""
    col = get_temp_collection()
    cursor = col.find().sort("createdAt", -1).limit(limit)
    records = []
    for doc in cursor:
        records.append({
            "id": str(doc.get("_id")),
            "date": doc.get("date"),
            "time": doc.get("time"),
            "iso": doc.get("iso"),
            "timestamp": doc.get("timestamp"),
            "createdAt": doc.get("createdAt").isoformat() if isinstance(doc.get("createdAt"), datetime) else doc.get("createdAt"),
        })
    return records


def upsert_user_to_mongo(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert user profile (including Google display name, email, avatar, provider) into MongoDB Atlas."""
    try:
        db = get_mongo_db()
        users_col = db["users"]
        uid = user_doc.get("userId") or user_doc.get("uid")
        if not uid:
            return {"error": "Missing userId"}

        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "userId": uid,
            "uid": uid,
            "email": user_doc.get("email", ""),
            "displayName": user_doc.get("displayName") or user_doc.get("name") or "User",
            "photoURL": user_doc.get("photoURL", ""),
            "authProvider": user_doc.get("authProvider") or user_doc.get("provider", "google.com"),
            "updatedAt": now,
        }
        if "createdAt" in user_doc:
            payload["createdAt"] = user_doc["createdAt"]
        else:
            payload.setdefault("createdAt", now)

        users_col.update_one(
            {"userId": uid},
            {"$set": payload, "$setOnInsert": {"firstSeenAt": now}},
            upsert=True,
        )
        return payload
    except Exception as exc:
        log.error("Failed to sync user to MongoDB Atlas: %s", exc)
        return {"error": str(exc)}


def ensure_core_indexes() -> None:
    """Create ownership + lookup indexes for all 11 `contentforge` collections + GridFS bucket.

    Every tenant-scoped document carries BOTH `firebaseUid` (spec name)
    and `userId` (legacy name) with the same value; indexes cover both.
    """
    try:
        db = get_mongo_db()
        db["users"].create_index([("firebaseUid", ASCENDING)], name="users_firebaseUid_idx", background=True)
        db["users"].create_index([("userId", ASCENDING)], name="users_userId_idx", background=True)
        
        all_collections = (
            "projects",
            "sources",
            "extracted_content",
            "analysis",
            "uckr",
            "deliverables",
            "validations",
            "quality",
            "exports",
            "jobs",
        )
        for col in all_collections:
            db[col].create_index(
                [("firebaseUid", ASCENDING)],
                name=f"{col}_firebaseUid_idx",
                background=True,
            )
            db[col].create_index(
                [("projectId", ASCENDING)],
                name=f"{col}_projectId_idx",
                background=True,
            )
        
        db["sources"].create_index(
            [("projectId", ASCENDING), ("firebaseUid", ASCENDING)],
            name="sources_project_owner_idx",
            background=True,
        )
        db["extracted_content"].create_index(
            [("sourceId", ASCENDING), ("firebaseUid", ASCENDING)],
            name="extracted_content_source_idx",
            background=True,
        )
        db["analysis"].create_index(
            [("sourceId", ASCENDING), ("firebaseUid", ASCENDING)],
            name="analysis_source_idx",
            background=True,
        )
        db["uckr"].create_index(
            [("projectId", ASCENDING), ("sourceId", ASCENDING), ("version", DESCENDING)],
            name="uckr_version_idx",
            background=True,
        )
        db["deliverables"].create_index(
            [("projectId", ASCENDING), ("type", ASCENDING)],
            name="deliverables_project_type_idx",
            background=True,
        )
        db["quality"].create_index(
            [("deliverableId", ASCENDING), ("firebaseUid", ASCENDING)],
            name="quality_deliverable_idx",
            background=True,
        )
        db["exports"].create_index(
            [("deliverableId", ASCENDING), ("firebaseUid", ASCENDING)],
            name="exports_deliverable_idx",
            background=True,
        )
        # GridFS bucket files index
        db["contentforge_files.files"].create_index(
            [("metadata.firebaseUid", ASCENDING), ("uploadDate", DESCENDING)],
            name="gridfs_owner_date_idx",
            background=True,
        )
        ensure_temp_ttl_index(db["temp"])
        log.info("MongoDB Phase 9 core indexes verified (db=%s).", get_settings().mongodb_db_name)
    except Exception as exc:
        log.warning("Could not verify MongoDB core indexes: %s", exc)


def start_temp_scheduler() -> Optional[BackgroundScheduler]:
    """Start 30-minute temp logging background job."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return _scheduler

    settings = get_settings()
    interval_minutes = max(1, settings.temp_log_interval_minutes)

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        log_temp_timestamp,
        trigger="interval",
        minutes=interval_minutes,
        id="temp_timestamp_logger",
        replace_existing=True,
    )
    _scheduler.start()
    log.info("Started background scheduler for 'temp' logging every %d minutes.", interval_minutes)

    try:
        log_temp_timestamp()
    except Exception as exc:
        log.warning("Initial immediate temp log skipped: %s", exc)

    return _scheduler


def stop_temp_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
