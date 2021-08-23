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
    
    def testQueryDocumentation(self):
        '''
        test QueryDocumentation
        '''
        show=self.debug
        #show=True
        queries=[{
            "endpoint":"https://query.wikidata.org/sparql",
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
            try:
                qlod=endpoint.queryAsListOfDicts(query.query)
                for tablefmt in ["mediawiki","github","latex"]:
                    lod=copy.deepcopy(qlod)
                    query.prefixToLink(lod,"http://www.wikidata.org/entity/",tablefmt)
                    tryItUrl=query.getTryItUrl(endpointUrl.replace("/sparql",""))
                    doc=query.documentQueryResult(lod, tablefmt=tablefmt,floatfmt=".0f",tryItUrl=tryItUrl)
                    if show:
                        print(doc)
            except Exception as ex:
                print(f"{query.title} at {endpointUrl} failed: {ex}")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()