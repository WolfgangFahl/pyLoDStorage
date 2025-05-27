"""
Created on 2025-05-27

@author: wf
"""

import json

from owlready2 import default_world, get_ontology

from tests.basetest import Basetest


class TestOwl2Ready(Basetest):
    """
    test Owl2Ready
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testDblp(self):
        """
        https://dblp.org/rdf/docu/
        """
        onto_url = "https://dblp.org/rdf/schema.rdf#"
        onto = get_ontology(onto_url)
        onto.load()
        classes = list(onto.classes())
        classes_by_name = {}
        for oc in classes:
            classes_by_name[oc.name] = oc
        if self.debug:
            print(f"Ontology loaded: {onto}")
            print(f"Base IRI: {onto.base_iri}")
            print(f"Imported ontologies: {list(onto.imported_ontologies)}")
            for c in classes:
                print(c)
        self.assertTrue("Inproceedings" in classes_by_name)
