'''
Created on 2021-01-29

@author: wf
'''
import unittest
import os
import copy
from lodstorage.query import QueryManager, Query
from lodstorage.sparql import SPARQL
import tests.testSqlite3
from tests.basetest import Basetest

class TestQueries(Basetest):
    '''
    Test query handling
    '''

    def testQueries(self):
        '''
        see https://github.com/WolfgangFahl/pyLoDStorage/issues/19
        '''
        show=self.debug
        #show=True
        path="%s/../sampledata" % os.path.dirname(__file__)
        qm=QueryManager(lang='sql',debug=False,path=path)
        self.assertEqual(2,len(qm.queriesByName)) 
        sqlDB=tests.testSqlite3.TestSQLDB.getSampleTableDB()
        #print(sqlDB.getTableDict())
        for _name,query in qm.queriesByName.items():
            listOfDicts=sqlDB.query(query.query)
            resultDoc=query.documentQueryResult(listOfDicts)         
            if show:
                print(resultDoc)
        pass
    
    def uniCode2Latex(self,s:str):
        for code in range(8320,8330):
            s=s.replace(chr(code),f"$_{code-8320}$")
        return s
    
    def testUnicode(self):
        '''
        
        '''
        for code in range(8320,8330):
            uc=chr(code)
            print(f"{uc}:{self.uniCode2Latex(uc)}")
            
    def fixUnicode(self,tab:str,tableFmt):
        if tableFmt!="latex":
            result= tab
        else:
            result=self.uniCode2Latex(tab)
        return result
            
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
            prefixes=queryMap.pop("prefixes")
            endpoint=SPARQL(endpointUrl)
            query=Query(**queryMap)
            try:
                qlod=endpoint.queryAsListOfDicts(query.query)
                for tablefmt in ["mediawiki","github","latex"]:
                    lod=copy.deepcopy(qlod)
                    for prefix in prefixes:
                        query.prefixToLink(lod,prefix,tablefmt)
                    tryItUrl=query.getTryItUrl(endpointUrl.replace("/sparql",""))
                    doc=query.documentQueryResult(lod, tablefmt=tablefmt,floatfmt=".0f",tryItUrl=tryItUrl)
                    if show:
                        docstr=str(doc)
                        fixedStr=self.fixUnicode(docstr,tablefmt)
                        print(fixedStr)
            except Exception as ex:
                print(f"{query.title} at {endpointUrl} failed: {ex}")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()