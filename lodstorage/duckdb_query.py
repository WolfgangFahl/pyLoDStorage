"""
duckdb_query.py

DuckDB backend for pyLoDStorage.

Created on 2026-02-21

@author: wf
"""

import logging
from typing import Any, Generator

import duckdb

from lodstorage.query import Endpoint


class DuckDBQuery:
    """
    A class to manage and execute DuckDB queries.

    Attributes:
        path (str): path to the DuckDB database file, or ':memory:'.
        debug (bool): flag to enable debugging.
    """

    RAM = ":memory:"

    def __init__(self, endpoint: Endpoint, debug: bool = False):
        """
        Initialise with the given endpoint configuration.

        Args:
            endpoint (Endpoint): endpoint configuration; endpoint.database
                holds the file path or ':memory:'.
            debug (bool): flag to enable debugging.
        """
        self.path = endpoint.database or DuckDBQuery.RAM
        self.debug = debug
        self.con = duckdb.connect(self.path)

    def query(self, sql: str, params: Any = None) -> list[dict]:
        """
        Execute an SQL query and return all results eagerly.

        Args:
            sql: the SQL query string to execute
            params: optional positional parameters (list or tuple)

        Returns:
            list of dicts, one per row
        """
        if self.debug:
            logging.debug(f"DuckDBQuery.query: {sql!r} params={params}")
        rel = self.con.execute(sql, params or [])
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()
        result = [dict(zip(cols, row)) for row in rows]
        return result

    def query_gen(self, sql: str, params: Any = None) -> Generator[dict, None, None]:
        """
        Execute an SQL query and yield results one row at a time.

        Args:
            sql: the SQL query string to execute
            params: optional positional parameters (list or tuple)

        Yields:
            one dict per row
        """
        if self.debug:
            logging.debug(f"DuckDBQuery.query_gen: {sql!r} params={params}")
        rel = self.con.execute(sql, params or [])
        cols = [d[0] for d in rel.description]
        while True:
            row = rel.fetchone()
            if row is None:
                break
            record = dict(zip(cols, row))
            yield record
