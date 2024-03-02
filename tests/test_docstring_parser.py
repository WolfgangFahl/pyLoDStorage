"""
Created on 2024-01-21

@author: wf
"""
import json

from lodstorage.docstring_parser import DocstringParser
from tests.basetest import Basetest


class TestDocstringParser(Basetest):
    """
    test the Docstring Parser
    """

    def test_parse_docstring(self):
        """
        Test parsing of a class docstring.
        """
        docstring = """
        Represents a member of the royal family, with various personal details.

        Attributes:
            name (str): The full name of the royal member.
            wikidata_id (str): The Wikidata identifier associated with the royal member.
            number_in_line (Optional[int]): The number in line to succession, if applicable.
            born_iso_date (Optional[str]): The ISO date of birth.
            died_iso_date (Optional[str]): The ISO date of death, if deceased.
            last_modified_iso (str): ISO timestamp of the last modification.
            age (Optional[int]): The age of the royal member.
            of_age (Optional[bool]): Indicates whether the member is of legal age.
            wikidata_url (Optional[str]): URL to the Wikidata page of the member.
        """
        parser = DocstringParser()
        class_description, attributes = parser.parse(docstring)
        debug = self.debug
        # debug = True
        if debug:
            print(class_description)
            print(json.dumps(attributes, indent=2))
        # Assertions to check if the parser is working correctly
        self.assertEqual(
            "Represents a member of the royal family, with various personal details.",
            class_description,
        )
        self.assertIn("name", attributes)
        self.assertEqual(attributes["name"]["type"], "str")
        self.assertEqual(
            attributes["name"]["description"], "The full name of the royal member."
        )
