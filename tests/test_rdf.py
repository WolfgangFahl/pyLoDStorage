"""
Created on 2024-01-21

@author: wf
"""
from tests.basetest import Basetest
from lodstorage.sample import Sample
import json

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
        lod = Sample.getRoyals()
        debug=self.debug
        debug=True
        if debug:
            print(json.dumps(lod,indent=2,default=str))
        