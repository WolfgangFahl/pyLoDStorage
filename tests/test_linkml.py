"""
Created on 2024-01-21

@author: wf
"""
from lodstorage.linkml_gen import LinkMLGen, Schema
from lodstorage.sample2 import Sample
from tests.basetest import Basetest

class TestLinkMLConversion(Basetest):
    """
    Test class for generating LinkML YAML schema from Python data models.
    """

    def setUp(self, debug=False, profile=True):
        super().setUp(debug=debug, profile=profile)

    def test_yaml_schema_generation(self):
        """
        Test the generation of a LinkML YAML schema from Python data models.
        """
        # Retrieve the data model instances
        royals_samples = Sample.get("royals")
        royals= list(royals_samples.values())[0]
        debug = self.debug
        debug = True
        schema = Schema(
            id="http://royal-family.bitplan.com",
            name="royals",
            description="Royal family member schema",
            default_prefix="royals",
            prefixes = {
                  "linkml": "https://w3id.org/linkml/",
                  "royals": "http://royal-family.bitplan.com/royals-schema"
            },
            imports = ["linkml:types"]
        )
        linkml_gen = LinkMLGen(schema)
        # Introspect the data model and generate YAML schema
        linkml_schema = linkml_gen.gen_schema(royals)
        if debug:
            print(linkml_schema.to_yaml())
        linkml_schema.save_to_file("/tmp/royals_linkml_schema.yaml")
