"""Neo4j Knowledge Graph Architectural Boundary Interface (Phase 2 Boundary Preparation).

Full implementation belongs to Phase 5.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class GraphStoreInterface(ABC):
    """Abstract interface for Knowledge Graph persistence."""

    @abstractmethod
    def add_entity(self, entity_id: str, label: str, properties: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        pass

    @abstractmethod
    def query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        pass
