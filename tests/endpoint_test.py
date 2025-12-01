"""
Created on 2025-11-23

@author: wf
"""

import os

from lodstorage.query import EndpointManager
from tests.basetest import Basetest


class EndpointTest(Basetest):
    """
    base class for endpoint tests
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.sampledata_dir = f"{os.path.dirname(__file__)}/../sampledata"
        self.wikidata_queries_path = f"{self.sampledata_dir}/wikidata.yaml"

    def yieldSampleEndpoints(self):
        """
        yield all sample Endpoints
        """
        for filename in ["endpoints.yaml", "endpoints_qlever.yaml"]:
            full_path = f"{self.sampledata_dir}/{filename}"
            endpoints = EndpointManager.getEndpoints(
                endpointPath=full_path, lang="sparql", with_default=False
            )
            for key, endpoint in endpoints.items():
                yield key, endpoint
