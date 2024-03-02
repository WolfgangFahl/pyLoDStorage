"""
Created on 2024-03-02

@author: wf
"""


class Prefixes:
    """
    handle standard SPARQL Prefixes
    """

    @classmethod
    def getPrefixes(
        cls, prefixes=["rdf", "rdfs", "schema", "wd", "wdt", "wikibase", "xsd"]
    ) -> str:
        """ 
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
