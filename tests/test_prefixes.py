"""
Created on 2024-03-02

@author: wf
"""

import json

from lodstorage.prefixes import Prefixes
from lodstorage.query import QueryManager, EndpointManager
from lodstorage.sparql import SPARQL

from lodstorage.yaml_path import YamlPath
from tests.basetest import Basetest
from tests.endpoint_test import EndpointTest


class TestPrefixes(EndpointTest):
    """
    test SPARQL prefixes
    """

    def setUp(self, debug=False, profile=True):
        EndpointTest.setUp(self, debug=debug, profile=profile)
        self.sparql_query = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?item ?label WHERE {
  ?item wdt:P31 wd:Q5 .
  ?item rdfs:label ?label .
  FILTER(LANG(?label) = "en")
}
"""

    def test_prefixes(self):
        """
        test the SPARQL prefix providing
        """
        sparql_code = Prefixes.getPrefixes(prefixes=["rdf", "xsd"])
        expected = """PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""
        self.assertEqual(expected, sparql_code)

    def test_extract_prefixes(self):
        """
        Test the SPARQL prefix extraction functionality.
        """
        prefixes = Prefixes.extract_prefixes(self.sparql_query)
        if self.debug:
            print(json.dumps(prefixes, indent=2))
        expected = ["rdf", "rdfs", "wd", "wdt"]
        for prefix in expected:
            self.assertTrue(prefix in prefixes)
            self.assertEqual(prefixes[prefix], Prefixes.prefixMap[prefix])

    def test_merge_prefixes(self):
        """
        Test merging prefixes into SPARQL query.
        """
        prefixes = Prefixes.getPrefixes(prefixes=["rdf", "xsd"])
        merged_query = Prefixes.merge_prefixes(self.sparql_query, prefixes)
        if self.debug:
            print(merged_query)
        expected = Prefixes.getPrefixes(["xsd"])
        self.assertTrue(merged_query.startswith(expected))


    def test_issue151_prefix_sets_refactoring(self):
        """
        Test Issue #151: Simplify endpoints.yaml by referencing prefix sets.

        Verifies:
        1. Endpoints use prefix_sets (List[str]) instead of inline prefixes
        2. Prefix resolution works correctly via Prefixes.getPrefixes()
        3. Queries using resolved prefixes execute successfully

        Uses queries_olympics.yaml as test data.
        """
        debug = self.debug
        debug = True
        # Get QLever Olympics endpoint
        endpoint_path=YamlPath.getSamplePath("endpoints_qlever.yaml")
        endpoints = EndpointManager.getEndpoints(endpointPath=endpoint_path,lang="sparql", with_default=False)
        ep_name="olympics-qlever"
        self.assertIn(ep_name, endpoints, f"{ep_name} endpoint not found")
        endpoint = endpoints[ep_name]

        # Load Olympics queries which use prefix_sets
        olympics_queries_path = f"{self.sampledata_dir}/queries/queries_olympics.yaml"
        qm = QueryManager(
            queriesPath=olympics_queries_path,
            with_default=False,
            lang="sparql",
            debug=False
        )


        if debug:
            print(f"\n=== Testing Issue #151: Prefix Sets Refactoring ===")
            print(f"Endpoint: {endpoint.name}")
            print(f"URL: {endpoint.endpoint}")

        # 1. Verify endpoint has prefix_sets field
        if debug:
            print(f"\n1. Checking endpoint structure...")
            print(f"   Has prefix_sets: {hasattr(endpoint, 'prefix_sets')}")
            if hasattr(endpoint, 'prefix_sets'):
                print(f"   Prefix sets: {endpoint.prefix_sets}")

        self.assertTrue(
            hasattr(endpoint, 'prefix_sets'),
            f"Endpoint {endpoint.name} lacks 'prefix_sets' field"
        )
        self.assertIsInstance(
            endpoint.prefix_sets,
            list,
            f"prefix_sets for {endpoint.name} is not a list"
        )

        # 2. Verify prefix resolution
        if debug:
            print(f"\n2. Testing prefix resolution...")

        combined_prefixes = Prefixes.getPrefixes(endpoint.prefix_sets)

        if debug:
            print(f"   Combined prefixes from {endpoint.prefix_sets}:")
            for line in combined_prefixes.split('\n')[:5]:  # Show first 5
                print(f"     {line}")
            print(f"   ... (total {len(combined_prefixes.split(chr(10)))} lines)")

        # Verify expected prefixes are present
        expected_prefixes = [
            "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
            "PREFIX olympics: <https://olympics.qlever.cs.uni-freiburg.de/>"
        ]

        for expected in expected_prefixes:
            if debug:
                print(f"   Checking for: {expected[:50]}...")
            self.assertIn(
                expected,
                combined_prefixes,
                f"Expected prefix missing: {expected}"
            )

        # 3. Test query execution with resolved prefixes
        if debug:
            print(f"\n3. Testing query execution...")

        query = qm.queriesByName["Athletes_by_gold_medals"]

        if debug:
            print(f"   Query: {query.name}")
            print(f"   Query prefix_sets: {query.prefix_sets}")

        # Resolve query-specific prefixes
        query_prefixes = Prefixes.getPrefixes(query.prefix_sets)
        query.prefixes = query_prefixes.split('\n')

        if debug:
            print(f"   Resolved {len(query.prefixes)} prefix lines for query")

        # Execute query
        sparql = SPARQL(endpoint.endpoint, method=endpoint.method)

        try:
            if debug:
                print(f"   Executing query at {endpoint.endpoint}...")

            qlod = sparql.queryAsListOfDicts(query.query)

            if debug:
                print(f"   ✅ Query succeeded: {len(qlod)} results")
                if qlod:
                    print(f"   Sample result: {qlod[0]}")

            self.assertIsInstance(qlod, list, "Query result is not a list")
            self.assertGreater(
                len(qlod),
                0,
                "Query with assembled prefixes returned no results"
            )

        except Exception as ex:
            if debug:
                print(f"   ❌ Query failed: {ex}")
            self.fail(f"Query failed with refactored prefixes: {ex}")

        if debug:
            print(f"\n=== Issue #151 Test Complete ===\n")
