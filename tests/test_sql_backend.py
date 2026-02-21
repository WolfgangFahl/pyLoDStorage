"""
test_sql_backend.py

Tests for lodstorage.sql_backend — the SQLBackend Protocol and
get_sql_backend() factory.

Created on 2026-02-21

@author: wf
"""

import unittest

from lodstorage.query import Endpoint
from lodstorage.sql import SQLDB
from lodstorage.sql_backend import DuckDBQuery, MySqlQuery, SQLBackend, get_sql_backend
from tests.basetest import Basetest

mysql_available = MySqlQuery is not None
duckdb_available = DuckDBQuery is not None


class TestSQLBackend(Basetest):
    """
    Verify the SQLBackend Protocol and the get_sql_backend() factory.
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.db: SQLDB = SQLDB(SQLDB.RAM)
        self.db.execute("CREATE TABLE person (name TEXT, age INTEGER)")
        self.db.execute("INSERT INTO person VALUES ('Alice', 30)")
        self.db.execute("INSERT INTO person VALUES ('Bob', 25)")

    def tearDown(self):
        self.db.close()
        Basetest.tearDown(self)

    def sqlite_endpoint(self, path: str = SQLDB.RAM) -> Endpoint:
        """Return an Endpoint configured for SQLite."""
        ep = Endpoint()
        ep.endpoint = path
        return ep

    def duckdb_endpoint(self, path: str = ":memory:") -> Endpoint:
        """Return an Endpoint configured for DuckDB."""
        ep = Endpoint()
        ep.endpoint = "jdbc:duckdb"
        ep.database = path
        return ep

    def mysql_endpoint(
        self, url: str = "jdbc:mysql://localhost:3306/testdb"
    ) -> Endpoint:
        """Return a minimal Endpoint configured for MySQL (no live connection needed)."""
        ep = Endpoint()
        ep.endpoint = url
        ep.host = "localhost"
        ep.port = 3306
        ep.user = "root"
        ep.password = ""
        ep.database = "testdb"
        ep.charset = "utf8mb4"
        return ep

    def testProtocolConformance(self):
        """SQLDB must satisfy SQLBackend; optional backends checked when available."""
        self.assertIsInstance(self.db, SQLBackend)

    @unittest.skipUnless(duckdb_available, "duckdb not installed")
    def testDuckDBProtocolConformance(self):
        """DuckDBQuery must satisfy SQLBackend at runtime."""
        self.assertIsInstance(DuckDBQuery(endpoint=self.duckdb_endpoint()), SQLBackend)

    @unittest.skipUnless(mysql_available, "PyMySQL not installed")
    def testMySQLProtocolConformance(self):
        """MySqlQuery must satisfy SQLBackend at runtime."""
        self.assertIsInstance(MySqlQuery(endpoint=self.mysql_endpoint()), SQLBackend)

    def testFactoryRoutingSQLite(self):
        """Factory must route str→SQLDB and sqlite Endpoint→SQLDB."""
        self.assertIsInstance(get_sql_backend(SQLDB.RAM), SQLDB)
        self.assertIsInstance(get_sql_backend(self.sqlite_endpoint()), SQLDB)

    @unittest.skipUnless(duckdb_available, "duckdb not installed")
    def testFactoryRoutingDuckDB(self):
        """Factory must route jdbc:duckdb Endpoint→DuckDBQuery."""
        self.assertIsInstance(get_sql_backend(self.duckdb_endpoint()), DuckDBQuery)

    @unittest.skipUnless(mysql_available, "PyMySQL not installed")
    def testFactoryRoutingMySQL(self):
        """Factory must route jdbc:mysql Endpoint→MySqlQuery."""
        self.assertIsInstance(get_sql_backend(self.mysql_endpoint()), MySqlQuery)

    def testQuery(self):
        """query() returns a correctly ordered list of dicts."""
        rows = self.db.query("SELECT name, age FROM person ORDER BY age")
        self.assertEqual(2, len(rows))
        self.assertEqual("Bob", rows[0]["name"])
        self.assertEqual("Alice", rows[1]["name"])

    def testQueryGen(self):
        """query_gen() yields the same rows as query()."""
        names = [
            r["name"]
            for r in self.db.query_gen("SELECT name FROM person ORDER BY name")
        ]
        self.assertEqual(["Alice", "Bob"], names)

    @unittest.skipUnless(duckdb_available, "duckdb not installed")
    def testDuckDBQuery(self):
        """DuckDBQuery must execute query() and query_gen() correctly."""
        duck = DuckDBQuery(endpoint=self.duckdb_endpoint())
        duck.con.execute("CREATE TABLE person (name TEXT, age INTEGER)")
        duck.con.execute("INSERT INTO person VALUES ('Alice', 30), ('Bob', 25)")
        rows = duck.query("SELECT name, age FROM person ORDER BY age")
        self.assertEqual(2, len(rows))
        self.assertEqual("Bob", rows[0]["name"])
        self.assertEqual("Alice", rows[1]["name"])
        names = [
            r["name"] for r in duck.query_gen("SELECT name FROM person ORDER BY name")
        ]
        self.assertEqual(["Alice", "Bob"], names)
