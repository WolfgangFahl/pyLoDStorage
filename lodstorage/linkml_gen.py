"""
Created on 2024-01-21

@author: wf
"""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Dict, List

# Import necessary modules
from dataclasses_json import dataclass_json

from lodstorage.docstring_parser import DocstringParser
from lodstorage.yamlable import lod_storable

@lod_storable
class Slot:
    """
    Represents a slot in the LinkML schema, equivalent to a field or property.
    """

    description: str
    range: str = "string"
    multivalued: bool = False


@lod_storable
class Class:
    """
    Represents a class in the LinkML schema.
    """

    description: str
    slots: List[Slot]


@lod_storable
class Schema:
    """
    Represents the entire LinkML schema.
    """

    id: str
    name: str
    description: str
    default_prefix: str
    prefixes: Dict[str, str] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    default_range: str = "string"
    classes: Dict[str, Class] = field(default_factory=dict)
    slots: Dict[str, Slot] = field(default_factory=dict)


class LinkMLGen:
    """
    Class for generating LinkML YAML schema from Python data models using dataclasses.
    """

    def __init__(self, schema: Schema):
        """
        Initialize the LinkMLGen.

        Args:
            schema (Schema): The LinkML schema to be generated.
        """
        self.schema = schema
        # Define a mapping from Python types to LinkML ranges
        self.python_to_linkml_ranges = {
            str: "string",
            int: "integer",
            float: "float",
            bool: "boolean",
            list: "list",
            dict: "dictionary",
        }

    def gen_schema(self, data_model_instance) -> Schema:
        """
        Generate a LinkML YAML schema from a Python data model using dataclasses.

        Args:
            data_model_instance: An instance of the Python data model.

        Returns:
            Schema: The LinkML schema generated from the data model.
        """
        # Use DocstringParser to extract class description and attributes
        parser = DocstringParser()
        class_description, doc_attributes = parser.parse(data_model_instance.__doc__)

        class_name = data_model_instance.__class__.__name__
        new_class = Class(description=class_description, slots=[])

        for field_info in fields(data_model_instance):
            attr_name = field_info.name
            attr_type = field_info.type

            # Extract field type/range
            linkml_range = self.get_linkml_range(attr_type)

            # Check values for multivalued and type consistency
            attr_value = getattr(data_model_instance, attr_name)
            multivalued, actual_type = self.check_value(attr_value)

            # Ensure documentation, declaration, and value type are consistent
            self.ensure_consistency(attr_name, linkml_range, actual_type, doc_attributes)

            # Prepare slot
            description = doc_attributes.get(attr_name, {}).get("description", f"{attr_name} - missing description")
            if attr_name not in self.schema.slots:
                new_slot = Slot(description=description, range=linkml_range, multivalued=multivalued)
                self.schema.slots[attr_name] = new_slot
                new_class.slots.append(attr_name)

        self.schema.classes[class_name] = new_class
        return self.schema

    def get_linkml_range(self, attr_type):
        # Method to determine the LinkML range from attribute type
        return self.python_to_linkml_ranges.get(attr_type, "string")

    def check_value(self, value):
        # Method to check if the value is multivalued and determine its type
        multivalued = isinstance(value, (Iterable, Mapping)) and not isinstance(value, (str, bytes))
        value_type = type(value).__name__
        return multivalued, value_type

    def ensure_consistency(self, name, declared_type, actual_type, doc_attributes):
        # Adjust this method to handle complex types like list, dict, etc.

        # Check if the actual type is a list or dict, and if so, get the type of its elements
        if actual_type == 'list' or actual_type == 'dict':
            # You may need a more complex logic here to handle lists of custom dataclasses
            # For simplicity, let's assume it's a list of strings for now
            actual_type = 'string'

        # Now compare the adjusted actual type with the declared type
        if declared_type != actual_type:
            raise ValueError(f"Type mismatch for '{name}': declared as '{declared_type}', actual type is '{actual_type}'")

        # Check for documentation
        if name not in doc_attributes:
            raise ValueError(f"Missing documentation for field '{name}'")

