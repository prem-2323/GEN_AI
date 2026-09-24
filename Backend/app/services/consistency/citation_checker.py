"""Citation and provenance link checker (Phase 7)."""
from __future__ import annotations

from typing import Any, Dict, List
from ...models.validation import CheckItem


def check_citation_consistency(uckr: Dict[str, Any], deliverable_doc: Dict[str, Any]) -> List[CheckItem]:
    """Validates citations declared in deliverable against canonical UCKR citations."""
    checks: List[CheckItem] = []
    uckr_citations = uckr.get("citations", [])
    valid_citation_ids = {c.get("citationId") for c in uckr_citations if c.get("citationId")}
    valid_chunk_ids = {c.get("chunkId") for c in uckr_citations if c.get("chunkId")}

    deliv_citations = deliverable_doc.get("citations", [])
    if isinstance(deliv_citations, list):
        for cit in deliv_citations:
            if not isinstance(cit, dict):
                continue
            cid = cit.get("citationId")
            chunk_id = cit.get("chunkId")
            page_num = cit.get("pageNumber")

            if cid and cid not in valid_citation_ids:
                checks.append(CheckItem(
                    category="citation",
                    expected="Valid UCKR citationId",
                    found=cid,
                    status="contradiction",
                    message=f"Broken citation link: citationId '{cid}' does not exist in UCKR.",
                ))
            elif chunk_id and chunk_id not in valid_chunk_ids:
                checks.append(CheckItem(
                    category="citation",
                    expected="Valid UCKR chunkId",
                    found=chunk_id,
                    status="contradiction",
                    message=f"Broken citation link: chunkId '{chunk_id}' does not exist in UCKR.",
                ))
            else:
                checks.append(CheckItem(
                    category="citation",
                    expected=chunk_id or cid,
                    found=chunk_id or cid,
                    status="consistent",
                    message=f"Citation verified: Chunk {chunk_id or cid} (Page {page_num or 1}).",
                ))

    return checks
