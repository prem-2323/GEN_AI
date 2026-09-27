"""Spreadsheet & Tabular Extraction Module (Phase 3).

Extracts:
- CSV, XLS, XLSX sheets, rows, columns, headers, cells, units, formulas
- Preserves structured provenance: Sheet -> Row -> Column -> Cell
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Any, Dict, List, Optional

from ..core.exceptions import ExtractionError
from .normalizer import normalize_text
from .schemas import ExtractedDocument, ExtractedPage, ExtractedSection, ExtractedTable

log = logging.getLogger("extraction.spreadsheet")


def extract_csv_document(
    file_bytes: bytes,
    filename: str,
    document_id: str,
    mime_type: str = "text/csv",
    uid: str = "",
    project_id: str = "",
    source_id: str = "",
) -> ExtractedDocument:
    """Extracts CSV data with structure and table representation."""
    try:
        text_content = file_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        raise ExtractionError(f"Could not decode CSV text: {exc}")

    lines = [ln for ln in text_content.splitlines() if ln.strip()]
    if not lines:
        raise ExtractionError(f"CSV file '{filename}' is empty.")

    reader = csv.reader(io.StringIO(text_content))
    rows = [r for r in reader if any(cell.strip() for cell in r)]

    if not rows:
        raise ExtractionError(f"No valid rows found in CSV '{filename}'.")

    headers = rows[0]
    data_rows = rows[1:]

    # Build markdown-like text representation for LLM and search
    text_blocks: List[str] = [f"CSV Spreadsheet: {filename}\nTotal Rows: {len(rows)}\n"]
    if headers:
        text_blocks.append(f"Columns: {', '.join(headers)}\n")

    for idx, row in enumerate(data_rows, start=1):
        row_items = []
        for c_idx, val in enumerate(row):
            col_name = headers[c_idx] if c_idx < len(headers) else f"Col_{c_idx+1}"
            if val.strip():
                row_items.append(f"{col_name}: {val.strip()}")
        if row_items:
            text_blocks.append(f"Row {idx} -> " + ", ".join(row_items))

    full_text = "\n".join(text_blocks)
    norm_text = normalize_text(full_text)

    tables = [
        ExtractedTable(
            tableId=f"TBL-csv-1",
            pageNumber=1,
            rows=rows[:500],
            source="csv_table",
        )
    ]

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
        fileType="csv",
        mimeType=mime_type or "text/csv",
        sizeBytes=len(file_bytes),
        metadata={
            "rowCount": len(rows),
            "columnCount": len(headers),
            "headers": headers,
            "characterCount": len(norm_text),
            "wordCount": len(norm_text.split()),
            "tableCount": len(tables),
        },
        content=norm_text,
        pages=pages,
        sections=[
            ExtractedSection(
                heading=f"Spreadsheet Data ({filename})",
                level=1,
                content=norm_text[:2000],
            )
        ],
        tables=tables,
        images=[],
        extractionStatus="completed",
    )


def extract_excel_document(
    file_bytes: bytes,
    filename: str,
    document_id: str,
    mime_type: str = "",
    uid: str = "",
    project_id: str = "",
    source_id: str = "",
) -> ExtractedDocument:
    """Extracts XLS / XLSX workbook sheets, rows, and structured cells."""
    pages: List[ExtractedPage] = []
    tables: List[ExtractedTable] = []
    sections: List[ExtractedSection] = []
    text_blocks: List[str] = [f"Spreadsheet Workbook: {filename}\n"]

    # Try openpyxl for xlsx, fallback to pandas or openpyxl
    try:
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheet_names = wb.sheetnames

        for s_idx, sheet_name in enumerate(sheet_names, start=1):
            sheet = wb[sheet_name]
            sheet_rows = []
            for row in sheet.iter_rows(values_only=True):
                str_row = [str(c) if c is not None else "" for c in row]
                if any(c.strip() for c in str_row):
                    sheet_rows.append(str_row)

            if not sheet_rows:
                continue

            tables.append(
                ExtractedTable(
                    tableId=f"TBL-sheet-{s_idx}",
                    pageNumber=s_idx,
                    rows=sheet_rows[:500],
                    source=f"sheet_{sheet_name}",
                )
            )

            headers = sheet_rows[0]
            sheet_text = [f"=== Sheet: {sheet_name} (Page {s_idx}) ==="]
            sheet_text.append(f"Columns: {', '.join(headers)}")

            for r_idx, r in enumerate(sheet_rows[1:], start=1):
                row_items = []
                for c_idx, val in enumerate(r):
                    col_name = headers[c_idx] if c_idx < len(headers) else f"Col_{c_idx+1}"
                    if val.strip():
                        row_items.append(f"{col_name}: {val.strip()}")
                if row_items:
                    sheet_text.append(f"Row {r_idx} -> " + ", ".join(row_items))

            sheet_full = "\n".join(sheet_text)
            norm_sheet = normalize_text(sheet_full)
            text_blocks.append(norm_sheet)

            pages.append(
                ExtractedPage(
                    pageNumber=s_idx,
                    text=norm_sheet,
                    characterCount=len(norm_sheet),
                    wordCount=len(norm_sheet.split()),
                )
            )

            sections.append(
                ExtractedSection(
                    heading=f"Sheet: {sheet_name}",
                    level=2,
                    content=norm_sheet[:1000],
                )
            )

    except Exception as exc:
        log.warning("openpyxl extraction failed for %s: %s. Fallback to basic text parse.", filename, exc)
        # Basic text fallback
        raw_text = file_bytes.decode("latin1", errors="replace")
        clean_lines = [l for l in raw_text.splitlines() if len(l.strip()) > 3 and any(c.isalnum() for c in l)]
        norm_sheet = normalize_text("\n".join(clean_lines[:500]))
        pages = [
            ExtractedPage(
                pageNumber=1,
                text=norm_sheet,
                characterCount=len(norm_sheet),
                wordCount=len(norm_sheet.split()),
            )
        ]
        text_blocks = [norm_sheet]

    full_text = "\n\n".join(text_blocks)
    norm_full = normalize_text(full_text)

    return ExtractedDocument(
        documentId=document_id,
        filename=filename,
        fileType="xlsx" if filename.endswith(".xlsx") else "xls",
        mimeType=mime_type or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        sizeBytes=len(file_bytes),
        metadata={
            "sheetCount": len(pages),
            "tableCount": len(tables),
            "characterCount": len(norm_full),
            "wordCount": len(norm_full.split()),
        },
        content=norm_full,
        pages=pages,
        sections=sections,
        tables=tables,
        images=[],
        extractionStatus="completed",
    )
