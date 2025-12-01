"""
Created on 2022-02-13

@author: wf
"""

import logging
import os
import re
import sys
import traceback
import urllib.parse
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import requests

from lodstorage.mysql import MySqlQuery
from lodstorage.prefix_config import PrefixConfigs
from lodstorage.query import Endpoint, EndpointManager, Format, ValueFormatter
from lodstorage.query_cmd import QueryCmd
from lodstorage.rate_limiter import RateLimiter
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB
from lodstorage.version import Version  # Use sqlq.py module for MySQL endpoints

__version__ = Version.version
__date__ = Version.date
__updated__ = Version.updated

DEBUG = 0


class QueryMain(QueryCmd):
    """
    Commandline handler
    """

    def __init__(self, args):
        """
        command line args

        Args:
            args(list): the command line arguments
        """
        super().__init__(args=args)
        self.rate_limiter = RateLimiter(
            calls_per_minute=(
                args.calls_per_minute if hasattr(args, "calls_per_minute") else None
            )
        )

    def handle_args(self) -> bool:
        args = self.args
        handled = super().handle_args()

        if self.queryCode:
            endpointConf = Endpoint()
            endpointConf.method = "POST"
            if args.endpointName:
                endpointConf = self.endpoints.get(args.endpointName)
            else:
                endpointConf.endpoint = self.query.endpoint
            if args.method:
                endpointConf.method = args.method
            if endpointConf:
                self.query.tryItUrl = endpointConf.website
                self.query.database = endpointConf.database
            if self.query.limit:
                if "limit" in self.queryCode or "LIMIT" in self.queryCode:
                    self.queryCode = re.sub(
                        r"(limit|LIMIT)\s+(\d+)",
                        f"LIMIT {self.query.limit}",
                        self.queryCode,
                    )
                else:
                    self.queryCode += f"\nLIMIT {self.query.limit}"
            if args.language == "sparql":
                sparql = SPARQL.fromEndpointConf(endpointConf)
                if args.prefixes and endpointConf is not None:
                    self.query.add_endpoint_prefixes(
                        endpointConf, PrefixConfigs.get_instance()
                    )
                if args.raw:
                    qres = self.rawQuery(
                        endpointConf,
                        query=self.query.query,
                        resultFormat=args.format,
                        mimeType=args.mimeType,
                    )
                    print(qres)
                    return
                if "wikidata" in args.endpointName and self.formats is None:
                    self.formats = ["*:wikidata"]
                qlod = sparql.queryAsListOfDicts(self.queryCode)
            elif args.language == "sql":
                if endpointConf.endpoint.startswith("jdbc:mysql"):
                    query_tool = MySqlQuery(endpointConf, debug=args.debug)
                    qlod = query_tool.execute_sql_query(self.queryCode)
                else:
                    # Use existing SQLDB for other SQL endpoints
                    sqlDB = SQLDB(endpointConf.endpoint)
                    qlod = sqlDB.query(self.queryCode)
            else:
                raise Exception(f"language {args.language} not known/supported")
            self.format_output(qlod)
            handled = True
        return handled

    def rawQuery(
        self,
        endpointConf,
        query: str,
        resultFormat: str,
        mimeType: str,
        content_type: str = "application/sparql-query",
        timeout: float = 10.0,
        lenient: bool = True,
    ):
        """
        Returns raw result of the endpoint.

        Args:
            endpointConf: EndPoint
            query (str): query
            resultFormat (str): format of the result
            mimeType (str): mimeType
            content_type (str): content type of the request
            timeout (float): timeout in seconds
            lenient (bool): if True do not raise errors but just log

        Returns:
            raw result of the query
        """

        headers = {"User-Agent": f"{Version.name}/{Version.version}"}

        if mimeType:
            headers["Accept"] = mimeType

        endpoint = endpointConf.endpoint
        method = endpointConf.method.upper()

        if method == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            data = urllib.parse.urlencode({"query": query, "format": resultFormat})
            params = None
        else:
            headers["Content-Type"] = content_type
            params = {"query": query, "format": resultFormat}
            data = None

        try:
            response = requests.request(
                method,
                endpoint,
                headers=headers,
                data=data,
                params=params,
                timeout=timeout,
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Handle different response content types
            if "application/json" in response.headers.get("Content-Type", ""):
                return response.json()  # Return JSON if applicable
            else:
                return response.text  # Fallback to plain text

        except requests.exceptions.RequestException as e:
            # Log or handle the error as needed
            err_msg = f"An error occurred while querying the endpoint: {e}"
            # Attempt to retrieve response content if available
            if hasattr(e, "response") and e.response is not None:
                error_content = e.response.content.decode("utf-8", errors="replace")
                err_msg += f"\nResponse content: {error_content}"

            if lenient:
                logging.error(err_msg)
                return None
            else:
                raise RuntimeError(err_msg)


def mainSQL(argv=None):
    """
    commandline for SQL queries
    """
    main(argv, lang="sql")


def mainSPARQL(argv=None):
    """
    commandline for SPARQL queries
    """
    main(argv, lang="sparql")


def main(argv=None, lang=None):  # IGNORE:C0111
    """
    main program.

    commandline access to List of Dicts / Linked Open Data Queries
    """
    if argv is None:
        argv = sys.argv[1:]

    program_name = os.path.basename(__file__)
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = "%%(prog)s %s (%s)" % (
        program_version,
        program_build_date,
    )
    program_shortdesc = (
        "commandline query of endpoints in diverse languages such as SPARQL/SQL"
    )
    user_name = "Wolfgang Fahl"
    program_license = """%s

  Created by %s on %s.
  Copyright 2020-2025 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
""" % (
        program_shortdesc,
        user_name,
        str(__date__),
    )

    try:
        # Setup argument parser
        parser = ArgumentParser(
            description=program_license, formatter_class=RawDescriptionHelpFormatter
        )
        QueryCmd.add_args(parser)

        parser.add_argument(
            "-en",
            "--endpointName",
            default="wikidata",
            help=f"Name of the endpoint to use for queries. Available by default: {EndpointManager.getEndpointNames()}",
        )
        parser.add_argument("--method", help="method to be used for SPARQL queries")
        parser.add_argument("-f", "--format", type=Format, choices=list(Format))
        parser.add_argument(
            "-m", "--mimeType", help="MIME-type to use for the raw query"
        )
        parser.add_argument(
            "-p",
            "--prefixes",
            action="store_true",
            help="add predefined prefixes for endpoint",
        )
        parser.add_argument(
            "-raw",
            action="store_true",
            help="return the raw query result from the endpoint. (MIME type defined over -f or -m)",
        )
        parser.add_argument(
            "-V", "--version", action="version", version=program_version_message
        )
        if lang is None:
            parser.add_argument(
                "-l", "--language", help="the query language to use", required=True
            )
        args = parser.parse_args(argv)
        if lang is not None:
            args.language = lang
        query_main = QueryMain(args)
        query_main.handle_args()

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        if DEBUG:
            raise (e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        print(traceback.format_exc())
        return 2


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
