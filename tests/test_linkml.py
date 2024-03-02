"""
Created on 2024-01-21

@author: wf
"""
from rdflib.namespace import XSD

from lodstorage.linkml_gen import LinkMLGen, Schema
from lodstorage.rdf import RDFDumper
from lodstorage.sample2 import Royals, Sample
from tests.basetest import Basetest


class TestLinkMLConversion(Basetest):
    """
    Test class for generating LinkML YAML schema from Python data models.
    """

    def setUp(self, debug=False, profile=True):
        super().setUp(debug=debug, profile=profile)
        # Retrieve the data model instances
        royals_samples = Sample.get("royals")
        self.royals = list(royals_samples.values())[0]
        pass

    def get_linkml_schema(self):
        """
        get the example Royals LinkML schema
        """
        debug = self.debug
        # debug = True
        schema = Schema(
            id="http://royal-family.bitplan.com",
            name="royals",
            description="Royal family member schema",
            default_prefix="royals",
            prefixes={
                "linkml": "https://w3id.org/linkml/",
                "royals": "http://royal-family.bitplan.com/royals-schema",
            },
            imports=["linkml:types"],
        )
        linkml_gen = LinkMLGen(schema)
        # Introspect the data model and generate YAML schema
        linkml_schema = linkml_gen.gen_schema(Royals)
        return linkml_schema

    def test_yaml_schema_generation(self):
        """
        Test the generation of a LinkML YAML schema from Python data models.
        """
        linkml_schema = self.get_linkml_schema()

        if self.debug:
            print(linkml_schema.to_yaml())
        linkml_schema.save_to_yaml_file("/tmp/royals_linkml_schema.yaml")

    def test_convert_to_literal(self):
        """
        Test the conversion of Python types to RDFLib Literals with appropriate datatypes using the RDFDumper.
        """
        linkml_schema = self.get_linkml_schema()
        rdf_dumper = RDFDumper(linkml_schema, self.royals)

        # Test data: a list of (value, expected_datatype) pairs
        test_data = [
            ("string", XSD.string),
            (42, XSD.integer),
            (3.14, XSD.float),
            (True, XSD.boolean),
            # Add more test cases as needed
        ]

        for value, expected_datatype in test_data:
            literal = rdf_dumper.convert_to_literal(
                value, None
            )  # slot_obj is not used currently
            assert (
                literal.datatype == expected_datatype
            ), f"Expected datatype {expected_datatype}, got {literal.datatype} for value {value}"

    def test_rdf_dumper(self):
        """
        test the LinkML Schema driven RDF Dumper
        """

        linkml_schema = self.get_linkml_schema()

        # Step 1: Instantiate RDFDumper with the generated schema and a sample instance
        rdf_dumper = RDFDumper(linkml_schema, self.royals)

        # Step 2: Convert the instance to RDF
        rdf_dumper.convert_to_rdf()

        # Step 3: Serialize the RDF graph for debugging or saving
        rdf_output = rdf_dumper.serialize()
        debug = self.debug
        # debug = True
        if debug:
            print(rdf_output)
        # Optionally, save the RDF graph to a file
        with open("/tmp/royals_rdf_output.ttl", "w") as rdf_file:
            rdf_file.write(rdf_output)
