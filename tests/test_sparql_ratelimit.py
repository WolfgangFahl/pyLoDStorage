"""
Created on 2026-06-21

@author: wf
"""

import time
from unittest.mock import MagicMock

from lodstorage.sparql import SPARQL
from tests.basetest import Basetest


class TestSparqlRateLimit(Basetest):
    """
    test that the SPARQL query path honors the rate limiter (issue #165)
    """

    def test_rawQuery_is_rate_limited(self):
        """
        rawQuery must route the actual query() call through the rate limiter
        so that calls_per_minute is honored (regression for issue #165).

        The limiter is burst-based: it allows up to calls_per_minute calls in
        a 60s window, then blocks. With a budget of 2, the 3rd call must block.
        """
        calls_per_minute = 2
        sparql = SPARQL("https://example.org/sparql", calls_per_minute=calls_per_minute)
        # replace the underlying SPARQLWrapper2 with a fast mock - we are only
        # testing throttling, not network access
        sparql.sparql = MagicMock()
        sparql.sparql.query.return_value = []

        # the first `calls_per_minute` calls run within budget (fast)
        start = time.time()
        for _ in range(calls_per_minute):
            sparql.rawQuery("SELECT * WHERE { ?s ?p ?o } LIMIT 1")
        within_budget = time.time() - start
        if self.debug:
            print(f"{calls_per_minute} in-budget calls took {within_budget:.2f}s")
        self.assertLess(within_budget, 5.0)
        self.assertEqual(calls_per_minute, sparql.sparql.query.call_count)
        # the rate limiter is applied (a persistent throttle object exists)
        self.assertTrue(hasattr(sparql, "_rate_limited_query"))
