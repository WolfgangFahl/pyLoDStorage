"""
Created on 2020-09-12

@author: wf
"""
import json
import tempfile
import time
import unittest

from lodstorage.jsonable import JSONAble, JSONAbleList, Types
from lodstorage.sample import Cities, Royal, Royals, RoyalsORMList
from tests.basetest import Basetest


class ServerConfig(JSONAble):
    def __init__(self):
        pass


class TestJsonAble(Basetest):
    """
    test JSON serialization with JsonAble mixin
    """

    def setUp(self):
        super().setUp(debug=False)
        self.doProfile = True
        self.maxDiff = None
        pass

    def testSingleToDoubleQuote(self):
        jsonStr = """
        {
            "cities": [
            {
                "name": "Upper Hell's Gate"
            },
            {
                 "name": "N'zeto"
            }
            ]
        }
        """
        listOfDicts = json.loads(jsonStr)
        dictStr = str(listOfDicts)
        if self.debug:
            print(dictStr)
        jsonStr2 = JSONAble.singleQuoteToDoubleQuote(dictStr)
        if self.debug:
            print(jsonStr2)
        self.assertEqual(
            """{"cities": [{"name": "Upper Hell's Gate"}, {"name": "N'zeto"}]}""",
            jsonStr2,
        )

    def testSingleQuoteToDoubleQuoteStackoverflow(self):
        """
        see
            - https://stackoverflow.com/a/63862387/1497139
            - https://stackoverflow.com/a/50257217/1497139
        """
        singleQuotedExamples = [
            """{'cities': [{'name': "Upper Hell's Gate"}, {'name': "N'zeto"}]"""
        ]
        for example in singleQuotedExamples:
            if self.debug:
                print(example)
            for useRegex in [False, True]:
                doubleQuoted = JSONAble.singleQuoteToDoubleQuote(
                    example, useRegex=useRegex
                )
                if self.debug:
                    print(doubleQuoted)
            if self.debug:
                print

    def dumpListOfDicts(self, listOfDicts, limit):
        if self.debug:
            for index, record in enumerate(listOfDicts[:limit]):
                print("%2d:%s" % (index, record))

    def check(self, manager, manager1, listName, debugLimit):
        """
        check that the list of the two managers are the same
        """
        d1 = manager.__dict__[listName]
        d2 = manager1.__dict__[listName]
        self.dumpListOfDicts(d1, debugLimit)
        self.dumpListOfDicts(d2, debugLimit)
        self.assertEqual(d1, d2)

    def testJsonAble(self):
        """
        test JSONAble
        """
        examples = [
            {"manager": Royals(load=True), "listName": "royals"},
            {"manager": Cities(load=True), "listName": "cities"},
        ]
        debugLimit = 10
        debugChars = debugLimit * 100
        index = 0
        for useToJson in [True, False]:
            for example in examples:
                starttime = time.time()
                manager = example["manager"]
                listName = example["listName"]
                if useToJson:
                    jsonStr = manager.toJSON()
                else:
                    jsonStr = manager.asJSON()
                if self.debug:
                    print(jsonStr[:debugChars])
                    # print(jsonStr,file=open('/tmp/example%d.json' %index,'w'))
                index += 1
                if self.doProfile:
                    print(
                        "->JSON for %d took %7.3f s"
                        % (index, (time.time() - starttime))
                    )
                self.assertTrue(isinstance(jsonStr, str))
                starttime = time.time()
                jsonDict = json.loads(jsonStr)
                self.assertTrue(isinstance(jsonDict, dict))
                if self.debug:
                    print(str(jsonDict)[:debugChars])
                if self.doProfile:
                    print(
                        "<-JSON for %d took %7.3f s" % (index, time.time() - starttime)
                    )
                cls = manager.__class__
                types = Types(cls.__name__)
                types.getTypes(listName, manager.__dict__[listName])
                manager1 = cls()
                manager1.fromJson(jsonStr, types=types)
                self.check(manager, manager1, listName, debugLimit=debugLimit)
        pass

    def testRoyals(self):
        """
        test Royals example
        """
        royals1 = Royals(load=True)
        self.assertEqual(4, len(royals1.royals))
        json = royals1.toJSON()
        if self.debug:
            print(json)
        types = Types.forTable(royals1, "royals", debug=True)
        royals2 = Royals()
        royals2.fromJson(json, types=types)
        self.assertEqual(4, len(royals2.royals))
        if self.debug:
            print(royals1.royals)
            print(royals2.royals)
        self.assertEqual(royals1.royals, royals2.royals)

    def testPluralName(self):
        royal = Royal()
        self.assertEqual("Royals", royal.getPluralname())

    def testStoreAndRestore(self):
        """
        test storing and restoring from a JSON file
        https://github.com/WolfgangFahl/pyLoDStorage/issues/21
        """
        royals1 = RoyalsORMList(load=True)
        jsonFile = "/tmp/royals-pylodstorage.json"
        royals1.storeToJsonFile(jsonFile)
        royals2 = RoyalsORMList()
        royals2.restoreFromJsonFile(jsonFile)
        self.assertEqual(4, len(royals2.royals))
        for royal in royals2.royals:
            self.assertTrue(isinstance(royal, Royal))
            self.assertEqual("float", type(royal.age).__name__)

    def testIssue22(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/22
        Regression: storeToJsonFile and restoreFromJsonFile missing in JSONAble
        """
        jsonStr = """{
    "adminPassword": "tiger2021",
    "adminUser": "scott",
    "credentials": [
        {
            "dbname": "doedb",
            "password": "doesSecret!",
            "user": "john"
        }
    ],
    "frontendConfigs": [
        {
            "defaultPage": "Frontend",
            "site": "or",
            "template": "bootstrap.html",
            "wikiId": "or"
        },
        {
            "defaultPage": "Main Page",
            "site": "cr",
            "template": "bootstrap.html",
            "wikiId": "cr"
        }
    ],
    "logo": "https://commons.wikimedia.org/wiki/Category:Mona_Lisa#/media/File:Mona_Lisa,_by_Leonardo_da_Vinci,_from_C2RMF_retouched.jpg"
}"""
        jsonFilePath = f"{tempfile.gettempdir()}/serverConfig.json"
        JSONAble.storeJsonToFile(jsonStr, jsonFilePath)
        serverConfig = ServerConfig()
        serverConfig.restoreFromJsonFile(jsonFilePath)
        self.assertTrue(serverConfig.logo.endswith("_retouched.jpg"))
        self.assertTrue(isinstance(serverConfig.frontendConfigs, list))
        self.assertEqual(2, len(serverConfig.frontendConfigs))
        serverConfig.storeToJsonFile(jsonFilePath)
        jsonStr2 = JSONAble.readJsonFromFile(jsonFilePath)
        if self.debug:
            print(jsonStr2)
        self.assertEqual(jsonStr, jsonStr2)

    def testRestoreFromJsonStr(self):
        """
        Tests restoring a JsonAbleList form a json string
        """
        samples = """
                {
                    "countries": [
                        {
                            "name": "Afghanistan",
                            "wikidataid": "Q889",
                            "coordinates": "34,66",
                            "partOf": null,
                            "level": 3,
                            "locationKind": "Country",
                            "comment": null,
                            "iso": "AF"
                        },
                        {
                            "name": "United States of America",
                            "wikidataid": "Q30",
                            "coordinates": "39.828175,-98.5795",
                            "partOf": null,
                            "level": 3,
                            "locationKind": "Country",
                            "comment": null,
                            "labels": [
                                "America",
                                "UNITED STATES OF AMERICA",
                                "USA",
                                "United States",
                                "United States of America (the)"
                            ],
                            "iso": "US"
                        },
                        {
                            "name": "Australia",
                            "wikidataid": "Q408",
                            "coordinates": "-28,137",
                            "partOf": null,
                            "level": 3,
                            "locationKind": "Country",
                            "comment": null,
                            "labels": [
                                "AUS"
                            ],
                            "iso": "AU"
                        }
                    ]
                }
                """
        countryList = JSONAbleList("countries")
        countryList.restoreFromJsonStr(samples)
        countries = countryList.countries
        self.assertTrue(len(countries) == 3)
        countryIds = [x["wikidataid"] for x in countries]
        self.assertTrue("Q30" in countryIds)

    def testIssue27_Lookup(self):
        """
        add Lookup map option
        """
        # first try with List of Dicts
        royals = Royals(load=True)
        # print(len(royals.royals))
        # print(royals.royals)
        royalsByNumberInLine, duplicates = royals.getLookup(
            "numberInLine", withDuplicates=False
        )
        # print(royalsByNumberInLine)
        self.assertEqual(0, len(duplicates))
        self.assertEqual(4, len(royalsByNumberInLine))
        self.assertEqual("Charles, Prince of Wales", royalsByNumberInLine[1]["name"])
        # then with list of Entities
        royalsORM = RoyalsORMList(load=True)
        royalsByNumberInLine, duplicates = royalsORM.getLookup(
            "numberInLine", withDuplicates=False
        )
        self.assertEqual(0, len(duplicates))
        self.assertEqual(4, len(royalsByNumberInLine))
        self.assertEqual("Charles, Prince of Wales", royalsByNumberInLine[1].name)

    def testIssue30_SampleLimited(self):
        """
        tests if the json export is correctly limited to the fields that are used in the samples
        """
        royalDict = {"name": "Test royal"}
        royal = Royal()
        royal.fromDict(royalDict)
        # add attributes that are not in the samples
        royal.__dict__["not_in_samples"] = "test"
        expectedJSON = """{
    "name": "Test royal"
}"""
        actualJSON = royal.toJSON(limitToSampleFields=True)
        self.assertEqual(actualJSON, expectedJSON)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
