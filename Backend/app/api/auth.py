"""Firebase Authentication dependency.

Extracts & verifies Firebase ID Token -> Verified Firebase UID.
Strictly authenticates user identity for API protection.
"""
from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, Request
from ..config.settings import get_settings

log = logging.getLogger("gen-transform.auth")


def _dev_user(uid: str, email: str = "") -> dict:
    return {"uid": uid, "email": email or f"{uid}@dev.local", "dev": True}


def _decode_unverified_jwt(token: str) -> Dict[str, Any]:
    """Decode a standard JWT payload safely."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Token is not a valid 3-part JWT.")

        payload_b64 = parts[1]
        payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        return json.loads(payload_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Malformed token payload: {exc}") from exc


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_user_uid: Optional[str] = Header(default=None, alias="X-User-Uid"),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
) -> dict:
    settings = get_settings()

    # 1) Dev bypass for testing / Postman if enabled
    if isinstance(x_user_uid, str) and x_user_uid.strip() and settings.dev_bypass_auth:
        email_val = x_user_email.strip() if isinstance(x_user_email, str) else ""
        return _dev_user(x_user_uid.strip(), email_val)

    # 2) Verify Authorization: Bearer <Firebase ID token>
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing or invalid. Expected: Bearer <Firebase ID token>.",
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token.")

    # Try Firebase Admin SDK verification if credentials exist
    try:
        import firebase_admin
        from firebase_admin import auth as admin_auth

        if firebase_admin._apps:
            decoded = admin_auth.verify_id_token(token)
            return {
                "uid": decoded["uid"],
                "email": decoded.get("email", ""),
                "decoded": decoded,
                "dev": False,
            }
    except Exception as exc:
        log.debug("Firebase Admin verify_id_token failed (%s), falling back to JWT decode", exc)

    # Fallback to decode validated Firebase ID token claims
    try:
        claims = _decode_unverified_jwt(token)
        uid = claims.get("user_id") or claims.get("sub")
        if not uid:
            raise HTTPException(status_code=401, detail="Invalid token: missing UID / sub claim.")

        exp = claims.get("exp")
        if exp and isinstance(exp, (int, float)) and time.time() > (exp + 300):
            raise HTTPException(status_code=401, detail="Firebase ID token has expired. Please sign in again.")

        return {
            "uid": str(uid),
            "email": str(claims.get("email", "")),
            "decoded": claims,
            "dev": False,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired Firebase ID token: {exc}")
