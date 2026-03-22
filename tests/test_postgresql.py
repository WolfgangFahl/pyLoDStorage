"""
test_postgresql.py

Tests for lodstorage.postgresql — PostgreSqlQuery with mocked psycopg2.

Created on 2026-03-22

@author: wf
"""

import unittest
from unittest.mock import MagicMock, patch

from lodstorage.query import Endpoint
from lodstorage.sql_backend import PostgreSqlQuery, SQLBackend, get_sql_backend
from tests.basetest import Basetest

postgresql_available = PostgreSqlQuery is not None


class TestPostgreSqlQuery(Basetest):
    """
    Verify PostgreSqlQuery with mocked psycopg2.
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def postgresql_endpoint(self) -> Endpoint:
        """Return an Endpoint configured for PostgreSQL."""
        ep = Endpoint()
        ep.endpoint = "jdbc:postgresql"
        ep.host = "127.0.0.1"
        ep.port = 5432
        ep.user = "postgres"
        ep.password = "testpass"
        ep.database = "template1"
        return ep

    @unittest.skipUnless(postgresql_available, "psycopg2 not installed")
    def testProtocolConformance(self):
        """PostgreSqlQuery must satisfy SQLBackend at runtime."""
        with patch("lodstorage.postgresql.psycopg2"):
            pq = PostgreSqlQuery(endpoint=self.postgresql_endpoint())
            self.assertIsInstance(pq, SQLBackend)

    @unittest.skipUnless(postgresql_available, "psycopg2 not installed")
    def testFactoryRouting(self):
        """Factory must route jdbc:postgresql Endpoint -> PostgreSqlQuery."""
        backend = get_sql_backend(self.postgresql_endpoint())
        self.assertIsInstance(backend, PostgreSqlQuery)

    @unittest.skipUnless(postgresql_available, "psycopg2 not installed")
    @patch("lodstorage.postgresql.psycopg2")
    def testQuery(self, mock_psycopg2):
        """query() returns a list of dicts from mocked cursor."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"datname": "template1"},
            {"datname": "n8n"},
        ]
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        pq = PostgreSqlQuery(endpoint=self.postgresql_endpoint())
        rows = pq.query("SELECT datname FROM pg_database")

        self.assertEqual(2, len(rows))
        self.assertEqual("template1", rows[0]["datname"])
        self.assertEqual("n8n", rows[1]["datname"])
        mock_cursor.execute.assert_called_once_with("SELECT datname FROM pg_database")
        mock_connection.close.assert_called_once()

    @unittest.skipUnless(postgresql_available, "psycopg2 not installed")
    @patch("lodstorage.postgresql.psycopg2")
    def testQueryGen(self, mock_psycopg2):
        """query_gen() yields rows one by one from mocked cursor."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"datname": "template1"},
            {"datname": "n8n"},
            None,
        ]
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        pq = PostgreSqlQuery(endpoint=self.postgresql_endpoint())
        names = [r["datname"] for r in pq.query_gen("SELECT datname FROM pg_database")]

        self.assertEqual(["template1", "n8n"], names)
        mock_cursor.close.assert_called_once()
        mock_connection.close.assert_called_once()

    @unittest.skipUnless(postgresql_available, "psycopg2 not installed")
    @patch("lodstorage.postgresql.psycopg2")
    def testDecodeBytes(self, mock_psycopg2):
        """Binary values should be decoded to UTF-8 strings."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"name": b"caf\xc3\xa9"},
        ]
        mock_connection = MagicMock()
        mock_psycopg2.connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        pq = PostgreSqlQuery(endpoint=self.postgresql_endpoint())
        rows = pq.query("SELECT name FROM test")

        self.assertEqual(1, len(rows))
        self.assertEqual("café", rows[0]["name"])

    def testFactoryRaisesWithoutPsycopg2(self):
        """Factory must raise if psycopg2 is not installed."""
        ep = self.postgresql_endpoint()
        with patch("lodstorage.sql_backend.PostgreSqlQuery", None):
            with self.assertRaises(Exception) as ctx:
                get_sql_backend(ep)
            self.assertIn("psycopg2", str(ctx.exception))
