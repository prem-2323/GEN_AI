"""Structured Data Extraction Module (Phase 3).

Extracts:
- JSON files (hierarchical key-value structures, arrays, schemas, tables)
- XML files (elements, attributes, nested tree data)
"""
from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from ..core.exceptions import ExtractionError
from .normalizer import normalize_text
from .schemas import ExtractedDocument, ExtractedPage, ExtractedSection, ExtractedTable

log = logging.getLogger("extraction.structured")


def _flatten_json_dict(d: Any, prefix: str = "") -> List[str]:
    lines = []
    if isinstance(d, dict):
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                lines.extend(_flatten_json_dict(v, full_key))
            else:
                lines.append(f"{full_key}: {v}")
    elif isinstance(d, list):
        for idx, item in enumerate(d):
            full_key = f"{prefix}[{idx}]"
            if isinstance(item, (dict, list)):
                lines.extend(_flatten_json_dict(item, full_key))
            else:
                lines.append(f"{full_key}: {item}")
    else:
        lines.append(f"{prefix}: {d}")
    return lines


def extract_json_document(
    file_bytes: bytes,
    filename: str,
    document_id: str,
    mime_type: str = "application/json",
    uid: str = "",
    project_id: str = "",
    source_id: str = "",
) -> ExtractedDocument:
    """Extracts JSON documents into clean, structured facts and tables."""
    try:
        raw_str = file_bytes.decode("utf-8", errors="replace")
        data = json.loads(raw_str)
    except Exception as exc:
        raise ExtractionError(f"Could not parse JSON document '{filename}': {exc}")

    lines = _flatten_json_dict(data)
    full_text = f"JSON Document: {filename}\n\n" + "\n".join(lines)
    norm_text = normalize_text(full_text)

    tables = []
    # If root is a list of dicts, format as table
    if isinstance(data, list) and data and isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [headers]
        for item in data[:200]:
            if isinstance(item, dict):
                rows.append([str(item.get(h, "")) for h in headers])
        if len(rows) > 1:
            tables.append(
                ExtractedTable(
                    tableId="TBL-json-1",
                    pageNumber=1,
                    rows=rows,
                    source="json_records",
                )
            )

    pages = [
        ExtractedPage(
            pageNumber=1,
            text=norm_text,
            characterCount=len(norm_text),
            wordCount=len(norm_text.split()),
        )
    ]

    return ExtractedDocument(
        documentId=document_id,
        filename=filename,
        fileType="json",
        mimeType=mime_type or "application/json",
        sizeBytes=len(file_bytes),
        metadata={
            "keyCount": len(lines),
            "isList": isinstance(data, list),
            "characterCount": len(norm_text),
            "wordCount": len(norm_text.split()),
        },
        content=norm_text,
        pages=pages,
        sections=[
            ExtractedSection(
                heading=f"Structured JSON Content ({filename})",
                level=1,
                content=norm_text[:2000],
            )
        ],
        tables=tables,
        images=[],
        extractionStatus="completed",
    )


def extract_xml_document(
    file_bytes: bytes,
    filename: str,
    document_id: str,
    mime_type: str = "application/xml",
    uid: str = "",
    project_id: str = "",
    source_id: str = "",
) -> ExtractedDocument:
    """Extracts XML documents into clean hierarchical structured text."""
    try:
        raw_str = file_bytes.decode("utf-8", errors="replace")
        root = ET.fromstring(raw_str)
    except Exception as exc:
        raise ExtractionError(f"Could not parse XML document '{filename}': {exc}")

    lines = [f"XML Document: {filename} (Root Tag: <{root.tag}>)\n"]

    def _traverse(node: ET.Element, depth: int = 0):
        indent = "  " * depth
        attrs = " ".join(f'{k}="{v}"' for k, v in node.attrib.items())
        attr_str = f" [{attrs}]" if attrs else ""
        text = (node.text or "").strip()
        if text:
            lines.append(f"{indent}<{node.tag}>{attr_str}: {text}")
        else:
            lines.append(f"{indent}<{node.tag}>{attr_str}")
        for child in node:
            _traverse(child, depth + 1)

    _traverse(root)
    full_text = "\n".join(lines)
    norm_text = normalize_text(full_text)

    pages = [
        ExtractedPage(
            pageNumber=1,
            text=norm_text,
            characterCount=len(norm_text),
            wordCount=len(norm_text.split()),
        )
    ]

    return ExtractedDocument(
        documentId=document_id,
        filename=filename,
        fileType="xml",
        mimeType=mime_type or "application/xml",
        sizeBytes=len(file_bytes),
        metadata={
            "rootTag": root.tag,
            "characterCount": len(norm_text),
            "wordCount": len(norm_text.split()),
        },
        content=norm_text,
        pages=pages,
        sections=[
            ExtractedSection(
                heading=f"XML Tree ({filename})",
                level=1,
                content=norm_text[:2000],
            )
        ],
        tables=[],
        images=[],
        extractionStatus="completed",
    )
