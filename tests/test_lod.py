'''
Created on 2021-06-11

@author: wf
'''
import unittest
from lodstorage.lod import LOD


class TestLOD(unittest.TestCase):
    '''
    test list of dicts base functionality
    '''

    def setUp(self):
        self.debug=False
        pass

    def tearDown(self):
        pass

    def testListIntersect(self):
        '''
        test a list intersection
        '''
        lod1 = [
           { "name":"London" },
           { "name":"Athens" }
        ]
        lod2 = [
            { "name":"Athens" },
            { "name":"Paris" }
        ]
        lodi = LOD.intersect(lod1, lod2, "name")
        self.assertEqual(1, len(lodi))
        self.assertEqual("Athens", lodi[0]["name"])
        pass
    
    def testGetLookupIssue31And32(self):
        '''
        test for https://github.com/WolfgangFahl/pyLoDStorage/issues/31
        test for https://github.com/WolfgangFahl/pyLoDStorage/issues/32
        '''
        lod = [
                { "name": "Athens",              "Q": 1524},
                { "name": "Paris",               "Q": 90},
                { "name": ["München", "Munich"], "Q": 1726},
                { "name": "Athens",              "Q": 1524},
            
            ]
        cityMap,duplicates = LOD.getLookup(lod, "name")
        if self.debug:
            print(cityMap)
        self.assertEqual(1,len(duplicates))
        self.assertEqual(4,len(cityMap))
        self.assertEqual(cityMap["München"],cityMap["Munich"])
            
    
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
