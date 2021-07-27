'''
Created on 2021-07-23

@author: wf
'''
import unittest
from lodstorage.sample import Sample
from lodstorage.entity import EntityManager
from lodstorage.storageconfig import StoreMode, StorageConfig
import os

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
        self.debug=True
        royalsLoD=Sample.getRoyals()
        if self.debug:
            print(royalsLoD)
        for config in [StorageConfig.getDefault(debug=self.debug),StorageConfig.getJSON(debug=self.debug),StorageConfig.getJsonPickle(self.debug)]:
            em=EntityManager("royal","Royal","royals",config=config)
            em.royals=royalsLoD
            cacheFile=em.store(royalsLoD)
            self.assertTrue(os.path.isfile(cacheFile))
            result=em.fromStore()
            if isinstance(result,list):
                lod2=result
                self.assertEqual(len(royalsLoD),len(lod2))        
            pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()