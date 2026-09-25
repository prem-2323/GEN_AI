"""Graph Mapper (Phase 5).

Converts DocLink output (DocLinkResult / UCKR / GraphReadyGraph) into typed
`GraphPayload` (DocumentNodeModel, GraphNodeModel, GraphRelationshipModel) for Neo4j persistence.
"""
from __future__ import annotations

from typing import Any, Dict, List, Union

from ..doclink.schemas import DocLinkEntity, DocLinkFact, DocLinkRelation, DocLinkResult
from .models import DocumentNodeModel, GraphNodeModel, GraphPayload, GraphRelationshipModel


def map_doclink_result_to_payload(result: Union[DocLinkResult, GraphPayload, Dict[str, Any]]) -> GraphPayload:
    """Map Phase 4 DocLink result or GraphPayload into Phase 5 GraphPayload."""
    if isinstance(result, GraphPayload):
        return result

    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif isinstance(result, dict):
        data = result
    else:
        raise ValueError("Invalid DocLink result input for graph mapping.")

    doc_id = data.get("document_id") or data.get("documentId") or "doc_001"
    doc_name = data.get("document_name") or data.get("title") or doc_id

    # 1. Document Node
    document_node = DocumentNodeModel(
        document_id=doc_id,
        filename=doc_name,
        file_type="pdf" if doc_name.endswith(".pdf") else "document",
    )

    # Index entities by canonical name / surface form for resolving endpoint IDs
    entities_raw = data.get("entities") or data.get("nodes") or []

    entity_nodes: List[GraphNodeModel] = []
    name_to_id: Dict[str, str] = {}

    for idx, ent in enumerate(entities_raw, start=1):
        if isinstance(ent, dict):
            eid = ent.get("entity_id") or ent.get("id") or f"ent_{idx:03d}"
            cname = ent.get("canonical_name") or ent.get("canonicalName") or ent.get("text") or f"Entity_{idx}"
            etype = ent.get("type") or "ORGANIZATION"
            surfaces = ent.get("surface_forms") or ent.get("aliases") or [cname]
            conf = float(ent.get("confidence", 0.9))
        else:
            eid = getattr(ent, "entity_id", f"ent_{idx:03d}")
            cname = getattr(ent, "canonical_name", f"Entity_{idx}")
            etype = getattr(ent, "type", "ORGANIZATION")
            surfaces = getattr(ent, "surface_forms", [cname])
            conf = getattr(ent, "confidence", 0.9)

        name_to_id[cname.lower()] = eid
        for s in surfaces:
            if isinstance(s, str):
                name_to_id[s.lower()] = eid

        entity_nodes.append(
            GraphNodeModel(
                entity_id=eid,
                label=etype,
                canonical_name=cname,
                entity_type=etype,
                surface_forms=surfaces,
                confidence=conf,
            )
        )

    # 2. Relationships
    relations_raw = data.get("relations", [])
    rel_models: List[GraphRelationshipModel] = []

    for idx, rel in enumerate(relations_raw, start=1):
        if isinstance(rel, dict):
            rid = rel.get("relation_id") or rel.get("id") or f"rel_{idx:03d}"
            src = rel.get("source") or ""
            src_id = rel.get("source_id") or rel.get("sourceId") or name_to_id.get(src.lower(), src)
            tgt = rel.get("target") or ""
            tgt_id = rel.get("target_id") or rel.get("targetId") or name_to_id.get(tgt.lower(), tgt)
            rtype = rel.get("relation") or rel.get("relation_type") or "RELATED_TO"
            conf = float(rel.get("confidence", 0.9))
            ev_list = rel.get("evidence") or []
        else:
            rid = getattr(rel, "relation_id", f"rel_{idx:03d}")
            src = getattr(rel, "source", "")
            src_id = getattr(rel, "source_id", None) or name_to_id.get(src.lower(), src)
            tgt = getattr(rel, "target", "")
            tgt_id = getattr(rel, "target_id", None) or name_to_id.get(tgt.lower(), tgt)
            rtype = getattr(rel, "relation", "RELATED_TO")
            conf = getattr(rel, "confidence", 0.9)
            ev_list = getattr(rel, "evidence", [])

        # Extract page number & text span from evidence if available
        page = 1
        ev_text = ""
        if ev_list and isinstance(ev_list, list):
            first_ev = ev_list[0]
            if isinstance(first_ev, dict):
                page = int(first_ev.get("page", 1))
                ev_text = str(first_ev.get("text_span") or first_ev.get("quote") or "")
            elif hasattr(first_ev, "page"):
                page = getattr(first_ev, "page", 1)
                ev_text = getattr(first_ev, "text_span", "")

        rel_models.append(
            GraphRelationshipModel(
                relation_id=rid,
                source_id=src_id,
                target_id=tgt_id,
                relation_type=rtype,
                confidence=conf,
                document_id=doc_id,
                page=page,
                evidence_text=ev_text,
            )
        )

    return GraphPayload(
        document=document_node,
        nodes=entity_nodes,
        relationships=rel_models,
    )


__all__ = ["map_doclink_result_to_payload"]
