"""
Created on 2025-06-01

@author: wf
"""

from enum import Enum

from SPARQLWrapper import JSON, N3, RDF, TURTLE


class RdfFormat(Enum):
    """
    RDF serialization formats with MIME types, file extensions, and SPARQLWrapper constants.
    """

    TURTLE = ("turtle", "text/turtle", ".ttl", TURTLE)
    RDF_XML = ("rdf-xml", "application/rdf+xml", ".rdf", RDF)
    N3 = ("n3", "text/n3", ".n3", N3)
    JSON_LD = ("json-ld", "application/ld+json", ".jsonld", JSON)

    def __init__(self, label: str, mime_type: str, extension: str, sparql_format):
        self.label = label
        self.mime_type = mime_type
        self.extension = extension
        self.sparql_format = sparql_format

    @classmethod
    def by_label(cls, label: str):
        """Get format by label"""
        for rdf_format in cls:
            if rdf_format.label == label:
                return rdf_format
        raise ValueError(f"Unknown format: {label}")
