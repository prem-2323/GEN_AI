"""Phase 14 Provenance Engine — Cryptographic Hashing & Integrity Verification.

Provides SHA-256 content hashing utilities for original documents, extracted text chunks,
evidence items, and generated outputs, enabling tamper detection and hash verification.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Union
from .schemas import IntegrityResult

log = logging.getLogger("gen-transform.provenance.hashing")


class ProvenanceHasher:
    """Utility class for computing and verifying SHA-256 content hashes."""

    @staticmethod
    def hash_string(content: str) -> str:
        """Compute SHA-256 hex digest for string content."""
        if content is None:
            content = ""
        clean_bytes = content.encode("utf-8")
        return hashlib.sha256(clean_bytes).hexdigest()

    @staticmethod
    def hash_dict(data: Dict[str, Any]) -> str:
        """Compute SHA-256 hex digest for dictionary by serializing keys in deterministic order."""
        if not data:
            return ProvenanceHasher.hash_string("")
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return ProvenanceHasher.hash_string(serialized)

    @classmethod
    def generate_hash(cls, content: Union[str, Dict[str, Any], bytes]) -> str:
        """Generate SHA-256 hash for str, dict, or bytes."""
        if isinstance(content, bytes):
            return hashlib.sha256(content).hexdigest()
        elif isinstance(content, dict):
            return cls.hash_dict(content)
        else:
            return cls.hash_string(str(content))

    @classmethod
    def verify_hash(cls, content: Union[str, Dict[str, Any], bytes], expected_hash: str) -> bool:
        """Verify if generated content hash matches expected hash."""
        if not expected_hash:
            return False
        actual = cls.generate_hash(content)
        return actual.lower() == expected_hash.lower()

    @classmethod
    def verify_integrity(
        cls, artifact_id: str, content: Union[str, Dict[str, Any], bytes], expected_hash: Optional[str] = None
    ) -> IntegrityResult:
        """Verify content integrity and return detailed IntegrityResult."""
        actual_hash = cls.generate_hash(content)
        if expected_hash is None or expected_hash == "":
            expected_hash = actual_hash

        is_valid = actual_hash.lower() == expected_hash.lower()
        msg = "INTEGRITY_VALID" if is_valid else "INTEGRITY_FAILED"

        return IntegrityResult(
            valid=is_valid,
            source_id=artifact_id,
            expected_hash=expected_hash,
            actual_hash=actual_hash,
            message=msg,
        )


__all__ = ["ProvenanceHasher"]
