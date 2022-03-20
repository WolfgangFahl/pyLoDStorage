'''
Created on 2021-01-29

@author: wf
'''
import unittest
import copy
import io
import os

from contextlib import redirect_stdout
from lodstorage.query import QueryManager, Query, QueryResultDocumentation, EndpointManager, ValueFormatter, Format
from lodstorage.querymain import main as queryMain
from lodstorage.querymain import QueryMain
from lodstorage.sparql import SPARQL
import tests.testSqlite3
from tests.basetest import Basetest

class TestQueries(Basetest):
    '''
    Test query handling
    '''

    def testSQLQueries(self):
        '''
        see https://github.com/WolfgangFahl/pyLoDStorage/issues/19
        '''
        show=self.debug
        qm=QueryManager(lang='sql',debug=False)
        self.assertEqual(2,len(qm.queriesByName)) 
        sqlDB=tests.testSqlite3.TestSQLDB.getSampleTableDB()
        #print(sqlDB.getTableDict())
        for _name,query in qm.queriesByName.items():
            listOfDicts=sqlDB.query(query.query)
            resultDoc=query.documentQueryResult(listOfDicts)         
            if show:
                print(resultDoc)
        pass
    
    def testSparqlQueries(self):
        '''
        test SPARQL queries 
        '''
        show=self.debug
        show=True
        qm=QueryManager(lang='sparql',debug=False)
        for name,query in qm.queriesByName.items():
            if name in ["US President Nicknames"]:
                if show:
                    print(f"{name}:{query}")
                endpoint=SPARQL(query.endpoint)
                try:
                    qlod=endpoint.queryAsListOfDicts(query.query)
                    for tablefmt in ["mediawiki","github","latex"]:
                        doc=query.documentQueryResult(qlod, tablefmt=tablefmt,floatfmt=".0f")
                        docstr=doc.asText()
                        if show:
                            print (docstr)
                            
                except Exception as ex:
                    print(f"{query.title} at {query.endpoint} failed: {ex}")
        
    def testUnicode2LatexWorkaround(self):
        '''
        test the uniCode2Latex conversion workaround
        '''
        debug=self.debug
        for code in range(8320,8330):
            uc=chr(code)
            latex=QueryResultDocumentation.uniCode2Latex(uc)
            if debug:
                print(f"{uc}→{latex}")
            #self.assertTrue(latex.startswith("$_"))
        unicode="À votre santé!"
        latex=QueryResultDocumentation.uniCode2Latex(unicode,withConvert=True)
        if debug:
            print(f"{unicode}→{latex}")
        self.assertEqual("\\`A votre sant\\'e!",latex)
        
    def captureQueryMain(self,args):
        '''
        run queryMain and capture stdout
        
        Args:
            args(list): command line arguments
            
        Returns:
            str: the stdout content of the command line call
        '''
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            queryMain(args)
            result = stdout.getvalue()
        return result
             
    def testQueryCommandLine(self):
        '''
        test the sparql query command line
        '''
        debug=self.debug
        #debug=True
        for testArg in [
            {"format":"csv", "expected":'''Theodore Roosevelt","Teddy"'''},
            {"format":"latex","expected":'''Theodore Roosevelt     & Teddy'''},
            {"format":"mediawiki", "expected":'''| [https://www.wikidata.org/wiki/Q33866 Q33866] || Theodore Roosevelt     || Teddy'''},
            {"format":"github","expected":'''| [Q33866](https://www.wikidata.org/wiki/Q33866) | Theodore Roosevelt     | Teddy                           |'''}
        ]:
            resultFormat=testArg["format"]
            expected=testArg["expected"]
            args=["-d","-qn","US President Nicknames","-l","sparql","-f",resultFormat]
            result=self.captureQueryMain(args)
            if debug:
                print(f"{resultFormat}:{result}")
            self.assertTrue(expected in result)
    

    def testQueryEndpoints(self):
        """
        tests the sparql endpoint commandline endpoint selection
        """
        testArgs=[
            {"en":"wikidata",},
            {"en":"qlever-wikidata",},
            # workaround https://github.com/ad-freiburg/qlever/issues/631
            {"en":"qlever-wikidata-proxy",},
        ]
        debug=self.debug
        showServerDown=True
        for testArg in testArgs:
            endpointName = testArg.get("en")
            args = ["-d", "-qn", "cities", "-p","-l", "sparql", "-f", "json", "-en", endpointName, "-raw"]
            result=self.captureQueryMain(args)
            
            if not "503 Service Unavailable" in result:
                #if debug:
                #    print(result)
                self.assertTrue("Arnis" in result, f"{endpointName}: Arnis not in query result")
            elif showServerDown:
                print(f"{endpointName} returns 503 Service Unavailable")
    
    def testIssue69showEndpoints(self):
        '''
        test the listEndpoints option
        
        https://github.com/WolfgangFahl/pyLoDStorage/issues/69
        '''
        debug=self.debug
        #debug=True
        expected={"sparql":"wikidata"}
        for option in ["-le","--listEndpoints"]:
            for lang in ["sparql","sql"]:  
                args=[option,"-l",lang]
                result=self.captureQueryMain(args)
                if debug:
                    print(result)
                if lang in expected:
                    self.assertTrue(expected[lang] in result)
        
    def testIssue70showQuery(self):
        '''
        test the showQuery option
        
        https://github.com/WolfgangFahl/pyLoDStorage/issues/70
        '''
        for option in ["-sq","--showQuery"]:
            args=["-qn","10 Largest Cities Of The World",option,"-l","sparql"]
            result=self.captureQueryMain(args)
            if self.debug:
                print(result)
            self.assertTrue("SELECT DISTINCT ?city ?cityLabel" in result)
            
    def testIssue73Formatting(self):
        '''
        test formatting
        '''
        debug=self.debug
        #debug=True
        qlod=[
            {"wikidata":"http://www.wikidata.org/entity/Q1353","label":"Delhi"},
            {"wikidata":"Q2","label":"Earth"},
            {"wikidata":"https://www.wikidata.org/wiki/Property:P31","label":"instanceof"}
        ]
        vf=ValueFormatter(name="wikidata",regexps=[
            r"(?P<value>(Q|Property:P)[0-9]+)",
            r"http(s)?://.*/(?P<value>(Q|Property:P)[0-9]+)"
        ],formatString="https://www.wikidata.org/wiki/{value}")
        key="wikidata"
        for tablefmt in [Format.mediawiki,Format.github,Format.latex]:
            lod=copy.deepcopy(qlod) 
            for record in lod:
                vf.applyFormat(record, key,tablefmt.value)
                if (debug):
                    print(tablefmt)
                    print(record)
            if tablefmt is Format.mediawiki:
                self.assertEqual("[https://www.wikidata.org/wiki/Q1353 Q1353]",lod[0]["wikidata"])
                self.assertEqual("[https://www.wikidata.org/wiki/Q2 Q2]",lod[1]["wikidata"])
                self.assertEqual("[https://www.wikidata.org/wiki/Property:P31 Property:P31]",lod[2]["wikidata"])
                        
    def testIssue73ReadFormats(self):
        '''
        test reading the valueFormatters
        '''
        vfs=ValueFormatter.getFormats(ValueFormatter.formatsPath)
        self.assertTrue("wikidata" in vfs)
       
    def testCommandLineUsage(self):
        '''
        test the command line usage
        '''
        args=["-h"]
        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                queryMain(args)
            self.fail("system exit expected")
        except SystemExit:
            pass
        debug=self.debug
        #debug=True
        if debug:
            print(stdout.getvalue())
        self.assertTrue("--queryName" in stdout.getvalue())
            
    def testQueryDocumentation(self):
        '''
        test QueryDocumentation
        '''
        show=self.debug
        #show=True
        queries=[
            {
                "endpoint":"https://query.wikidata.org/sparql",
                "prefixes": [],
                "lang": "sparql",
                "name": "Nicknames",
                "description": "https://stackoverflow.com/questions/70206791/sparql-i-have-individual-with-multiple-values-for-single-object-property-how",
                "title": "Nick names of US Presidents",
                "query":"""SELECT ?item ?itemLabel (GROUP_CONCAT(DISTINCT ?nickName; SEPARATOR=",") as ?nickNames)
WHERE 
{
  # president
  ?item wdt:P39 wd:Q11696.
  ?item wdt:P1449 ?nickName
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
} GROUP BY ?item ?itemLabel"""
            },
            {
            "endpoint":"https://query.wikidata.org/sparql",
            "prefixes": ["http://www.wikidata.org/entity/","http://commons.wikimedia.org/wiki/Special:FilePath/"],
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
"""
            },
            {
            "endpoint":"https://query.wikidata.org/sparql",
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
LIMIT 10"""
            },
            {
            "endpoint":"https://sophox.org/sparql",
            "lang": "sparql",
            "prefixes": [],
            "query":
        """# count osm place type instances
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
        "description":"""This SPARQL query 
determines the number of instances available in the OpenStreetMap for the placeTypes city,town and village
"""}]
        for queryMap in queries:
            endpointUrl=queryMap.pop("endpoint")
            endpoint=SPARQL(endpointUrl)
            query=Query(**queryMap)
            showYaml=False
            if showYaml:
                yamlMarkup=query.asYaml()
                print(yamlMarkup)
            try:
                qlod=endpoint.queryAsListOfDicts(query.query)
                for tablefmt in ["mediawiki","github","latex"]:
                    doc=query.documentQueryResult(qlod, tablefmt=tablefmt,floatfmt=".0f")
                    docstr=doc.asText()
                    if show:
                        print (docstr)
                        
            except Exception as ex:
                print(f"{query.title} at {endpointUrl} failed: {ex}")

    def testIssue61(self):
        """
        tests different query path

        see https://github.com/WolfgangFahl/pyLoDStorage/issues/61
        """
        queriesPath=f"{os.path.dirname(__file__)}/../sampledata/scholia.yaml"
        args=["-qp", f"{queriesPath}", "--list"]
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            queryMain(args, lang="sparql")
            result = stdout.getvalue()
        #debug=self.debug
        debug=True
        if debug:
            print(result)
        self.assertTrue("WorksAndAuthor" in result)    


class TestEndpoints(Basetest):
    """
    tests Endpoint
    """

    def testEndpoints(self):
        """
        tests getting and rawQuerying Endpoints
        """
        debug=self.debug
        #debug=True
        endpoints=EndpointManager.getEndpoints()
        qm=QueryManager(lang='sparql',debug=False)
        query=qm.queriesByName["FirstTriple"]
        self.assertTrue("wikidata" in endpoints)
        for i,item in enumerate(endpoints.items()):
            name,endpoint=item
            if debug:
                print (f"{i}:{name}")
            resultFormat="json"
            jsonStr=QueryMain.rawQuery(endpoint.endpoint, query.query, resultFormat, mimeType=None)
            if debug:
                print(jsonStr)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()