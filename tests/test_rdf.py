"""
Created on 2024-01-21

@author: wf
"""
from lodstorage.sample2 import Sample
from tests.basetest import Basetest


class TestTriplify(Basetest):

    """
    Tests https://github.com/WolfgangFahl/pyLoDStorage/issues/57
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_rdf_triples(self):
        """
        test creating RDF triples
        """
        royals_samples = Sample.get("royals")
        debug = self.debug
        # debug = True
        for name, royals in royals_samples.items():
            json_str = royals.to_json(indent=2)
            if debug:
                print(f"Sample {name}:")
                print(json_str)
