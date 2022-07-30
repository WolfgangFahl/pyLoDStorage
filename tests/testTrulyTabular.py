'''
Created on 2022-03-4

@author: wf
'''
import unittest
from lodstorage.trulytabular import TrulyTabular, WikidataItem, WikidataProperty
from lodstorage.query import Query, QuerySyntaxHighlight
from lodstorage.sparql import SPARQL
from pprint import pprint

class TestTrulyTabular(unittest.TestCase):
    '''
    test Truly tabular analysis
    '''

    def setUp(self):
        self.debug=False
        pass


    def tearDown(self):
        pass

    def testGetFirst(self):
        '''
        test the get First helper function
        '''
        tt=TrulyTabular("Q2020153")
        testcases=[
            { 
                "qlod":[{"name":"firstname"}],
                "expected": "firstname"
            },
            {
                "qlod":[],
                "expected": None
            },
            {
                "qlod":[{"name":"firstname"},{"name":"second name"}],
                "expected": None
            }
        ]
        for testcase in testcases:
            qLod=testcase["qlod"]
            expected=testcase["expected"]
            try:
                value=tt.sparql.getFirst(qLod,"name")
                self.assertEqual(expected,value)
            except Exception as ex:
                if self.debug:
                    print(str(ex))
                self.assertIsNone(expected)
                
    def documentQuery(self,tt,query,show=True,formats=["mediawiki"]):
        '''
        document the given query for the given TrueTabular instance
        '''
        qlod=tt.sparql.queryAsListOfDicts(query.query)
        for tablefmt in formats:
            tryItUrl="https://query.wikidata.org/"
            doc=query.documentQueryResult(qlod, tablefmt=tablefmt,tryItUrl=tryItUrl,floatfmt=".0f")
            docstr=doc.asText()
            if show:
                print (docstr)
                
    def testGetPropertiesByLabel(self):
        '''
        try getting properties by label
        '''
        debug=self.debug
        #debug=True
        propertyLabels=["title","country","location"]
        tt=TrulyTabular("Q2020153",propertyLabels=propertyLabels)
        if debug:
            print (tt.properties)
        for prop in propertyLabels:
            self.assertTrue(prop in tt.properties)
            
    def testGetPropertiesById(self):
        '''
        try getting properties by label
        '''
        debug=self.debug
        #debug=True
        propertyIds=["P1800"]
        expected=["Wikimedia database name"]
        sparql=SPARQL(TrulyTabular.endpoint)
        propList=WikidataProperty.getPropertiesByIds(sparql, propertyIds, lang="en")
        for i,prop in enumerate(propList):
            if debug:
                print(f"{i}:{prop}")
            self.assertEqual(prop,expected[i])
            
    def testGetItemsByLabel(self):
        '''
        try getting items by label
        '''
        #debug=self.debug
        debug=True
        qLabels=["academic conference","scientific conference series","whisky distillery","human"]
        sparql=SPARQL(TrulyTabular.endpoint)
        items={}
        for qLabel in qLabels:
            items4Label=WikidataItem.getItemsByLabel(sparql, qLabel)
            for item in items4Label:
                if debug:
                    print(item)
            items[qLabel]=items4Label[0]
        for qLabel in qLabels:
            self.assertTrue(qLabel in items)

    def testTrulyTabularTables(self):
        '''
        test Truly Tabular for different tabular queries
        '''
        debug=self.debug
        #debug=True
        show=False
        showStats=["mediawiki","github","latex"]
        tables=[ 
            {
               "name": "computer scientist",
               "title": "humans with the occupation computer scientist",
               "qid":"Q5", # human
               "where": "?item wdt:P106 wd:Q82594.", # computer scientist only
               "propertyLabels": ["sex or gender","date of birth","place of birth","field of work","occupation","ORCID iD",
                                  "GND ID","DBLP author ID","Google Scholar author ID","VIAF ID"],
               "expected": 10  
            },
            {
               "name": "academic conferences",
               "title": "academic conferences",
               "qid": "Q2020153",# academic conference
               "propertyLabels":["title","country","location","short name","start time",
                "end time","part of the series","official website","described at URL",
                "WikiCFP event ID","GND ID","VIAF ID","main subject","language used",
                "is proceedings from"
               ],
               "expected": 7500
            },
            {
                "name": "scientific conferences series",
                "title": "scientific conference series",
                "qid": "Q47258130", # scientific conference series
                "propertyLabels":["title","short name","inception","official website","DBLP venue ID","GND ID",
                    "Microsoft Academic ID","Freebase ID","WikiCFP conference series ID",
                    "Publons journals/conferences ID","ACM conference ID"],
                "expected": 4200
            },
            {
                "name": "whisky distilleries",
                "title": "whisky distilleries",
                "qid": "Q10373548", # whisky distillery
                "propertyLabels":["inception","official website","owned by","country","headquarters location","Whiskybase distillery ID"],
                "expected": 200
            }
        ]
        errors=0
        for table in tables[3:]:
            # academic conference
            where=None
            if "where" in table:
                where=table["where"]
            tt=TrulyTabular(table["qid"],table["propertyLabels"],where=where,debug=debug)
            if "is proceedings from" in tt.properties:
                tt.properties["is proceedings from"].reverse=True
            count=tt.count()
            if (debug):
                print(count)
            self.assertTrue(count>table["expected"])
            stats=tt.getPropertyStatistics()
            # sort descending by total percentage
            stats = sorted(stats, key=lambda row: row['total%'],reverse=True) 
            for tablefmt in showStats:
                query=Query(name=table["name"],title=table["title"],query="")
                doc=query.documentQueryResult(stats, tablefmt=tablefmt, withSourceCode=False)
                print(doc)
            if show:
                for wdProperty in tt.properties.values():
                    for asFrequency in [True,False]:
                        query=tt.noneTabularQuery(wdProperty,asFrequency=asFrequency)
                        try:
                            self.documentQuery(tt, query)
                        except Exception as ex:
                            print(f"query for {wdProperty} failed\n{str(ex)}")
                            errors+=1
                self.assertEqual(0,errors)
            
                
    def testMostFrequentProperties(self):
        '''
        test getting the most frequent properties for some Wikidata Item types
        '''
        #show=True
        show=False
        debug=self.debug
        #debug=True
        for qid in ["Q6256"]:
            tt=TrulyTabular(qid,debug=debug)
            query=tt.mostFrequentPropertiesQuery()
            self.documentQuery(tt, query,formats=["github"],show=show)

    def testSyntaxHighlighting(self):
        '''
        https://github.com/WolfgangFahl/pyLoDStorage/issues/81
        '''
        #debug=self.debug
        debug=True
        qid="Q6256" # country
        tt=TrulyTabular(qid,debug=debug)
        query=tt.mostFrequentPropertiesQuery()
        sh=QuerySyntaxHighlight(query,"html")
        html=sh.highlight()
        if debug:
            print(html)
        self.assertTrue('<span class="k">SELECT</span>' in html)
        pass
    
    def testCount(self):
        '''
        test the count function of truly tabular
        '''
        debug=True  
        qid="Q55488" # railway stations
        tt=TrulyTabular(qid,debug=debug)
        count=tt.count()
        if debug:
            print(f"count of railway stations is {count}")
        self.assertTrue(count>=106195)
            
        self.assertTrue(tt.error is None)
        
    def testGenerateSparqlQuery(self):
        '''
        test Generating a SPARQL query
        '''
        debug=True
        configs=[

            {
                "naive":True,
                "qid": "Q2020153", # academic conference
                "propertyIdMap": {
                    "P1813": ["label"],
                    "P17": ["label"],
                    "P1476": ["label"]
                },
                "expected": []
            },
            {
                "naive":False,
                "qid": "Q2020153", # academic conference
                "propertyIdMap": {
                    "P1813": ["sample"],
                    "P17": ["sample"],
                    "P1476": ["sample"]
                },
                "expected": ["GROUP BY","SAMPLE"]
            },
            {
                "naive":False,
                "qid": "Q2020153", # academic conference
                "propertyIdMap": {
                    "P1813": ["count","list"],
                    "P17": ["sample","ignore"],
                    "P1476": ["count","list"]
                },
                "expected": ["COUNT (DISTINCT","GROUP BY","GROUP_CONCAT (DISTINCT","HAVING"]
            },
            {
                "naive":False,
                "qid": "Q1667921", # novel series
                "propertyIdMap": {
                    "P50": ["sample","ignore"], # author
                    "P136": ["sample","ignore"],# genre
                    "P1476": ["sample","ignore"] #title
                },
                "expected": ["GROUP BY","HAVING","COUNT","<=1"]
            },
            {
                "naive":False,
                "qid": "Q1667921", # novel series
                "propertyIdMap": {
                    "P50": ["sample","ignore","label"], # author
                    "P136": ["sample","ignore","label"],# genre
                    "P1476": ["sample","ignore"] #title
                },
                "expected": ["GROUP BY","HAVING","COUNT","<=1"]
            },
            
        ]
        # loop over different test configurations
        for i,config in enumerate(configs):
            # get the test configuration
            qid=config["qid"]
            naive=config["naive"]
            propertyIdMap=config["propertyIdMap"]
            expectedList=config["expected"]
            
            # create a truly tabular analysis
            tt=TrulyTabular(qid, propertyIds=list(propertyIdMap.keys()))
            varname=tt.item.varname
            # generate a SPARQL Query
            sparqlQuery=tt.generateSparqlQuery(genMap=propertyIdMap,naive=naive)
            if debug:
                print(f"config {i}:")
                pprint(config)
                print(f"{sparqlQuery}")
            # all queries should have basic graph patterns for the instance of 
            self.assertTrue(f"?{varname} wdt:P31 wd:{qid}." in sparqlQuery)
            # and for the properties
            for pid in propertyIdMap.keys():
                self.assertTrue(f"?{varname} wdt:{pid}" in sparqlQuery)
            for expected in expectedList:
                self.assertTrue(expected in sparqlQuery,f"config {i}:{expected} missing")
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()