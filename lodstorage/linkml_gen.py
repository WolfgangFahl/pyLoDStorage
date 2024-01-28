"""
Created on 2024-01-21

@author: wf
"""

from collections.abc import Iterable, Mapping
from dataclasses import fields, is_dataclass
from typing import Union

from lodstorage.docstring_parser import DocstringParser
from lodstorage.linkml import Class, PythonTypes, Schema, Slot


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

    def gen_schema(self, data_model_class) -> Schema:
        # Use DocstringParser to extract class description
        parser = DocstringParser()
        class_description, doc_attributes = parser.parse(data_model_class.__doc__)

        class_name = data_model_class.__name__
        new_class = Class(description=class_description, slots=[])

        # Iterate over the fields of the dataclass
        for field_info in fields(data_model_class):
            attr_name = field_info.name
            attr_type = field_info.type

            # Handle Optional and List types
            is_optional = False
            is_list = False
            content_type = None
            if hasattr(attr_type, "__origin__"):
                if attr_type.__origin__ is Union and type(None) in attr_type.__args__:
                    is_optional = True
                    attr_type = [t for t in attr_type.__args__ if t is not type(None)][
                        0
                    ]  # unwrap Optional type
                elif attr_type.__origin__ is list:
                    is_list = True
                    content_type = attr_type.__args__[0]  # unwrap List type
                elif attr_type.__origin__ is dict:
                    # Assuming dictionary values are of interest, keys are strings
                    content_type = attr_type.__args__[
                        1
                    ]  # unwrap Dict type, focusing on value type

            # Check and handle nested dataclasses for lists or dicts
            if is_dataclass(content_type):
                # Recursive call to handle nested dataclass
                self.gen_schema(content_type)
                # Set the range to the name of the dataclass
                linkml_range = (
                    content_type.__name__
                )  # Use the name of the dataclass as the range
            elif is_list:
                # If it's a list, get the LinkML range for the base type
                # Use self.get_linkml_range to ensure consistent type mapping
                linkml_range = PythonTypes.get_linkml_range(content_type)
            else:
                # For non-list and non-dataclass types, use self.get_linkml_range for consistent type mapping
                linkml_range = PythonTypes.get_linkml_range(attr_type)

            # Extract description from doc_attributes
            description = doc_attributes.get(attr_name, {}).get(
                "description", f"{attr_name} - missing description"
            )

            # Create a new slot for the field
            new_slot = Slot(
                description=description, range=linkml_range, multivalued=is_list
            )
            self.schema.slots[attr_name] = new_slot
            new_class.slots.append(attr_name)

        self.schema.classes[class_name] = new_class
        return self.schema

    def gen_schema_from_instance(self, data_model_instance) -> Schema:
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
            linkml_range = PythonTypes.get_linkml_range(attr_type)

            # Check values for multivalued and type consistency
            attr_value = getattr(data_model_instance, attr_name)
            multivalued, actual_type = self.check_value(attr_value)

            # Ensure documentation, declaration, and value type are consistent
            self.ensure_consistency(
                attr_name, linkml_range, actual_type, doc_attributes
            )

            # Prepare slot
            description = doc_attributes.get(attr_name, {}).get(
                "description", f"{attr_name} - missing description"
            )
            if attr_name not in self.schema.slots:
                new_slot = Slot(
                    description=description, range=linkml_range, multivalued=multivalued
                )
                self.schema.slots[attr_name] = new_slot
                new_class.slots.append(attr_name)

            if multivalued:
                # recursive call if type of list or dict is a dataclass
                if hasattr(attr_type, "__args__"):
                    content_type = attr_type.__args__[
                        0
                    ]  # Get the declared content type
                    if is_dataclass(content_type):
                        self.gen_schema(content_type)

        self.schema.classes[class_name] = new_class
        return self.schema

    def check_value(self, value):
        # Method to check if the value is multivalued and determine its type
        multivalued = isinstance(value, (Iterable, Mapping)) and not isinstance(
            value, (str, bytes)
        )
        value_type = type(value).__name__
        return multivalued, value_type

    def ensure_consistency(self, name, declared_type, actual_type, doc_attributes):
        # Adjust this method to handle complex types like list, dict, etc.

        # Check if the actual type is a list or dict, and if so, get the type of its elements
        if actual_type == "list" or actual_type == "dict":
            # You may need a more complex logic here to handle lists of custom dataclasses
            # For simplicity, let's assume it's a list of strings for now
            actual_type = "string"

        # Now compare the adjusted actual type with the declared type
        if declared_type != actual_type:
            raise ValueError(
                f"Type mismatch for '{name}': declared as '{declared_type}', actual type is '{actual_type}'"
            )

        # Check for documentation
        if name not in doc_attributes:
            raise ValueError(f"Missing documentation for field '{name}'")
