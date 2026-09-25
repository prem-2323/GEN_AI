"""Neo4j Driver Adapter (Phase 5).

Provides a clean interface for Neo4j driver connection management,
session scopes, transactional Cypher execution, and connectivity verification.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..core.config import get_settings

log = logging.getLogger("gen-transform.graph.neo4j")


class Neo4jDriverAdapter:
    """Encapsulates official Neo4j Python driver connection & transaction lifecycle."""

    def __init__(
        self,
        uri: str = "",
        username: str = "",
        password: str = "",
        database: str = "",
    ) -> None:
        settings = get_settings()
        self.uri = uri or settings.neo4j_uri
        self.username = username or settings.neo4j_username
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database
        self._driver = None

    def get_driver(self) -> Any:
        """Lazy-initialize official Neo4j Driver instance."""
        if self._driver is not None:
            return self._driver

        try:
            from neo4j import GraphDatabase

            log.info("Initializing Neo4j driver connection to %s (database: %s)", self.uri, self.database)
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=300,
                max_connection_pool_size=50,
                connection_acquisition_timeout=10.0,
            )
            return self._driver
        except Exception as exc:
            log.warning("Failed to initialize Neo4j driver: %s", exc)
            self._driver = None
            return None

    def connect(self) -> Any:
        """Explicitly connect and verify Neo4j driver."""
        driver = self.get_driver()
        if driver is None:
            raise ConnectionError(f"Could not initialize Neo4j driver to {self.uri}")
        try:
            driver.verify_connectivity()
            return driver
        except Exception as exc:
            raise ConnectionError(f"Failed to connect to Neo4j database at {self.uri}: {exc}") from exc

    def verify_connectivity(self) -> bool:
        """Check if Neo4j database is reachable and authenticated."""
        try:
            driver = self.get_driver()
            if driver is None:
                return False
            driver.verify_connectivity()
            return True
        except Exception as exc:
            log.debug("Neo4j connectivity check failed: %s", exc)
            return False

    def execute_transaction(self, work_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute write transaction scope with automatic commit/rollback."""
        driver = self.connect()
        with driver.session(database=self.database) as session:
            return session.execute_write(work_fn, *args, **kwargs)

    def execute_write(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute Cypher write transaction and return records."""
        driver = self.connect()
        with driver.session(database=self.database) as session:
            result = session.run(cypher, parameters=params or {})
            return [record.data() for record in result]

    def execute_read(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute Cypher read query and return records."""
        driver = self.connect()
        with driver.session(database=self.database) as session:
            result = session.run(cypher, parameters=params or {})
            return [record.data() for record in result]

    def execute_query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute Cypher query and return list of result record dicts."""
        return self.execute_read(cypher, params)

    def close(self) -> None:
        """Gracefully close Neo4j driver connection pool."""
        if self._driver is not None:
            try:
                self._driver.close()
                log.info("Neo4j driver connection closed.")
            except Exception as exc:
                log.warning("Error closing Neo4j driver: %s", exc)
            finally:
                self._driver = None


__all__ = ["Neo4jDriverAdapter"]
