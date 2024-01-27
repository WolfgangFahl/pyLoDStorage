"""
Created on 2024-01-27

@author: wf, using ChatGPT-4 prompting
"""
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD

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
        self.namespaces = {prefix: Namespace(uri) for prefix, uri in schema.prefixes.items()}

    def convert_to_rdf(self):
        """
        Converts the provided instance into RDF triples based on the LinkML schema.
        """
        # Process the instance data according to its class in the schema
        instance_class = self.instance.__class__.__name__
        if instance_class in self.schema.classes:
            self._process_class(instance_class, self.instance)
    
    def _process_class(self, class_name: str, instance_data: object):
        """
        Processes a single class instance, converting its fields and the corresponding slot data into RDF triples.

        Args:
            class_name (str): The name of the class being processed.
            instance_data (object): The instance data corresponding to the class.
        """
        class_obj = self.schema.classes[class_name]
        class_uri = URIRef(self.namespaces[self.schema.default_prefix][class_name])
        
        for field_info in fields(instance_data):
            slot_name = field_info.name
            slot_obj = self.schema.slots.get(slot_name)
            if not slot_obj:
                continue
            
            field_uri = URIRef(self.namespaces[self.schema.default_prefix][slot_name])
            field_value = getattr(instance_data, slot_name, None)
            
            if field_value is not None:
                if isinstance(field_value, list):
                    # Handle multivalued fields
                    for item in field_value:
                        self.graph.add((class_uri, field_uri, Literal(item)))
                else:
                    # Handle single valued fields
                    self.graph.add((class_uri, field_uri, Literal(field_value)))
    
    def serialize(self, format: str = 'turtle') -> str:
        """
        Serializes the RDF graph into a string representation in the specified format.
        
        Args:
            format (str): The serialization format (e.g., 'turtle', 'xml', 'json-ld').
            
        Returns:
            str: The serialized RDF graph.
        """
        return self.graph.serialize(format=format)




