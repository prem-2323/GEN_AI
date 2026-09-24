"""MongoDB service and 30-minute temp collection logger with 24-hour TTL auto-deletion."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .config import get_settings

log = logging.getLogger("gen-transform.mongo")

_client: Optional[MongoClient] = None
_scheduler: Optional[BackgroundScheduler] = None


def get_mongo_client() -> MongoClient:
    """Get or create singleton MongoDB client."""
    global _client
    if _client is None:
        settings = get_settings()
        uri = settings.MONGODB_URI or settings.MONGO_URI
        if not uri:
            raise ValueError("MONGODB_URI is not set in environment or config.")
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_mongo_db() -> Database:
    """Get the active MongoDB database."""
    settings = get_settings()
    client = get_mongo_client()
    return client[settings.MONGODB_DB_NAME]


def get_temp_collection() -> Collection:
    """Get the `temp` collection and ensure 24h TTL index exists."""
    db = get_mongo_db()
    temp_col = db["temp"]
    ensure_temp_ttl_index(temp_col)
    return temp_col


def ensure_temp_ttl_index(col: Optional[Collection] = None) -> None:
    """Ensure a MongoDB TTL index on `createdAt` so documents auto-delete after 24 hours."""
    try:
        settings = get_settings()
        if col is None:
            col = get_mongo_db()["temp"]

        ttl_seconds = settings.TEMP_TTL_HOURS * 3600
        # Create or verify TTL index on 'createdAt' field
        col.create_index(
            [("createdAt", ASCENDING)],
            expireAfterSeconds=ttl_seconds,
            name="temp_created_at_ttl_idx",
            background=True,
        )
        log.info(
            "MongoDB TTL index verified on 'temp' collection (expireAfterSeconds=%d [%d hrs])",
            ttl_seconds,
            settings.TEMP_TTL_HOURS,
        )
    except Exception as exc:
        log.warning("Could not create/verify MongoDB TTL index: %s", exc)


def log_temp_timestamp() -> Dict[str, Any]:
    """Insert current date and time into the `temp` collection.

    Automatically expires 24 hours from `createdAt`.
    """
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
        log.info(
            "Logged timestamp to temp collection: id=%s date=%s time=%s (UTC)",
            res.inserted_id,
            doc["date"],
            doc["time"],
        )
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
    """Retrieve recent records from the `temp` collection."""
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


def start_temp_scheduler() -> Optional[BackgroundScheduler]:
    """Start the background scheduler that logs date & time to `temp` every 30 minutes."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        log.info("Temp collection scheduler is already running.")
        return _scheduler

    settings = get_settings()
    interval_minutes = max(1, settings.TEMP_LOG_INTERVAL_MINUTES)

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

    # Trigger an immediate first run on startup
    try:
        log_temp_timestamp()
    except Exception as exc:
        log.warning("Initial immediate temp log failed: %s", exc)

    return _scheduler


def stop_temp_scheduler() -> None:
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("Stopped temp collection background scheduler.")
        _scheduler = None


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
        log.info("Synced user %s (%s) to MongoDB Atlas 'users' collection", uid, payload["displayName"])
        return payload
    except Exception as exc:
        log.error("Failed to sync user to MongoDB Atlas: %s", exc)
        return {"error": str(exc)}

