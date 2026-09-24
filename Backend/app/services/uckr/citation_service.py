"""Citation mapping and multimodal evidence tracking for UCKR Engine."""
from __future__ import annotations

from typing import Any, Dict, List
from ...models.uckr import Citation, Fact


def build_citations(
    facts: List[Fact],
    visual_evidence: List[Dict[str, Any]],
    source_id: str,
    doc_name: str = "source",
) -> List[Citation]:
    """Generates structured citation records for all facts and visual items."""
    citations: List[Citation] = []

    # 1. Text citations from grounded facts
    for idx, fact in enumerate(facts, start=1):
        cid = f"citation_{idx:03d}"
        quote_text = fact.quote or fact.statement or fact.value or ""
        page_num = fact.page or 1
        chunk_id = fact.chunkId or f"chunk_{page_num:03d}"

        cit = Citation(
            citationId=cid,
            id=cid,
            factId=fact.factId or fact.id,
            sourceId=source_id,
            sourceDoc=doc_name,
            type="text",
            pageNumber=page_num,
            page=page_num,
            chunkId=chunk_id,
            location={"page": page_num, "chunkId": chunk_id},
            textQuote=quote_text,
            excerpt=quote_text,
            quote=quote_text,
        )
        citations.append(cit)

    # 2. Multimodal / visual citations from Gemma Vision analysis
    for v_idx, v in enumerate(visual_evidence, start=1):
        v_cid = f"citation_vis_{v_idx:03d}"
        img_id = v.get("imageId") or f"image_{v_idx:03d}"
        v_type = v.get("type", "chart")
        desc = v.get("description", "")
        page_num = int(v.get("page") or 1)
        chunk_id = f"chunk_vis_{v_idx:03d}"

        cit = Citation(
            citationId=v_cid,
            id=v_cid,
            sourceId=source_id,
            sourceDoc=doc_name,
            type=v_type,
            pageNumber=page_num,
            page=page_num,
            chunkId=chunk_id,
            location={"page": page_num, "imageId": img_id},
            textQuote=desc,
            excerpt=desc,
            quote=desc,
            imageId=img_id,
            description=desc,
        )
        citations.append(cit)

    return citations
