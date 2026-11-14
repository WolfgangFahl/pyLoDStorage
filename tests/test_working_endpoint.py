"""
Created on 2026-09-30

@author: wf
"""

from lodstorage.action_stats import ActionStats
from lodstorage.query import Endpoint, EndpointManager
from tests.basetest import Basetest


class TestWorkingEndpoint(Basetest):
    """
    test the selection of a working endpoint from an ordered list of candidates
    see https://github.com/WolfgangFahl/pyLoDStorage/issues/169
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_action_stats(self):
        """
        test the success ratio bookkeeping
        """
        stats = ActionStats()
        self.assertEqual(0.0, stats.ratio)
        for is_success in [True, False, True, True]:
            stats.add(is_success)
        self.assertEqual(0.75, stats.ratio)
        self.assertEqual("❌ :3/4 available", str(stats))
        self.assertTrue(stats.state("ok", "failed").startswith("✅"))

    def test_availability_unreachable(self):
        """
        an endpoint on a closed port is not available
        """
        endpoint = Endpoint(name="closed", endpoint="http://127.0.0.1:9/sparql")
        self.assertFalse(endpoint.test_availability(timeout=2.0))

    def test_working_endpoint_selection(self):
        """
        the first answering candidate wins, below min_ratio nothing is returned
        """
        closed = Endpoint(name="closed", endpoint="http://127.0.0.1:9/sparql")
        packaged = EndpointManager.getEndpoints(lang="sparql", with_default=False)
        wikidata = packaged["wikidata"]
        endpoints = {"closed": closed, "wikidata": wikidata}
        if not wikidata.test_availability():
            self.skipTest(f"{wikidata.endpoint} does not answer")
        working = EndpointManager.get_working_endpoint(
            ["closed", "wikidata"], endpoints=endpoints, min_ratio=0.5, debug=self.debug
        )
        self.assertIsNotNone(working)
        self.assertEqual("wikidata", working.name)
        none_working = EndpointManager.get_working_endpoint(
            ["closed", "missing", "wikidata"], endpoints=endpoints, min_ratio=0.5
        )
        self.assertIsNone(none_working)

    def test_wikidata_qlever_dbis(self):
        """
        the RWTH Aachen QLever is a packaged endpoint with the prefix sets
        a query without PREFIX lines needs on QLever
        """
        packaged = EndpointManager.getEndpoints(lang="sparql", with_default=False)
        self.assertIn("wikidata-qlever-dbis", packaged)
        endpoint = packaged["wikidata-qlever-dbis"]
        self.assertEqual("qlever", endpoint.database)
        for prefix_set in ["rdf", "wikidata"]:
            self.assertIn(prefix_set, endpoint.prefix_sets)
        if not endpoint.test_availability():
            self.skipTest(f"{endpoint.endpoint} does not answer")
        working = EndpointManager.get_working_endpoint(
            ["wikidata-qlever-dbis"], endpoints=packaged, min_ratio=0.5
        )
        self.assertEqual("wikidata-qlever-dbis", working.name)
