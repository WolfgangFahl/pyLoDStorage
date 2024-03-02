"""
Created on 2020-08-14

@author: wf
"""
import datetime
import time
import unittest
import warnings

from SPARQLWrapper import SPARQLExceptions

from lodstorage.lod import LOD
from lodstorage.query import Query
from lodstorage.sample import Sample
from lodstorage.sparql import SPARQL
from tests.basetest import Basetest


class TestSPARQL(Basetest):
    """Test SPARQL access e.g. Apache Jena via Wrapper"""

    def getJena(self, mode="query", debug=False, typedLiterals=False, profile=False):
        """
        get the jena endpoint for the given mode

        Args:
           mode(string): query or update
           debug(boolean): True if debug information should be output
           typedLiterals(boolean): True if INSERT DATA SPARQL commands should use typed literals
           profile(boolean): True if profile/timing information should be shown
        """
        endpoint = "http://localhost:3030/example/"
        if mode == "query":
            endpoint += "sparql"
        elif mode == "update":
            endpoint += "update"
        jena = SPARQL(
            endpoint,
            mode=mode,
            debug=debug,
            typedLiterals=typedLiterals,
            profile=profile,
        )
        return jena

    def get_wikidata_endpoint(self) -> SPARQL:
        """
        get the default wikidata query service endpoint
        """
        endpoint = "https://query.wikidata.org/sparql"
        wd = SPARQL(endpoint)
        return wd

    def testJenaQuery(self):
        """
        test Apache Jena Fuseki SPARQL endpoint with example SELECT query
        """
        jena = self.getJena()
        queryString = "SELECT * WHERE { ?s ?p ?o. }"
        results = jena.query(queryString)
        result_count = len(results)
        self.assertTrue(result_count >= 20)
        pass

    def testJenaInsert(self):
        """
        test a Jena INSERT DATA
        """
        jena = self.getJena(mode="update")
        insertCommands = [
            """
        PREFIX cr: <http://cr.bitplan.com/>
        INSERT DATA {
          cr:version cr:author "Wolfgang Fahl".
        }
        """,
            "INSERT DATA { INVALID COMMAND } ",
        ]
        for index, insertCommand in enumerate(insertCommands):
            with self.subTest(insertCommand=insertCommand):
                if index != 0:
                    warnings.simplefilter("ignore")

                result, ex = jena.insert(insertCommand)
                if index == 0:
                    if ex:
                        print(f"Exception: {ex}")
                    self.assertIsNone(ex)
                    if self.debug:
                        print(result)
                else:
                    msg = ex.args[0]
                    if self.debug:
                        print(msg)
                    self.assertTrue("QueryBadFormed" in msg)
                    # self.assertTrue("Error 400" in msg)
                    pass

    def checkErrors(self, errors, expected=0):
        """
        check the given list of errors - print any errors if there are some
        and after that assert that the length of the list of errors is zero

        Args:
            errors(list): the list of errors to check
        """
        if self.debug:
            if len(errors) > 0:
                print("ERRORS:")
                for error in errors:
                    print(error)
        self.assertEqual(expected, len(errors))

    def testDob(self):
        """
        test the DOB (date of birth) function that converts from ISO-Date to
        datetime.date
        """
        dt = Sample.dob("1926-04-21")
        self.assertEqual(1926, dt.year)
        self.assertEqual(4, dt.month)
        self.assertEqual(21, dt.day)

    def testListOfDictInsert(self):
        """
        test inserting a list of Dicts and retrieving the values again
        using a person based example
        instead of
        https://en.wikipedia.org/wiki/FOAF_(ontology)

        we use an object oriented derivate of FOAF with a focus on datatypes
        """
        listofDicts = Sample.getRoyals()
        typedLiteralModes = [True, False]
        entityType = "foafo:Person"
        primaryKey = "name"
        prefixes = "PREFIX foafo: <http://foafo.bitplan.com/foafo/0.1/>"
        for typedLiteralMode in typedLiteralModes:
            jena = self.getJena(
                mode="update", typedLiterals=typedLiteralMode, debug=self.debug
            )
            deleteString = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX foafo: <http://foafo.bitplan.com/foafo/0.1/>
            DELETE WHERE {  
              ?person a 'foafo:Person'.
              ?person ?p ?o. 
            }
            """
            jena.query(deleteString)
            errors = jena.insertListOfDicts(
                listofDicts, entityType, primaryKey, prefixes
            )
            self.checkErrors(errors)

            jena = self.getJena(mode="query", debug=self.debug)
            queryString = """
            PREFIX foafo: <http://foafo.bitplan.com/foafo/0.1/>
            SELECT ?name ?born ?numberInLine ?wikidataurl ?age ?ofAge ?lastmodified WHERE { 
                ?person a 'foafo:Person'.
                ?person foafo:Person_name ?name.
                ?person foafo:Person_born ?born.
                ?person foafo:Person_numberInLine ?numberInLine.
                ?person foafo:Person_wikidataurl ?wikidataurl.
                ?person foafo:Person_age ?age.
                ?person foafo:Person_ofAge ?ofAge.
                ?person foafo:Person_lastmodified ?lastmodified. 
            }"""
            personResults = jena.query(queryString)
            self.assertEqual(len(listofDicts), len(personResults))
            personList = jena.asListOfDicts(personResults)
            for index, person in enumerate(personList):
                if self.debug:
                    print("%d: %s" % (index, person))
            # check the correct round-trip behavior
            self.assertEqual(listofDicts, personList)

    def testControlEscape(self):
        """
        check the control-escaped version of an UTF-8 string
        """
        controls = "Α\tΩ\r\n"
        expected = "Α\\tΩ\\r\\n"
        esc = SPARQL.controlEscape(controls)
        self.assertEqual(expected, esc)

    def testSPARQLErrorMessage(self):
        """
        test error handling
        see https://stackoverflow.com/questions/63486767/how-can-i-get-the-fuseki-api-via-sparqlwrapper-to-properly-report-a-detailed-err
        """
        listOfDicts = [
            {
                "title": "“Bioinformatics of Genome Regulation and Structure\Systems Biology” – BGRS\SB-2018",
                "url": "https://thenode.biologists.com/event/11th-international-multiconference-bioinformatics-genome-regulation-structuresystems-biology-bgrssb-2018/",
            }
        ]
        entityType = "cr:Event"
        primaryKey = "title"
        prefixes = "PREFIX cr: <http://cr.bitplan.com/Event/0.1/>"
        jena = self.getJena(mode="update", typedLiterals=False, debug=self.debug)
        errors = jena.insertListOfDicts(listOfDicts, entityType, primaryKey, prefixes)
        self.checkErrors(errors, 1)
        error = errors[0]
        print(f"error is {error}")
        self.assertTrue("Lexical error" in error)

    def testEscapeStringContent(self):
        """
        test handling of double quoted strings
        """
        helpListOfDicts = [
            {
                "topic": "edit",
                "description": """Use 
the "edit" 
button to start editing - you can use 
- tab \t 
- carriage return \r 
- newline \n

as escape characters 
""",
            }
        ]
        entityType = "help:Topic"
        primaryKey = "topic"
        prefixes = "PREFIX help: <http://help.bitplan.com/help/0.0.1/>"
        jena = self.getJena(mode="update", debug=self.debug)
        errors = jena.insertListOfDicts(
            helpListOfDicts, entityType, primaryKey, prefixes, profile=self.profile
        )
        self.checkErrors(errors)
        query = """
PREFIX help: <http://help.bitplan.com/help/0.0.1/>
        SELECT ?topic ?description
WHERE {
  ?help help:Topic_topic ?topic.
  ?help help:Topic_description ?description.
}
        """
        jena = self.getJena(mode="query")
        listOfDicts = jena.queryAsListOfDicts(query)
        # check round trip equality
        self.assertEqual(helpListOfDicts, listOfDicts)

    def testIssue7(self):
        """
        test conversion of dates with timezone info
        """
        values = ["2020-01-01T00:00:00Z", "42000-01-01T00:00:00Z"]
        expected = [datetime.datetime(2020, 1, 1, 0, 0), None]
        for index, value in enumerate(values):
            dt = SPARQL.strToDatetime(value, debug=self.debug)
            self.assertEqual(expected[index], dt)

    def testListOfDictSpeed(self):
        """
        test the speed of adding data
        """
        limit = 5000
        for batchSize in [None, 1000]:
            listOfDicts = Sample.getSample(limit)
            jena = self.getJena(mode="update", profile=self.profile)
            entityType = "ex:TestRecord"
            primaryKey = "pkey"
            prefixes = "PREFIX ex: <http://example.com/>"
            startTime = time.time()
            errors = jena.insertListOfDicts(
                listOfDicts, entityType, primaryKey, prefixes, batchSize=batchSize
            )
            self.checkErrors(errors)
            elapsed = time.time() - startTime
            if self.profile:
                print(
                    "adding %d records took %5.3f s => %5.f records/s"
                    % (limit, elapsed, limit / elapsed)
                )

    def testWikdata(self):
        """
        check wikidata
        """
        # check we have local wikidata copy:
        # if getpass.getuser()=="wf":
        #    # use 2018 wikidata copy
        #    endpoint="http://jena.zeus.bitplan.com/wikidata/"
        wd = self.get_wikidata_endpoint()
        queryString = """# get a list of whisky distilleries
PREFIX wd: <http://www.wikidata.org/entity/>            
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?item ?coord 
WHERE 
{
  # instance of whisky distillery
  ?item wdt:P31 wd:Q10373548.
  # get the coordinate
  ?item wdt:P625 ?coord.
}
"""
        results = wd.query(queryString)
        self.assertTrue(238 <= len(results))

    def testIssue20And76(self):
        """
        see https://github.com/WolfgangFahl/pyLoDStorage/issues/20
        add fixNone option to SPARQL results (same functionality as in SQL)

         https://github.com/WolfgangFahl/pyLoDStorage/issues/76
        SPARQL GET method support
        """
        endpoint = "https://query.wikidata.org/sparql"
        for method in ["POST", "GET"]:
            wd = SPARQL(endpoint, method=method)
            queryString = """
        # Conference Series wikidata query
# see https://confident.dbis.rwth-aachen.de/dblpconf/wikidata
# WF 2021-01-30
SELECT ?confSeries ?short_name ?official_website
WHERE 
{
  #  scientific conference series (Q47258130) 
  ?confSeries wdt:P31 wd:Q47258130.
  OPTIONAL { 
    ?confSeries wdt:P1813 ?short_name . 
  }
  #  official website (P856) 
  OPTIONAL {
    ?confSeries wdt:P856 ?official_website
  } 
}
LIMIT 200
"""
            lod = wd.queryAsListOfDicts(queryString, fixNone=True)
            fields = LOD.getFields(lod)
            if self.debug:
                print(fields)
            for row in lod:
                for field in fields:
                    self.assertTrue(field in row)

    def testStackoverflow55961615Query(self):
        """
        see
        https://stackoverflow.com/questions/55961615/how-to-integrate-wikidata-query-in-python
        https://stackoverflow.com/a/69771615/1497139
        """
        qlod = None
        try:
            endpoint = "https://query.wikidata.org/sparql"
            wd = SPARQL(endpoint)
            queryString = """SELECT ?s ?sLabel ?item ?itemLabel ?sourceCode ?webSite ?stackexchangeTag  {
    SERVICE wikibase:mwapi {
        bd:serviceParam wikibase:api "EntitySearch".
        bd:serviceParam wikibase:endpoint "www.wikidata.org".
        bd:serviceParam mwapi:search "natural language processing".
        bd:serviceParam mwapi:language "en".
        ?item wikibase:apiOutputItem mwapi:item.
        ?num wikibase:apiOrdinal true.
    }
    ?s wdt:P279|wdt:P31 ?item .
    OPTIONAL { 
      ?s wdt:P1324 ?sourceCode.
    }
    OPTIONAL {    
      ?s wdt:P856 ?webSite.
    }
    OPTIONAL {    
      ?s wdt:P1482 ?stackexchangeTag.
    }
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }
}
ORDER BY ?itemLabel ?sLabel"""
            qlod = wd.queryAsListOfDicts(queryString, fixNone=True)
        except Exception as ex:
            print(f"{endpoint} access failed with {ex}- could not run test")

        if qlod is not None:
            query = Query(name="EntitySearch", query=queryString, lang="sparql")
            debug = self.debug
            for tablefmt in ["github", "mediawiki", "latex"]:
                qdoc = query.documentQueryResult(qlod, tablefmt=tablefmt)
                if debug:
                    print(qdoc)

    def testStackoverflow71444069(self):
        """
        https://stackoverflow.com/questions/71444069/create-csv-from-result-of-a-for-google-colab/71548650#71548650
        """
        from lodstorage.csv import CSV
        from lodstorage.sparql import SPARQL

        sparqlQuery = """SELECT ?org ?orgLabel
WHERE
{
  ?org wdt:P31 wd:Q4830453. #instance of organizations
  ?org wdt:P17 wd:Q96. #Mexico country

  SERVICE wikibase:label { bd:serviceParam wikibase:language "en"}
}"""
        sparql = SPARQL("https://query.wikidata.org/sparql")
        qlod = sparql.queryAsListOfDicts(sparqlQuery)
        csv = CSV.toCSV(qlod)
        if self.debug:
            print(csv)

    @unittest.skipIf(
        not Basetest.isUser("holzheim"),
        "Tests against local stardog instance → once confident sparql endpoint is online change to this endpoint",
    )
    def test_query_with_authentication(self):
        """tests querying an endpoint that requires authentication"""
        query = (
            """SELECT * WHERE { ?proceeding dblp:publishedInSeriesVolume "2816" .}"""
        )
        sparql = SPARQL("http://localhost:5820/dblp/query", method="POST")
        self.assertRaises(
            SPARQLExceptions.Unauthorized, sparql.queryAsListOfDicts, queryString=query
        )
        sparql.addAuthentication("admin", "admin")
        qres = sparql.queryAsListOfDicts(query)
        self.assertEqual(2, len(qres))

    def testIssue199(self):
        """
        test https://github.com/WolfgangFahl/pyLoDStorage/issues/119
        405 (Method not allowed) from endpoints for tt.genWdPropertyStatistic #
        """
        wd = self.get_wikidata_endpoint()
        sparql_query = """# Count all Q44613:monastery items
# with the given street address(P6375) https://www.wikidata.org/wiki/Property:P6375 
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?count (COUNT(?count) AS ?frequency) WHERE {{
SELECT ?item ?itemLabel (COUNT (?value) AS ?count)
WHERE
{
  # instance of monastery
  ?item wdt:P31 wd:Q44613.
  ?item rdfs:label ?itemLabel.
  FILTER (LANG(?itemLabel) = "en").
  # street address
  ?item wdt:P6375 ?value.
} GROUP BY ?item ?itemLabel

}}
GROUP BY ?count
ORDER BY DESC (?frequency)
"""
        lod = wd.queryAsListOfDicts(sparql_query)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
