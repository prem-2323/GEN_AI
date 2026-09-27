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
            with open(self.file_path, "r", encoding="utf-8-sig") as f:
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
            if k == "$or" and isinstance(v, list):
                if not any(self._matches_filter(doc, sub_filter) for sub_filter in v):
                    return False
            elif k == "$and" and isinstance(v, list):
                if not all(self._matches_filter(doc, sub_filter) for sub_filter in v):
                    return False
            else:
                doc_val = doc.get(k)
                if doc_val != v:
                    return False
        return True

    def _apply_projection(self, doc: Dict[str, Any], projection: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not projection:
            return dict(doc)
        exclude_keys = [k for k, v in projection.items() if not v]
        include_keys = [k for k, v in projection.items() if v]
        if exclude_keys:
            return {k: v for k, v in doc.items() if k not in exclude_keys}
        if include_keys:
            return {k: v for k, v in doc.items() if k in include_keys}
        return dict(doc)

    def find_all(self, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            return [r for r in records if self._matches_filter(r, filter_dict)]

    def find(
        self,
        query: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        skip: int = 0,
        projection: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            results = [r for r in records if self._matches_filter(r, query)]

            if sort:
                for sort_key, direction in reversed(sort):
                    reverse = direction < 0 or direction == "desc" or direction == -1
                    results.sort(key=lambda x: str(x.get(sort_key, "") or ""), reverse=reverse)

            if skip > 0:
                results = results[skip:]
            if limit is not None and limit > 0:
                results = results[:limit]

            if projection:
                results = [self._apply_projection(r, projection) for r in results]

            return results

    def find_by_id(self, id_val: str, projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            for r in records:
                if str(r.get("id")) == str(id_val) or str(r.get("_id")) == str(id_val):
                    return self._apply_projection(r, projection)
            return None

    def find_one(
        self,
        filter_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        projection: Optional[Dict[str, Any]] = None,
        skip: int = 0,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            results = [r for r in records if self._matches_filter(r, filter_dict)]

            if sort:
                for sort_key, direction in reversed(sort):
                    reverse = direction < 0 or direction == "desc" or direction == -1
                    results.sort(key=lambda x: str(x.get(sort_key, "") or ""), reverse=reverse)

            if skip > 0:
                results = results[skip:]

            if results:
                return self._apply_projection(results[0], projection)
            return None

    def insert(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            records = self._read_records()
            doc_copy = dict(doc)
            records.append(doc_copy)
            self._write_records(records)
            return doc_copy

    def insert_one(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return self.insert(doc)

    def insert_many(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        with self._lock:
            records = self._read_records()
            copied = [dict(d) for d in docs]
            records.extend(copied)
            self._write_records(records)
            return copied

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

    def update_one(
        self,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any],
        upsert: bool = False,
    ) -> bool:
        with self._lock:
            records = self._read_records()
            fields_to_set = update_dict.get("$set", update_dict) if isinstance(update_dict, dict) else update_dict
            fields_to_unset = update_dict.get("$unset", {}) if isinstance(update_dict, dict) else {}

            found = False
            for idx, r in enumerate(records):
                if self._matches_filter(r, filter_dict):
                    if isinstance(fields_to_set, dict):
                        records[idx].update(fields_to_set)
                    if isinstance(fields_to_unset, dict):
                        for k in fields_to_unset:
                            records[idx].pop(k, None)
                    found = True
                    break

            if not found and upsert:
                new_doc = {}
                if isinstance(filter_dict, dict):
                    for k, v in filter_dict.items():
                        if not k.startswith("$"):
                            new_doc[k] = v
                if isinstance(fields_to_set, dict):
                    new_doc.update(fields_to_set)
                records.append(new_doc)
                found = True

            if found:
                self._write_records(records)
            return found

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

    def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        with self._lock:
            records = self._read_records()
            target_idx = None
            for idx, r in enumerate(records):
                if self._matches_filter(r, filter_dict):
                    target_idx = idx
                    break
            if target_idx is not None:
                records.pop(target_idx)
                self._write_records(records)
                return True
            return False

    def delete_many(self, filter_dict: Dict[str, Any]) -> int:
        with self._lock:
            records = self._read_records()
            new_records = [r for r in records if not self._matches_filter(r, filter_dict)]
            deleted_count = len(records) - len(new_records)
            if deleted_count > 0:
                self._write_records(new_records)
            return deleted_count

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
