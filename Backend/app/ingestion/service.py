"""Document ingestion service orchestrating validation, storage, and extraction."""
from __future__ import annotations

import io
from typing import Any, Dict

from ..core.exceptions import DocumentValidationError, ExtractionError, ResourceNotFoundError
from ..core.logging import get_logger
from .file_manager import save_file_to_storage
from .validator import validate_file_upload

log = get_logger("ingestion.service")


class IngestionService:
    """Orchestrates incoming document validation, storage, and handoff to extraction."""

    @staticmethod
    def process_project_upload(
        project_id: str,
        uid: str,
        filename: str,
        content_bytes: bytes,
        content_type: str = "",
    ) -> Dict[str, Any]:
        """Ingest a project document: validate -> store -> register -> extract -> complete."""
        from ..services.projects.project_service import get_project
        from ..services.sources.source_service import create_source, set_stage, store_extraction
        from ..extraction.service import ExtractionService

        # 1. Verify project exists & user has ownership
        get_project(project_id, uid=uid)

        # 2. Validation
        size = len(content_bytes)
        safe_name, resolved_mime = validate_file_upload(filename, size, content_type)

        # 3. Save to storage & GridFS
        saved = save_file_to_storage(
            uid=uid,
            project_id=project_id,
            filename=safe_name,
            data_bytes=content_bytes,
            mime_type=resolved_mime,
        )

        # 4. Create Source Record
        file_meta = {
            "originalName": filename,
            "storedName": saved["storedName"],
            "mimeType": resolved_mime,
            "size": size,
            "storagePath": saved["storagePath"],
            "fileId": saved.get("fileId", ""),
            "sha256": saved.get("sha256", ""),
        }
        src_doc = create_source(uid, project_id, file_meta)
        sid = src_doc["sourceId"]

        # 5. Extract text, tables, images
        try:
            set_stage(sid, uid, "validating", 20)
            set_stage(sid, uid, "extracting", 50)

            ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "txt"
            normalized = ExtractionService.extract_normalized(
                content_bytes,
                filename=filename,
                ext=ext,
                uid=uid,
                project_id=project_id,
                source_id=sid,
            )

            # 6. Store extraction & transition to completed
            final_doc = store_extraction(sid, uid, normalized)
            final_doc = set_stage(sid, uid, "completed", 100)

            return {
                "ok": True,
                "source": final_doc,
            }
        except Exception as exc:
            log.error("Source extraction failed for %s: %s", sid, exc)
            set_stage(sid, uid, "failed", error=str(exc))
            raise ExtractionError(f"Source extraction failed: {exc}") from exc

    @staticmethod
    def process_standalone_upload(
        filename: str,
        content_bytes: bytes,
        content_type: str = "",
    ) -> Dict[str, Any]:
        """Standalone lightweight document ingestion and extraction."""
        from ..extraction.service import ExtractionService

        size = len(content_bytes)
        safe_name, resolved_mime = validate_file_upload(filename, size, content_type)
        result = ExtractionService.extract_content(
            content_bytes,
            filename=safe_name,
            mime_type=resolved_mime,
        )
        return {
            "ok": True,
            "source": result,
        }


# Singleton service instance
ingestion_service = IngestionService()
