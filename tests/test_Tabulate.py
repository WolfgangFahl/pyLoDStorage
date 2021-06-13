'''
Created on 2021-06-13

@author: wf
'''
import unittest
from lodstorage.sample import Royals, Sample
from tabulate import tabulate
from collections import Counter
from lodstorage.tabulateCounter import TabulateCounter

class TestTabulate(unittest.TestCase):
    '''
    test tabulate support/compatibility
    '''

    def setUp(self):
        self.debug=True
        pass


    def tearDown(self):
        pass


    def testIssue24_IntegrateTabulate(self):
        '''
        https://github.com/WolfgangFahl/pyLoDStorage/issues/24
        
        test https://pypi.org/project/tabulate/ support
        '''
        royals=Royals(load=True)
        for fmt in ["latex","grid","mediawiki","github"]:
            table=tabulate(royals.royals,headers="keys",tablefmt=fmt)
            print (table)
    
        cities=Sample.getCities()    
        counter=Counter()
        for city in cities:
            counter[city["country"]]+=1;
        tabulateCounter=TabulateCounter(counter)
        for fmt in ["latex","grid","mediawiki","github"]:
            table=tabulateCounter.mostCommonTable(tablefmt=fmt,limit=7)
            print(table)
        pass
    


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()