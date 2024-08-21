"""
Created on 2024-08-21

@author: wf
"""

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path

from lodstorage.lod_csv import CSV
from lodstorage.params import Params, StoreDictKeyPair
from lodstorage.query import (
    EndpointManager,
    Format,
    Query,
    QueryManager,
    ValueFormatter,
)
from lodstorage.xml import Lod2Xml
from typing import Dict, List, Any


class QueryCmd:
    """
    command line support queries
    """

    def __init__(self, args: Namespace):
        """
        command line args

        Args:
            args (Namespace): the command line arguments
        """
        self.args = args
        self.debug = args.debug

    def handle_args(self) -> bool:
        """
        handle the command line arguments
        """
        handled = False
        debug = self.debug
        args = self.args
        self.endpoints = EndpointManager.getEndpoints(self.args.endpointPath)
        self.qm = QueryManager(
            lang=args.language, debug=debug, queriesPath=args.queriesPath
        )
        self.query = None
        self.queryCode = args.query
        self.formats = None
        # preload ValueFormatter
        ValueFormatter.getFormats(args.formatsPath)
        if args.list:
            for name, query in self.qm.queriesByName.items():
                print(f"{name}:{query.title}")
            handled = True
        elif args.listEndpoints:
            # list endpoints
            for endpoint in self.endpoints.values():
                if hasattr(endpoint, "lang") and endpoint.lang == args.language:
                    print(endpoint)
            handled = True
        elif args.queryName is not None:
            if debug or args.showQuery:
                print(f"named query {args.queryName}:")
            if args.queryName not in self.qm.queriesByName:
                raise Exception(f"named query {args.queryName} not available")
            self.query = self.qm.queriesByName[args.queryName]
            if self.query.limit is None and args.limit is not None:
                self.query.limit = args.limit
            self.formats = self.query.formats
            self.queryCode = self.query.query
            if debug or args.showQuery:
                if (
                    hasattr(self.query, "description")
                    and self.query.description is not None
                ):
                    print(self.query.description)
        if self.query is None:
            name = "?"
            if self.queryCode is None and args.queryFile is not None:
                queryFilePath = Path(args.queryFile)
                self.queryCode = queryFilePath.read_text()
                name = queryFilePath.stem
            query = Query(name="?", query=self.queryCode, lang=args.language)

        if self.queryCode:
            params = Params(self.query.query)
            self.query.query = params.apply_parameters_with_check(args.params)
            self.queryCode = self.query.query
            if debug or args.showQuery:
                print(f"{args.language}:\n{self.query.query}")
        return handled

    def format_output(self, qlod: List[Dict[str, Any]]):
        """
        Format and print the query results.

        This method formats the query results based on the specified output format
        (e.g., CSV, JSON, XML) and prints them to the console.

        Args:
            qlod (List[Dict[str, Any]]): A list of dictionaries containing the query results.
                Each dictionary represents a row of the query result, with column names as keys
                and the corresponding values.
        """
        args = self.args
        if args.format is Format.csv:
            csv = CSV.toCSV(qlod)
            print(csv)
        elif args.format in [Format.latex, Format.github, Format.mediawiki]:
            doc = self.query.documentQueryResult(
                qlod, tablefmt=str(args.format), floatfmt=".0f"
            )
            docstr = doc.asText()
            print(docstr)
        elif args.format in [Format.json] or args.format is None:  # set as default
            # https://stackoverflow.com/a/36142844/1497139
            print(json.dumps(qlod, indent=2, sort_keys=True, default=str))
        elif args.format in [Format.xml]:
            lod2xml = Lod2Xml(qlod)
            xml = lod2xml.asXml()
            print(xml)

        else:
            raise Exception(f"format {args.format} not supported yet")

    @classmethod
    def add_args(cls, parser: ArgumentParser):
        parser.add_argument(
            "-ep",
            "--endpointPath",
            default=None,
            help="path to yaml file to configure endpoints to use for queries",
        )
        parser.add_argument(
            "-li",
            "--list",
            action="store_true",
            help="show the list of available queries",
        )
        parser.add_argument(
            "--limit", type=int, default=None, help="set limit parameter of query"
        )
        parser.add_argument(
            "--params",
            action=StoreDictKeyPair,
            help="query parameters as Key-value pairs in the format key1=value1,key2=value2",
        )
        parser.add_argument(
            "-le",
            "--listEndpoints",
            action="store_true",
            help="show the list of available endpoints",
        )
        parser.add_argument(
            "-sq", "--showQuery", action="store_true", help="show the query"
        )
        parser.add_argument(
            "-qp", "--queriesPath", help="path to YAML file with query definitions"
        )
        parser.add_argument("-q", "--query", help="the query to run")
        parser.add_argument("-qf", "--queryFile", help="the query file to run")
        parser.add_argument("-qn", "--queryName", help="run a named query")
