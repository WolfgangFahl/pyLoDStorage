"""
Created on 2020-08-24

@author: wf
"""
import os
import sys
import time
import unittest
from datetime import datetime

from lodstorage.sample import Sample
from lodstorage.schema import Schema
from lodstorage.sql import SQLDB, EntityInfo
from lodstorage.uml import UML
from tests.basetest import Basetest


class TestSQLDB(Basetest):
    """
    Test the SQLDB database wrapper
    """

    def checkListOfRecords(
        self,
        listOfRecords,
        entityName,
        primaryKey=None,
        executeMany=True,
        fixNone=False,
        fixDates=False,
        debug=False,
        doClose=True,
    ):
        """
        check the handling of the given list of Records

        Args:

           listOfRecords(list): a list of dicts that contain the data to be stored
           entityName(string): the name of the entity type to be used as a table name
           primaryKey(string): the name of the key / column to be used as a primary key
           executeMany(boolean): True if executeMany mode of sqlite3 should be used
           fixNone(boolean): fix dict entries that are undefined to have a "None" entry
           debug(boolean): True if debug information e.g. CREATE TABLE and INSERT INTO commands should be shown
           doClose(boolean): True if the connection should be closed

        """
        size = len(listOfRecords)
        if self.debug:
            print(
                "%s size is %d fixNone is %r fixDates is: %r"
                % (entityName, size, fixNone, fixDates)
            )
        self.sqlDB = SQLDB(debug=debug, errorDebug=True)
        entityInfo = self.sqlDB.createTable(listOfRecords[:10], entityName, primaryKey)
        startTime = time.time()
        self.sqlDB.store(
            listOfRecords, entityInfo, executeMany=executeMany, fixNone=fixNone
        )
        elapsed = time.time() - startTime
        if self.debug:
            print(
                "adding %d %s records took %5.3f s => %5.f records/s"
                % (size, entityName, elapsed, size / elapsed)
            )
        resultList = self.sqlDB.queryAll(entityInfo, fixDates=fixDates)
        if self.debug:
            print(
                "selecting %d %s records took %5.3f s => %5.f records/s"
                % (len(resultList), entityName, elapsed, len(resultList) / elapsed)
            )
        if doClose:
            self.sqlDB.close()
        return resultList

    def testEntityInfo(self):
        """
        test creating entityInfo from the sample record
        """
        listOfRecords = Sample.getRoyals()
        entityInfo = EntityInfo(listOfRecords[:3], "Person", "name", debug=True)
        self.assertEqual(
            "CREATE TABLE Person(name TEXT PRIMARY KEY,born DATE,numberInLine INTEGER,wikidataurl TEXT,age FLOAT,ofAge BOOLEAN,lastmodified TIMESTAMP)",
            entityInfo.createTableCmd,
        )
        self.assertEqual(
            "INSERT INTO Person (name,born,numberInLine,wikidataurl,age,ofAge,lastmodified) values (:name,:born,:numberInLine,:wikidataurl,:age,:ofAge,:lastmodified)",
            entityInfo.insertCmd,
        )
        self.sqlDB = SQLDB(debug=self.debug, errorDebug=True)
        entityInfo = self.sqlDB.createTable(
            listOfRecords[:10], entityInfo.name, entityInfo.primaryKey
        )
        tableList = self.sqlDB.getTableList()
        if self.debug:
            print(tableList)
        self.assertEqual(1, len(tableList))
        personTable = tableList[0]
        self.assertEqual("Person", personTable["name"])
        self.assertEqual(7, len(personTable["columns"]))
        uml = UML()
        plantUml = uml.tableListToPlantUml(
            tableList, packageName="Royals", withSkin=False
        )
        if self.debug:
            print(plantUml)
        expected = """package Royals {
  class Person << Entity >> {
   age : FLOAT 
   born : DATE 
   lastmodified : TIMESTAMP 
   name : TEXT <<PK>>
   numberInLine : INTEGER 
   ofAge : BOOLEAN 
   wikidataurl : TEXT 
  }
}
"""
        self.assertEqual(expected, plantUml)

        # testGeneralization
        listOfRecords = [
            {"name": "Royal family", "country": "UK", "lastmodified": datetime.now()}
        ]
        entityInfo = self.sqlDB.createTable(listOfRecords[:10], "Family", "name")
        tableList = self.sqlDB.getTableList()
        self.assertEqual(2, len(tableList))
        uml = UML()
        plantUml = uml.tableListToPlantUml(
            tableList, generalizeTo="PersonBase", withSkin=False
        )
        if self.debug:
            print(plantUml)
        expected = """class PersonBase << Entity >> {
 lastmodified : TIMESTAMP 
 name : TEXT <<PK>>
}
class Person << Entity >> {
 age : FLOAT 
 born : DATE 
 numberInLine : INTEGER 
 ofAge : BOOLEAN 
 wikidataurl : TEXT 
}
class Family << Entity >> {
 country : TEXT 
}
PersonBase <|-- Person
PersonBase <|-- Family
"""
        self.assertEqual(expected, plantUml)

    def testIssue15(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/15

        auto create view ddl in mergeschema

        """
        self.sqlDB = SQLDB(debug=self.debug, errorDebug=self.debug)
        listOfRecords = Sample.getRoyals()
        entityInfo = EntityInfo(listOfRecords[:3], "Person", "name", debug=self.debug)
        entityInfo = self.sqlDB.createTable(
            listOfRecords[:10], entityInfo.name, entityInfo.primaryKey
        )
        listOfRecords = [
            {"name": "Royal family", "country": "UK", "lastmodified": datetime.now()}
        ]
        entityInfo = self.sqlDB.createTable(listOfRecords[:10], "Family", "name")
        tableList = self.sqlDB.getTableList()
        viewDDL = Schema.getGeneralViewDDL(tableList, "PersonBase")
        if self.debug:
            print(viewDDL)
        expected = """CREATE VIEW PersonBase AS 
  SELECT name,lastmodified FROM Person
UNION
  SELECT name,lastmodified FROM Family"""
        self.assertEqual(expected, viewDDL)
        pass

    def testUniqueConstraint(self):
        """
        test for https://github.com/WolfgangFahl/pyLoDStorage/issues/4
        sqlite3.IntegrityError: UNIQUE constraint failed: ... show debug info
        """
        listOfDicts = [
            {"name": "John Doe"},
            {"name": "Frank Doe"},
            {"name": "John Doe"},
            {"name": "Tim Doe"},
        ]
        sqlDB = SQLDB(debug=self.debug, errorDebug=True)
        entityInfo = sqlDB.createTable(listOfDicts[:10], "Does", "name")
        try:
            sqlDB.store(listOfDicts, entityInfo, executeMany=False)
            self.fail("There should be an exception")
        except Exception as ex:
            expected = """INSERT INTO Does (name) values (:name)
failed:UNIQUE constraint failed: Does.name
record  #3={'name': 'John Doe'}"""
            errMsg = str(ex)
            self.assertEqual(expected, errMsg)

    def testSqlite3(self):
        """
        test sqlite3 with a few records from the royal family
        """
        listOfRecords = Sample.getRoyals()
        resultList = self.checkListOfRecords(
            listOfRecords, "Person", "name", debug=True
        )
        if self.debug:
            print(resultList)
        self.assertEqual(listOfRecords, resultList)

    def testIssue13_setNoneValue(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/13
        set None value for undefined LoD entries
        """
        listOfRecords = [
            {"make": "Ford", "model": "Model T", "color": "black"},
            {"make": "VW", "model": "beetle"},
        ]
        entityName = "Car"
        primaryKey = "Model"
        resultList = self.checkListOfRecords(
            listOfRecords, entityName, primaryKey, fixNone=True
        )
        if self.debug:
            print(resultList)

    def testIssue14_execute(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/14

        offer execute wrapper directly via sqlDB
        """
        sqlDB = SQLDB()
        ddl = """
        CREATE TABLE contacts (
            contact_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL
        )
        """
        sqlDB.execute(ddl)
        tableList = sqlDB.getTableList()
        if self.debug:
            print(tableList)
        self.assertEqual(1, len(tableList))
        self.assertEqual("contacts", tableList[0]["name"])

    def testIssue41(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/41
        improve error message when create table command fails
        """
        listOfRecords = [{"name": "value", "py/object": "datetime.time"}]
        self.sqlDB = SQLDB(debug=self.debug, errorDebug=True)
        try:
            _entityInfo = self.sqlDB.createTable(listOfRecords[:1], "Invalid", "name")
            self.fail("There should be an exception")
        except Exception as ex:
            self.assertTrue("CREATE TABLE Invalid" in str(ex))

    def testBindingError(self):
        """
        test list of Records with incomplete record leading to
        "You did not supply a value for binding 2"
        see https://bugs.python.org/issue41638
        """
        listOfRecords = [{"name": "Pikachu", "type": "Electric"}, {"name": "Raichu"}]
        for executeMany in [True, False]:
            try:
                self.checkListOfRecords(
                    listOfRecords, "Pokemon", "name", executeMany=executeMany
                )
                self.fail("There should be an exception")
            except Exception as ex:
                if self.debug:
                    print(str(ex))
                self.assertTrue("no value supplied for column" in str(ex))

    def testListOfCities(self):
        """
        test sqlite3 with some 120000 city records
        """
        listOfRecords = Sample.getCities()
        for fixDates in [True, False]:
            retrievedList = self.checkListOfRecords(
                listOfRecords, "City", fixDates=fixDates
            )
            self.assertEqual(len(listOfRecords), len(retrievedList))

    def testQueryParams(self):
        """
        test Query Params
        """
        listOfDicts = [
            {"city": "New York", "country": "US"},
            {"city": "Amsterdam", "country": "NL"},
            {"city": "Paris", "country": "FR"},
        ]
        sqlDB = SQLDB(debug=self.debug, errorDebug=True)
        entityInfo = sqlDB.createTable(listOfDicts[:10], "cities", "city")
        sqlDB.store(listOfDicts, entityInfo, executeMany=False)
        query = "SELECT * from cities WHERE country in (?)"
        params = ("FR",)
        frCities = sqlDB.query(query, params)
        if self.debug:
            print(frCities)
        self.assertEqual([{"city": "Paris", "country": "FR"}], frCities)

    def testSqllite3Speed(self):
        """
        test sqlite3 speed with some 100000 artificial sample records
        consisting of two columns with a running index
        """
        limit = 100000
        listOfRecords = Sample.getSample(limit)
        self.checkListOfRecords(listOfRecords, "Sample", "pKey")

    def testIssue87AllowUsingQueryWithGenerator(self):
        """
        test the query gen approach
        """
        debug = self.debug
        # debug=True
        sqlDB = self.getSampleTableDB(sampleSize=5)
        sqlQuery = "select * FROM sample"
        for cindex, record in enumerate(sqlDB.queryGen(sqlQuery)):
            if debug:
                print(record)
            self.assertEqual(cindex, record["cindex"])

    def testBackup(self):
        """
        test creating a backup of the SQL database
        """
        if sys.version_info >= (3, 7):
            listOfRecords = Sample.getCities()
            self.checkListOfRecords(listOfRecords, "City", fixDates=True, doClose=False)
            backupDB = "/tmp/testSqlite.db"
            showProgress = 200 if self.debug else 0
            self.sqlDB.backup(backupDB, profile=self.debug, showProgress=showProgress)
            size = os.stat(backupDB).st_size
            if self.debug:
                print("size of backup DB is %d" % size)
            self.assertTrue(size > 600000)
            self.sqlDB.close()
            # restore
            ramDB = SQLDB.restore(
                backupDB, SQLDB.RAM, profile=self.debug, showProgress=showProgress
            )
            entityInfo = EntityInfo(listOfRecords[:50], "City", debug=self.debug)
            allCities = ramDB.queryAll(entityInfo)
            self.assertEqual(len(allCities), len(listOfRecords))

    def testCopy(self):
        """
        test copying databases into another database
        """
        dbFile = "/tmp/DAWT_Sample3x1000.db"
        copyDB = SQLDB(dbFile)
        for sampleNo in range(3):
            listOfRecords = Sample.getSample(1000)
            self.checkListOfRecords(
                listOfRecords, "Sample_%d_1000" % sampleNo, "pKey", doClose=False
            )
            self.sqlDB.copyTo(copyDB)
        size = os.stat(dbFile).st_size
        if self.debug:
            print("size of copy DB is %d" % size)
        self.assertTrue(size > 70000)
        tableList = copyDB.getTableList()
        if self.debug:
            print(tableList)
        for sampleNo in range(3):
            self.assertEqual("Sample_%d_1000" % sampleNo, tableList[sampleNo]["name"])
        # check that database is writable
        # https://stackoverflow.com/a/44707371/1497139
        copyDB.execute("pragma user_version=0")

    @staticmethod
    def getSampleTableDB(
        withDrop=False, debug=False, failIfTooFew=False, sampleSize=1000
    ):
        listOfRecords = Sample.getSample(sampleSize)
        sqlDB = SQLDB()
        entityName = "sample"
        primaryKey = "pKey"
        sampleRecordCount = sampleSize * 10
        sqlDB.debug = debug
        entityInfo = sqlDB.createTable(
            listOfRecords,
            entityName,
            primaryKey=primaryKey,
            withDrop=withDrop,
            sampleRecordCount=sampleRecordCount,
            failIfTooFew=failIfTooFew,
        )
        executeMany = True
        fixNone = True
        sqlDB.store(listOfRecords, entityInfo, executeMany=executeMany, fixNone=fixNone)
        return sqlDB

    def testIssue16(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/16
        allow to only warn if samplerecordcount is higher than number of available records
        """
        self.getSampleTableDB(withDrop=False, debug=True, failIfTooFew=False)
        try:
            self.getSampleTableDB(withDrop=True, debug=True, failIfTooFew=True)
            self.fail(
                "There should be an exception that too few sample records where provided"
            )
        except Exception as ex:
            self.assertTrue(
                "only 1000/10000 of needed sample records to createTable available"
                in str(ex)
            )

    def testIssue18(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/18
        """
        sqlDB = self.getSampleTableDB()
        tableDict = sqlDB.getTableDict()
        debug = self.debug
        # debug=True
        if debug:
            print(tableDict)
        self.assertTrue("sample" in tableDict)
        cols = tableDict["sample"]["columns"]
        self.assertTrue("pkey" in cols)

    def testIssue110(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/110
        """
        sqlDB = self.getSampleTableDB()
        sample1 = Sample.getSample(10)
        sample2 = Sample.getSample(10)
        sample1.extend(sample2)
        entityInfo = sqlDB.createTable(sample1, "sample1", "pkey")
        sqlDB.store(sample1, entityInfo=entityInfo, replace=True)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testSqllit3']
    unittest.main()
