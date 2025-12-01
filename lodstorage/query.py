"""
Created on 2020-08-22
2025-12-01 version for prefix sets

@author: wf
"""

import copy
from lodstorage.exception_handler import ExceptionHandler
import os
import re
import sys
import urllib
from dataclasses import field
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml
from basemkit.yamlable import lod_storable
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.formatters.latex import LatexFormatter
from pygments.lexers import get_lexer_by_name
from tabulate import tabulate

from lodstorage.mwTable import MediaWikiTable
from lodstorage.params import Param, Params
from lodstorage.prefix_config import PrefixConfigs
from lodstorage.prefixes import Prefixes
from lodstorage.yaml_path import YamlPath


# from wikibot.mwTable import MediaWikiTable
# redundant copy in this library to avoid dependency issues
# original is at
class Format(Enum):
    """
    the supported formats for the results to be delivered
    """

    csv = "csv"
    json = "json"
    html = "html"
    xml = "xml"
    tsv = "tsv"
    latex = "latex"
    mediawiki = "mediawiki"
    raw = "raw"
    github = "github"

    def __str__(self):
        return self.value


@lod_storable
class ValueFormatter:
    """
    a value Formatter
    """

    format: str
    regexps: List[str] = field(default_factory=list)

    def apply_format(self, record, key, resultFormat: Format):
        """
        apply the given format to the given record

        Args:
            record(dict): the record to handle
            key(str): the property key
            resultFormat(str): the resultFormat Style to apply
        """
        if key in record:
            value = record[key]
            if value is not None and isinstance(value, str):
                # if there are no regular expressions specified always format
                doformat = len(self.regexps) == 0
                for regexp in self.regexps:
                    try:
                        vmatch = re.match(regexp, value)
                        if vmatch:
                            # we found a match and will format it if the value is not none
                            doformat = True
                            value = vmatch.group("value")
                    except Exception as ex:
                        print(
                            f"ValueFormatter: {self.name}\nInvalid regular expression:{regexp}\n{str(ex)}",
                            file=sys.stderr,
                        )
                if value is not None and doformat:
                    link = self.format.format(value=value)
                    newValue = None
                    if resultFormat == "github":
                        newValue = f"[{value}]({link})"
                    elif resultFormat == "mediawiki":
                        newValue = f"[{link} {value}]"
                    elif resultFormat == "latex":
                        newValue = rf"\href{{{link}}}{{{value}}}"
                    if newValue is not None:
                        record[key] = newValue

    def applyFormat(self, record, key, resultFormat: Format):
        """
        legacy delegate
        """
        self.apply_format(record, key, resultFormat)


@lod_storable
class ValueFormatters:
    """
    manages a set of ValueFormatters
    """

    formatters: Dict[str, ValueFormatter] = field(default_factory=dict)

    _instance: Optional["ValueFormatters"] = None
    _formats_path: Optional[str] = None

    @classmethod
    def get_instance(cls) -> "ValueFormatters":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls.of_yaml()
        return cls._instance

    @classmethod
    def preload(cls, formats_path: str) -> "ValueFormatters":
        """Preload singleton with specific formats path."""
        cls._instance = cls.of_yaml(formats_path)
        return cls._instance

    @classmethod
    def of_yaml(cls, yaml_path: str = None) -> "ValueFormatters":
        """Load ValueFormatters from YAML file."""
        vf = None
        if yaml_path is None:
            paths = YamlPath.getPaths("formats.yaml")
            if len(paths) > 0:
                yaml_path = paths[0]
        if yaml_path:
            vf = cls.load_from_yaml_file(yaml_path)
            cls._formats_path = yaml_path
        return vf


class QuerySyntaxHighlight:
    """
    Syntax highlighting for queries with pygments
    """

    def __init__(self, query, highlightFormat: str = "html"):
        """
        construct me for the given query and highlightFormat

        Args:
            query(Query): the query to do the syntax highlighting for
            highlightFormat(str): the highlight format to be used
        """
        self.query = query
        self.highlightFormat = highlightFormat
        self.lexer = get_lexer_by_name(self.query.lang)
        if self.highlightFormat == "html":
            self.formatter = HtmlFormatter()
        elif self.highlightFormat == "latex":
            self.formatter = LatexFormatter()

    def highlight(self):
        """
        Returns:
            str: the result of the syntax highlighting with pygments
        """
        syntaxResult = highlight(self.query.query, self.lexer, self.formatter)
        return syntaxResult


class QueryResultDocumentation:
    """
    documentation of a query result
    """

    def __init__(
        self,
        query,
        title: str,
        tablefmt: str,
        tryItMarkup: str,
        sourceCodeHeader: str,
        sourceCode: str,
        resultHeader: str,
        result: str,
    ):
        """
        constructor

        Args:
            query(Query): the query to be documented
            title(str): the title markup
            tablefmt(str): the tableformat that has been used
            tryItMarkup: the "try it!" markup to show
            sourceCodeHeader(str): the header title to use for the sourceCode
            sourceCode(str): the sourceCode
            resultCodeHeader(str): the header title to use for the result
            result(str): the result header

        """
        self.query = query
        self.title = title
        self.tablefmt = tablefmt
        self.tryItMarkup = f"\n{tryItMarkup}"
        self.sourceCodeHeader = sourceCodeHeader
        self.sourceCode = sourceCode
        self.resultHeader = resultHeader
        self.result = result

    @staticmethod
    def uniCode2Latex(text: str, withConvert: bool = False) -> str:
        """
        converts unicode text to latex and
        fixes UTF-8 chars for latex in a certain range:
            ₀:$_0$ ... ₉:$_9$

        see https://github.com/phfaist/pylatexenc/issues/72

        Args:
            text(str): the string to fix
            withConvert(bool): if unicode to latex libary conversion should be used

        Return:
            str: latex presentation of UTF-8 char
        """
        for code in range(8320, 8330):
            text = text.replace(chr(code), f"$_{code-8320}$")
        if withConvert:
            # workaround - hidden dependency!
            from pylatexenc.latexencode import unicode_to_latex

            latex = unicode_to_latex(text)
            # workaround {\textbackslash} being returned
            # latex=latex.replace("{\\textbackslash}",'\\')
            text = latex
        return text

    def __str__(self):
        """
        simple string representation
        """
        return self.asText()

    def asText(self):
        """
        return my text representation

        Returns:
            str: description, sourceCodeHeader, sourceCode, tryIt link and result table
        """
        text = f"{self.title}\n{self.query.description}\n{self.sourceCodeHeader}\n{self.sourceCode}{self.tryItMarkup}\n{self.resultHeader}\n{self.result}"
        fixedStr = (
            self.uniCode2Latex(text) if self.tablefmt.lower() == "latex" else text
        )
        return fixedStr


@lod_storable
class Query:
    """
    A Query e.g. for SPARQL

    Attributes:
        name (str): the name/label of the query
        query (str): the native Query text e.g. in SPARQL
        lang (str): the language of the query e.g. SPARQL

        sparql(str): SPARQL querycode
        sql(str): SQL query code
        ask(atr): SMW ASK query code

        endpoint (str): the endpoint url to use
        database (str): the type of database e.g. "blazegraph"
        title (str): the header/title of the query
        description (str): the description of the query
        limit (int): the limit of the query
        prefixes (list): list of prefixes to be resolved
        tryItUrl (str): the url of a "tryit" webpage
        short_urls (dict): dictionary of short urls keyed by endpoint name
        formats (list): key,value pairs of ValueFormatters to be applied
        debug (bool): true if debug mode should be switched on
    """

    name: str
    query: str
    lang: str = "sparql"
    sparql: Optional[str] = None
    sql: Optional[str] = None
    ask: Optional[str] = None
    endpoint: Optional[str] = None
    database: str = "blazegraph"
    title: Optional[str] = None
    description: Optional[str] = ""
    limit: Optional[int] = None
    prefixes: Optional[List[str]] = None
    tryItUrl: Optional[str] = None
    short_urls: Dict[str, str] = field(default_factory=dict)
    formats: Optional[List] = None
    debug: bool = False
    formatCallBacks: List = field(default_factory=list)
    param_list: List[Param] = field(default_factory=list)  # input
    output: List[Param] = field(default_factory=list)  # output

    def __post_init__(self):
        if self.title is None:
            self.title = self.name
        if self.query:
            self.params = Params(self.query)

    def __str__(self):
        queryStr = "\n".join(
            [
                f"{key}:{value}"
                for key, value in self.__dict__.items()
                if value is not None
            ]
        )
        return f"{queryStr}"

    def set_default_params(self, params_dict: Dict[str, Any]):
        """
        set the default parameters for the given params_dict
        """
        for param in self.param_list:
            value = param.default_value
            params_dict[param.name] = value

    def apply_default_params(self):
        """
        apply my default parameters
        """
        self.set_default_params(self.params.params_dict)
        self.params.apply_parameters()

    def addFormatCallBack(self, callback):
        self.formatCallBacks.append(callback)

    def preFormatWithCallBacks(self, lod, tablefmt: str):
        """
        run the configured call backs to pre-format the given list of dicts for the given tableformat

        Args:
            lod(list): the list of dicts to handle
            tablefmt(str): the table format (according to tabulate) to apply

        """
        for record in lod:
            for key in record.keys():
                value = record[key]
                if value is not None:
                    for formatCallBack in self.formatCallBacks:
                        formatCallBack(record, key, value, tablefmt)

    def formatWithValueFormatters(self, lod, tablefmt: str):
        """
        format the given list of Dicts with the ValueFormatters
        """
        # is there anything to do?
        if self.formats is None:
            # no
            return
        # get the value Formatters that might apply here
        valueFormatters = ValueFormatters.get_instance()
        formatsToApply = {}
        for valueFormatSpec in self.formats:
            parts = valueFormatSpec.split(":")
            # e.g. president:wikidata
            keytoformat = parts[0]
            formatName = parts[1]
            if formatName in valueFormatters.formatters:
                formatsToApply[keytoformat] = valueFormatters.formatters[formatName]
        for record in lod:
            for keytoformat in formatsToApply:
                valueFormatter = formatsToApply[keytoformat]
                # format all key values
                if keytoformat == "*":
                    for key in record:
                        valueFormatter.apply_format(record, key, tablefmt)
                # or just a selected one
                elif keytoformat in record:
                    valueFormatter.apply_format(record, keytoformat, tablefmt)

    def getTryItUrl(self, baseurl: str, database: str = "blazegraph"):
        """
        return the "try it!" url for the given baseurl

        Args:
            baseurl(str): the baseurl to used

        Returns:
            str: the "try it!" url for the given query
        """
        # https://stackoverflow.com/a/9345102/1497139
        prefixed_query = str(self.query)
        if self.prefixes:
            prepend = "\n".join(self.prefixes)
            prefixed_query = prepend + prefixed_query
        quoted = urllib.parse.quote(prefixed_query)
        if database == "blazegraph":
            delim = "/#"
        else:
            delim = "?query="
        url = f"{baseurl}{delim}{quoted}"
        return url

    def getLink(self, url, title, tablefmt):
        """
        convert the given url and title to a link for the given tablefmt

        Args:
            url(str): the url to convert
            title(str): the title to show
            tablefmt(str): the table format to use
        """
        # create a safe url
        if url is None:
            return ""
        markup = f"{title}:{url}"
        if tablefmt == "mediawiki":
            markup = f"[{url} {title}]"
        elif tablefmt == "github":
            markup = f"[{title}]({url})"
        elif tablefmt == "latex":
            markup = r"\href{%s}{%s}" % (url, title)
        return markup

    def add_endpoint_prefixes(
        self, endpoint: "Endpoint", prefix_configs: PrefixConfigs
    ) -> None:
        """
        Add endpoint-specific PREFIX declarations to this query (via prefix_sets or legacy prefixes).

        Merges (deduplicates by prefix name) endpoint prefixes into self.query using Prefixes.merge_prefixes().
        Updates self.prefixes to full unique PREFIX lines list. Safe/idempotent (no-op if prefixes_str empty).

        Args:
            endpoint (Endpoint): Endpoint config with prefix_sets or legacy prefixes.
            prefix_configs (PrefixConfigs): Loaded prefix configurations resolver.
        """
        prefixes_str = endpoint.get_prefixes(prefix_configs)
        if not prefixes_str.strip():
            return

        # Merge: Prepend ONLY missing prefixes (no dups like 'rdfs')
        self.query = Prefixes.merge_prefixes(self.query, prefixes_str)

        # Update self.prefixes: Full unique lines from merged query
        prefix_dict = Prefixes.extract_prefixes(self.query)
        self.prefixes = [
            Prefixes.prefix_line(prefix_dict, prefix) for prefix in sorted(prefix_dict)
        ]

    def prefixToLink(self, lod: list, prefix: str, tablefmt: str):
        """
        convert url prefixes to link according to the given table format
        TODO - refactor as preFormat callback

        Args:
            lod(list): the list of dicts to convert
            prefix(str): the prefix to strip
            tablefmt(str): the tabulate tableformat to use

        """
        for record in lod:
            for key in record.keys():
                value = record[key]
                if (
                    value is not None
                    and isinstance(value, str)
                    and value.startswith(prefix)
                ):
                    item = value.replace(prefix, "")
                    uqitem = urllib.parse.unquote(item)
                    if tablefmt == "latex":
                        link = uqitem
                    else:
                        link = self.getLink(value, uqitem, tablefmt)
                    record[key] = link

    def asWikiSourceMarkup(self):
        """
        convert me to Mediawiki markup for syntax highlighting using the "source" tag


        Returns:
            string: the Markup
        """
        markup = "<source lang='%s'>\n%s\n</source>\n" % (self.lang, self.query)
        return markup

    def asWikiMarkup(self, listOfDicts):
        """
        convert the given listOfDicts result to MediaWiki markup

        Args:
            listOfDicts(list): the list of Dicts to convert to MediaWiki markup

        Returns:
            string: the markup
        """
        if self.debug:
            print(listOfDicts)
        mwTable = MediaWikiTable()
        mwTable.fromListOfDicts(listOfDicts)
        markup = mwTable.asWikiMarkup()
        return markup

    def documentQueryResult(
        self,
        qlod: list,
        limit=None,
        tablefmt: str = "mediawiki",
        tryItUrl: str = None,
        withSourceCode=True,
        **kwArgs,
    ):
        """
        document the given query results - note that a copy of the whole list is going to be created for being able to format

        Args:
            qlod: the list of dicts result
            limit(int): the maximum number of records to display in result tabulate
            tablefmt(str): the table format to use
            tryItUrl: the "try it!" url to show
            withSourceCode(bool): if True document the source code

        Return:
            str: the documentation tabular text for the given parameters
        """
        sourceCode = self.query
        tryItMarkup = ""
        sourceCodeHeader = ""
        resultHeader = ""
        title = self.title
        if limit is not None:
            lod = copy.deepcopy(qlod[:limit])
        else:
            lod = copy.deepcopy(qlod)
        self.preFormatWithCallBacks(lod, tablefmt=tablefmt)
        self.formatWithValueFormatters(lod, tablefmt=tablefmt)
        result = tabulate(lod, headers="keys", tablefmt=tablefmt, **kwArgs)
        if tryItUrl is None and hasattr(self, "tryItUrl"):
            tryItUrl = self.tryItUrl
        if tablefmt == "github":
            title = f"## {self.title}"
            resultHeader = "## result"
        elif tablefmt == "mediawiki":
            title = f"== {self.title} =="
            resultHeader = "=== result ==="
        elif tablefmt == "latex":
            resultHeader = ""
            result = r"""\begin{table}
            \caption{%s}
            \label{tab:%s}
            %s
            \end{table}
            """ % (
                self.title,
                self.name,
                result,
            )
        else:
            title = f"{self.title}"
            resultHeader = "result:"
        if withSourceCode:
            tryItUrlEncoded = self.getTryItUrl(tryItUrl, self.database)
            tryItMarkup = self.getLink(tryItUrlEncoded, "try it!", tablefmt)
            if tablefmt == "github":
                sourceCodeHeader = "### query"
                sourceCode = f"""```{self.lang}
{self.query}
```"""
            elif tablefmt == "mediawiki":
                sourceCodeHeader = "=== query ==="
                sourceCode = f"""<source lang='{self.lang}'>
{self.query}
</source>
"""
            elif tablefmt == "latex":
                sourceCodeHeader = (
                    r"see query listing \ref{listing:%s} and result table \ref{tab:%s}"
                    % (self.name, self.name)
                )
                sourceCode = r"""\begin{listing}[ht]
\caption{%s}
\label{listing:%s}
\begin{minted}{%s}
%s
\end{minted}
%s
\end{listing}
""" % (
                    self.title,
                    self.name,
                    self.lang.lower(),
                    self.query,
                    tryItMarkup,
                )
            else:
                sourceCodeHeader = "query:"
                sourceCode = f"{self.query}"
        if self.lang != "sparql":
            tryItMarkup = ""
        queryResultDocumentation = QueryResultDocumentation(
            query=self,
            title=title,
            tablefmt=tablefmt,
            tryItMarkup=tryItMarkup,
            sourceCodeHeader=sourceCodeHeader,
            sourceCode=sourceCode,
            resultHeader=resultHeader,
            result=result,
        )
        return queryResultDocumentation


class QueryManager(object):
    """
    manages pre packaged Queries
    """

    def __init__(
        self, lang: str = None, debug=False, queriesPath=None, with_default: bool = True
    ):
        """
        Constructor
        Args:
            lang(str): the language to use for the queries sql or sparql
            queriesPath(str): the path of the yaml file to load queries from
            debug(bool): True if debug information should be shown
            with_default(bool): if True also load the default yaml file
        """
        if lang is None:
            lang = "sql"
        self.queriesByName = {}
        self.lang = lang
        self.debug = debug
        queries = self.getQueries(queriesPath=queriesPath, with_default=with_default)
        for name, queryDict in queries.items():
            if self.lang in queryDict:
                queryDict["name"] = name
                queryDict["lang"] = self.lang
                if not "query" in queryDict:
                    queryDict["query"] = queryDict[self.lang]
                try:
                    query = Query.from_dict(queryDict)
                    query.debug = self.debug
                    self.queriesByName[name] = query
                except Exception as ex:
                    msg = f"Failed to load query '{name}' ({self.lang})"
                    ExceptionHandler.handle(msg, ex, debug=self.debug)

    def getQueries(self, queriesPath=None, with_default: bool = True):
        """
        get the queries for the given queries Path

        Args:
            queriesPath(str): the path of the yaml file to load queries from
            with_default(bool): if True also load the default yaml file

        """
        queriesPaths = YamlPath.getPaths(
            "queries.yaml", queriesPath, with_default=with_default
        )
        queries = {}
        for queriesPath in queriesPaths:
            if os.path.isfile(queriesPath):
                with open(queriesPath, "r") as stream:
                    lqueries = yaml.safe_load(stream)
                    for key in lqueries:
                        queries[key] = lqueries[key]
        return queries


@lod_storable
class Endpoint:
    """
    a query endpoint
    """

    # Basic identification
    name: str = ""
    description: Optional[str] = None

    # Connection details
    lang: str = "SPARQL"
    endpoint: str = ""
    website: Optional[str] = None
    database: str = "blazegraph"
    method: str = "POST"
    # JDBC endpoints e.g. SQL
    host: Optional[str] = "localhost"
    port: Optional[int] = 3306
    charset: Optional[str] = "utf8mb4"

    # Authentication and rate limiting
    calls_per_minute: Optional[int] = None
    auth: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

    # Prefix handling
    prefix_sets: Optional[List[str]] = None  # References to prefix set names
    prefixes: Optional[str] = None  # Legacy: inline prefixes for backward compatibility

    # Dataset characteristics
    data_seeded: Optional[str] = (
        None  # ISO date when data was initially seeded/imported: "2012-10-29"
    )
    auto_update: Optional[bool] = (
        None  # if false data_seeded is the most recent state of data
    )
    mtriples: Optional[int] = None  # Dataset size in millions of triples

    @classmethod
    def getSamples(cls):
        samples = [
            {
                "name": "wikidata",
                "lang": "sparql",
                "endpoint": "https://query.wikidata.org/sparql",
                "website": "https://query.wikidata.org/",
                "database": "blazegraph",
                "method": "POST",
                "calls_per_minute": 30,
                "prefixes": "PREFIX bd: <http://www.bigdata.com/rdf#>\nPREFIX cc: <http://creativecommons.org/ns#>",
            },
            {
                "name": "dbis-jena",
                "lang": "sparql",
                "endpoint": "https://confident.dbis.rwth-aachen.de/jena/",
                "website": "https://confident.dbis.rwth-aachen.de",
                "auth": "BASIC",
                "user": "secret",
                "password": "#not public - example not usable for access#",
            },
            {
                "name": "qlever-wikidata",
                "lang": "sparql",
                "method": "POST",
                "database": "qlever",
                "endpoint": "https://qlever.cs.uni-freiburg.de/api/wikidata",
                "website": "https://qlever.cs.uni-freiburg.de/wikidata",
            },
        ]
        return samples

    @classmethod
    def get_samples(cls) -> dict[str, List["Endpoint"]]:
        """
        Get samples for Endpoint
        """
        sample_dicts = cls.getSamples()
        endpoint_list=[]
        for sample_dict in sample_dicts:
            endpoint=cls(**sample_dict)
            endpoint_list.append(endpoint)
        samples= {"sample-endpoints": endpoint_list}
        return samples

    @classmethod
    def getDefault(cls):
        """
        get the default endpoint cofiguration
        """
        sample_data = cls.getSamples()[0]
        endpoint_conf = cls.from_dict(sample_data)
        return endpoint_conf

    def get_prefixes(self, prefix_configs: Optional[PrefixConfigs] = None) -> str:
        """
        Get prefix declarations for this endpoint.

        Args:
            prefix_configs: PrefixConfigs instance to resolve prefix_sets

        Returns:
            str: PREFIX declarations
        """
        # default: empty
        prefixes = ""
        # Use inline prefixes if defined (legacy support)
        if self.prefixes:
            prefixes = self.prefixes

        # Resolve from prefix_sets if available
        if self.prefix_sets and prefix_configs:
            prefixes = prefix_configs.get_selected_declarations(self.prefix_sets)

        return prefixes

    def __str__(self):
        """
        Returns:
            str: a string representation of this Endpoint
        """
        text = f"{self.name or ''}:{self.website or ''}:{self.endpoint or ''}({self.method or ''})"
        return text


@lod_storable
class EndpointManager(object):
    """
    manages a set of SPARQL endpoints
    """

    endpoints: Dict[str, Endpoint] = field(default_factory=dict)

    @classmethod
    def of_yaml(cls, yaml_path: str) -> "EndpointManager":
        """Load prefix configurations from YAML file."""
        em = cls.load_from_yaml_file(yaml_path)
        return em

    @classmethod
    def ofYaml(cls, yaml_path: str) -> "EndpointManager":
        em = cls.of_yaml(yaml_path)
        return em

    def get_endpoint(self, name: str) -> Optional[Endpoint]:
        """Get endpoint by name."""
        return self.endpoints.get(name)

    def __len__(self) -> int:
        return len(self.endpoints)

    def __iter__(self):
        return iter(self.endpoints.values())


    @classmethod
    def getEndpoints(
        cls, endpointPath: str = None, lang: str = None, with_default: bool = True
    ):
        """
        get the endpoints for the given endpointPath

        Args:
            endpointPath(str): the path to the yaml file with the endpoint configurations
            lang(str): if lang is given filter by the given language
            with_default(bool): if True include the default endpoints
        """
        endpointPaths = YamlPath.getPaths(
            "endpoints.yaml", endpointPath, with_default=with_default
        )
        endpoints = {}
        for lEndpointPath in endpointPaths:
            em = cls.ofYaml(lEndpointPath)
            for name, endpoint in em.endpoints.items():
                selected = lang is None or endpoint.lang == lang
                if selected:
                    endpoints[name] = endpoint
                    endpoint.name = name
        return endpoints

    @staticmethod
    def getEndpointNames(endpointPath=None, lang: str = None) -> list:
        """
        Returns a list of all available endpoint names
        Args:
            endpointPath(str): the path to the yaml file with the endpoint configurations
            lang(str): if lang is given filter by the given language

        """
        endpoints = EndpointManager.getEndpoints(endpointPath, lang=lang)
        endpoint_names = list(endpoints.keys())
        return endpoint_names
