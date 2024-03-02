"""
Created on 2024-01-28

@author: wf
"""
from dataclasses import field
from typing import Dict, List, Optional, Type

from rdflib.namespace import XSD

from lodstorage.yamlable import lod_storable


@lod_storable
class Slot:
    """
    Represents a slot in the LinkML schema, equivalent to a field or property.
    """

    description: str
    range: str = "string"
    multivalued: bool = False
    identifier: bool = False


@lod_storable
class Class:
    """
    Represents a class in the LinkML schema.
    """

    description: str
    slots: List[Slot]


@lod_storable
class Type:
    """
    Represents a type in the LinkML schema.
    """

    uri: str
    base: str
    description: Optional[str]
    notes: Optional[str]
    conforms_to: Optional[str] = None
    comments: Optional[List[str]] = field(default_factory=list)
    exact_mappings: Optional[List[str]] = field(default_factory=list)
    close_mappings: Optional[List[str]] = field(default_factory=list)
    broad_mappings: Optional[List[str]] = field(default_factory=list)
    mappings: Optional[str] = field(init=False, default=None, repr=False)

    def __post_init__(self):
        # Take the first item from exact_mappings, close_mappings, or broad_mappings, in that order
        if self.exact_mappings:
            self.mappings = self.exact_mappings[0]
        elif self.close_mappings:
            self.mappings = self.close_mappings[0]
        elif self.broad_mappings:
            self.mappings = self.broad_mappings[0]


@lod_storable
class Schema:
    """
    Represents the entire LinkML schema.
    """

    name: str
    id: str
    description: str
    title: Optional[str] = None
    version: Optional[str] = None
    license: Optional[str] = None

    default_prefix: Optional[str] = None

    prefixes: Dict[str, str] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    default_range: str = "string"
    classes: Dict[str, Class] = field(default_factory=dict)
    slots: Dict[str, Slot] = field(default_factory=dict)
    types: Dict[str, Type] = field(default_factory=dict)

    def __post_init__(self):
        if not self.title:
            self.title = self.name


class PythonTypes:
    """
    python type handling
    """

    # Define a mapping from Python types to LinkML ranges
    to_linkml_ranges = {
        str: "string",
        int: "integer",
        float: "float",
        bool: "boolean",
        list: "list",
        dict: "dictionary",
    }
    # Mapping from Python types to RDF (XSD) datatypes
    to_rdf_datatypes = {
        str: XSD.string,
        int: XSD.integer,
        float: XSD.float,
        bool: XSD.boolean,
        # Add more mappings if needed
    }

    @classmethod
    def get_linkml_range(cls, ptype: Type) -> str:
        """
        Determines the LinkML range for a given Python type.

        Args:
            ptype (Type): The Python type for which the LinkML range is required.

        Returns:
            str: The corresponding LinkML range as a string. Defaults to "string" if the type is not found.
        """
        return cls.to_linkml_ranges.get(ptype, "string")

    @classmethod
    def get_rdf_datatype(cls, ptype: Type) -> Optional[XSD]:
        """
        Determines the RDF (XSD) datatype for a given Python type.

        Args:
            ptype (Type): The Python type for which the RDF (XSD) datatype is required.

        Returns:
            XSD: The corresponding RDF (XSD) datatype. Returns None if the type is not found.
        """
        return cls.to_rdf_datatypes.get(ptype)
