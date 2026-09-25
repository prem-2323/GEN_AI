"""Graph (Phase 5) API Routes — Neo4j Knowledge Graph.

Endpoints:
- POST /api/graph/ingest
- GET  /api/graph/entity/{entity_id}
- GET  /api/graph/entity/{entity_id}/relationships
- GET  /api/graph/entity/{entity_id}/neighbors
- GET  /api/graph/document/{document_id}
- GET  /api/graph/search
- GET  /health/neo4j & /api/graph/health
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_workspace_identity
from ...graph.models import GraphHealthResponse, GraphQueryResult, GraphStatusResponse
from ...graph.service import GraphService

router = APIRouter(tags=["graph"])
graph_router = APIRouter(prefix="/api/graph", tags=["graph"])

graph_service = GraphService()


@router.get("/health/neo4j", response_model=GraphHealthResponse)
@graph_router.get("/health", response_model=GraphHealthResponse)
async def neo4j_health_endpoint():
    """Neo4j Database connectivity and health check status."""
    return graph_service.health_check()


@graph_router.get("/status", response_model=GraphStatusResponse)
async def neo4j_status_endpoint():
    """Detailed Neo4j database node breakdown and relationship status."""
    return graph_service.get_status()


@graph_router.post("/ingest", response_model=GraphQueryResult, status_code=200)
async def ingest_document_graph_endpoint(
    payload: Dict[str, Any],
    user: dict = Depends(get_workspace_identity),
):
    """Ingest DocLink analysis result or document_id into Neo4j graph database."""
    doc_id = payload.get("document_id") or payload.get("documentId")
    if not doc_id:
        raise HTTPException(status_code=400, detail="Missing document_id in request body.")

    try:
        if "entities" in payload:
            return graph_service.ingest_doclink_result(payload)
        return graph_service.ingest_document(document_id=doc_id, use_llm=payload.get("useLlm", True))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph ingestion failed: {exc}")


@graph_router.get("/entity/{entity_id}")
async def get_entity_endpoint(
    entity_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Find entity node by entity_id or canonical name."""
    entity = graph_service.find_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in knowledge graph.")
    return {"ok": True, "entity": entity}


@graph_router.get("/entity/{entity_id}/relationships")
async def get_entity_relationships_endpoint(
    entity_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Get all relationships connected to entity_id."""
    relationships = graph_service.get_entity_relationships(entity_id)
    return {"ok": True, "entity_id": entity_id, "relationships": relationships}


@graph_router.get("/entity/{entity_id}/neighbors")
async def get_entity_neighbors_endpoint(
    entity_id: str,
    depth: int = Query(default=1, ge=1, le=3),
    user: dict = Depends(get_workspace_identity),
):
    """Get neighbor entity nodes connected to entity_id."""
    neighbors = graph_service.get_neighbors(entity_id, depth=depth)
    return {"ok": True, "entity_id": entity_id, "neighbors": neighbors}


@graph_router.get("/document/{document_id}", response_model=GraphQueryResult)
async def get_document_graph_endpoint(
    document_id: str,
    user: dict = Depends(get_workspace_identity),
):
    """Get complete subgraph associated with document_id."""
    return graph_service.get_document_graph(document_id)


@graph_router.get("/search")
async def search_entities_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_workspace_identity),
):
    """Search entity nodes by substring matching on canonical name or alias."""
    entities = graph_service.search_entities(q, limit=limit)
    return {"ok": True, "query": q, "entities": entities, "count": len(entities)}


__all__ = ["router", "graph_router"]
