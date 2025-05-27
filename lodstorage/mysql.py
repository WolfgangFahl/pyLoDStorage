"""
mysql.py:

MySQL and MariaDB support

"""

import logging
from typing import Any, Dict, Generator, List

import pymysql

from lodstorage.query import Endpoint


class MySqlQuery:
    """
    A class to manage and execute mySQL queries with optional debugging.

    Attributes:
        endpoint_info (Endpoint): endpoint configuration.
        debug (bool): Flag to enable debugging.
    """

    def __init__(self, endpoint: Endpoint, debug: bool = False):
        """
        Initializes the Query class with command-line arguments.

        Args:
            endpoint (Endpoint): endpoint configuration.
            debug (bool): Flag to enable debugging.
        """
        self.db_params = {
            "host": endpoint.host or "localhost",
            "port": endpoint.port or 3306,
            "user": endpoint.user or "root",
            "password": endpoint.password,
            "database": endpoint.database,
            "charset": endpoint.charset or "utf8mb4",
        }

        self.debug = debug

    def get_cursor(self, query: str):
        if self.debug:
            logging.debug(f"Executing query: {query}")
            logging.debug(f"With connection parameters: {self.db_params}")

        connection = pymysql.connect(**self.db_params)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        return connection, cursor

    def execute_sql_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes an SQL query using the provided connection parameters.

        Args:
            query (str): The SQL query to execute.
            connection_params (dict): Database connection parameters.

        Returns:
            list: A list of dictionaries representing the query results.
        """
        connection, cursor = self.get_cursor(query)
        cursor.execute(query)
        result = cursor.fetchall()
        connection.close()
        return result

    def query_generator(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generator for fetching records one by one from a SQL query.
        """
        connection, cursor = self.get_cursor(query)
        try:
            cursor.execute(query)
            while True:
                record = cursor.fetchone()
                if not record:
                    break
                yield record

        finally:
            cursor.close()
            connection.close()
