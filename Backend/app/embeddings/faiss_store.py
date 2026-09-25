"""Phase 4 — REAL Persistent FAISS Vector Store.

Production-grade FAISS-backed vector store with:
- FAISS IndexFlatIP (Inner Product on L2-normalized vectors ≡ cosine similarity)
- Disk persistence at STORAGE_ROOT/vector_db/
- Stable ID mapping (string chunk_id ↔ integer FAISS index)
- Idempotent upserts with document-level deletion
- Metadata filtering on search results
- NO silent fallback to MemoryVectorStore
"""
from __future__ import annotations

import copy
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..core.config import get_settings
from .interface import VectorStoreInterface
from .models import ChunkMetadata, SearchResult, VectorRecord

log = logging.getLogger("gen-transform.embeddings.faiss_store")


class FAISSVectorStore(VectorStoreInterface):
    """Production FAISS-backed persistent Vector Store.

    Uses FAISS IndexFlatIP for inner-product similarity on L2-normalized vectors
    (equivalent to cosine similarity). Persists the FAISS index binary and a
    JSON metadata sidecar to disk.

    Directory layout under persistence_dir:
        faiss.index       — FAISS binary index file
        metadata.json     — chunk ID mapping + ChunkMetadata + text payloads

    Thread-safety: All mutating operations are guarded by a reentrant lock.
    """

    # Default filenames inside persistence directory
    INDEX_FILENAME = "faiss.index"
    METADATA_FILENAME = "metadata.json"

    def __init__(
        self,
        persistence_dir: Optional[str] = None,
        dimension: int = 384,
        auto_save: bool = True,
    ) -> None:
        """Initialize FAISS vector store.

        Args:
            persistence_dir: Path to directory for index persistence.
                             Defaults to STORAGE_ROOT/vector_db.
            dimension: Embedding vector dimension. Must match the embedding model.
            auto_save: If True, automatically persist to disk after every mutation.
        """
        settings = get_settings()
        self._dimension = dimension or getattr(settings, "vector_dimension", 384)
        self._auto_save = auto_save
        self._lock = threading.RLock()

        if persistence_dir:
            self._persist_dir = Path(persistence_dir)
        else:
            self._persist_dir = Path(settings.storage_root) / "vector_db"

        # Create persistence directory
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        self._index_path = self._persist_dir / self.INDEX_FILENAME
        self._meta_path = self._persist_dir / self.METADATA_FILENAME

        # Metadata store: ordered list parallel to FAISS index rows
        # Each entry: {"id": str, "text": str, "metadata": dict}
        self._id_map: List[Dict[str, Any]] = []

        # Reverse lookup: chunk_id -> position in _id_map / FAISS index
        self._id_to_pos: Dict[str, int] = {}

        # Initialize FAISS
        try:
            import faiss
            self._faiss = faiss
        except ImportError as exc:
            raise RuntimeError(
                "FAISS is required for FAISSVectorStore but is not installed. "
                "Install with: pip install faiss-cpu (or faiss-gpu for GPU support)"
            ) from exc

        # Load existing index or create new one
        self._index = None
        self._load()

        if self._index is None:
            self._index = self._faiss.IndexFlatIP(self._dimension)
            log.info(
                "Created new FAISS IndexFlatIP (dim=%d) at '%s'",
                self._dimension,
                self._persist_dir,
            )
        else:
            log.info(
                "Loaded FAISS index with %d vectors (dim=%d) from '%s'",
                self._index.ntotal,
                self._dimension,
                self._persist_dir,
            )

    # ──────────────────────────────────────────────────
    # Persistence: Load / Save
    # ──────────────────────────────────────────────────

    def _load(self) -> None:
        """Load FAISS index and metadata from disk if available."""
        if self._index_path.exists() and self._meta_path.exists():
            try:
                self._index = self._faiss.read_index(str(self._index_path))
                with open(self._meta_path, "r", encoding="utf-8") as f:
                    self._id_map = json.load(f)
                self._rebuild_reverse_index()
                log.info(
                    "Loaded %d vectors from FAISS index at '%s'",
                    self._index.ntotal,
                    self._index_path,
                )
            except Exception as exc:
                log.error(
                    "Failed to load FAISS index from '%s': %s. Starting fresh.",
                    self._persist_dir,
                    exc,
                )
                self._index = None
                self._id_map = []
                self._id_to_pos = {}

    def _save(self) -> None:
        """Persist FAISS index and metadata to disk atomically."""
        try:
            self._persist_dir.mkdir(parents=True, exist_ok=True)

            # Write FAISS index
            temp_index = self._index_path.with_suffix(".tmp")
            self._faiss.write_index(self._index, str(temp_index))
            temp_index.replace(self._index_path)

            # Write metadata sidecar
            temp_meta = self._meta_path.with_suffix(".tmp")
            with open(temp_meta, "w", encoding="utf-8") as f:
                json.dump(self._id_map, f, indent=2, default=str)
            temp_meta.replace(self._meta_path)

            log.debug(
                "Persisted FAISS index (%d vectors) to '%s'",
                self._index.ntotal,
                self._persist_dir,
            )
        except Exception as exc:
            log.error("Failed to persist FAISS index to '%s': %s", self._persist_dir, exc)
            raise

    def _rebuild_reverse_index(self) -> None:
        """Rebuild chunk_id -> position mapping from _id_map."""
        self._id_to_pos = {entry["id"]: pos for pos, entry in enumerate(self._id_map)}

    # ──────────────────────────────────────────────────
    # Core Operations
    # ──────────────────────────────────────────────────

    def add_vectors(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> bool:
        """Add or upsert vectors into the FAISS index.

        Idempotent: if a chunk_id already exists, its vector and metadata are replaced.
        """
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError(
                f"Mismatched list lengths: ids={len(ids)}, vectors={len(vectors)}, metadata={len(metadata)}"
            )

        if not ids:
            return True

        with self._lock:
            # Handle upserts: remove existing entries for IDs that already exist
            existing_ids = [cid for cid in ids if cid in self._id_to_pos]
            if existing_ids:
                self._remove_ids(existing_ids)

            # Prepare numpy vectors
            vecs_np = np.array(vectors, dtype=np.float32)
            if vecs_np.shape[1] != self._dimension:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self._dimension}, got {vecs_np.shape[1]}"
                )

            # Add to FAISS index
            self._index.add(vecs_np)

            # Add metadata entries
            for cid, vec, meta in zip(ids, vectors, metadata):
                text = meta.get("text", "") if isinstance(meta, dict) else ""
                entry = {
                    "id": cid,
                    "text": text,
                    "metadata": meta if isinstance(meta, dict) else meta.model_dump() if hasattr(meta, "model_dump") else {},
                }
                self._id_map.append(entry)

            self._rebuild_reverse_index()

            if self._auto_save:
                self._save()

            log.info("Added %d vectors to FAISS index (total: %d)", len(ids), self._index.ntotal)

        return True

    def add_records(self, records: List[VectorRecord]) -> bool:
        """Batch insert typed VectorRecord instances."""
        if not records:
            return True

        ids = [rec.id for rec in records]
        vectors = [rec.vector for rec in records]
        metadata_list = []
        for rec in records:
            meta_dict = rec.metadata.model_dump()
            meta_dict["text"] = rec.text
            metadata_list.append(meta_dict)

        return self.add_vectors(ids, vectors, metadata_list)

    def similarity_search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Perform top-K inner-product similarity search with optional metadata filtering.

        For L2-normalized vectors, inner product equals cosine similarity.
        """
        if not query_vector or self._index.ntotal == 0:
            return []

        with self._lock:
            query_np = np.array([query_vector], dtype=np.float32)

            if query_np.shape[1] != self._dimension:
                raise ValueError(
                    f"Query vector dimension mismatch: expected {self._dimension}, got {query_np.shape[1]}"
                )

            # Search more results than needed if filtering is active
            search_k = min(top_k * 4, self._index.ntotal) if filter_dict else min(top_k, self._index.ntotal)

            scores, indices = self._index.search(query_np, search_k)

            results: List[SearchResult] = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(self._id_map):
                    continue

                entry = self._id_map[idx]
                meta = entry.get("metadata", {})

                # Apply metadata filtering
                if filter_dict:
                    match = True
                    for k, v in filter_dict.items():
                        if v is not None and meta.get(k) != v:
                            match = False
                            break
                    if not match:
                        continue

                # Clamp score to [0, 1] for normalized vectors
                clamped_score = max(0.0, min(1.0, float(score)))

                results.append(
                    SearchResult(
                        chunk_id=entry["id"],
                        score=round(clamped_score, 4),
                        text=entry.get("text", "") or meta.get("source_filename", ""),
                        document_id=meta.get("document_id", ""),
                        page=meta.get("page_start", 1),
                        section=meta.get("section", "Main"),
                        source_filename=meta.get("source_filename", ""),
                        metadata=meta,
                    )
                )

                if len(results) >= top_k:
                    break

            return results

    def delete_vectors(self, ids: List[str]) -> bool:
        """Remove specific vector IDs from the FAISS index.

        FAISS IndexFlatIP does not support in-place deletion, so we rebuild the index
        without the deleted vectors.
        """
        if not ids:
            return True

        with self._lock:
            to_remove = set(ids) & set(self._id_to_pos.keys())
            if not to_remove:
                return True

            self._remove_ids(list(to_remove))

            if self._auto_save:
                self._save()

            log.info("Deleted %d vectors from FAISS index (remaining: %d)", len(to_remove), self._index.ntotal)

        return True

    def delete_document_vectors(self, document_id: str) -> int:
        """Delete all vectors belonging to a specific document_id."""
        with self._lock:
            to_remove = [
                entry["id"]
                for entry in self._id_map
                if entry.get("metadata", {}).get("document_id") == document_id
            ]

            if not to_remove:
                log.info("No vectors found for document_id '%s'", document_id)
                return 0

            self._remove_ids(to_remove)

            if self._auto_save:
                self._save()

            log.info(
                "Deleted %d vectors for document_id '%s' (remaining: %d)",
                len(to_remove),
                document_id,
                self._index.ntotal,
            )

        return len(to_remove)

    def get_by_id(self, chunk_id: str) -> Optional[VectorRecord]:
        """Retrieve a single VectorRecord by chunk_id."""
        with self._lock:
            pos = self._id_to_pos.get(chunk_id)
            if pos is None:
                return None

            entry = self._id_map[pos]
            meta = entry.get("metadata", {})

            # Reconstruct vector from FAISS
            vec = self._index.reconstruct(pos)
            vector_list = [float(x) for x in vec]

            chunk_meta = ChunkMetadata(**meta) if not isinstance(meta, ChunkMetadata) else meta

            return VectorRecord(
                id=entry["id"],
                vector=vector_list,
                text=entry.get("text", ""),
                metadata=chunk_meta,
            )

    def get_document_vectors(self, document_id: str) -> List[VectorRecord]:
        """Retrieve all VectorRecords for a specific document_id."""
        with self._lock:
            results = []
            for pos, entry in enumerate(self._id_map):
                meta = entry.get("metadata", {})
                if meta.get("document_id") == document_id:
                    vec = self._index.reconstruct(pos)
                    vector_list = [float(x) for x in vec]
                    chunk_meta = ChunkMetadata(**meta) if not isinstance(meta, ChunkMetadata) else meta
                    results.append(
                        VectorRecord(
                            id=entry["id"],
                            vector=vector_list,
                            text=entry.get("text", ""),
                            metadata=chunk_meta,
                        )
                    )
            return results

    def clear(self) -> None:
        """Empty the entire FAISS vector store and remove persisted files."""
        with self._lock:
            self._index = self._faiss.IndexFlatIP(self._dimension)
            self._id_map = []
            self._id_to_pos = {}

            if self._auto_save:
                self._save()

            log.info("Cleared FAISS vector store at '%s'", self._persist_dir)

    # ──────────────────────────────────────────────────
    # Internal Helpers
    # ──────────────────────────────────────────────────

    def _remove_ids(self, ids_to_remove: List[str]) -> None:
        """Remove specific IDs by rebuilding the FAISS index without them.

        This is called within an already-acquired lock context.
        FAISS IndexFlat does not support in-place removal, so we:
        1. Collect all vectors NOT being removed
        2. Rebuild the index from the remaining vectors
        3. Rebuild the metadata map
        """
        remove_set = set(ids_to_remove)
        keep_positions = [
            pos for pos, entry in enumerate(self._id_map)
            if entry["id"] not in remove_set
        ]

        if len(keep_positions) == len(self._id_map):
            return  # Nothing to remove

        # Collect remaining vectors
        if keep_positions:
            remaining_vecs = np.array(
                [self._index.reconstruct(pos) for pos in keep_positions],
                dtype=np.float32,
            )
            remaining_meta = [self._id_map[pos] for pos in keep_positions]
        else:
            remaining_vecs = np.empty((0, self._dimension), dtype=np.float32)
            remaining_meta = []

        # Rebuild index
        self._index = self._faiss.IndexFlatIP(self._dimension)
        if len(remaining_vecs) > 0:
            self._index.add(remaining_vecs)

        self._id_map = remaining_meta
        self._rebuild_reverse_index()

    # ──────────────────────────────────────────────────
    # Status & Diagnostics
    # ──────────────────────────────────────────────────

    @property
    def total_vectors(self) -> int:
        """Total number of vectors in the index."""
        return self._index.ntotal if self._index else 0

    @property
    def dimension(self) -> int:
        """Vector dimensionality."""
        return self._dimension

    @property
    def persistence_dir(self) -> Path:
        """Path to the persistence directory."""
        return self._persist_dir

    @property
    def is_persisted(self) -> bool:
        """Check if index files exist on disk."""
        return self._index_path.exists() and self._meta_path.exists()

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the FAISS vector store."""
        return {
            "backend": "faiss",
            "index_type": "IndexFlatIP",
            "dimension": self._dimension,
            "total_vectors": self.total_vectors,
            "persistence_dir": str(self._persist_dir),
            "is_persisted": self.is_persisted,
            "auto_save": self._auto_save,
            "index_file_exists": self._index_path.exists(),
            "metadata_file_exists": self._meta_path.exists(),
        }

    def force_save(self) -> None:
        """Manually trigger persistence (useful when auto_save=False)."""
        with self._lock:
            self._save()


__all__ = ["FAISSVectorStore"]
