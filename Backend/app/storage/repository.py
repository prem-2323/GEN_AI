"""Local thread-safe JSON Document Repository implementation for metadata collections."""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.config import get_settings

log = logging.getLogger("gen-transform.repository")

_REPOSITORIES: Dict[str, JSONDocumentRepository] = {}
_REPO_LOCK = threading.Lock()


class JSONDocumentRepository:
    """Thread-safe file-backed JSON repository for domain data collections."""

    def __init__(self, collection_name: str, data_dir: Optional[str] = None) -> None:
        self.collection_name = collection_name
        settings = get_settings()
        self.data_dir = Path(data_dir or settings.data_storage_root)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.data_dir / f"{collection_name}.json"
        self._lock = threading.Lock()
        if not self.file_path.exists():
            self._write_records([])

    def _read_records(self) -> List[Dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception as exc:
            log.error("Failed to read JSON repository %s: %s", self.file_path, exc)
            return []

    def _write_records(self, records: List[Dict[str, Any]]) -> None:
        temp_file = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, self.file_path)
        except Exception as exc:
            log.error("Failed to write JSON repository %s: %s", self.file_path, exc)
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass

    def _matches_filter(self, doc: Dict[str, Any], filter_dict: Optional[Dict[str, Any]]) -> bool:
        if not filter_dict:
            return True
        for k, v in filter_dict.items():
            doc_val = doc.get(k)
            if doc_val != v:
                return False
        return True

    def find_all(self, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            return [r for r in records if self._matches_filter(r, filter_dict)]

    def find_by_id(self, id_val: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            for r in records:
                if str(r.get("id")) == str(id_val) or str(r.get("_id")) == str(id_val):
                    return r
            return None

    def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            for r in records:
                if self._matches_filter(r, filter_dict):
                    return r
            return None

    def insert(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            records = self._read_records()
            doc_copy = dict(doc)
            records.append(doc_copy)
            self._write_records(records)
            return doc_copy

    def update(self, id_val: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            updated_doc = None
            for idx, r in enumerate(records):
                if str(r.get("id")) == str(id_val) or str(r.get("_id")) == str(id_val):
                    records[idx].update(updates)
                    updated_doc = records[idx]
                    break
            if updated_doc:
                self._write_records(records)
            return updated_doc

    def upsert(self, id_val: str, doc: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            records = self._read_records()
            found = False
            doc_copy = dict(doc)
            if "id" not in doc_copy and "_id" not in doc_copy:
                doc_copy["id"] = id_val
            for idx, r in enumerate(records):
                if str(r.get("id")) == str(id_val) or str(r.get("_id")) == str(id_val):
                    records[idx] = doc_copy
                    found = True
                    break
            if not found:
                records.append(doc_copy)
            self._write_records(records)
            return doc_copy

    def delete(self, id_val: str) -> bool:
        with self._lock:
            records = self._read_records()
            new_records = [r for r in records if str(r.get("id")) != str(id_val) and str(r.get("_id")) != str(id_val)]
            if len(new_records) < len(records):
                self._write_records(new_records)
                return True
            return False

    def count(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        return len(self.find_all(filter_dict))


def get_repository(collection_name: str) -> JSONDocumentRepository:
    """Get or create singleton repository instance for named collection."""
    global _REPOSITORIES
    with _REPO_LOCK:
        if collection_name not in _REPOSITORIES:
            _REPOSITORIES[collection_name] = JSONDocumentRepository(collection_name)
        return _REPOSITORIES[collection_name]


__all__ = ["JSONDocumentRepository", "get_repository"]
