"""
postgresql.py:

PostgreSQL support

"""

import logging
from typing import Any, Dict, Generator, List

import psycopg2
import psycopg2.extras

from lodstorage.query import Endpoint


class PostgreSqlQuery:
    """
    A class to manage and execute PostgreSQL queries with optional debugging.

    Attributes:
        endpoint_info (Endpoint): endpoint configuration.
        debug (bool): Flag to enable debugging.
    """

    def __init__(self, endpoint: Endpoint, debug: bool = False):
        """
        Initializes the PostgreSqlQuery class.

        Args:
            endpoint (Endpoint): endpoint configuration.
            debug (bool): Flag to enable debugging.
        """
        self.db_params = {
            "host": endpoint.host or "localhost",
            "port": endpoint.port or 5432,
            "user": endpoint.user or "postgres",
            "password": endpoint.password,
            "dbname": endpoint.database,
        }

        self.debug = debug

    def get_cursor(self, query: str):
        if self.debug:
            logging.debug(f"Executing query: {query}")
            logging.debug(f"With connection parameters: {self.db_params}")

        connection = psycopg2.connect(**self.db_params)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return connection, cursor

    def decode_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts binary values to UTF-8 strings.

        Args:
            record (Dict[str, Any]): Raw database row data

        Returns:
            Dict[str, Any]: Data with binary values decoded to strings
        """
        decoded_record = {}
        for key, value in record.items():
            if isinstance(value, (bytes, memoryview)):
                decoded_record[key] = (
                    bytes(value).decode("utf-8", errors="replace")
                    if isinstance(value, memoryview)
                    else value.decode("utf-8", errors="replace")
                )
            else:
                decoded_record[key] = value
        return decoded_record

    def execute_sql_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes an SQL query using the provided connection parameters.

        Args:
            query (str): The SQL query to execute.

        Returns:
            list: A list of dictionaries representing the query results.
        """
        connection, cursor = self.get_cursor(query)
        cursor.execute(query)
        raw_lod = cursor.fetchall()
        connection.close()
        lod = []
        for raw_row in raw_lod:
            row = self.decode_record(dict(raw_row))
            lod.append(row)
        return lod

    def query_generator(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generator for fetching records one by one from a SQL query.
        """
        connection, cursor = self.get_cursor(query)
        try:
            cursor.execute(query)
            while True:
                raw_record = cursor.fetchone()
                if not raw_record:
                    break
                record = self.decode_record(dict(raw_record))
                yield record

        finally:
            cursor.close()
            connection.close()

    def query(self, sql: str, params: Any = None) -> List[Dict[str, Any]]:
        """
        SQLBackend protocol alias for execute_sql_query.

        Args:
            sql: the SQL query to execute
            params: ignored (not yet supported at the psycopg2 layer)

        Returns:
            list of dicts, one per row
        """
        return self.execute_sql_query(sql)

    def query_gen(
        self, sql: str, params: Any = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        SQLBackend protocol alias for query_generator.

        Args:
            sql: the SQL query to execute
            params: ignored (not yet supported at the psycopg2 layer)

        Yields:
            one dict per row
        """
        return self.query_generator(sql)
