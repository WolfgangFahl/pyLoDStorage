"""
Created on 2022-03-4

@author: wf
"""
import json
import unittest
from pprint import pprint
from urllib.error import HTTPError

from lodstorage.query import Endpoint, Query, QuerySyntaxHighlight
from lodstorage.sparql import SPARQL
from lodstorage.trulytabular import TrulyTabular, WikidataItem, WikidataProperty


class TestTrulyTabular(unittest.TestCase):
    """
    test Truly tabular analysis
    """

    def setUp(self):
        self.debug = False
        qleverEndpoint = Endpoint()
        qleverEndpoint.name = "qlever-wikidata"
        qleverEndpoint.method = "POST"
        qleverEndpoint.database = "qlever"
        qleverEndpoint.endpoint = "http://qlever-api.wikidata.dbis.rwth-aachen.de"
        self.endpointConfs = {qleverEndpoint, Endpoint.getDefault()}
        pass

    def handleServiceUnavailable(self, ex, endpointConf):
        """
        handle service unavailable

        Args:
            ex(Exception): the exception to handle
            endpointConf(Endpoint): the endpoint for which there is a problem
        """
        self.handleEndpointErrors(
            ex, ex, endpointConf, endpointConf, "503", "Service Unavailable"
        )

    def handleEndpointErrors(
        self, ex, endpointConf, status_code: str, status_text: str
    ):
        """
         handle Endpoint Errors

        Args:
            ex(Exception): the exception to handle
            endpointConf(Endpoint): the endpoint for which there is a problem
            status_code(str): the status code to filter
            status_text(str): the description of the status code
        """
        if status_code in str(ex):
            print(
                f"{endpointConf.name} at {endpointConf.endpoint} returns {status_code} ({status_text})",
                flush=True,
            )
        else:
            raise (ex)

    def tearDown(self):
        pass

    def testGetFirst(self):
        """
        test the get First helper function
        """
        tt = TrulyTabular("Q2020153")
        testcases = [
            {"qlod": [{"name": "firstname"}], "expected": "firstname"},
            {"qlod": [], "expected": None},
            {
                "qlod": [{"name": "firstname"}, {"name": "second name"}],
                "expected": None,
            },
        ]
        for testcase in testcases:
            qLod = testcase["qlod"]
            expected = testcase["expected"]
            try:
                value = tt.sparql.getFirst(qLod, "name")
                self.assertEqual(expected, value)
            except Exception as ex:
                if self.debug:
                    print(str(ex))
                self.assertIsNone(expected)

    def documentQuery(self, tt, query, show=True, formats=["mediawiki"]):
        """
        document the given query for the given TrueTabular instance
        """
        qlod = tt.sparql.queryAsListOfDicts(query.query)
        for tablefmt in formats:
            tryItUrl = "https://query.wikidata.org/"
            doc = query.documentQueryResult(
                qlod, tablefmt=tablefmt, tryItUrl=tryItUrl, floatfmt=".0f"
            )
            docstr = doc.asText()
            if show:
                print(docstr)

    def testGetPropertiesByLabel(self):
        """
        try getting properties by label
        """
        debug = self.debug
        # debug=True
        propertyLabels = ["title", "country", "location"]
        for endpointConf in self.endpointConfs:
            try:
                tt = TrulyTabular(
                    "Q2020153", propertyLabels=propertyLabels, endpointConf=endpointConf
                )
                if debug:
                    print(tt.properties)
                for prop in propertyLabels:
                    self.assertTrue(prop in tt.properties)
            except (Exception, HTTPError) as ex:
                self.handleServiceUnavailable(ex, endpointConf)
                pass

    def testGetPropertiesById(self):
        """
        try getting properties by label
        """
        debug = self.debug
        # debug=True
        propertyIds = ["P1800"]
        expected = ["Wikimedia database name"]
        for endpointConf in self.endpointConfs:
            try:
                sparql = SPARQL(endpointConf.endpoint, method=endpointConf.method)
                propList = WikidataProperty.getPropertiesByIds(
                    sparql, propertyIds, lang="en"
                )
                for i, prop in enumerate(propList):
                    if debug:
                        print(f"{endpointConf.name} {i}:{prop}")
                    self.assertEqual(prop, expected[i])
            except (Exception, HTTPError) as ex:
                self.handleServiceUnavailable(ex, endpointConf)
                pass

    def testGetItemsByLabel(self):
        """
        try getting items by label
        """
        debug = self.debug
        debug = True
        qLabels = [
            "academic conference",
            "scientific conference series",
            "whisky distillery",
            "human",
        ]
        for endpointConf in self.endpointConfs:
            try:
                sparql = SPARQL(endpointConf.endpoint, method=endpointConf.method)
                items = {}
                for qLabel in qLabels:
                    items4Label = WikidataItem.getItemsByLabel(
                        sparql, qLabel, debug=debug
                    )
                    count = len(items4Label)
                    if debug:
                        print(f"found {count} items for label {qLabel}")
                    self.assertTrue(count > 0)
                    for i, item in enumerate(items4Label):
                        if debug:
                            print(f"{endpointConf.name} {i+1}:{item}")
                    items[qLabel] = items4Label[0]
                for qLabel in qLabels:
                    self.assertTrue(qLabel in items)
            except (Exception, HTTPError) as ex:
                self.handleServiceUnavailable(ex, endpointConf)
                pass

    def testTrulyTabularTables(self):
        """
        test Truly Tabular for different tabular queries
        """
        debug = self.debug
        # debug=True
        show = False
        showStats = ["mediawiki", "github", "latex"]
        tables = [
            {
                "name": "computer scientist",
                "title": "humans with the occupation computer scientist",
                "qid": "Q5",  # human
                "where": "?item wdt:P106 wd:Q82594.",  # computer scientist only
                "propertyLabels": [
                    "sex or gender",
                    "date of birth",
                    "place of birth",
                    "field of work",
                    "occupation",
                    "ORCID iD",
                    "GND ID",
                    "DBLP author ID",
                    "Google Scholar author ID",
                    "VIAF ID",
                ],
                "expected": 10,
            },
            {
                "name": "academic conferences",
                "title": "academic conferences",
                "qid": "Q2020153",  # academic conference
                "propertyLabels": [
                    "title",
                    "country",
                    "location",
                    "short name",
                    "start time",
                    "end time",
                    "part of the series",
                    "official website",
                    "described at URL",
                    "WikiCFP event ID",
                    "GND ID",
                    "VIAF ID",
                    "main subject",
                    "language used",
                    "is proceedings from",
                ],
                "expected": 7500,
            },
            {
                "name": "scientific conferences series",
                "title": "scientific conference series",
                "qid": "Q47258130",  # scientific conference series
                "propertyLabels": [
                    "title",
                    "short name",
                    "inception",
                    "official website",
                    "DBLP venue ID",
                    "GND ID",
                    "Microsoft Academic ID",
                    "Freebase ID",
                    "WikiCFP conference series ID",
                    "Publons journals/conferences ID",
                    "ACM conference ID",
                ],
                "expected": 4200,
            },
            {
                "name": "whisky distilleries",
                "title": "whisky distilleries",
                "qid": "Q10373548",  # whisky distillery
                "propertyLabels": [
                    "inception",
                    "official website",
                    "owned by",
                    "country",
                    "headquarters location",
                    "Whiskybase distillery ID",
                ],
                "expected": 200,
            },
        ]
        errors = 0
        for table in tables[3:]:
            # academic conference
            where = None
            if "where" in table:
                where = table["where"]
            tt = TrulyTabular(
                table["qid"], table["propertyLabels"], where=where, debug=debug
            )
            if "is proceedings from" in tt.properties:
                tt.properties["is proceedings from"].reverse = True
            count, query = tt.count()
            if debug:
                print(count)
            self.assertTrue(count > table["expected"])
            stats = tt.getPropertyStatistics()
            # sort descending by total percentage
            stats = sorted(stats, key=lambda row: row["total%"], reverse=True)
            for tablefmt in showStats:
                query = Query(name=table["name"], title=table["title"], query="")
                doc = query.documentQueryResult(
                    stats, tablefmt=tablefmt, withSourceCode=False
                )
                if debug:
                    print(doc)
            if show:
                for wdProperty in tt.properties.values():
                    for asFrequency in [True, False]:
                        query = tt.noneTabularQuery(wdProperty, asFrequency=asFrequency)
                        try:
                            self.documentQuery(tt, query)
                        except Exception as ex:
                            print(f"query for {wdProperty} failed\n{str(ex)}")
                            errors += 1
                self.assertEqual(0, errors)

    def testMostFrequentProperties(self):
        """
        test getting the most frequent properties for some Wikidata Item types
        """
        # show=True
        show = False
        debug = self.debug
        # debug=True
        for endpointConf in self.endpointConfs:
            for qid in ["Q6256"]:
                try:
                    tt = TrulyTabular(qid, debug=debug, endpointConf=endpointConf)
                    for minCount in [0, 100]:
                        query = tt.mostFrequentPropertiesQuery(minCount=minCount)
                        if debug:
                            print(query.query)
                        self.documentQuery(tt, query, formats=["github"], show=show)
                except (Exception, HTTPError) as ex:
                    self.handleServiceUnavailable(ex, endpointConf)
                    pass

    def testSyntaxHighlighting(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/81
        """
        debug = self.debug
        # debug=True
        qid = "Q6256"  # country
        tt = TrulyTabular(qid, debug=debug)
        query = tt.mostFrequentPropertiesQuery()
        sh = QuerySyntaxHighlight(query, "html")
        html = sh.highlight()
        if debug:
            print(html)
        self.assertTrue('<span class="k">SELECT</span>' in html)
        pass

    def testCount(self):
        """
        test the count function of truly tabular
        """
        debug = self.debug
        #debug = True
        qid = "Q55488"  # railway stations
        for endpointConf in self.endpointConfs:
            try:
                tt = TrulyTabular(qid, endpointConf=endpointConf, debug=debug)
                count, query = tt.count()
                if debug:
                    print(query)
                    print(f"count of railway stations is {count}")
                self.assertTrue(qid in query)
                self.assertTrue(count >= 106195)
                self.assertTrue(tt.error is None)
            except (Exception, HTTPError) as ex:
                self.handleServiceUnavailable(ex, endpointConf)

    def testGenWdPropertyStatistic(self):
        """
        test generating a Wikidata property statistics row
        """
        qid = "Q44613"  # monastery
        debug = self.debug
        #debug = True
        for endpointConf in self.endpointConfs:
            try:
                tt = TrulyTabular(qid, debug=debug)
                for pid in ["P571", "P6375"]:
                    wdProperty = WikidataProperty.from_id(pid, sparql=tt.sparql)
                    #
                    itemCount, _itemCountQuery = tt.count()
                    statsRow = tt.genWdPropertyStatistic(wdProperty, itemCount)
                    if debug:
                        print(json.dumps(statsRow, indent=2))
            except (Exception, HTTPError) as ex:
                self.handleEndpointErrors(ex, endpointConf, "405", "Method not allowed")

    def testGenerateSparqlQuery(self):
        """
        test Generating a SPARQL query
        """
        configs = [
            {
                "naive": True,
                "qid": "Q2020153",  # academic conference
                "subclassPredicate": "wdt:P31",
                "propertyIdMap": {
                    "P1813": ["label"],
                    "P17": ["label"],
                    "P1476": ["label"],
                },
                "expected": [],
            },
            {
                "naive": False,
                "qid": "Q2020153",  # academic conference
                "subclassPredicate": "wdt:P31",
                "propertyIdMap": {
                    "P1813": ["sample"],
                    "P17": ["sample"],
                    "P1476": ["sample"],
                },
                "expected": ["GROUP BY", "SAMPLE"],
            },
            {
                "naive": False,
                "qid": "Q2020153",  # academic conference
                "subclassPredicate": "wdt:P31",
                "propertyIdMap": {
                    "P1813": ["count", "list"],
                    "P17": ["sample", "ignore"],
                    "P1476": ["count", "list"],
                },
                "expected": [
                    "COUNT (DISTINCT",
                    "GROUP BY",
                    "GROUP_CONCAT (DISTINCT",
                    "HAVING",
                ],
            },
            {
                "naive": False,
                "qid": "Q1667921",  # novel series
                "subclassPredicate": "wdt:P31",
                "propertyIdMap": {
                    "P50": ["sample", "ignore"],  # author
                    "P136": ["sample", "ignore"],  # genre
                    "P1476": ["sample", "ignore"],  # title
                },
                "expected": ["GROUP BY", "HAVING", "COUNT", "<=1"],
            },
            {
                "naive": False,
                "qid": "Q1667921",  # novel series
                "subclassPredicate": "wdt:P31",
                "propertyIdMap": {
                    "P50": ["sample", "ignore", "label"],  # author
                    "P136": ["sample", "ignore", "label"],  # genre
                    "P1476": ["sample", "ignore"],  # title
                },
                "expected": ["GROUP BY", "HAVING", "COUNT", "<=1"],
            },
            {
                "naive": False,
                "subclassPredicate": "wdt:P279*/wdt:P31*",
                "qid": "Q8063",  # rock
                "propertyIdMap": {
                    "P18": ["sample"],  # image
                },
                "expected": ["P279"],
            },
        ]
        debug = self.debug
        #debug = True
        # loop over different test configurations
        for i, config in enumerate(configs):
            # get the test configuration
            qid = config["qid"]
            naive = config["naive"]
            propertyIdMap = config["propertyIdMap"]
            subclassPredicate = config["subclassPredicate"]
            expectedList = config["expected"]

            # create a truly tabular analysis
            tt = TrulyTabular(
                qid,
                propertyIds=list(propertyIdMap.keys()),
                subclassPredicate=subclassPredicate,
            )
            varname = tt.item.itemVarname
            # generate a SPARQL Query
            sparqlQuery = tt.generateSparqlQuery(genMap=propertyIdMap, naive=naive)
            if debug:
                print(f"config {i}:")
                pprint(config)
                print(f"{sparqlQuery}")
            # all queries should have basic graph patterns for the subclass
            self.assertTrue(f"?{varname} {subclassPredicate} wd:{qid}." in sparqlQuery)
            # and for the properties
            for pid in propertyIdMap.keys():
                self.assertTrue(f"?{varname} wdt:{pid}" in sparqlQuery)
            for expected in expectedList:
                self.assertTrue(
                    expected in sparqlQuery, f"config {i}:{expected} missing"
                )


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
