"""
sql_backend.py

Unified SQL backend abstraction for pyLoDStorage.

Defines the SQLBackend Protocol (duck-typed interface) and the
get_sql_backend() factory that resolves the correct backend from
an endpoint descriptor, hiding the jdbc:mysql routing detail from
all call sites.

Created on 2026-02-21

@author: wf
"""

from typing import Any, Generator, Protocol, runtime_checkable

from lodstorage.mysql import MySqlQuery
from lodstorage.sql import SQLDB


@runtime_checkable
class SQLBackend(Protocol):
    """
    Protocol (structural duck-type interface) for SQL query backends.

    Any object that provides query() and query_gen() with the signatures
    below satisfies this protocol without explicit inheritance.

    Currently implemented by:
        - lodstorage.sql.SQLDB        (SQLite)
        - lodstorage.mysql.MySqlQuery  (MySQL / MariaDB)
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
    Endpoint object. The jdbc:mysql routing discriminator is encapsulated
    here so callers never need to inspect the endpoint URL themselves.

    Args:
        endpoint: a str (SQLite path / ':memory:') or lodstorage.query.Endpoint
        debug: enable debug output on the returned backend

    Returns:
        SQLBackend — either an SQLDB (SQLite) or MySqlQuery (MySQL/MariaDB)
    """
    if isinstance(endpoint, str):
        backend = SQLDB(dbname=endpoint, debug=debug)
        return backend

    # Endpoint object — route on the connection URL prefix
    url = getattr(endpoint, "endpoint", "") or ""
    if url.startswith("jdbc:mysql"):
        backend = MySqlQuery(endpoint=endpoint, debug=debug)
        return backend

    backend = SQLDB(dbname=url, debug=debug)
    return backend
