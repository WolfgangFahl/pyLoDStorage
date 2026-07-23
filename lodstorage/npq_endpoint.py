"""
Created on 2026-07-22

NPQ-FakeSparql: serve named parameterized queries (NPQs) over the SPARQL
protocol - without any SPARQL engine behind them. The technology stays
hidden; only input parameters and output variables are relevant (see the
snapquery EKAW2024 paper). The NPQ name lives in the URL path, input
parameters in the query string; the SERVICE graph pattern of a federated
caller merely declares the output variables.

see https://cr.bitplan.com/index.php/NPQ-FakeSparql

@author: wf
"""

import asyncio
import csv
import io
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from basemkit.yamlable import lod_storable

try:
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, PlainTextResponse, Response
    from rdflib import Graph
    from rdflib_endpoint import SparqlRouter
except ImportError:
    FastAPI = None  # type: ignore

# regex to extract the projected variables of an incoming SELECT query
SELECT_VARS_PATTERN = re.compile(
    r"SELECT\s+(?:DISTINCT\s+|REDUCED\s+)?(?P<vars>.*?)\s+WHERE",
    re.IGNORECASE | re.DOTALL,
)
VAR_PATTERN = re.compile(r"\?(\w+)")


@lod_storable
class NamedQueryStub:
    """
    A named parameterized query served by the fake endpoint.

    The records are the bindings to serve (fixture/fake mode); an executor
    callable may compute them instead (real mode); delay and error allow
    chaos-mode simulation of slow or failing infrastructure.
    """

    name: str
    records: List[Dict[str, Any]] = field(default_factory=list)
    description: Optional[str] = None
    delay_ms: int = 0  # chaos: artificial latency
    error_code: Optional[int] = None  # chaos: fail with this HTTP status

    def __post_init__(self):
        self.executor: Optional[Callable[[Dict[str, str]], List[Dict[str, Any]]]] = None

    def get_records(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Get the bindings for the given input parameters.

        Args:
            params: input parameter values from the URL query string

        Returns:
            list of dicts - one dict per result row
        """
        if self.executor:
            records = self.executor(params)
        else:
            records = self.records
        return records


class SparqlResults:
    """
    Convert a list of dicts to the SPARQL 1.1 query results JSON format.
    """

    @classmethod
    def binding_value(cls, value: Any) -> Dict[str, str]:
        """
        Convert a single value to a SPARQL results binding entry.

        URIs are detected by scheme prefix; other values become literals
        with an xsd datatype where applicable.

        Args:
            value: the value to convert

        Returns:
            the binding entry dict
        """
        if isinstance(value, str) and value.startswith(("http://", "https://", "urn:")):
            entry = {"type": "uri", "value": value}
        elif isinstance(value, bool):
            entry = {
                "type": "literal",
                "value": "true" if value else "false",
                "datatype": "http://www.w3.org/2001/XMLSchema#boolean",
            }
        elif isinstance(value, int):
            entry = {
                "type": "literal",
                "value": str(value),
                "datatype": "http://www.w3.org/2001/XMLSchema#integer",
            }
        elif isinstance(value, float):
            entry = {
                "type": "literal",
                "value": str(value),
                "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
            }
        else:
            entry = {"type": "literal", "value": str(value)}
        return entry

    @classmethod
    def as_json(
        cls, records: List[Dict[str, Any]], var_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convert records to a SPARQL results JSON document.

        Args:
            records: the result rows
            var_names: variables to project; default: union of record keys

        Returns:
            the results document as a dict
        """
        if var_names is None:
            var_names = []
            for record in records:
                for key in record.keys():
                    if key not in var_names:
                        var_names.append(key)
        bindings = []
        for record in records:
            binding = {}
            for var_name in var_names:
                value = record.get(var_name)
                if value is not None:
                    binding[var_name] = cls.binding_value(value)
            bindings.append(binding)
        results = {
            "head": {"vars": var_names},
            "results": {"bindings": bindings},
        }
        return results

    @classmethod
    def select_vars(cls, sparql_query: str) -> Optional[List[str]]:
        """
        Extract the projected variable names of an incoming SELECT query.

        A federated caller sends real SPARQL; its variable names are the
        output contract - we project our bindings onto them.

        Args:
            sparql_query: the incoming SPARQL query text

        Returns:
            the variable names or None for SELECT * / unparseable input
        """
        var_names = None
        match = SELECT_VARS_PATTERN.search(sparql_query)
        if match:
            vars_part = match.group("vars")
            if "*" not in vars_part:
                found = VAR_PATTERN.findall(vars_part)
                if found:
                    var_names = found
        return var_names


class NpqEndpoint:
    """
    NPQ-FakeSparql endpoint: a FastAPI app serving named parameterized
    queries as SPARQL endpoints addressed by name at /npq/{name}.

    Two modes:
    - graph mode: the NPQ's triples (e.g. a CONSTRUCT dump) are served by
      an embedded rdflib-endpoint SparqlRouter - full SPARQL evaluation and
      federation-grade content negotiation (JSON/XML/CSV);
    - bindings mode: where no triples exist, a lightweight stub serves the
      named query's fixed output bindings (fixture or executor), plus plain
      JSON/CSV for non-SPARQL clients.

    NiceGUI-stack compatible (FastAPI/Starlette only).
    """

    # URL parameters that are protocol, not NPQ input
    RESERVED_PARAMS = {"query", "format"}

    def __init__(self, stubs: Optional[List[NamedQueryStub]] = None):
        """
        Construct the endpoint from the given named query stubs.

        Args:
            stubs: the named queries to serve in bindings mode
        """
        if FastAPI is None:
            raise ImportError(
                "rdflib-endpoint is required for NpqEndpoint - "
                "install with pip install pylodstorage[endpoint]"
            )
        self.stubs: Dict[str, NamedQueryStub] = {}
        self.app = self.create_app()
        for stub in stubs or []:
            self.add_stub(stub)

    def add_stub(self, stub: NamedQueryStub) -> None:
        """
        Register the given named query stub (bindings mode).

        A route is registered for the stub's specific name so that graph-mode
        routers and bindings-mode stubs coexist without path shadowing.

        Args:
            stub: the stub to register
        """
        self.stubs[stub.name] = stub
        self.app.add_api_route(
            f"/npq/{stub.name}",
            self.make_handler(stub.name),
            methods=["GET", "POST"],
        )

    def make_handler(self, name: str) -> "Callable":
        """
        Build the request handler for the bindings-mode stub of the given name.

        Args:
            name: the NPQ name

        Returns:
            an async request handler
        """

        async def handler(request: Request) -> Response:
            stub = self.stubs[name]
            # chaos mode
            if stub.delay_ms:
                await asyncio.sleep(stub.delay_ms / 1000.0)
            if stub.error_code:
                return JSONResponse(
                    {"error": f"simulated failure for npq: {name}"},
                    status_code=stub.error_code,
                )
            # input params from the URL query string
            params = {
                key: value
                for key, value in request.query_params.items()
                if key not in self.RESERVED_PARAMS
            }
            # the federator's SPARQL text (if any) carries the output contract
            sparql_query = request.query_params.get("query")
            if sparql_query is None and request.method == "POST":
                form = await request.form()
                sparql_query = form.get("query")
            var_names = None
            if sparql_query:
                var_names = SparqlResults.select_vars(sparql_query)
            records = stub.get_records(params)
            response = self.render(request, records, var_names)
            return response

        return handler

    def add_graph(self, name: str, graph: "Graph") -> None:
        """
        Serve the given rdflib graph as a named SPARQL endpoint (graph mode).

        Mounts an rdflib-endpoint SparqlRouter at /npq/{name} - full SPARQL
        evaluation and federation-grade content negotiation come for free.

        Args:
            name: the NPQ name (URL path segment)
            graph: the rdflib graph to serve
        """
        router = SparqlRouter(graph=graph, path=f"/npq/{name}", title=f"npq:{name}")
        self.app.include_router(router)

    def add_dump(self, name: str, source: str, rdf_format: str = "turtle") -> "Graph":
        """
        Load an RDF dump and serve it as a named SPARQL endpoint (graph mode).

        Args:
            name: the NPQ name (URL path segment)
            source: file path or data string for the dump
            rdf_format: the RDF serialization format

        Returns:
            the loaded rdflib graph
        """
        graph = Graph()
        if "\n" in source or not source.endswith(
            (".ttl", ".nt", ".rdf", ".jsonld", ".n3")
        ):
            graph.parse(data=source, format=rdf_format)
        else:
            graph.parse(source=source, format=rdf_format)
        self.add_graph(name, graph)
        return graph

    def create_app(self) -> "FastAPI":
        """
        Create the bare FastAPI app.

        Bindings-mode routes are added per name via add_stub; graph-mode
        SparqlRouters via add_graph/add_dump.

        Returns:
            the FastAPI app
        """
        app = FastAPI(title="NPQ-FakeSparql")
        return app

    def render(
        self,
        request: "Any",
        records: List[Dict[str, Any]],
        var_names: Optional[List[str]],
    ) -> "Response":
        """
        Render records in the negotiated format.

        Args:
            request: the incoming request (format param / Accept header)
            records: the result rows
            var_names: projected variables or None for all

        Returns:
            the response in SPARQL results JSON, plain JSON or CSV
        """
        result_format = request.query_params.get("format")
        if result_format is None:
            accept = request.headers.get("accept", "")
            if "text/csv" in accept:
                result_format = "csv"
            elif "application/sparql-results+json" in accept:
                result_format = "sparql-json"
            elif "application/json" in accept:
                result_format = "json"
        if result_format == "json":
            response = JSONResponse(records)
        elif result_format == "csv":
            csv_io = io.StringIO()
            fieldnames = var_names
            if fieldnames is None:
                fieldnames = list(records[0].keys()) if records else []
            writer = csv.DictWriter(
                csv_io, fieldnames=fieldnames, extrasaction="ignore"
            )
            writer.writeheader()
            for record in records:
                writer.writerow(record)
            response = PlainTextResponse(csv_io.getvalue(), media_type="text/csv")
        else:
            results = SparqlResults.as_json(records, var_names)
            response = JSONResponse(
                results, media_type="application/sparql-results+json"
            )
        return response

    def run(self, host: str = "127.0.0.1", port: int = 9987) -> None:
        """
        Run the endpoint with uvicorn.

        Args:
            host: host to bind to
            port: port to bind to
        """
        uvicorn.run(self.app, host=host, port=port)
