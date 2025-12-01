"""
Created on 2024-03-02

@author: wf
"""

import json

from lodstorage.prefix_config import PrefixConfigs
from lodstorage.prefixes import Prefixes
from lodstorage.query import EndpointManager, QueryManager
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

        Verifies new add_endpoint_prefixes() merges prefix_sets → query.query.
        """
        debug = False

        endpoint_path = YamlPath.getSamplePath("endpoints_qlever.yaml")
        endpoints = EndpointManager.getEndpoints(endpointPath=endpoint_path, lang="sparql", with_default=False)
        endpoint_name = "olympics-qlever"
        endpoint = endpoints[endpoint_name]

        # Verify prefix_sets
        if debug:
            print(f"prefix_sets for {endpoint_name}: {endpoint.prefix_sets}")
        self.assertTrue(hasattr(endpoint, "prefix_sets"))
        self.assertEqual(endpoint.prefix_sets, ["rdf", "olympics"])

        olympics_queries_path = f"{self.sampledata_dir}/queries/queries_olympics.yaml"
        qm = QueryManager(queriesPath=olympics_queries_path, with_default=False, lang="sparql", debug=False)
        query = qm.queriesByName["Athletes_by_gold_medals"]

        if debug:
            print(f"Query before add_endpoint_prefixes:\n{query.query[:200]}...")

        query.add_endpoint_prefixes(endpoint, PrefixConfigs.get_instance())

        if debug:
            print(f"Query after (has rdf?: {'PREFIX rdf:' in query.query}, olympics?: {'PREFIX olympics:' in query.query})")
            print(f"Full query:\n{query.query}")

        self.assertIn("PREFIX rdf:", query.query)
        self.assertIn("PREFIX olympics:", query.query)

        sparql = SPARQL(endpoint.endpoint, method=endpoint.method)
        qlod = sparql.queryAsListOfDicts(query.query)

        if debug:
            print(f"Query results: {len(qlod)} rows")

        self.assertIsInstance(qlod, list)
        self.assertGreater(len(qlod), 0)
