""" /auth/me & /auth/sync — store and ensure users/{uid} exists in both Firestore and MongoDB Atlas. """
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import get_current_user
from .. import firebase_admin as db
from .. import mongo_service

router = APIRouter(prefix="/auth", tags=["auth"])


class UserProfileSync(BaseModel):
    displayName: Optional[str] = None
    email: Optional[str] = None
    photoURL: Optional[str] = None
    authProvider: Optional[str] = "google.com"


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    uid = user["uid"]
    existing = db.db_get_user(uid) or {}
    now = datetime.now(timezone.utc).isoformat()
    decoded = user.get("decoded") or {}

    display_name = (
        decoded.get("name")
        or existing.get("displayName")
        or (user.get("email", "").split("@")[0] if user.get("email") else "Authorized User")
    )
    photo_url = decoded.get("picture") or existing.get("photoURL", "")

    profile = {
        "userId": uid,
        "email": user.get("email") or existing.get("email", ""),
        "displayName": display_name,
        "photoURL": photo_url,
        "authProvider": decoded.get("firebase", {}).get("sign_in_provider", "google.com") if isinstance(decoded.get("firebase"), dict) else "google.com",
        "createdAt": existing.get("createdAt", now),
        "updatedAt": now,
    }

    # Save to Firestore
    db.db_set_user(uid, profile, merge=True)

    # Save to MongoDB Atlas
    mongo_service.upsert_user_to_mongo(profile)

    return {**profile, "uid": uid}


@router.post("/sync")
def sync_user(payload: UserProfileSync, user: dict = Depends(get_current_user)):
    uid = user["uid"]
    existing = db.db_get_user(uid) or {}
    now = datetime.now(timezone.utc).isoformat()

    display_name = payload.displayName or existing.get("displayName") or (user.get("email", "").split("@")[0] if user.get("email") else "Authorized User")
    photo_url = payload.photoURL or existing.get("photoURL", "")
    email = payload.email or user.get("email") or existing.get("email", "")
    provider = payload.authProvider or existing.get("authProvider", "google.com")

    profile = {
        "userId": uid,
        "email": email,
        "displayName": display_name,
        "photoURL": photo_url,
        "authProvider": provider,
        "createdAt": existing.get("createdAt", now),
        "updatedAt": now,
    }

    # Save to Firestore
    db.db_set_user(uid, profile, merge=True)

    # Save to MongoDB Atlas
    mongo_service.upsert_user_to_mongo(profile)

    return {**profile, "uid": uid}
