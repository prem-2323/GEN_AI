"""User profile and authentication routes."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...auth import get_current_user
from ...storage.repository import get_repository
from ...utils.helpers import utcnow_iso

router = APIRouter(tags=["auth"])


class UserProfileSync(BaseModel):
    displayName: Optional[str] = None
    email: Optional[str] = None
    photoURL: Optional[str] = None
    authProvider: Optional[str] = "google.com"


@router.get("/api/me")
@router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    uid = user["uid"]
    decoded = user.get("decoded") or {}
    now = utcnow_iso()

    display_name = (
        decoded.get("name")
        or (user.get("email", "").split("@")[0] if user.get("email") else "Authorized User")
    )
    photo_url = decoded.get("picture", "")
    email = user.get("email", "")

    profile = {
        "uid": uid,
        "userId": uid,
        "email": email,
        "displayName": display_name,
        "photoURL": photo_url,
        "authProvider": decoded.get("firebase", {}).get("sign_in_provider", "google.com") if isinstance(decoded.get("firebase"), dict) else "google.com",
        "createdAt": now,
        "updatedAt": now,
    }

    users_repo = get_repository("users")
    users_repo.update_one({"userId": uid}, {"$set": profile}, upsert=True)

    return profile


@router.post("/api/auth/sync")
async def sync_me(payload: UserProfileSync, user: dict = Depends(get_current_user)):
    uid = user["uid"]
    now = utcnow_iso()

    profile = {
        "uid": uid,
        "userId": uid,
        "email": payload.email or user.get("email", ""),
        "displayName": payload.displayName or "Authorized User",
        "photoURL": payload.photoURL or "",
        "authProvider": payload.authProvider or "google.com",
        "createdAt": now,
        "updatedAt": now,
    }

    users_repo = get_repository("users")
    users_repo.update_one({"userId": uid}, {"$set": profile}, upsert=True)

    return profile

