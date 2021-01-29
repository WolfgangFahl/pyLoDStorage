'''
Created on 2021-01-29

@author: wf
'''
import unittest
import os
from lodstorage.query import QueryManager
import tests.testSqlite3

class TestQueries(unittest.TestCase):


    def setUp(self):
        self.debug=False
        pass


    def tearDown(self):
        pass


    def testQueries(self):
        '''
        see https://github.com/WolfgangFahl/pyLoDStorage/issues/19
        '''
        path="%s/../sampledata" % os.path.dirname(__file__)
        qm=QueryManager(lang='sql',debug=False,path=path)
        self.assertEqual(2,len(qm.queriesByName)) 
        sqlDB=tests.testSqlite3.TestSQLDB.getSampleTableDB()
        #print(sqlDB.getTableDict())
        for name,query in qm.queriesByName.items():
            listOfDicts=sqlDB.query(query.query)
            markup=query.asWikiMarkup(listOfDicts)
            if self.debug:
                print("== %s ==" % (name))
                print("=== query ===")
                print (query.asWikiSourceMarkup())
                print("=== result ===")
                print(markup)
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()