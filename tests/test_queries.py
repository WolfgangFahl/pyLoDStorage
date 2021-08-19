'''
Created on 2021-01-29

@author: wf
'''
import unittest
import os
from lodstorage.query import QueryManager
import tests.testSqlite3
from tests.basetest import Basetest

class TestQueries(Basetest):



    def testQueries(self):
        '''
        see https://github.com/WolfgangFahl/pyLoDStorage/issues/19
        '''
        show=self.debug
        show=True
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


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()