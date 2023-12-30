"""
Created on 2021-07-23

@author: wf
"""
import os
import unittest

from lodstorage.entity import EntityManager
from lodstorage.sample import Royal, Sample
from lodstorage.storageconfig import StorageConfig, StoreMode
from tests.basetest import Basetest


class TestEntityManager(Basetest):
    """
    test the entity manager wrapper
    """

    def configure(self, config: StorageConfig):
        config.cacheDirName = "lodstorage-test"

    def testStoreMode(self):
        """
        test store mode display
        """
        config = StorageConfig.getDefault()
        self.configure(config)
        em = EntityManager("tst", "Test", "Tests", config=config)
        if self.debug:
            print(em.storeMode().name)
        self.assertEqual(StoreMode.SQL, em.storeMode())

    def checkItem(self, item1, item2, attrs, msg):
        # check mode
        isDict = False
        if isinstance(item1, dict):
            self.assertTrue(isinstance(item2, dict))
            isDict = True
        else:
            self.assertFalse(isinstance(item2, dict))
        for attr in attrs:
            if isDict:
                value1 = item1[attr]
                value2 = item2[attr]
            else:
                value1 = getattr(item1, attr)
                value2 = getattr(item2, attr)
            # if not value1==value2:
            #    print(f"{value1}!={value2} for {attr}-{msg}")
            self.assertEqual(value1, value2, f"{attr}-{msg}")

    def testEntityManager(self):
        """
        test the entity Manager handling
        """
        self.debug = True
        for i, royals in enumerate([Sample.getRoyals(), Sample.getRoyalsInstances()]):
            if self.debug:
                print(f"{i+1}:{royals}")
            sparqlConfig = StorageConfig.getSPARQL(
                "http://example.bitplan.com",
                "http://localhost:3030/example",
                host="localhost",
            )
            # TODO use sparql Config
            for config in [
                StorageConfig.getDefault(debug=self.debug),
                StorageConfig.getJSON(debug=self.debug),
                StorageConfig.getJsonPickle(self.debug),
            ]:
                self.configure(config)
                name = "royal" if i == 0 else "royalorm"
                clazz = None if i == 0 else Royal
                em = EntityManager(
                    name=name,
                    entityName="Royal",
                    entityPluralName="Royals",
                    clazz=clazz,
                    listName="royals",
                    config=config,
                )
                em.royals = royals
                if i == 0:
                    cacheFile = em.storeLoD(royals)
                else:
                    cacheFile = em.store()
                if cacheFile is not None:
                    self.assertTrue(os.path.isfile(cacheFile))
                royalsLod = em.fromStore()
                self.assertTrue(isinstance(royalsLod, list))
                hint = f"{i}({config.mode}):{name}"
                for item in royalsLod:
                    self.assertTrue(isinstance(item, dict), f"{hint}:expecting dict")
                royalsList = em.getList()
                self.assertEqual(len(royals), len(royalsList))
                for j, item in enumerate(royalsList):
                    hint = f"{hint}/{j}"
                    royal = royals[j]
                    # TODO check type handling e.g. "born"
                    self.checkItem(
                        royal,
                        item,
                        ["name", "age", "numberInLine", "wikidataurl"],
                        hint,
                    )
            pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
