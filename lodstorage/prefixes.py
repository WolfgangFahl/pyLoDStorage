"""
Created on 2024-03-02

@author: wf
"""

import re


class Prefixes:
    """
    Handles the generation of standard SPARQL prefix declarations for queries.
    This utility class simplifies the inclusion of common prefixes used in SPARQL
    queries by providing a method to generate the necessary PREFIX lines based on
    a list of prefix keys.

    The class supports a wide range of prefixes relevant to Wikidata and general RDF/SPARQL
    usage, including RDF, RDFS, Wikibase, Schema.org, and more. It aims to reduce redundancy
    and improve clarity in SPARQL query construction by centralizing prefix management.

    Attributes:
        None

    Methods:
        getPrefixes(prefixes): Generates SPARQL PREFIX lines for a given list of prefix keys.
    """

    # see https://www.wikidata.org/wiki/EntitySchema:E49
    prefixMap = {
        "bd": "<http://www.bigdata.com/rdf#>",
        "cc": "<http://creativecommons.org/ns#>",
        "dct": "<http://purl.org/dc/terms/>",
        "geo": "<http://www.opengis.net/ont/geosparql#>",
        "mwapi": "<https://www.mediawiki.org/ontology#API/>",
        "ontolex": "<http://www.w3.org/ns/lemon/ontolex#>",
        "owl": "<http://www.w3.org/2002/07/owl#>",
        "p": "<http://www.wikidata.org/prop/>",
        "pq": "<http://www.wikidata.org/prop/qualifier/>",
        "pqn": "<http://www.wikidata.org/prop/qualifier/value-normalized/>",
        "pqv": "<http://www.wikidata.org/prop/qualifier/value/>",
        "pr": "<http://www.wikidata.org/prop/reference/>",
        "prn": "<http://www.wikidata.org/prop/reference/value-normalized/>",
        "prov": "<http://www.w3.org/ns/prov#>",
        "prv": "<http://www.wikidata.org/prop/reference/value/>",
        "ps": "<http://www.wikidata.org/prop/statement/>",
        "psn": "<http://www.wikidata.org/prop/statement/value-normalized/>",
        "psv": "<http://www.wikidata.org/prop/statement/value/>",
        "rdf": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
        "rdfs": "<http://www.w3.org/2000/01/rdf-schema#>",
        "schema": "<http://schema.org/>",
        "skos": "<http://www.w3.org/2004/02/skos/core#>",
        "wd": "<http://www.wikidata.org/entity/>",
        "wdsubgraph": "<https://query.wikidata.org/subgraph/>",
        "wdata": "<http://www.wikidata.org/wiki/Special:EntityData/>",
        "wdno": "<http://www.wikidata.org/prop/novalue/>",
        "wdref": "<http://www.wikidata.org/reference/>",
        "wds": "<http://www.wikidata.org/entity/statement/>",
        "wdt": "<http://www.wikidata.org/prop/direct/>",
        "wdtn": "<http://www.wikidata.org/prop/direct-normalized/>",
        "wdv": "<http://www.wikidata.org/value/>",
        "wikibase": "<http://wikiba.se/ontology#>",
        "xsd": "<http://www.w3.org/2001/XMLSchema#>",
    }

    @classmethod
    def getPrefixes(
        cls, prefixes=["rdf", "rdfs", "schema", "wd", "wdt", "wikibase", "xsd"]
    ) -> str:
        """Generates SPARQL PREFIX lines for a given list of prefix keys.

        This method looks up URIs for the specified prefixes from a predefined map and constructs
        PREFIX lines suitable for inclusion at the beginning of a SPARQL query. It allows for easy
        and flexible specification of the prefixes needed for a particular query.

        Args:
            prefixes (list of str): A list of prefix keys for which PREFIX lines should be generated.
                Defaults to a common set of prefixes used in Wikidata queries.

        Returns:
            str: A string containing the SPARQL PREFIX lines for the specified prefixes, each ending
                with a newline character. If a prefix key is not recognized, it is ignored.

        Example:
            >>> Prefixes.getPrefixes(["wd", "wdt"])
            'PREFIX wd: <http://www.wikidata.org/entity/>\nPREFIX wdt: <http://www.wikidata.org/prop/direct/>\n'
        """

        # see also https://www.wikidata.org/wiki/EntitySchema:E49
        prefixes = cls.prefix_string(cls.prefixMap, prefixes)
        return prefixes

    @classmethod
    def prefix_string(cls, prefix_dict: dict, prefix_keys: list[str]):
        prefixes = ""
        for prefix in prefix_keys:
            if prefix in prefix_dict:
                prefixes += cls.prefix_line(prefix_dict, prefix)
        return prefixes

    @classmethod
    def prefix_line(cls, prefix_dict: dict, prefix: str) -> str:
        line = f"PREFIX {prefix}: {prefix_dict[prefix]}\n"
        return line

    @classmethod
    def extract_prefixes(cls, sparql_query: str) -> dict:
        """
        Extract only the explicitly declared prefixes from a SPARQL query string.
        Simple regex-based extraction that finds PREFIX declarations in the query text.

        Args:
            sparql_query (str): The SPARQL query containing PREFIX declarations

        Returns:
            dict: Dictionary mapping prefix names to their URI strings
        """
        declared_prefixes = {}

        # Simple pattern to match PREFIX declarations: PREFIX name: <uri>
        prefix_pattern = r"PREFIX\s+(\w+):\s*<([^>]+)>"

        # Find all PREFIX declarations (case insensitive)
        matches = re.findall(prefix_pattern, sparql_query, re.IGNORECASE)

        # Convert matches to dictionary
        for prefix_name, uri in matches:
            declared_prefixes[prefix_name] = f"<{uri}>"

        return declared_prefixes

    @classmethod
    def merge_prefix_dict(cls, query: str, prefix_dict: dict) -> str:
        """
        Merge prefixes from dict into SPARQL query by prepending missing prefix declarations.

        Args:
            query (str): The SPARQL query
            prefix_dict (dict): Dictionary of prefixes to merge

        Returns:
            str: SPARQL query with missing prefixes prepended
        """
        existing_prefixes = cls.extract_prefixes(query)
        missing = set(prefix_dict.keys()) - set(existing_prefixes.keys())
        prepend = cls.prefix_string(prefix_dict, list(missing))
        query = prepend + query

        return query

    @classmethod
    def merge_prefixes(cls, query: str, prefixes: str) -> str:
        """
        Merge prefixes from string into SPARQL query by prepending missing prefix declarations.

        Args:
            query (str): The SPARQL query
            prefixes (str): String containing PREFIX declarations

        Returns:
            str: SPARQL query with missing prefixes prepended
        """
        prefix_dict = cls.extract_prefixes(prefixes)
        merged_query = cls.merge_prefix_dict(query, prefix_dict)
        return merged_query
