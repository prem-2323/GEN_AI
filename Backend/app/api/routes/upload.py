"""Upload API route."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from ..auth import get_current_user
from ...services.extraction_service import extract_content

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("")
async def upload_source(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    contents = await file.read()
    result = extract_content(contents, filename=file.filename or "source.txt", mime_type=file.content_type or "")
    return {
        "ok": True,
        "source": result,
    }
