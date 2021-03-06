'''
Created on 2021-06-07

@author: mk
'''

from lodstorage.sample import Sample
import unittest
import pandas as pd

class TestPandas(unittest.TestCase):


    def setUp(self):
        self.debug=False
        pass


    def tearDown(self):
        pass


    def testIssue25(self):
        '''
        see https://github.com/WolfgangFahl/pyLoDStorage/issues/25
        '''
        listOfRecords = Sample.getRoyals()
        df= pd.DataFrame(listOfRecords)
        self.assertEqual(len(df), len(listOfRecords))
        self.assertEqual(len(df.columns.values), len(listOfRecords[0].keys()))
        averageAge= df['age'].mean()
        self.assertIsNotNone(averageAge)
        self.assertGreater(averageAge,53)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()