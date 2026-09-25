"""Phase 14 Provenance Engine — Internal Models & Data Structures.

Provides domain representations for provenance nodes, directional edges,
and lookup indices used during graph traversal and lineage building.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProvenanceGraphNode:
    """Internal graph node for lineage resolution."""
    node_id: str
    node_type: str
    content: str = ""
    document_id: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    incoming_edges: List[str] = field(default_factory=list)
    outgoing_edges: List[str] = field(default_factory=list)


@dataclass
class ProvenanceGraphEdge:
    """Internal graph edge for lineage resolution."""
    edge_id: str
    source_id: str
    target_id: str
    relationship: str
    metadata: Dict[str, Any] = field(default_factory=dict)


__all__ = ["ProvenanceGraphNode", "ProvenanceGraphEdge"]
