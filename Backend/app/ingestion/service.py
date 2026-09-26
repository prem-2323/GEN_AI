"""Document Ingestion Service Orchestrator (Phase 3).

Pipeline:
Upload API -> File Validation -> Type Detection -> File Storage (original/) -> Content Extraction -> Text Normalization -> Extracted Storage (extracted/text.json) -> ExtractedDocument schema output -> Ready for Phase 4 DocLink.
"""
from __future__ import annotations

import io
import time
from typing import Any, Dict, Optional

from ..core.exceptions import DocumentValidationError, ExtractionError
from ..core.logging import get_logger
from ..extraction.schemas import ExtractedDocument
from ..extraction.service import ExtractionService
from .detector import detect_document_type
from .file_manager import generate_document_id, save_extracted_content, save_original_file
from .schemas import IngestionResponse
from .validator import validate_file_upload

log = get_logger("ingestion.service")


class IngestionService:
    """Main Ingestion Pipeline Service."""

    @staticmethod
    def process_document_ingestion(
        filename: str,
        content_bytes: bytes,
        content_type: str = "",
        uid: str = "dev_user",
        project_id: str = "proj_default",
        source_id: Optional[str] = None,
    ) -> ExtractedDocument:
        """Full Document Ingestion & Extraction Pipeline.

        Steps:
        1. Log UPLOAD_STARTED
        2. Validate File (existence, extension, size, MIME)
        3. Detect Document Type & Encoding
        4. Save Original File to storage/documents/<doc_id>/original/<filename>
        5. Extract Text, Pages, Sections, Tables, Metadata
        6. Save Extracted Content to storage/documents/<doc_id>/extracted/text.json
        7. Return ExtractedDocument
        """
        start_time = time.time()
        doc_id = source_id or generate_document_id("src")

        log.info("UPLOAD_STARTED doc_id=%s filename=%s size=%d", doc_id, filename, len(content_bytes))

        # 1. Validation
        safe_name, resolved_mime = validate_file_upload(filename, len(content_bytes), content_type)
        log.info("FILE_VALIDATED doc_id=%s safe_name=%s mime=%s", doc_id, safe_name, resolved_mime)

        # 2. Type Detection
        file_type, ext = detect_document_type(safe_name, content_bytes, resolved_mime)

        # 3. Store Original File
        saved_file = save_original_file(
            uid=uid,
            project_id=project_id,
            filename=safe_name,
            data_bytes=content_bytes,
            source_id=doc_id,
        )
        log.info("FILE_STORED doc_id=%s storage_path=%s", doc_id, saved_file.get("storagePath"))

        # 4. Extract & Normalize Content
        log.info("EXTRACTION_STARTED doc_id=%s file_type=%s", doc_id, file_type)
        try:
            extracted_doc = ExtractionService.extract_document(
                file_bytes=content_bytes,
                filename=safe_name,
                document_id=doc_id,
                mime_type=resolved_mime,
                ext=ext,
                uid=uid,
                project_id=project_id,
                source_id=doc_id,
                persist_images=True,
            )

            # 5. Save Extracted Content Sidecar
            save_extracted_content(
                document_id=doc_id,
                extracted_data=extracted_doc.model_dump(by_alias=True),
                metadata_data=extracted_doc.metadata,
            )

            duration_ms = int((time.time() - start_time) * 1000)
            log.info("EXTRACTION_COMPLETED doc_id=%s duration_ms=%d chars=%d pages=%d", doc_id, duration_ms, len(extracted_doc.content), len(extracted_doc.pages))

            return extracted_doc
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            log.error("EXTRACTION_FAILED doc_id=%s duration_ms=%d error=%s", doc_id, duration_ms, exc)
            raise

    @staticmethod
    def process_project_upload(
        project_id: str,
        uid: str,
        filename: str,
        content_bytes: bytes,
        content_type: str = "",
    ) -> Dict[str, Any]:
        """Project upload entry point registering source in project data repository."""
        from ..services.projects.project_service import get_project
        from ..services.sources.source_service import create_source, set_stage, store_extraction

        # Verify project ownership
        get_project(project_id, uid=uid)

        # Generate source ID
        doc_id = generate_document_id("src")

        # Ingest and Extract
        extracted_doc = IngestionService.process_document_ingestion(
            filename=filename,
            content_bytes=content_bytes,
            content_type=content_type,
            uid=uid,
            project_id=project_id,
            source_id=doc_id,
        )

        # Register source metadata
        file_meta = {
            "originalName": filename,
            "storedName": extracted_doc.filename,
            "mimeType": extracted_doc.mimeType,
            "size": extracted_doc.sizeBytes,
            "storagePath": f"documents/{doc_id}/original/{extracted_doc.filename}",
            "fileId": doc_id,
            "sha256": extracted_doc.metadata.get("sha256", ""),
        }
        src_doc = create_source(uid, project_id, file_meta)
        sid = src_doc["sourceId"]

        # Store normalized extraction
        norm_dict = {
            "sourceId": sid,
            "document": {"name": extracted_doc.filename, "type": extracted_doc.fileType},
            "text": {"content": extracted_doc.content, "characterCount": len(extracted_doc.content)},
            "pages": [p.model_dump(by_alias=True) for p in extracted_doc.pages],
            "sections": [s.model_dump(by_alias=True) for s in extracted_doc.sections],
            "tables": [t.model_dump(by_alias=True) for t in extracted_doc.tables],
            "images": [i.model_dump(by_alias=True) for i in extracted_doc.images],
            "metadata": extracted_doc.metadata,
        }

        set_stage(sid, uid, "validating", 20)
        set_stage(sid, uid, "extracting", 50)
        final_doc = store_extraction(sid, uid, norm_dict)
        final_doc = set_stage(sid, uid, "completed", 100)

        return {
            "ok": True,
            "source": final_doc,
            "extractedDocument": extracted_doc.model_dump(by_alias=True),
        }


ingestion_service = IngestionService()
