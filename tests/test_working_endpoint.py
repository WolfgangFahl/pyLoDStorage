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
