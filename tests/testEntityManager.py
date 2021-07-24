'''
Created on 2021-07-23

@author: wf
'''
import unittest
from lodstorage.sample import Sample
from lodstorage.entity import EntityManager
from lodstorage.storageconfig import StoreMode, StorageConfig


class TestEntityManager(unittest.TestCase):
    '''
    test the entity manager wrapper
    '''

    def setUp(self):
        self.debug=False
        pass


    def tearDown(self):
        pass

    def testStoreMode(self):
        '''
        test store mode display
        '''
        config=StorageConfig.getDefault()
        em=EntityManager("tst","Test","Tests",config=config)
        if self.debug:
            print (em.storeMode().name)
        self.assertEqual(StoreMode.SQL,em.storeMode())
        
    def testEntityManager(self):
        '''
        test the entity Manager handling
        '''
        for config in [StorageConfig.getJSON(debug=self.debug),StorageConfig.getDefault(debug=self.debug)]:
            em=EntityManager("royal","Royal","Royals",config=config)
            listOfDicts=Sample.getRoyals()
            em.store(listOfDicts)
            result=em.fromStore()
            if isinstance(result,list):
                lod2=result
                self.assertEqual(len(listOfDicts),len(lod2))        
            pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()