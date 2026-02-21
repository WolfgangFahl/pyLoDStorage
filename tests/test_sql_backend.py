"""
test_sql_backend.py

Tests for lodstorage.sql_backend — the SQLBackend Protocol and
get_sql_backend() factory.

Created on 2026-02-21

@author: wf
"""

from lodstorage.mysql import MySqlQuery
from lodstorage.query import Endpoint
from lodstorage.sql import SQLDB
from lodstorage.sql_backend import SQLBackend, get_sql_backend
from tests.basetest import Basetest


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
        """Both SQLDB and MySqlQuery must satisfy SQLBackend at runtime."""
        self.assertIsInstance(self.db, SQLBackend)
        self.assertIsInstance(MySqlQuery(endpoint=self.mysql_endpoint()), SQLBackend)

    def testFactoryRouting(self):
        """Factory must route str→SQLDB and jdbc:mysql Endpoint→MySqlQuery."""
        self.assertIsInstance(get_sql_backend(SQLDB.RAM), SQLDB)
        self.assertIsInstance(get_sql_backend(self.sqlite_endpoint()), SQLDB)
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
