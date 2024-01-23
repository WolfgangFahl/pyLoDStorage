"""
Created on 2024-01-21

@author: wf
"""
from dataclasses import dataclass, field, fields, is_dataclass
from collections.abc import Iterable, Mapping
from typing import List, Dict
# Import necessary modules
from dataclasses_json import dataclass_json

from lodstorage.yamlable import yamlable
from lodstorage.docstring_parser import DocstringParser

@yamlable
@dataclass_json
@dataclass
class Slot:
    """
    Represents a slot in the LinkML schema, equivalent to a field or property.
    """
    description: str
    range: str = "string"
    multivalued: bool = False


@yamlable
@dataclass_json
@dataclass
class Class:
    """
    Represents a class in the LinkML schema.
    """
    description: str
    slots: List[Slot]


@yamlable
@dataclass_json
@dataclass
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
        class_description, attributes = parser.parse(data_model_instance.__doc__)

        # Add class description to the schema
        class_name = data_model_instance.__class__.__name__
        new_class = Class(description=class_description, slots=[])
  
        # Add attributes to the schema
        for field_info in fields(data_model_instance):
            attr_name = field_info.name
            attr_type = field_info.type
            # Get the value of the attribute from the instance
            value = getattr(data_model_instance, attr_name)
            # 
            multivalued = isinstance(value, (Iterable,Mapping))
            if multivalued:
                if isinstance(value,Mapping):
                    value_list=list(value.values())
                else: 
                    value_list=value
                if len(value_list)>0:
                    value_element = value_list[0]
                    if is_dataclass(value_element):
                        linkml_range=type(value_element).__name__
                        self.gen_schema(value_element)
                        pass
                    else:
                        linkml_range=self.python_to_linkml_ranges.get(type(value_element))
                    
            attr_data=attributes.get(attr_name)
            new_class.slots.append(attr_name)
            if attr_data:
                description =attr_data.get("description") 
            else:
                f"{attr_name} - missing description"
            new_slot=Slot(description=description,range=linkml_range,multivalued=multivalued)
            self.schema.slots[attr_name] = new_slot
        self.schema.classes[class_name]=new_class

        return self.schema
