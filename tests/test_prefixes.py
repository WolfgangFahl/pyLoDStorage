"""
Created on 2024-03-02

@author: wf
"""

import json

from lodstorage.prefixes import Prefixes
from tests.basetest import Basetest


class TestPrefixes(Basetest):
    """
    test SPARQL prefixes
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
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
