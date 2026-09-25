"""Phase 14 Provenance Engine — Append-Oriented Repository.

Provides persistent file-based JSON storage for OutputProvenance, ClaimProvenance,
EvidenceRecord, and ProvenanceRecord objects adhering to the existing project storage patterns.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .schemas import (
    ClaimProvenance,
    EvidenceRecord,
    OutputProvenance,
    ProvenanceRecord,
)

log = logging.getLogger("gen-transform.provenance.repository")


class ProvenanceRepository:
    """Repository handling read/write persistence for provenance records."""

    def __init__(self, storage_dir: str = "data/provenance") -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.output_file = self.storage_dir / "outputs.json"
        self.claims_file = self.storage_dir / "claims.json"
        self.evidence_file = self.storage_dir / "evidence.json"
        self.records_file = self.storage_dir / "records.json"

        # In-memory indices for speed
        self._outputs: Dict[str, OutputProvenance] = {}
        self._claims: Dict[str, ClaimProvenance] = {}
        self._evidence: Dict[str, EvidenceRecord] = {}
        self._records: List[ProvenanceRecord] = []

        self._load_all()

    def _load_json(self, path: Path) -> List[Dict]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Failed to load provenance file {path}: {e}")
            return []

    def _save_json(self, path: Path, data: List[Dict]) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Failed to save provenance file {path}: {e}")

    def _load_all(self) -> None:
        """Load stored records from disk into memory indices."""
        raw_outputs = self._load_json(self.output_file)
        for item in raw_outputs:
            obj = OutputProvenance.model_validate(item)
            self._outputs[obj.output_id] = obj

        raw_claims = self._load_json(self.claims_file)
        for item in raw_claims:
            obj = ClaimProvenance.model_validate(item)
            self._claims[obj.claim_id] = obj

        raw_evidence = self._load_json(self.evidence_file)
        for item in raw_evidence:
            obj = EvidenceRecord.model_validate(item)
            self._evidence[obj.evidence_id] = obj

        raw_records = self._load_json(self.records_file)
        for item in raw_records:
            obj = ProvenanceRecord.model_validate(item)
            self._records.append(obj)

    def save_output_provenance(self, output_prov: OutputProvenance) -> None:
        """Append or update OutputProvenance."""
        self._outputs[output_prov.output_id] = output_prov
        data = [o.model_dump() for o in self._outputs.values()]
        self._save_json(self.output_file, data)

    def save_claims(self, claims: List[ClaimProvenance]) -> None:
        """Append or update ClaimProvenance list."""
        for c in claims:
            self._claims[c.claim_id] = c
        data = [c.model_dump() for c in self._claims.values()]
        self._save_json(self.claims_file, data)

    def save_evidence(self, evidence_list: List[EvidenceRecord]) -> None:
        """Append or update EvidenceRecord list."""
        for e in evidence_list:
            self._evidence[e.evidence_id] = e
        data = [e.model_dump() for e in self._evidence.values()]
        self._save_json(self.evidence_file, data)

    def save_records(self, records: List[ProvenanceRecord]) -> None:
        """Append ProvenanceRecord directional links."""
        self._records.extend(records)
        data = [r.model_dump() for r in self._records]
        self._save_json(self.records_file, data)

    def get_output(self, output_id: str) -> Optional[OutputProvenance]:
        return self._outputs.get(output_id)

    def get_claim(self, claim_id: str) -> Optional[ClaimProvenance]:
        return self._claims.get(claim_id)

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceRecord]:
        return self._evidence.get(evidence_id)

    def get_claims_for_output(self, output_id: str) -> List[ClaimProvenance]:
        return [c for c in self._claims.values() if c.output_id == output_id]

    def get_records_by_source(self, source_id: str) -> List[ProvenanceRecord]:
        return [r for r in self._records if r.source_id == source_id]

    def get_records_by_target(self, target_id: str) -> List[ProvenanceRecord]:
        return [r for r in self._records if r.target_id == target_id]

    def get_all_outputs(self) -> List[OutputProvenance]:
        return list(self._outputs.values())

    def get_all_evidence(self) -> List[EvidenceRecord]:
        return list(self._evidence.values())


__all__ = ["ProvenanceRepository"]
