"""
Created on 2026-02-21

@author: wf
"""

import os
import tempfile

import yaml

from lodstorage.multilang_querymanager import MultiLanguageQueryManager
from lodstorage.sql import SQLDB
from tests.basetest import Basetest


class TestMultiLanguageQueryManager(Basetest):
    """
    Isolated unit tests for MultiLanguageQueryManager.
    All tests use in-memory SQLite — no external endpoints needed.
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        # Write a temporary queries YAML with both sql and sparql entries
        self.queries = {
            "all_items": {
                "sql": "SELECT * FROM item",
            },
            "items_by_category": {
                "sql": "SELECT * FROM item WHERE category = '{{ category }}'",
                "param_list": [
                    {"name": "category", "type": "str", "default_value": "book"}
                ],
            },
            "items_limited": {
                "sql": "SELECT * FROM item LIMIT {{ limit }}",
                "param_list": [{"name": "limit", "type": "int", "default_value": "5"}],
            },
            "needs_param": {
                "sql": "SELECT * FROM item WHERE id = {{ item_id }}",
                "param_list": [{"name": "item_id", "type": "int"}],
            },
            "sparql_query": {
                "sparql": "SELECT ?s WHERE { ?s a <http://example.org/Thing> }",
            },
        }
        tf = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        yaml.dump(self.queries, tf)
        tf.close()
        self.queries_path = tf.name

        # In-memory SQLite with a small fixture table
        self.db = SQLDB(":memory:")
        items = [
            {"id": 1, "name": "Alice in Wonderland", "category": "book"},
            {"id": 2, "name": "Python 101", "category": "book"},
            {"id": 3, "name": "Hamlet", "category": "play"},
        ]
        entity_info = self.db.createTable(items, "item", "id")
        self.db.store(items, entityInfo=entity_info)

    def tearDown(self):
        Basetest.tearDown(self)
        os.unlink(self.queries_path)

    def make_mlqm(self) -> MultiLanguageQueryManager:
        """
        Build a MultiLanguageQueryManager backed by the in-memory SQLite fixture.
        We bypass the endpoint resolution by injecting _backend directly.
        """
        mlqm = MultiLanguageQueryManager(
            yaml_path=self.queries_path,
            languages=["sql", "sparql"],
            debug=self.debug,
        )
        mlqm._backend = self.db
        return mlqm

    def testQueryNames(self):
        """
        All query names defined in the YAML should be accessible.
        """
        mlqm = self.make_mlqm()
        for name in ["all_items", "items_by_category", "items_limited", "needs_param"]:
            self.assertIn(name, mlqm.query_names)

    def testQuery4Name(self):
        """
        query4Name should return the correct Query object, None for unknown names.
        """
        mlqm = self.make_mlqm()
        q = mlqm.query4Name("all_items")
        self.assertIsNotNone(q)
        self.assertEqual("all_items", q.name)

        missing = mlqm.query4Name("does_not_exist")
        self.assertIsNone(missing)

    def testQueryNoParams(self):
        """
        A query without parameters should return all rows.
        """
        mlqm = self.make_mlqm()
        rows = mlqm.query("all_items")
        self.assertEqual(3, len(rows))

    def testQueryWithExplicitParam(self):
        """
        Passing param_dict explicitly should override the template placeholder.
        """
        mlqm = self.make_mlqm()
        rows = mlqm.query("items_by_category", param_dict={"category": "play"})
        self.assertEqual(1, len(rows))
        self.assertEqual("Hamlet", rows[0]["name"])

    def testQueryUsesDefaultValue(self):
        """
        When param_dict is None, default_value from param_list must be used
        (this is the core fix from issue #158).
        """
        mlqm = self.make_mlqm()
        # default_value for 'limit' is '5', but only 3 rows exist — expect all 3
        rows = mlqm.query("items_limited")
        self.assertEqual(3, len(rows))

    def testQueryDefaultOverriddenByParamDict(self):
        """
        An explicit param_dict value should take precedence over default_value.
        """
        mlqm = self.make_mlqm()
        rows = mlqm.query("items_limited", param_dict={"limit": "1"})
        self.assertEqual(1, len(rows))

    def testQueryRaisesWhenParamMissingAndNoDefault(self):
        """
        A query with a required parameter and no default_value should raise
        when called without param_dict.
        """
        mlqm = self.make_mlqm()
        with self.assertRaises(Exception) as ctx:
            mlqm.query("needs_param")
        self.assertIn("item_id", str(ctx.exception))

    def testQueryRaisesWhenQueryNotFound(self):
        """
        Querying an unknown name should raise ValueError.
        """
        mlqm = self.make_mlqm()
        with self.assertRaises(ValueError) as ctx:
            mlqm.query("nonexistent_query")
        self.assertIn("nonexistent_query", str(ctx.exception))

    def testQueryRaisesWithoutBackend(self):
        """
        Calling query() without a configured backend should raise ValueError.
        """
        mlqm = MultiLanguageQueryManager(
            yaml_path=self.queries_path,
            languages=["sql"],
            debug=self.debug,
        )
        # _backend is None — no endpoint_name was given
        with self.assertRaises(ValueError) as ctx:
            mlqm.query("all_items")
        self.assertIn("endpoint", str(ctx.exception).lower())

    def testStoreLod(self):
        """
        store_lod should write rows into the backend and query should return them.
        """
        mlqm = self.make_mlqm()
        new_items = [
            {"id": 10, "name": "New Book", "category": "book"},
            {"id": 11, "name": "New Play", "category": "play"},
        ]
        mlqm.store_lod(new_items, "item2", primary_key="id")
        # Verify via direct DB query
        rows = self.db.query("SELECT * FROM item2")
        self.assertEqual(2, len(rows))

    def testMultipleLanguages(self):
        """
        Queries from different languages should all appear in query_names.
        """
        mlqm = self.make_mlqm()
        self.assertIn("all_items", mlqm.query_names)  # sql
        self.assertIn("sparql_query", mlqm.query_names)  # sparql
