"""
Created on 2024-01-25

@author: wf
"""
from lodstorage.sample2 import Sample, Royals, Countries
from tests.basetest import Basetest
from dataclasses import fields, is_dataclass


class TestSamples(Basetest):
    """
    test the samples
    """
    
    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
    
    def check_fields(self, check_instance, expected_instance, hint: str):
        """
        Recursively check fields for both lists and dictionaries in a dataclass.

        Args:
            check_instance: The instance to check.
            expected_instance: The expected instance for comparison.
            hint (str): A hint for context.
        """
        for field_info in fields(check_instance):
            attr_name = field_info.name
            attr_value_check = getattr(check_instance, attr_name)
            attr_value_expected = getattr(expected_instance, attr_name)
            field_hint = f"{hint}.{attr_name}"  # Field-specific hint

            # Check type equality
            self.assertTrue(type(attr_value_check) == type(attr_value_expected), f"Type mismatch in {field_hint}: {type(attr_value_check)} ↔ {type(attr_value_expected)}")

            if is_dataclass(attr_value_check):
                # Recursively check fields if the attribute is a dataclass
                self.check_fields(attr_value_check, attr_value_expected, field_hint)
            elif isinstance(attr_value_check, list):
                # Check lists recursively
                self.assertEqual(len(attr_value_check), len(attr_value_expected), f"Length mismatch in {field_hint}")
                for i, (item_check, item_expected) in enumerate(zip(attr_value_check, attr_value_expected)):
                    self.check_fields(item_check, item_expected, f"{field_hint}[{i}]")
            elif isinstance(attr_value_check, dict):
                # Check dictionaries recursively
                self.assertDictEqual(attr_value_check, attr_value_expected, f"Dictionary mismatch in {field_hint}")
                for key in attr_value_check:
                    if key in attr_value_expected:
                        self.check_fields(attr_value_check[key], attr_value_expected[key], f"{field_hint}[{key}]")
            else:
                state = attr_value_check == attr_value_expected
                state_indicator = "✅" if state else "❌"
                msg = f"{state_indicator} {field_hint}: {attr_value_check} ↔ {attr_value_expected}"
                self.assertTrue(state, msg)
                if self.debug:
                    print(msg)
    
    def check_sample(self, 
        clazz,
        sample_name: str, 
        example_name: str,
        check_instance) -> None:
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
        self.assertTrue(example_name in samples,f"invalid example {example_name}")
        sample_instance=samples.get(example_name)
        self.assertIsInstance(sample_instance, clazz)
        hint=f"{sample_name}:{example_name}"
        self.assertIsNotNone(check_instance,f"check instance for {hint} should not be none")
        self.assertIsInstance(check_instance, clazz)
        self.check_fields(check_instance, sample_instance,hint)
        

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

    def test_samples_round_trip(self):
        """
        Test round-trip serialization and deserialization for the royals using YamlAble.
        """
        for sample_name,sample_class in [("royals",Royals),("countries",Countries)]:
            samples=Sample.get(sample_name)
            for name, original_item in samples.items():
                # Serialize to YAML
                yaml_str = original_item.to_yaml()
                # Optional: Print the YAML string in debug mode
                debug = self.debug
                # debug=True
                if debug:
                    print(f"Original YAML String for {sample_name}/{name}:")
                    print(yaml_str)

                # Deserialize back to sample class instance
                deserialized_item = original_item.from_yaml(yaml_str)
                self.check_sample(sample_class,sample_name,name, deserialized_item)
