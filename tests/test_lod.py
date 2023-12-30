"""
Created on 2021-06-11

@author: wf
"""
import copy
import unittest

from lodstorage.jsonable import JSONAble, JSONAbleList
from lodstorage.lod import LOD
from tests.basetest import Basetest


class TestLOD(Basetest):
    """
    test list of dicts base functionality
    """

    def testListIntersect(self):
        """
        test a list intersection
        """
        lod1 = [{"name": "London"}, {"name": "Athens"}]
        lod2 = [{"name": "Athens"}, {"name": "Paris"}]
        lodi = LOD.intersect(lod1, lod2, "name")
        self.assertEqual(1, len(lodi))
        self.assertEqual("Athens", lodi[0]["name"])
        pass

    def testGetLookupIssue31And32(self):
        """
        test for https://github.com/WolfgangFahl/pyLoDStorage/issues/31
        test for https://github.com/WolfgangFahl/pyLoDStorage/issues/32
        """
        lod = [
            {"name": "Athens", "Q": 1524},
            {"name": "Paris", "Q": 90},
            {"name": ["München", "Munich"], "Q": 1726},
            {"name": "Athens", "Q": 1524},
        ]
        cityMap, duplicates = LOD.getLookup(lod, "name")
        if self.debug:
            print(cityMap)
        self.assertEqual(1, len(duplicates))
        self.assertEqual(4, len(cityMap))
        self.assertEqual(cityMap["München"], cityMap["Munich"])

    def checkHandleListTypeResult(self, lod, expectedLen, expected):
        """
        check the result of the handleListType function

        Args:
            lod(list): the list of dicts to check
            expectedLen(int): the expected Length
            expected(str): the expected entry for the München,Munich Q1524 record with a list
        """
        if self.debug:
            print(lod)
        self.assertEqual(expectedLen, len(lod))
        cityByQ, _duplicates = LOD.getLookup(lod, "Q")
        if self.debug:
            print(cityByQ)
        if expected is not None:
            munichRecord = cityByQ[1726]
            self.assertEqual(expected, munichRecord["name"])
        else:
            self.assertFalse(1726 in cityByQ)

    def testListHandlingIssue33(self):
        """
        test for handling list
        """
        exampleLod = [
            {"name": "Athens", "Q": 1524},
            {"name": "Paris", "Q": 90},
            {"name": ["München", "Munich"], "Q": 1726},
            {"name": "Athens", "Q": 1524},
        ]
        # self.debug=True
        lod = copy.deepcopy(exampleLod)
        LOD.handleListTypes(lod)
        self.checkHandleListTypeResult(lod, 4, "München,Munich")
        lod = copy.deepcopy(exampleLod)
        LOD.handleListTypes(lod, doFilter=True)
        self.checkHandleListTypeResult(lod, 3, None)
        lod = copy.deepcopy(exampleLod)
        LOD.handleListTypes(lod, separator=";")
        self.checkHandleListTypeResult(lod, 4, "München;Munich")

    def testGetFields(self):
        """
        tests field extraction from list of JSONAble objects and LoD
        """
        lod = [
            {"name": "Test", "label": 1},
            {"name": "Test 2", "label": 2},
            {"name": "Different", "location": "Munich"},
        ]
        expectedFields = ["name", "label", "location"]
        actualFieldsLoD = LOD.getFields(lod)
        self.assertEqual(actualFieldsLoD, expectedFields)
        jsonAbleList = JSONAbleList(clazz=JSONAble)
        jsonAbleList.fromLoD(lod)
        loj = jsonAbleList.getList()
        actualFieldsLoJ = LOD.getFields(loj)
        self.assertEqual(actualFieldsLoJ, expectedFields)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
