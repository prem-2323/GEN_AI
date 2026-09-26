"""Image File Extraction Module (Phase 3).

Handles standalone uploaded image files (.png, .jpg, .jpeg):
- Persists the binary to document storage so the Gemma vision stage can analyze it
- Captures dimensions / format metadata
- Best-effort OCR via Tesseract (pytesseract) when installed; graceful fallback otherwise

The persisted image is later routed through Gemma (vision model) in the analysis
orchestrator, while any OCR text merges into the text-analysis channel (Qwen).
"""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, List

from ..core.exceptions import ExtractionError
from .normalizer import normalize_text
from .schemas import ExtractedDocument, ExtractedImageMeta, ExtractedPage

log = logging.getLogger("extraction.image")

_OCR_MIN_CONFIDENCE = 30.0


def _ocr_image_bytes(image_bytes: bytes) -> str:
    """Best-effort OCR. Returns '' when pytesseract/Tesseract is unavailable."""
    try:
        import pytesseract
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as img:
            gray = img.convert("L")
            text = pytesseract.image_to_string(gray)
        return normalize_text(text or "")
    except Exception as exc:
        log.info("OCR skipped for image (pytesseract/Tesseract unavailable): %s", exc)
        return ""


def extract_image_document(
    file_bytes: bytes,
    filename: str,
    document_id: str,
    mime_type: str = "image/png",
    uid: str = "",
    project_id: str = "",
    source_id: str = "",
    persist_images: bool = False,
) -> ExtractedDocument:
    """Extract an uploaded image file: persist binary + metadata + optional OCR text."""
    if not file_bytes:
        raise ExtractionError("Image file payload is empty.")

    width: int | None = None
    height: int | None = None
    fmt = ""
    try:
        from PIL import Image

        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            fmt = (img.format or "").lower()
    except Exception as exc:
        log.warning("Could not read image metadata for '%s': %s", filename, exc)

    ext = mime_type.rsplit("/", 1)[-1].lower() if "/" in mime_type else "png"
    if ext in ("jpeg", "jpg"):
        ext = "jpg"
    if ext not in ("png", "jpg", "webp", "gif", "bmp", "tiff"):
        ext = "png"

    images: List[ExtractedImageMeta] = []
    if persist_images and uid and project_id and source_id:
        try:
            from ..storage.service import save_extracted_image

            img_id, key = save_extracted_image(
                uid=uid,
                project_id=project_id,
                source_id=source_id,
                image_bytes=file_bytes,
                ext=ext,
            )
            images.append(
                ExtractedImageMeta(
                    imageId=img_id,
                    filename=f"{img_id}.{ext}",
                    path=key,
                    pageNumber=1,
                    width=width,
                    height=height,
                    format=fmt,
                )
            )
        except Exception as exc:
            log.warning("Could not persist uploaded image '%s': %s", filename, exc)

    ocr_text = _ocr_image_bytes(file_bytes)

    metadata: Dict[str, Any] = {
        "imageFormat": fmt,
        "width": width,
        "height": height,
        "ocrApplied": bool(ocr_text),
        "ocrCharacterCount": len(ocr_text),
        "characterCount": len(ocr_text),
        "wordCount": len(ocr_text.split()) if ocr_text else 0,
        "visionChannel": "gemma",
        "imageId": images[0].imageId if images else "",
        "imagePath": images[0].path if images else "",
    }

    # OCR text becomes the page content; may be empty (vision-only document)
    ocr_page = ExtractedPage(
        pageNumber=1,
        text=ocr_text,
        characterCount=len(ocr_text),
        wordCount=len(ocr_text.split()) if ocr_text else 0,
    )

    status = "completed" if (ocr_text or images) else "partial"
    return ExtractedDocument(
        documentId=document_id,
        filename=filename,
        fileType="image",
        mimeType=mime_type,
        sizeBytes=len(file_bytes),
        metadata=metadata,
        content=ocr_text,
        pages=[ocr_page],
        sections=[],
        tables=[],
        images=images,
        extractionStatus=status,
    )
