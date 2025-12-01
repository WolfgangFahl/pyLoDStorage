"""
Created on 2024-01-25

@author: wf
"""

import os
from dataclasses import fields, is_dataclass

from lodstorage.sample2 import Countries, Royals, Sample
from tests.basetest import Basetest


class TestSamples(Basetest):
    """
    test the samples
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.sample_cases = [("royals", Royals), ("countries", Countries)]
        self.tmp = "/tmp/lod_storable"
        os.makedirs(self.tmp, exist_ok=True)

    def check_fields(
        self, check_instance, expected_instance, hint: str, level: int = 0
    ):
        """
        Recursively check fields for both lists and dictionaries in a dataclass.

        Args:
            check_instance: The instance to check.
            expected_instance: The expected instance for comparison.
            hint (str): A hint for context.
        """
        if not is_dataclass(check_instance):
            if level == 0:
                self.fail(f"{hint} is not a dataclass")
            return
        for field_info in fields(check_instance):
            attr_name = field_info.name
            attr_value_check = getattr(check_instance, attr_name)
            attr_value_expected = getattr(expected_instance, attr_name)
            field_hint = f"{hint}.{attr_name}"  # Field-specific hint

            same_type = type(attr_value_check) == type(
                attr_value_expected
            )  # Check type equality
            if not same_type:
                pass
            self.assertTrue(
                same_type,
                f"Type mismatch in {field_hint}: {type(attr_value_check)} ↔ {type(attr_value_expected)}",
            )

            if is_dataclass(attr_value_check):
                # Recursively check fields if the attribute is a dataclass
                self.check_fields(
                    attr_value_check, attr_value_expected, field_hint, level + 1
                )
            elif isinstance(attr_value_check, list):
                # Check lists recursively
                self.assertEqual(
                    len(attr_value_check),
                    len(attr_value_expected),
                    f"Length mismatch in {field_hint}",
                )
                for i, (item_check, item_expected) in enumerate(
                    zip(attr_value_check, attr_value_expected)
                ):
                    self.check_fields(
                        item_check, item_expected, f"{field_hint}[{i}]", level + 1
                    )
            elif isinstance(attr_value_check, dict):
                # Check dictionaries recursively
                self.assertDictEqual(
                    attr_value_check,
                    attr_value_expected,
                    f"Dictionary mismatch in {field_hint}",
                )
                for key in attr_value_check:
                    if key in attr_value_expected:
                        self.check_fields(
                            attr_value_check[key],
                            attr_value_expected[key],
                            f"{field_hint}[{key}]",
                            level + 1,
                        )
            else:
                state = attr_value_check == attr_value_expected
                state_indicator = "✅" if state else "❌"
                msg = f"{state_indicator} {field_hint}: {attr_value_check} ↔ {attr_value_expected}"
                self.assertTrue(state, msg)
                if self.debug:
                    print(msg)

    def check_sample(
        self, clazz, sample_name: str, example_name: str, check_instance
    ) -> None:
        """
        Checks the attributes of each member in the given sample instance against the sample data.

        Args:
            clazz: The expected class
            sample_name (str): The name of the sample to be checked.
            example_name (str): The name of the example to be checked.
            check_instance: The instance to be checked.
        """
        # Retrieve the expected data from the sample
        samples = Sample.get(sample_name)
        self.assertTrue(example_name in samples, f"invalid example {example_name}")
        sample_instance = samples.get(example_name)
        self.assertIsInstance(sample_instance, clazz)
        hint = f"{sample_name}:{example_name}"
        self.assertIsNotNone(
            check_instance, f"check instance for {hint} should not be none"
        )
        self.assertIsInstance(check_instance, clazz)
        self.check_fields(check_instance, sample_instance, hint)

    def test_royals(self):
        """
        test lod_storable decorator for the royals
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

    def test_samples_yaml_round_trip(self):
        """
        Test round-trip serialization and deserialization for the royals using YamlAble.
        """
        for sample_name, sample_class in [("royals", Royals), ("countries", Countries)]:
            samples = Sample.get(sample_name)
            for name, original_item in samples.items():
                # Serialize to YAML
                yaml_str = original_item.to_yaml()
                # Optional: Print the YAML string in debug mode
                debug = self.debug
                # debug = True
                if debug:
                    print(f"Original YAML String for {sample_name}/{name}:")
                    print(yaml_str)

                # Deserialize back to sample class instance
                deserialized_item = original_item.from_yaml(yaml_str)
                self.check_sample(sample_class, sample_name, name, deserialized_item)

    def test_json_serialization(self):
        """
        Test JSON serialization and deserialization.
        """
        for sample_name, sample_class in self.sample_cases:
            samples = Sample.get(sample_name)
            for name, original_item in samples.items():
                # Serialize to JSON
                json_str = original_item.to_json()

                # Deserialize back to sample class instance
                deserialized_item = sample_class.from_json(json_str)
                self.check_sample(sample_class, sample_name, name, deserialized_item)

    def test_yaml_file_operations(self):
        """
        Test saving to and loading from YAML files.
        """
        for sample_name, sample_class in self.sample_cases:
            samples = Sample.get(sample_name)
            for name, original_item in samples.items():
                filename = f"{self.tmp}/{sample_name}-{name}.yaml"
                # Save to YAML file
                original_item.save_to_yaml_file(filename)

                # Load from YAML file
                loaded_item = sample_class.load_from_yaml_file(filename)
                self.check_sample(sample_class, sample_name, name, loaded_item)

    def test_json_file_operations(self):
        """
        Test saving to and loading from JSON files.
        """
        for sample_name, sample_class in self.sample_cases:
            samples = Sample.get(sample_name)
            for name, original_item in samples.items():
                filename = f"{self.tmp}/{sample_name}-{name}.json"
                # Save to JSON file
                original_item.save_to_json_file(filename)

                # Load from JSON file
                loaded_item = sample_class.load_from_json_file(filename)
                self.check_sample(sample_class, sample_name, name, loaded_item)

    def test_load_from_yaml_url(self) -> None:
        """
        Test loading a dataclass instance from a YAML string obtained from a URL.
        """
        debug = self.debug
        # debug=True
        # royals
        royals_sample = Sample.getRoyalsSample()
        if debug:
            print(royals_sample.to_yaml())
        royals_url = "https://raw.githubusercontent.com/WolfgangFahl/pyLoDStorage/master/sampledata/royals.yaml"
        royals = Royals.load_from_yaml_url(royals_url)  # @UndefinedVariable

        self.check_sample(Royals, "royals", "QE2 heirs up to number in line 5", royals)
