"""DocLink (Phase 4) API Routes — Document Entity / Fact / Relation Engine.

Endpoints:
- POST /doclink/analyze & POST /api/doclink/analyze
- POST /doclink/analyze-text & POST /api/doclink/analyze-text
- GET /doclink/{document_id} & GET /api/doclink/{document_id}
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from ...auth import get_current_user
from ...doclink.schemas import (
    DocLinkAnalyzeRequest,
    DocLinkAnalyzeResponse,
    DocLinkResult,
    DocLinkTextRequest,
)
from ...doclink.service import DocLinkService
from ...storage.repository import JSONDocumentRepository

router = APIRouter(tags=["doclink"])
doclink_router = APIRouter(prefix="/api/doclink", tags=["doclink"])

doclink_repo = JSONDocumentRepository("doclink")
service = DocLinkService()


@router.post("/doclink/analyze", response_model=DocLinkAnalyzeResponse, status_code=200)
@doclink_router.post("/analyze", response_model=DocLinkAnalyzeResponse, status_code=200)
async def analyze_document_endpoint(
    req: DocLinkAnalyzeRequest,
    user: dict = Depends(get_current_user),
):
    """Run Phase 4 DocLink pipeline on a stored document by document_id."""
    doc_id = req.resolved_document_id()
    if not doc_id:
        raise HTTPException(status_code=400, detail="Missing document_id in request body.")

    # Check repository cache unless force=True
    if not req.force:
        cached = doclink_repo.find_one({"document_id": doc_id})
        if not cached:
            cached = doclink_repo.find_one({"documentId": doc_id})
        if cached:
            return DocLinkAnalyzeResponse(**cached)

    result: DocLinkResult = service.analyze_document(
        document_id=doc_id,
        project_id=req.projectId or "",
        user_id=user.get("uid", ""),
        use_llm=req.useLlm,
        chunk_size=req.chunk_size,
    )

    result_dict = result.model_dump()
    doclink_repo.update_one({"document_id": doc_id}, {"$set": result_dict}, upsert=True)

    return DocLinkAnalyzeResponse(**result_dict)


@router.post("/doclink/analyze-text", response_model=DocLinkAnalyzeResponse, status_code=200)
@doclink_router.post("/analyze-text", response_model=DocLinkAnalyzeResponse, status_code=200)
async def analyze_text_endpoint(
    req: DocLinkTextRequest,
    user: dict = Depends(get_current_user),
):
    """Run Phase 4 DocLink pipeline directly on arbitrary text."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text parameter cannot be empty.")

    result: DocLinkResult = service.analyze_text(
        text=req.text,
        document_id=req.document_id,
        document_name=req.name,
        use_llm=req.useLlm,
        chunk_size=req.chunk_size,
    )

    result_dict = result.model_dump()
    return DocLinkAnalyzeResponse(**result_dict)


@router.get("/doclink/{document_id}", response_model=DocLinkAnalyzeResponse)
@doclink_router.get("/{document_id}", response_model=DocLinkAnalyzeResponse)
async def get_doclink_result_endpoint(
    document_id: str,
    user: dict = Depends(get_current_user),
):
    """Retrieve DocLink analysis result for a document_id."""
    cached = doclink_repo.find_one({"document_id": document_id})
    if not cached:
        cached = doclink_repo.find_one({"documentId": document_id})
    if not cached:
        # Run on demand
        result = service.analyze_document(document_id=document_id, user_id=user.get("uid", ""))
        cached = result.model_dump()
        doclink_repo.update_one({"document_id": document_id}, {"$set": cached}, upsert=True)

    return DocLinkAnalyzeResponse(**cached)


__all__ = ["router", "doclink_router"]
