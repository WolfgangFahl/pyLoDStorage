"""
Created on 2024-03-02

@author: wf
"""


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
        prefixMap = {
            "bd": "<http://www.bigdata.com/rdf#>",
            "cc": "<http://creativecommons.org/ns#>",
            "dct": "<http://purl.org/dc/terms/>",
            "geo": "<http://www.opengis.net/ont/geosparql#>",
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
        # see also https://www.wikidata.org/wiki/EntitySchema:E49
        sparql = ""
        for prefix in prefixes:
            if prefix in prefixMap:
                sparql += f"PREFIX {prefix}: {prefixMap[prefix]}\n"
        return sparql
