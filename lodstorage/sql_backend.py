"""
sql_backend.py

Unified SQL backend abstraction for pyLoDStorage.

Defines the SQLBackend Protocol (duck-typed interface) and the
get_sql_backend() factory that resolves the correct backend from
an endpoint descriptor, hiding the jdbc:mysql, jdbc:duckdb, and jdbc:postgresql
routing details from all call sites.

Created on 2026-02-21

@author: wf
"""

from typing import Any, Generator, Optional, Protocol, Type, runtime_checkable

from lodstorage.sql import SQLDB

try:
    from lodstorage.mysql import MySqlQuery
except ImportError:
    MySqlQuery = None  # type: ignore

try:
    from lodstorage.duckdb_query import DuckDBQuery
except ImportError:
    DuckDBQuery = None  # type: ignore

try:
    from lodstorage.postgresql import PostgreSqlQuery
except ImportError:
    PostgreSqlQuery = None  # type: ignore


@runtime_checkable
class SQLBackend(Protocol):
    """
    Protocol (structural duck-type interface) for SQL query backends.

    Any object that provides query() and query_gen() with the signatures
    below satisfies this protocol without explicit inheritance.

    Currently implemented by:
        - lodstorage.sql.SQLDB              (SQLite, always available)
        - lodstorage.mysql.MySqlQuery       (MySQL/MariaDB, optional: pip install pyLodStorage[mysql])
        - lodstorage.duckdb_query.DuckDBQuery (DuckDB, optional: pip install pyLodStorage[duckdb])
        - lodstorage.postgresql.PostgreSqlQuery (PostgreSQL, optional: pip install pyLodStorage[postgresql])
    """

    def query(self, sql: str, params: Any = None) -> list[dict]:
        """
        Execute an SQL query and return all results eagerly.

        Args:
            sql: the SQL query string to execute
            params: optional query parameters (support depends on backend)

        Returns:
            list of dicts, one per row
        """
        pass

    def query_gen(self, sql: str, params: Any = None) -> Generator[dict, None, None]:
        """
        Execute an SQL query and yield results one row at a time.

        Args:
            sql: the SQL query string to execute
            params: optional query parameters (support depends on backend)

        Yields:
            one dict per row
        """
        pass


def get_sql_backend(endpoint, debug: bool = False) -> SQLBackend:
    """
    Return the appropriate SQL backend for the given endpoint.

    Accepts either a plain string (SQLite file path or ':memory:') or an
    Endpoint object. The jdbc:mysql and jdbc:duckdb routing discriminators
    are encapsulated here so callers never need to inspect the endpoint URL.

    Args:
        endpoint: a str (SQLite path / ':memory:') or lodstorage.query.Endpoint
        debug: enable debug output on the returned backend

    Returns:
        SQLBackend — SQLDB, MySqlQuery, DuckDBQuery, or PostgreSqlQuery depending on endpoint

    Raises:
        Exception: if the requested backend's optional dependency is not installed
    """
    if isinstance(endpoint, str):
        backend = SQLDB(dbname=endpoint, debug=debug)
        return backend

    # Endpoint object — route on the connection URL prefix
    url = getattr(endpoint, "endpoint", "") or ""

    if url.startswith("jdbc:mysql"):
        if MySqlQuery is None:
            raise Exception(
                "MySQL backend requested but PyMySQL is not installed. "
                "Install it with: pip install pyLodStorage[mysql]"
            )
        backend = MySqlQuery(endpoint=endpoint, debug=debug)
        return backend

    if url.startswith("jdbc:duckdb"):
        if DuckDBQuery is None:
            raise Exception(
                "DuckDB backend requested but duckdb is not installed. "
                "Install it with: pip install pyLodStorage[duckdb]"
            )
        backend = DuckDBQuery(endpoint=endpoint, debug=debug)
        return backend

    if url.startswith("jdbc:postgresql"):
        if PostgreSqlQuery is None:
            raise Exception(
                "PostgreSQL backend requested but psycopg2 is not installed. "
                "Install it with: pip install pyLodStorage[postgresql]"
            )
        backend = PostgreSqlQuery(endpoint=endpoint, debug=debug)
        return backend

    backend = SQLDB(dbname=url, debug=debug)
    return backend
