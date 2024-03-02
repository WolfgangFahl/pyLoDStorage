"""
Created on 2024-03-02

@author: wf
"""
from lodstorage.prefixes import Prefixes
from tests.basetest import Basetest


class TestPrefixes(Basetest):
    """
    test SPARQL prefixes
    """

    def test_prefixes(self):
        """
        test the SPARQL prefix providing 
        """
        sparql_code = Prefixes.getPrefixes(prefixes=["rdf","xsd"])
        expected="""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""
        self.assertEqual(expected, sparql_code)
