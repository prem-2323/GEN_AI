"""Central settings for the FastAPI backend."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.getenv(name, default)


class Settings:
    FIREBASE_PROJECT_ID: str = _get("FIREBASE_PROJECT_ID", "gen-lang-client-0421331706")
    # Named Firestore DB from Frontend/firebase-applet-config.json
    FIRESTORE_DATABASE_ID: str = _get(
        "FIRESTORE_DATABASE_ID",
        "ai-studio-gentransformai-ccc00148-cf41-4379-89fb-7302425611e2",
    )
    FIREBASE_SERVICE_ACCOUNT_PATH: str = _get("FIREBASE_SERVICE_ACCOUNT_PATH", "./serviceAccountKey.json")
    FIREBASE_SERVICE_ACCOUNT_JSON: str = _get("FIREBASE_SERVICE_ACCOUNT_JSON", "")

    # MongoDB Atlas — secrets come from env only, never hardcoded.
    MONGODB_URI: str = _get("MONGODB_URI", _get("MONGO_URI", ""))
    MONGO_URI: str = _get("MONGO_URI", MONGODB_URI)
    MONGODB_DB_NAME: str = _get("MONGODB_DB_NAME", "gen_transform_ai")
    TEMP_LOG_INTERVAL_MINUTES: int = int(_get("TEMP_LOG_INTERVAL_MINUTES", "30") or "30")
    TEMP_TTL_HOURS: int = int(_get("TEMP_TTL_HOURS", "24") or "24")

    PORT: int = int(_get("PORT", "8000") or "8000")
    FRONTEND_ORIGIN: str = _get("FRONTEND_ORIGIN", "http://localhost:3000")
    EXTRA_CORS_ORIGINS: str = _get("EXTRA_CORS_ORIGINS", "")

    DEV_BYPASS_AUTH: bool = _get("DEV_BYPASS_AUTH", "true").lower() in ("1", "true", "yes")
    ALLOW_MOCK_DB: bool = _get("ALLOW_MOCK_DB", "true").lower() in ("1", "true", "yes")
    MOCK_DB_PATH: str = _get("MOCK_DB_PATH", "./mock_db.json")


@lru_cache
def get_settings() -> Settings:
    return Settings()
