"""
Created on 2026-07-22

Tests for the NPQ-FakeSparql endpoint.
see https://cr.bitplan.com/index.php/NPQ-FakeSparql

@author: wf
"""

from lodstorage.npq_endpoint import NamedQueryStub, NpqEndpoint, SparqlResults
from tests.basetest import Basetest

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None

# fixture bindings: papers-of-my-network - the npq from pyomnigraph#36
PAPERS_RECORDS = [
    {
        "work": "http://www.wikidata.org/entity/Q115055567",
        "workLabel": "Getting and hosting your own copy of Wikidata",
        "orcid": "0000-0002-0821-6995",
        "year": 2022,
    },
    {
        "work": "http://www.wikidata.org/entity/Q59650978",
        "workLabel": "SALT - Semantically Annotated LaTeX",
        "orcid": "0000-0001-6324-7164",
        "year": 2007,
    },
]


class TestNpqEndpoint(Basetest):
    """
    test the NPQ-FakeSparql endpoint
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        if TestClient is None:
            self.skipTest("fastapi not installed - pip install pylodstorage[endpoint]")
        self.papers_stub = NamedQueryStub(
            name="papers-of-my-network",
            records=PAPERS_RECORDS,
            description="papers of the co-author network (fixture)",
        )
        self.endpoint = NpqEndpoint(stubs=[self.papers_stub])
        self.client = TestClient(self.endpoint.app)

    def test_sparql_results_json(self):
        """the default response is SPARQL 1.1 results JSON"""
        response = self.client.get("/npq/papers-of-my-network")
        self.assertEqual(200, response.status_code)
        self.assertIn(
            "application/sparql-results+json", response.headers["content-type"]
        )
        results = response.json()
        self.assertIn("work", results["head"]["vars"])
        bindings = results["results"]["bindings"]
        self.assertEqual(2, len(bindings))
        work = bindings[0]["work"]
        self.assertEqual("uri", work["type"])
        year = bindings[0]["year"]
        self.assertEqual("http://www.w3.org/2001/XMLSchema#integer", year["datatype"])

    def test_service_projection(self):
        """an incoming federator SELECT projects onto its variable names"""
        sparql = "SELECT ?work ?orcid WHERE { ?work ?p ?orcid }"
        response = self.client.get(
            "/npq/papers-of-my-network", params={"query": sparql}
        )
        self.assertEqual(200, response.status_code)
        results = response.json()
        self.assertEqual(["work", "orcid"], results["head"]["vars"])
        for binding in results["results"]["bindings"]:
            self.assertNotIn("year", binding)

    def test_formats(self):
        """plain JSON and CSV are served for non-SPARQL clients"""
        response = self.client.get(
            "/npq/papers-of-my-network", params={"format": "json"}
        )
        self.assertEqual(PAPERS_RECORDS, response.json())
        response = self.client.get(
            "/npq/papers-of-my-network", params={"format": "csv"}
        )
        self.assertIn("text/csv", response.headers["content-type"])
        self.assertTrue(response.text.startswith("work,"))

    def test_unknown_npq(self):
        """an unknown npq name yields 404"""
        response = self.client.get("/npq/does-not-exist")
        self.assertEqual(404, response.status_code)

    def test_executor_with_params(self):
        """real mode: an executor computes bindings from input params"""
        stub = NamedQueryStub(name="echo")
        stub.executor = lambda params: [{"echoed": params.get("value", "")}]
        self.endpoint.add_stub(stub)
        response = self.client.get("/npq/echo", params={"value": "hello"})
        results = response.json()
        binding = results["results"]["bindings"][0]
        self.assertEqual("hello", binding["echoed"]["value"])

    def test_chaos_error(self):
        """chaos mode: a configured error code is returned"""
        stub = NamedQueryStub(name="broken", error_code=502)
        self.endpoint.add_stub(stub)
        response = self.client.get("/npq/broken")
        self.assertEqual(502, response.status_code)

    def test_select_vars(self):
        """SELECT variable extraction handles star and distinct"""
        self.assertIsNone(SparqlResults.select_vars("SELECT * WHERE { ?s ?p ?o }"))
        var_names = SparqlResults.select_vars(
            "SELECT DISTINCT ?a ?b WHERE { ?a ?p ?b }"
        )
        self.assertEqual(["a", "b"], var_names)

    def test_graph_mode_select(self):
        """graph mode: an NPQ dump is served as a real SPARQL endpoint"""
        ttl = """
        @prefix wdt: <http://www.wikidata.org/prop/direct/> .
        <http://www.wikidata.org/entity/Q115055567>
            wdt:P50 <http://www.wikidata.org/entity/Q110462723> .
        """
        self.endpoint.add_dump("papers-graph", ttl, rdf_format="turtle")
        client = TestClient(self.endpoint.app)
        sparql = "SELECT ?work ?author WHERE { ?work ?p ?author }"
        response = client.get(
            "/npq/papers-graph",
            params={"query": sparql},
            headers={"accept": "application/sparql-results+json"},
        )
        self.assertEqual(200, response.status_code)
        results = response.json()
        bindings = results["results"]["bindings"]
        self.assertEqual(1, len(bindings))
        self.assertEqual(
            "http://www.wikidata.org/entity/Q115055567",
            bindings[0]["work"]["value"],
        )

    def test_graph_mode_xml_conneg(self):
        """graph mode serves results XML - what real federators (Jena) request"""
        ttl = "<urn:s> <urn:p> <urn:o> ."
        self.endpoint.add_dump("triple", ttl, rdf_format="turtle")
        client = TestClient(self.endpoint.app)
        response = client.get(
            "/npq/triple",
            params={"query": "SELECT ?s WHERE { ?s ?p ?o }"},
            headers={"accept": "application/sparql-results+xml"},
        )
        self.assertEqual(200, response.status_code)
        self.assertIn("xml", response.headers["content-type"])
        self.assertIn("urn:s", response.text)
