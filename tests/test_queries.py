"""
Created on 2021-01-29

@author: wf
"""

import copy
import io
import json
import os
import traceback
from argparse import Namespace
from contextlib import redirect_stdout

import tests.test_sqlite3
from lodstorage.prefix_config import PrefixConfigs
from lodstorage.prefixes import Prefixes
from lodstorage.query import (
    EndpointManager,
    Format,
    Query,
    QueryManager,
    QueryResultDocumentation,
    ValueFormatter,
    ValueFormatters,
)
from lodstorage.querymain import QueryMain
from lodstorage.querymain import main as queryMain
from lodstorage.sparql import SPARQL
from tests.action_stats import ActionStats
from tests.endpoint_test import EndpointTest


class TestQueries(EndpointTest):
    """
    Test query handling
    """

    def setUp(self, debug=False, profile=True):
        EndpointTest.setUp(self, debug=debug, profile=profile)

    def testSQLQueries(self):
        """
        see https://github.com/WolfgangFahl/pyLoDStorage/issues/19
        """
        show = self.debug
        qm = QueryManager(lang="sql", debug=False)
        self.assertTrue(len(qm.queriesByName) >= 2)
        sqlDB = tests.test_sqlite3.TestSQLDB.getSampleTableDB()
        # print(sqlDB.getTableDict())
        for _name, query in qm.queriesByName.items():
            listOfDicts = sqlDB.query(query.query)
            resultDoc = query.documentQueryResult(listOfDicts)
            if show:
                print(resultDoc)
        pass

    def runQuery(self, query, show: bool = False):
        if show:
            print(f"{query.name}:{query}")
        endpoint = SPARQL(query.endpoint)
        try:
            if query.params.has_params:
                query.apply_default_params()
                pass
            qlod = endpoint.queryAsListOfDicts(
                query.query, param_dict=query.params.params_dict
            )
            for tablefmt in ["mediawiki", "github", "latex"]:
                doc = query.documentQueryResult(qlod, tablefmt=tablefmt, floatfmt=".0f")
                docstr = doc.asText()
                if show:
                    print(docstr)

        except Exception as ex:
            print(f"{query.title} at {query.endpoint} failed: {ex}")
            print(traceback.format_exc())

    def testQueryWithParams(self):
        """
        test SPARQL Query with parameters
        """
        show = self.debug
        # show = True
        qm = QueryManager(
            queriesPath=self.wikidata_queries_path,
            with_default=False,
            lang="sparql",
            debug=False,
        )
        query = qm.queriesByName["WikidataItemsNearItem"]
        query.endpoint = "https://query.wikidata.org/sparql"
        self.assertIsInstance(query, Query)
        self.runQuery(query, show=show)
        pass

    def testSparqlQueries(self):
        """
        test SPARQL queries
        """
        show = self.debug
        # show = True
        qm = QueryManager(lang="sparql", debug=False)
        for name, query in qm.queriesByName.items():
            if name in ["US President Nicknames"]:
                self.runQuery(query, show=show)

    def testUnicode2LatexWorkaround(self):
        """
        test the uniCode2Latex conversion workaround
        """
        debug = self.debug
        for code in range(8320, 8330):
            uc = chr(code)
            latex = QueryResultDocumentation.uniCode2Latex(uc)
            if debug:
                print(f"{uc}→{latex}")
            # self.assertTrue(latex.startswith("$_"))
        unicode = "À votre santé!"
        latex = QueryResultDocumentation.uniCode2Latex(unicode, withConvert=True)
        if debug:
            print(f"{unicode}→{latex}")
        self.assertEqual("\\`A votre sant\\'e!", latex)

    def captureQueryMain(self, args):
        """
        run queryMain and capture stdout

        Args:
            args(list): command line arguments

        Returns:
            str: the stdout content of the command line call
        """
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            queryMain(args)
            result = stdout.getvalue()
        return result

    def testQueryCommandLine(self):
        """
        test the sparql query command line
        """
        debug = self.debug
        # debug=True
        for testArg in [
            {"format": "csv", "expected": '''Theodore Roosevelt","Teddy"'''},
            {"format": "xml", "expected": """<?xml version="1.0" ?>"""},
            {"format": "latex", "expected": """Theodore Roosevelt     & Teddy"""},
            {
                "format": "mediawiki",
                "expected": """| [https://www.wikidata.org/wiki/Q33866 Q33866] || Theodore Roosevelt     || Teddy""",
            },
            {
                "format": "github",
                "expected": """| [Q33866](https://www.wikidata.org/wiki/Q33866) | Theodore Roosevelt     | Teddy""",
            },
        ]:
            resultFormat = testArg["format"]
            expected = testArg["expected"]
            args = [
                "-d",
                "-qn",
                "US President Nicknames",
                "-l",
                "sparql",
                "-f",
                resultFormat,
            ]
            result = self.captureQueryMain(args)
            if debug:
                print(f"{resultFormat}:{result}")
            self.assertTrue(expected in result, f"{expected}({resultFormat})")

    def test_add_endpoint_prefixes(self):
        """
        Test Query.add_endpoint_prefixes() merges endpoint prefixes without duplicates.
        https://github.com/WolfgangFahl/pyLoDStorage/issues/140 (related prefix handling)
        """
        debug = self.debug
        # debug=True
        endpoints = EndpointManager.getEndpoints(lang="sparql")
        wikidata_ep = endpoints["wikidata"]
        prefix_configs = PrefixConfigs.get_instance()

        qm = QueryManager(lang="sparql", debug=False)
        cities_query = qm.queriesByName["cities"]  # Has rdfs, wd, wdt

        original_query = cities_query.query
        original_prefixes = Prefixes.extract_prefixes(original_query)
        self.assertEqual(3, len(original_prefixes))  # rdfs, wd, wdt

        # Add endpoint prefixes (Wikidata full set → overlaps)
        cities_query.add_endpoint_prefixes(wikidata_ep, prefix_configs)

        # Debug: Always show merged state (before asserts → visible on fail)
        merged_query = cities_query.query
        prefix_dict = Prefixes.extract_prefixes(merged_query)
        prefix_lines = [
            line
            for line in merged_query.splitlines()
            if line.strip().startswith("PREFIX")
        ]
        if debug:
            print("Merged query prefixes:")
            print("\n".join(prefix_lines))
            print(f"Unique prefixes: {len(prefix_dict)}")
            print(f"self.prefixes len: {len(cities_query.prefixes)}")
            print("self.prefixes sample:", cities_query.prefixes[:3])

        # Verify: Unique prefixes (no dups like 'rdfs')
        self.assertEqual(len(prefix_dict), len(prefix_lines))  # 1:1 → no dup lines

        # Specific: 'rdfs', 'wd', 'wdt' appear exactly once
        for prefix in ["rdfs", "wd", "wdt"]:
            count = sum(1 for line in prefix_lines if f"{prefix}: " in line)
            self.assertEqual(1, count)

        # Full Wikidata set merged (many more)
        self.assertGreater(len(prefix_dict), 10)

        # Query body preserved
        self.assertIn("SELECT ?city_id ?name", merged_query)

        # self.prefixes: Unique PREFIX lines list (len + sorted names match)
        self.assertEqual(len(prefix_lines), len(cities_query.prefixes))  # same count

        def get_prefix_names(lines):
            return sorted(
                [line.split(":")[0].strip("PREFIX ").strip() for line in lines]
            )

        self.assertEqual(
            get_prefix_names(prefix_lines), get_prefix_names(cities_query.prefixes)
        )  # same set (order-insensitive)
        used_prefixes = {line.split(":")[0].strip() for line in cities_query.prefixes}
        self.assertEqual(len(used_prefixes), len(cities_query.prefixes))  # no dups

    def testQueryEndpoints(self):
        """
        tests the sparql endpoint commandline endpoint selection
        """
        testArgs = [
            {
                "en": "wikidata",
            },
            # {"en":"qlever-wikidata",},
            # workaround https://github.com/ad-freiburg/qlever/issues/631
            # {"en":"qlever-wikidata-proxy",},
        ]
        showServerDown = True
        showResult = self.debug
        #showResult = True
        for testArg in testArgs:
            endpointName = testArg.get("en")
            args = [
                "-d",
                "-qn",
                "cities",
                "--params",
                "country=Q32",
                "-p",
                "-l",
                "sparql",
                "-f",
                "json",
                "-en",
                endpointName,
                "-raw",
            ]
            result = self.captureQueryMain(args)

            if not "503 Service Unavailable" in result and not "Error 403" in result:
                if showResult:
                    print(result)
                self.assertTrue(
                    "Dudelange" in result,
                    f"{endpointName}: Dudelange not in query result",
                )
            elif showServerDown:
                print(f"{endpointName} returns 503 Service Unavailable")

    def testIssue69showEndpoints(self):
        """
        test the listEndpoints option

        https://github.com/WolfgangFahl/pyLoDStorage/issues/69
        """
        debug = self.debug
        # debug=True
        expected = {"sparql": "wikidata"}
        for option in ["-le", "--listEndpoints"]:
            for lang in ["sparql", "sql"]:
                args = [option, "-l", lang]
                result = self.captureQueryMain(args)
                if debug:
                    print(result)
                if lang in expected:
                    self.assertTrue(expected[lang] in result)

    def testIssue70showQuery(self):
        """
        test the showQuery option

        https://github.com/WolfgangFahl/pyLoDStorage/issues/70
        """
        for option in ["-sq", "--showQuery"]:
            args = ["-qn", "10 Largest Cities Of The World", option, "-l", "sparql"]
            result = self.captureQueryMain(args)
            if self.debug:
                print(result)
            self.assertTrue("SELECT DISTINCT ?city ?cityLabel" in result)

    def testIssue73Formatting(self):
        """
        test formatting
        """
        debug = self.debug
        # debug=True
        qlod = [
            {"wikidata": "http://www.wikidata.org/entity/Q1353", "label": "Delhi"},
            {"wikidata": "Q2", "label": "Earth"},
            {
                "wikidata": "https://www.wikidata.org/wiki/Property:P31",
                "label": "instanceof",
            },
        ]
        vf = ValueFormatter(
            regexps=[
                r"(?P<value>(Q|Property:P)[0-9]+)",
                r"http(s)?://.*/(?P<value>(Q|Property:P)[0-9]+)",
            ],
            format="https://www.wikidata.org/wiki/{value}",
        )
        key = "wikidata"
        for tablefmt in [Format.mediawiki, Format.github, Format.latex]:
            lod = copy.deepcopy(qlod)
            for record in lod:
                vf.applyFormat(record, key, tablefmt.value)
                if debug:
                    print(tablefmt)
                    print(record)
            if tablefmt is Format.mediawiki:
                self.assertEqual(
                    "[https://www.wikidata.org/wiki/Q1353 Q1353]", lod[0]["wikidata"]
                )
                self.assertEqual(
                    "[https://www.wikidata.org/wiki/Q2 Q2]", lod[1]["wikidata"]
                )
                self.assertEqual(
                    "[https://www.wikidata.org/wiki/Property:P31 Property:P31]",
                    lod[2]["wikidata"],
                )

    def testIssue61(self):
        """
        tests different query path

        see https://github.com/WolfgangFahl/pyLoDStorage/issues/61
        """
        queriesPath = f"{os.path.dirname(__file__)}/../sampledata/scholia.yaml"
        args = ["-qp", f"{queriesPath}", "-l", "sparql", "--list"]
        result = self.captureQueryMain(args)
        debug = self.debug
        if debug:
            print(result)
        self.assertTrue("WorksAndAuthor" in result)

    def testIssue73ReadFormats(self):
        """
        test reading the valueFormatters
        """
        vfs = ValueFormatters.of_yaml()
        self.assertTrue("wikidata" in vfs.formatters)

    def testIssue89(self):
        """
        test fix TypeError('Object of type datetime is not JSON serializable') #89
        """
        queriesPath = self.wikidata_queries_path
        args = [
            "-qp",
            f"{queriesPath}",
            "-l" "sparql",
            "-qn",
            "MachadoDeAssis",
            "-f",
            "json",
        ]
        result = self.captureQueryMain(args)
        debug = self.debug
        if debug:
            print(result)
        self.assertTrue("1839-06-21" in result)

    def testIssue111(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/111
        add basicauth support for endpoints
        """
        debug = self.debug
        # debug = True
        if not self.inPublicCI():
            endpoints = EndpointManager.getEndpoints(lang="sparql")
            # for endpoint in endpoints:
            #    print(endpoint)
            # queriesPath=f"{os.path.dirname(__file__)}/../sampledata/dblp.yaml"
            for endpoint_name in ["qlever-dblp", "dblp"]:
                self.assertTrue(endpoint_name in endpoints)
                endpoint = endpoints[endpoint_name]
                if endpoint_name == "dblp":
                    for attrname in "auth", "user", "passwd":
                        self.assertTrue(hasattr(endpoint, attrname))
                args = [
                    # "-qp", f"{queriesPath}",
                    "-l" "sparql",
                    "-en",
                    f"{endpoint_name}",
                    "-qn",
                    "propertyHistogramm",
                    "-f",
                    "json",
                    "-sq",
                ]
                result = self.captureQueryMain(args)
                debug = self.debug
                debug = True
                if debug:
                    print(result)

    def testIssue115Limit(self):
        """
        test the limit argument
        """
        limit = 5
        args_list = [
            [
                "-qn",
                "10 Largest Cities Of The World",
                "-l",
                "sparql",
                "--limit",
                f"{limit}",
            ],
            ["-qn", "US President Nicknames", "-l", "sparql", "--limit", f"{limit}"],
        ]
        debug = self.debug
        debug = True
        for args in args_list:
            json_str = self.captureQueryMain(args)
            json_data = json.loads(json_str)
            if debug:
                print(json.dumps(json_data, indent=2,default=str))
                print(len(json_data))
            self.assertEqual(limit, len(json_data))

    def test_issue130_rate_limit_support(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/130
        """
        debug = self.debug
        debug = True
        endpoints = EndpointManager.getEndpoints(lang="sparql")
        for ep_name, ep in endpoints.items():
            if ep.calls_per_minute is not None:
                if debug:
                    print(f"{ep_name}: {ep.calls_per_minute} calls per min")
                self.assertTrue(ep.calls_per_minute > 1 and ep.calls_per_minute <= 60)

    def test_issue140_prefixes_for_tryit(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/140
        fix PREFIXES for tryit button
        """
        qm = QueryManager(lang="sparql", debug=False)
        query = qm.queriesByName["US President Nicknames"]
        baseurl = "https://query.wikidata.org/"
        prefixes = Prefixes.getPrefixes(["wdt", "wd", "rdfs"])
        prefixes_list = prefixes.split("\n")
        query.prefixes = prefixes_list
        tryit = query.getTryItUrl(baseurl=baseurl)
        debug = self.debug
        debug = True
        if debug:
            print(prefixes)
            print(tryit)
        pass

    def testCommandLineUsage(self):
        """
        test the command line usage
        """
        args = ["-h"]
        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                queryMain(args)
            self.fail("system exit expected")
        except SystemExit:
            pass
        debug = self.debug
        # debug=True
        if debug:
            print(stdout.getvalue())
        self.assertTrue("--queryName" in stdout.getvalue())

    def testQueryDocumentation(self):
        """
        test QueryDocumentation
        """
        show = self.debug
        # show=True
        queries = [
            {
                "endpoint": "https://query.wikidata.org/sparql",
                "prefixes": [],
                "lang": "sparql",
                "name": "Nicknames",
                "description": "https://stackoverflow.com/questions/70206791/sparql-i-have-individual-with-multiple-values-for-single-object-property-how",
                "title": "Nick names of US Presidents",
                "query": """SELECT ?item ?itemLabel (GROUP_CONCAT(DISTINCT ?nickName; SEPARATOR=",") as ?nickNames)
WHERE
{
  # president
  ?item wdt:P39 wd:Q11696.
  ?item wdt:P1449 ?nickName
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} GROUP BY ?item ?itemLabel""",
            },
            {
                "endpoint": "https://query.wikidata.org/sparql",
                "prefixes": [
                    "http://www.wikidata.org/entity/",
                    "http://commons.wikimedia.org/wiki/Special:FilePath/",
                ],
                "lang": "sparql",
                "name": "CAS15",
                "title": "15 Random substances with CAS number",
                "description": "Wikidata SPARQL query showing the 15 random chemical substances with their CAS Number",
                "query": """# List of 15 random chemical components with CAS-Number, formula and structure
# see also https://github.com/WolfgangFahl/pyLoDStorage/issues/46
# WF 2021-08-23
SELECT ?substance ?substanceLabel ?formula ?structure ?CAS
WHERE {
  ?substance wdt:P31 wd:Q11173.
  ?substance wdt:P231 ?CAS.
  ?substance wdt:P274 ?formula.
  ?substance wdt:P117  ?structure.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
LIMIT 15
""",
            },
            {
                "endpoint": "https://query.wikidata.org/sparql",
                "prefixes": ["http://www.wikidata.org/entity/"],
                "lang": "sparql",
                "name": "CityTop10",
                "title": "Ten largest cities of the world",
                "description": "Wikidata SPARQL query showing the 10 most populated cities of the world using the million city class Q1637706 for selection",
                "query": """# Ten Largest cities of the world
# WF 2021-08-23
# see also http://wiki.bitplan.com/index.php/PyLoDStorage#Examples
# see also https://github.com/WolfgangFahl/pyLoDStorage/issues/46
SELECT DISTINCT ?city ?cityLabel ?population ?country ?countryLabel
WHERE {
  VALUES ?cityClass { wd:Q1637706}.
  ?city wdt:P31 ?cityClass .
  ?city wdt:P1082 ?population .
  ?city wdt:P17 ?country .
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
  }
}
ORDER BY DESC(?population)
LIMIT 10""",
            },
            {
                "endpoint": "https://sophox.org/sparql",
                "lang": "sparql",
                "prefixes": [],
                "query": """# count osm place type instances
# WF 2021-08-23
# see also http://wiki.bitplan.com/index.php/PyLoDStorage#Examples
# see also https://github.com/WolfgangFahl/pyLoDStorage/issues/46
SELECT (count(?instance) as ?count) ?placeType ?placeTypeLabel
WHERE {
  VALUES ?placeType {
    "city"
    "town"
    "village"
  }
  ?instance osmt:place ?placeType
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
GROUP BY ?placeType ?placeTypeLabel
ORDER BY ?count""",
                "name": "OSM place types",
                "title": "count OpenStreetMap place type instances",
                "description": """This SPARQL query
determines the number of instances available in the OpenStreetMap for the placeTypes city,town and village
""",
            },
        ]
        for queryMap in queries:
            endpointUrl = queryMap.pop("endpoint")
            endpoint = SPARQL(endpointUrl)
            query = Query(**queryMap)
            showYaml = False
            if showYaml:
                yamlMarkup = query.asYaml()
                print(yamlMarkup)
            try:
                qlod = endpoint.queryAsListOfDicts(query.query)
                for tablefmt in ["mediawiki", "github", "latex"]:
                    doc = query.documentQueryResult(
                        qlod, tablefmt=tablefmt, floatfmt=".0f"
                    )
                    docstr = doc.asText()
                    if show:
                        print(docstr)

            except Exception as ex:
                print(f"{query.title} at {endpointUrl} failed: {ex}")


class TestEndpoints(EndpointTest):
    """
    tests Endpoint
    """

    def testEndpoints(self):
        """
        tests getting and rawQuerying
        Endpoints: checks raw access first, then proper API
        """
        debug = self.debug
        debug = True

        qm = QueryManager(lang="sparql", debug=False)
        query_names = ["FirstTriple", "CountAllTriples"]

        # Initialize helper class
        stats = ActionStats()

        for i, (name, endpoint) in enumerate(self.yieldSampleEndpoints()):
            if debug:
                print(f"--- {i}:{name} ---")

            # Setup for Raw Query
            cpm = getattr(endpoint, "calls_per_minute", 60)
            query_main = QueryMain(Namespace(debug=debug, calls_per_minute=cpm))

            for query_name in query_names:
                query = qm.queriesByName[query_name]

                # 1. Raw Query (Connectivity Check)
                if debug:
                    print(f"[{name}] {query_name} (Raw)...")
                # We don't count rawQuery in stats, it acts as a gatekeeper
                raw_res = query_main.rawQuery(
                    endpoint, query.query, "json", mimeType=None
                )

                # Only proceed to "Proper" if Raw succeeded
                if raw_res:
                    # 2. Proper API (List of Dicts)
                    if debug:
                        print(f"[{name}] {query_name} (Proper)...")
                    try:
                        sparql = SPARQL(endpoint.endpoint, method=endpoint.method)
                        qlod = sparql.queryAsListOfDicts(query.query)

                        # Determine success based on if we got a list back
                        success = isinstance(qlod, list)
                        stats.add(success)

                        if debug:
                            # Use stats.state for consistent logging
                            msg = (
                                f"Rows: {len(qlod)}" if success else "No list returned"
                            )
                            print(f"  {stats.state(msg, 'Failed to retrieve list')}")
                            if success and qlod:
                                print(qlod[0])

                        # 3. Compare Counts (Specific Logic)
                        # We use getattr defaults instead of hasattr
                        mtriples = getattr(endpoint, "mtriples", 0)

                        if (
                            query_name == "CountAllTriples"
                            and success
                            and qlod
                            and mtriples > 0
                        ):
                            count = int(qlod[0].get("count", 0))
                            # Logic: Verify actual count meets the expected million-triple threshold
                            # $Count > mtriples \times 10^6$
                            expected = mtriples * 1000000

                            print(f"  Config mTriples: {mtriples} M ({expected:,.0f})")
                            print(f"  Actual Count:    {count:,.0f}")

                            if count < expected:
                                print(
                                    f"  ⚠️ Warning: Actual count is lower than expected config!"
                                )
                            else:
                                print(f"  ✅ Count verification passed.")

                    except Exception as ex:
                        stats.add(False)
                        print(f"  {stats.state('', str(ex))}")
                else:
                    # If raw failed, the proper attempt implicitly failed availability check
                    stats.add(False)
                    print(
                        f"  {stats.state('', 'Raw query failed, skipping proper API')}"
                    )

        if debug:
            print(f"\nSummary: {stats}")

        # Assert acceptable success ratio
        self.assertTrue(stats.ratio > 0.5)

    def test_availability_of_endpoints(self):
        """
        Test the availability of all SPARQL endpoints using the test_query method.
        """
        debug = self.debug
        debug = True

        stats = ActionStats()

        for i, (name, endpoint) in enumerate(self.yieldSampleEndpoints()):
            if debug:
                print(f"Testing endpoint {i+1}: {name}")

            sparql = SPARQL(endpoint.endpoint)  # Assuming SPARQL class is available
            sparql.sparql.setTimeout(5.0)

            exception = sparql.test_query()
            stats.add(exception is None)

            if debug:
                msg = f"Endpoint {name}{stats.state('', str(exception))}"
                print(msg)

        if debug:
            print(stats)

        # Assert that success rate is strictly greater than 50%
        # logic: $ratio > 0.5$
        self.assertTrue(stats.ratio > 0.5)
