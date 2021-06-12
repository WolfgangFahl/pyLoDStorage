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
        pass


    def tearDown(self):
        pass


    def testListIntersect(self):
        '''
        test a list intersection
        '''
        lod1=[
           { "name":"London" },
           { "name":"Athens" }
        ]
        lod2=[
            { "name":"Athens" },
            { "name":"Paris" }
        ]
        lodi=LOD.intersect(lod1, lod2, "name")
        self.assertEqual(1,len(lodi))
        self.assertEqual("Athens",lodi[0]["name"])
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()