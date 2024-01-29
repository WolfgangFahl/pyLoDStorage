"""
Created on 2024-01-27

@author: wf, using ChatGPT-4 prompting
"""
from collections.abc import Iterable, Mapping
from dataclasses import fields
from typing import Any

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

from lodstorage.linkml_gen import PythonTypes, Schema


class RDFDumper:
    """
    A class to convert instances of data models (based on a LinkML schema) into an RDF graph.
    """

    def __init__(self, schema: Schema, instance: object):
        """
        Initialize the RDFDumper.

        Args:
            schema (Schema): The LinkML schema defining the structure of the data models.
            instance (object): The instance of the data model to be converted into RDF.
        """
        self.schema = schema
        self.instance = instance
        self.graph = Graph()
        self.namespaces = {
            prefix: Namespace(uri) for prefix, uri in schema.prefixes.items()
        }

    def convert_to_rdf(self):
        """
        Converts the provided instance into RDF triples based on the LinkML schema.
        """
        # Process the instance data according to its class in the schema
        instance_class = self.instance.__class__.__name__
        if instance_class in self.schema.classes:
            self.process_class(instance_class, self.instance)

    def serialize(self, rdf_format: str = "turtle") -> str:
        """
        Serializes the RDF graph into a string representation in the specified format.

        Args:
            format (str): The serialization format (e.g., 'turtle', 'xml', 'json-ld').

        Returns:
            str: The serialized RDF graph.
        """
        return self.graph.serialize(format=rdf_format)

    def value_iterator(self, value: Any):
        """
        Iterates over values in a mapping or iterable.

        Args:
            value: The value to iterate over. It can be a mapping, iterable, or a single value.

        Yields:
            Tuples of (key, value) from the input value. For single values, key is None.
        """
        if isinstance(value, Mapping):
            yield from value.items()
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            yield from ((None, v) for v in value)
        else:
            yield (None, value)

    def process_class(self, class_name: str, instance_data: object):
        # Get the base namespace URI
        self.base_uri = self.namespaces[self.schema.default_prefix]
        # get the class object
        # class_obj = self.schema.classes[class_name]
        # Construct class_uri using the namespace and class_name with a separator
        class_uri = URIRef(f"{self.base_uri}:{class_name}")

        # Create a unique URI or a Blank Node for the instance
        instance_uri = self.get_instance_uri(instance_data)

        # Type the instance with its class
        self.graph.add((instance_uri, RDF.type, class_uri))

        # loop over all fieds of the instance data
        for field_info in fields(instance_data):
            slot_name = field_info.name
            # assure we only work on fields defined
            # in our schema
            slot_obj = self.schema.slots.get(slot_name)
            if not slot_obj:
                continue

            # Combine the namespace with the slot name to form the field URI
            field_uri = URIRef(f"{self.base_uri}:{slot_name}")
            field_value = getattr(instance_data, slot_name, None)

            # Use value_iterator to handle different types of values
            for key, item in self.value_iterator(field_value):
                if key is not None:
                    # Handle as a mapping
                    key_uri = URIRef(self.namespaces[self.schema.default_prefix][key])
                    self.graph.add((instance_uri, field_uri, key_uri))
                    self.graph.add(
                        (key_uri, RDF.value, self.convert_to_literal(item, slot_obj))
                    )
                else:
                    # Handle as a single value or an item from an iterable
                    # Check if item has an 'identifier' property
                    if hasattr(item, "identifier") and getattr(item, "identifier"):
                        item_uri = self.get_instance_uri(item)
                        self.graph.add((instance_uri, field_uri, item_uri))
                        self.process_class(item.__class__.__name__, item)
                    else:
                        self.graph.add(
                            (
                                instance_uri,
                                field_uri,
                                self.convert_to_literal(item, slot_obj),
                            )
                        )

    def get_instance_uri(self, instance_data):
        """
        Generates a URI for an instance. If the instance has an 'identifier' property, it uses that as part of the URI.
        Otherwise, it generates or retrieves a unique URI.
        """
        if hasattr(instance_data, "identifier") and getattr(
            instance_data, "identifier"
        ):
            identifier = getattr(instance_data, "identifier")
            return URIRef(f"{self.base_uri}:{identifier}")
        else:
            # Fallback to a blank node if no identifier is found
            return BNode()

    def convert_to_literal(self, value, slot_obj):
        """
        Converts a value to an RDFLib Literal with appropriate datatype.

        Args:
            value: The value to be converted.
            slot_obj: The slot object containing information about the field.

        Returns:
            An RDFLib Literal with the value and appropriate datatype.
        """
        # Determine the datatype based on the Python type of the value
        datatype = PythonTypes.get_rdf_datatype(type(value))

        # Create and return the literal
        return Literal(value, datatype=datatype)
