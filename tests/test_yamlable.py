"""
Created on 2023-12-03

@author: wf, ChatGPT

Prompts:
- Implement a YAML conversion class for dataclasses with specific handling for multi-line strings and omission of None values.
- Create a test suite for the YAML conversion class, ensuring proper formatting and functionality.
"""
import os
import tempfile
from dataclasses import dataclass

from lodstorage.sample2 import Royals, Sample
from lodstorage.yamlable import YamlAble
from tests.basetest import Basetest


@dataclass
class MockDataClass(YamlAble["MockDataClass"]):
    """
    Mock dataclass for testing YAML conversion.

    Attributes:
        name (str): The name attribute.
        id (int): The identifier attribute.
        description (str, optional): Description attribute. Defaults to None.
        url (str, optional): URL attribute. Defaults to None.
    """

    name: str
    id: int
    description: str = None
    url: str = None
    sample_tuple: tuple = (1, 2, 3)  # Add a tuple attribute for testing


class TestYamlAble(Basetest):
    """
    Test the Yaml handler for dataclass to YAML conversion.
    """

    def setUp(self, debug: bool = False, profile: bool = True) -> None:
        """
        Set up the test case environment.

        Args:
            debug (bool): Flag to enable debugging output. Defaults to True.
            profile (bool): Flag to enable profiling. Defaults to True.
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.mock_data = MockDataClass(
            name="Example",
            id=123,
            description="This is an example description with\nmultiple lines to test block scalar style.",
            url="http://example.com",
        )

    def check_yaml(self) -> str:
        """
        Converts the mock dataclass to a YAML string and optionally prints it for debugging.

        Returns:
            str: The YAML string representation of the mock dataclass.
        """
        yaml_str = self.mock_data.to_yaml()
        if self.debug:
            print(yaml_str)
        return yaml_str

    def test_to_yaml(self) -> None:
        """
        Test converting a dataclass object to a YAML string.
        """
        yaml_str = self.check_yaml()
        self.assertIn(
            "Example", yaml_str, "The name should be included in the YAML string."
        )
        self.assertIn(
            "|", yaml_str, "Block scalar style should be used for multi-line strings."
        )
        self.assertNotIn(
            "null", yaml_str, "None values should not be included in the YAML string."
        )
        self.assertIn("url: http", yaml_str, "url should be included")

    def test_omit_none(self) -> None:
        """
        Test that None values are omitted in the YAML output.
        """
        self.mock_data.url = None  # Explicitly set url to None to test omission
        yaml_str = self.check_yaml()
        self.assertNotIn("url", yaml_str, "Keys with None values should be omitted.")

    def test_block_scalar(self) -> None:
        """
        Test that multi-line strings use block scalar style.
        """
        yaml_str = self.check_yaml()
        expected_block_indicator = "|-"
        expected_first_line_of_description = "This is an example description with"
        self.assertIn(
            expected_block_indicator,
            yaml_str,
            "Block scalar style should be used for multi-line strings.",
        )
        self.assertIn(
            expected_first_line_of_description,
            yaml_str,
            "The description should be included as a block scalar.",
        )

    def test_tuple_serialization(self) -> None:
        """
        Test that tuples in the dataclass are serialized as regular YAML lists.
        """
        self.mock_data.sample_tuple = (1, 2, 3)
        yaml_str = self.mock_data.to_yaml()
        debug = self.debug
        if debug:
            print(yaml_str)
        self.assertIn(
            "- 1\n- 2\n- 3",
            yaml_str,
            "Tuples should be serialized as regular YAML lists.",
        )
        self.assertNotIn(
            "!!python/tuple",
            yaml_str,
            "Python tuple notation should not appear in the YAML output.",
        )

    def check_royals(self, royals: Royals) -> None:
        """
        Checks the attributes of each member in the given Royals instance against the sample data.

        Args:
            royals (Royals): The Royals instance to be checked.
        """
        # Retrieve the expected data from the sample
        expected_royals = Sample.get("royals")[
            "QE2 heirs up to number in line 5"
        ].members

        # Check if the number of members matches
        self.assertEqual(
            len(royals.members),
            len(expected_royals),
            "Number of members should match the expected data.",
        )

        # Check each member's attributes
        for i, member in enumerate(royals.members):
            expected_member = expected_royals[i]

            self.assertEqual(
                member.name, expected_member.name, f"Name of member {i} does not match."
            )
            self.assertEqual(
                member.wikidata_id,
                expected_member.wikidata_id,
                f"Wikidata ID of member {i} does not match.",
            )
            self.assertEqual(
                member.born_iso_date,
                expected_member.born_iso_date,
                f"Born date of member {i} does not match.",
            )
            self.assertEqual(
                member.died_iso_date,
                expected_member.died_iso_date,
                f"Died date of member {i} does not match.",
            )
            self.assertEqual(
                member.age, expected_member.age, f"Age of member {i} does not match."
            )
            self.assertEqual(
                member.of_age,
                expected_member.of_age,
                f"Of age status of member {i} does not match.",
            )

    def test_royals(self):
        """
        test yamlable decorator for the royals
        """
        royals_samples = Sample.get("royals")
        for name, royals in royals_samples.items():
            yaml_str = royals.to_yaml()
            self.assertTrue("Charles" in yaml_str)
            debug = self.debug
            # debug=True
            if debug:
                print(f"Sample {name}:")
                print(yaml_str)

    def test_royals_round_trip(self):
        """
        Test round-trip serialization and deserialization for the royals using YamlAble.
        """
        royals_samples = Sample.get("royals")
        for name, original_royals in royals_samples.items():
            # Serialize to YAML
            yaml_str = original_royals.to_yaml()
            # Optional: Print the YAML string in debug mode
            debug = self.debug
            # debug=True
            if debug:
                print(f"Original YAML String for {name}:")
                print(yaml_str)

            # Deserialize back to Royals instance
            deserialized_royals = Royals.from_yaml(yaml_str)

            # Assertions to check if deserialized royals match the original
            self.assertEqual(
                len(deserialized_royals.members), len(original_royals.members)
            )
            for original, deserialized in zip(
                original_royals.members, deserialized_royals.members
            ):
                self.assertEqual(original.name, deserialized.name)
                self.assertEqual(original.wikidata_id, deserialized.wikidata_id)
                self.assertEqual(original.number_in_line, deserialized.number_in_line)
                self.assertEqual(original.born_iso_date, deserialized.born_iso_date)
                self.assertEqual(original.died_iso_date, deserialized.died_iso_date)
                # Add more assertions as necessary for other fields

    def test_save_to_yaml_file(self) -> None:
        """
        Test saving a dataclass instance to a YAML file.
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            self.mock_data.save_to_yaml_file(temp_file.name)
            # Check if file is created
            self.assertTrue(os.path.exists(temp_file.name))
            # Optionally read back the file to check contents
            with open(temp_file.name, "r") as file:
                yaml_content = file.read()
                self.assertIn("Example", yaml_content)

    def test_load_from_yaml_file(self) -> None:
        """
        Test loading a dataclass instance from a YAML file.
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            self.mock_data.save_to_yaml_file(temp_file.name)
            loaded_instance = MockDataClass.load_from_yaml_file(temp_file.name)
            # Check if the loaded instance matches the original
            self.assertEqual(loaded_instance.name, self.mock_data.name)
            self.assertEqual(loaded_instance.id, self.mock_data.id)
            # Clean up the temp file
            os.remove(temp_file.name)

    def test_load_from_yaml_url(self) -> None:
        """
        Test loading a dataclass instance from a YAML string obtained from a URL.
        """
        # royals
        royals_url = "https://raw.githubusercontent.com/WolfgangFahl/pyLoDStorage/master/sampledata/royals.yaml"
        royals = Royals.load_from_yaml_url(royals_url)
        self.check_royals(royals)
