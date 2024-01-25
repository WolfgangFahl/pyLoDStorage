"""
Created on 2024-01-21

@author: wf
"""
from pyparsing import (
    Group,
    Literal,
    OneOrMore,
    Optional,
    Suppress,
    Word,
    alphanums,
    alphas,
    restOfLine,
)


class DocstringParser:
    """
    A Python docstring parser.
    """

    def __init__(self):
        # Define basic elements
        identifier = Word(alphas, alphanums + "_")
        type_identifier = Word(alphas, alphanums + "_.[]")
        description = restOfLine

        # Define patterns for capturing attributes
        attribute_start = Suppress(Literal("Attributes:"))
        self.attribute = Group(
            identifier("name")
            + Suppress("(")
            + Optional(type_identifier("type"))
            + Suppress("):")
            + description("description")
        )

        # Define pattern for class docstring
        class_docstring = restOfLine("class_description") + Optional(
            attribute_start + OneOrMore(self.attribute)("attributes")
        )

        # Updated class_docstring pattern to correctly handle multi-line class descriptions
        self.class_docstring = class_docstring + Optional(
            OneOrMore(~attribute_start + restOfLine)("class_description")
            + attribute_start
            + OneOrMore(self.attribute)("attributes")
        )

    def parse(self, docstring: str):
        """
        Parse the given docstring.
        """
        result = self.class_docstring.parseString(docstring, parseAll=True)
        class_description = " ".join(result.class_description).strip()
        attributes = {
            attr.name: {"type": attr.type, "description": attr.description.strip()}
            for attr in result.attributes
        }
        return class_description, attributes
