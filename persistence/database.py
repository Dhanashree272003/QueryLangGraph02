"""
Persistence Database Module for Query LangGraph (querylanggraph02).

Manages SQLite connection pooling, context management, and thread-safe session execution
against the shared AIOps persistence database (aiops.db).
"""

import os
import sqlite3
import logging
from typing import Generator, Optional, Dict, Any, List, Tuple
from contextlib import contextmanager

logger = logging.getLogger("QueryLangGraph.Persistence.Database")


class DatabaseManager:
    """
    SQLite Database Manager for AIOps Persistence Layer.
    
    Reads from the shared SQLite database populated by the Inference Graph.
    """

    DEFAULT_DB_PATH = os.path.join(
        os.path.dirname(__file__), "aiops.db"
    )

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize DatabaseManager with database file path.

        Args:
            db_path (Optional[str]): Absolute path to SQLite database file.
        """
        self.db_path = db_path or os.environ.get("AIOPS_DB_PATH") or self.DEFAULT_DB_PATH
        self._ensure_database_schema_exists()

    def _ensure_database_schema_exists(self) -> None:
        """Initializes tables using persistence/schema.sql if aiops.db doesn't exist or is missing tables."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        schema_file = os.path.join(os.path.dirname(__file__), "schema.sql")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if os.path.exists(schema_file):
                    with open(schema_file, "r", encoding="utf-8") as f:
                        schema_sql = f.read()
                    cursor.executescript(schema_sql)
                    logger.info(f"DatabaseManager: Applied schema from '{schema_file}' to '{self.db_path}'")

                # Create query execution history table if not present in schema.sql
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id VARCHAR(100),
                    user_query TEXT,
                    parsed_intent TEXT,
                    status VARCHAR(50),
                    execution_time_ms REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """)

                conn.commit()
                logger.info(f"DatabaseManager: Verified persistence schema at '{self.db_path}'")
        except Exception as e:
            logger.error(f"DatabaseManager: Failed schema verification/creation: {e}")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for acquiring SQLite connections.

        Yields:
            sqlite3.Connection: Thread-safe connection instance with dictionary rows.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        """
        Executes parameterized SELECT SQL query and returns list of dictionaries.

        Args:
            sql (str): Parameterized SQL query string.
            params (Optional[Tuple[Any, ...]]): Tuple of binding parameters.

        Returns:
            List[Dict[str, Any]]: Query result rows as dictionaries.
        """
        params = params or ()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                logger.debug(f"DatabaseManager: Executing SQL: {sql} | Params: {params}")
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"DatabaseManager: Query execution failed: {e} | SQL: {sql}")
            raise RuntimeError(f"Database execution error: {e}") from e


# Global instance default
db_manager = DatabaseManager()
