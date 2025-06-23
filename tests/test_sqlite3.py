"""
Created on 2020-08-24

@author: wf
"""

import logging
import os
import sys
import time
from datetime import datetime, timezone
from io import StringIO

from lodstorage.sample2 import Sample
from lodstorage.schema import Schema
from lodstorage.sql import SQLDB, EntityInfo
from lodstorage.sqlite_api import SQLiteApiFixer
from lodstorage.uml import UML
from tests.basetest import Basetest


class TestSQLDB(Basetest):
    """
    Test the SQLDB database wrapper
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        logging.basicConfig(level=logging.WARNING)
        self.logger = logging.getLogger()

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

           listOfRecords (list): a list of dicts that contain the data to be stored
           entityName (string): the name of the entity type to be used as a table name
           primaryKey (string): the name of the key / column to be used as a primary key
           executeMany (boolean): True if executeMany mode of sqlite3 should be used
           fixNone (boolean): fix dict entries that are undefined to have a "None" entry
           debug (boolean): True if debug information e.g. CREATE TABLE and INSERT INTO commands should be shown
           doClose å(boolean): True if the connection should be closed

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
        debug = self.debug
        # debug=True
        listOfRecords = Sample.getRoyals()
        entityInfo = EntityInfo(
            listOfRecords[:3], "Person", "name", debug=debug, quiet=not debug
        )
        self.assertEqual(
            "CREATE TABLE Person(name TEXT PRIMARY KEY,wikidata_id TEXT,number_in_line INTEGER,born_iso_date TEXT,died_iso_date TEXT,lastmodified_iso TEXT,age INTEGER,of_age BOOLEAN,wikidata_url TEXT)",
            entityInfo.createTableCmd,
        )
        self.assertEqual(
            "INSERT INTO Person (name,wikidata_id,number_in_line,born_iso_date,died_iso_date,lastmodified_iso,age,of_age,wikidata_url) values (:name,:wikidata_id,:number_in_line,:born_iso_date,:died_iso_date,:lastmodified_iso,:age,:of_age,:wikidata_url)",
            entityInfo.insertCmd,
        )
        self.sqlDB = SQLDB(debug=self.debug, errorDebug=True)
        entityInfo = self.sqlDB.createTable(
            listOfRecords[:10], entityInfo.name, entityInfo.primaryKey
        )
        tableList = self.sqlDB.getTableList()
        if debug:
            print(tableList)
        self.assertEqual(1, len(tableList))
        personTable = tableList[0]
        self.assertEqual("Person", personTable["name"])
        self.assertEqual(9, len(personTable["columns"]))
        uml = UML()
        plantUml = uml.tableListToPlantUml(
            tableList, packageName="Royals", withSkin=False
        )
        if debug:
            print(plantUml)
        expected = """package Royals {
  class Person << Entity >> {
   age : INTEGER
   born_iso_date : TEXT
   died_iso_date : TEXT
   lastmodified_iso : TEXT
   name : TEXT <<PK>>
   number_in_line : INTEGER
   of_age : BOOLEAN
   wikidata_id : TEXT
   wikidata_url : TEXT
  }
}
"""
        self.assertEqual(expected.strip(), plantUml.strip())

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
        if debug:
            print(plantUml)
        expected = """class PersonBase << Entity >> {
 name : TEXT <<PK>>
}
class Person << Entity >> {
 age : INTEGER
 born_iso_date : TEXT
 died_iso_date : TEXT
 lastmodified_iso : TEXT
 number_in_line : INTEGER
 of_age : BOOLEAN
 wikidata_id : TEXT
 wikidata_url : TEXT
}
class Family << Entity >> {
 country : TEXT
 lastmodified : TIMESTAMP
}
PersonBase <|-- Person
PersonBase <|-- Family
"""
        self.maxDiff = None
        self.assertEqual(expected, plantUml)

    def testIssue15(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/15

        auto create view ddl in mergeschema

        """
        debug = self.debug
        # debug=True
        self.sqlDB = SQLDB(debug=self.debug, errorDebug=self.debug)
        listOfRecords = Sample.getRoyals()
        entityInfo = EntityInfo(listOfRecords[:3], "Person", "name", debug=self.debug)
        entityInfo = self.sqlDB.createTable(
            listOfRecords[:10], entityInfo.name, entityInfo.primaryKey
        )
        listOfRecords = [
            {"name": "Royal family", "country": "UK", "lastmodified_iso": "2022-09-08"}
        ]
        entityInfo = self.sqlDB.createTable(listOfRecords[:10], "Family", "name")
        tableList = self.sqlDB.getTableList()
        viewDDL = Schema.getGeneralViewDDL(tableList, "PersonBase")
        if debug:
            print(viewDDL)
        expected = """CREATE VIEW PersonBase AS
  SELECT name,lastmodified_iso FROM Person
UNION
  SELECT name,lastmodified_iso FROM Family"""
        self.assertEqual(expected.strip(), viewDDL.strip())
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
            listOfRecords, "Person", "name", debug=self.debug
        )
        debug = self.debug
        debug = True
        if debug:
            print(listOfRecords)
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
        self.getSampleTableDB(withDrop=False, debug=self.debug, failIfTooFew=False)
        try:
            self.getSampleTableDB(withDrop=True, debug=self.debug, failIfTooFew=True)
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

    def testIssue127And55(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/127
        sqlite3 default adapter and converter deprecated as of python 3.12

        https://github.com/WolfgangFahl/pyLoDStorage/issues/55
        datetime handling sqlite error should lead to warning and not raise an exception
        """
        # Reset singleton for test isolation
        SQLiteApiFixer._instance = None
        # Initialize the SQLiteApiFixer singleton
        SQLiteApiFixer.install(lenient=True)

        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        examples = [
            (b"not-a-timestamp", None),
            (
                b"725811479000000",
                datetime.fromtimestamp(725811479),
            ),  # Correct microseconds to seconds
            (b"1995-04-07 00:00:00", datetime(1995, 4, 7, 0, 0)),
        ]

        for val, expected in examples:
            with self.subTest(val=val):
                result = SQLiteApiFixer._instance.adapter.convert_timestamp(
                    val
                )  # Use the correct method from the singleton
                if expected is None:
                    self.assertIsNone(
                        result, "Expected None for invalid timestamp input"
                    )
                    # Check if the expected log message is in log_stream
                    log_content = log_stream.getvalue()
                    self.assertIn("Failed to convert", log_content)
                    # Clear log stream after checking
                    log_stream.truncate(0)
                    log_stream.seek(0)
                else:
                    self.assertEqual(
                        result,
                        expected,
                        f"Expected correct datetime conversion for {val}",
                    )

        # Remove the handler after the test to clean up
        logger.removeHandler(handler)
        log_stream.close()

    def testMultipleAdapters(self):
        """
        Test the behavior of multiple registered adapters for datetime.datetime
        https://github.com/WolfgangFahl/pyLoDStorage/issues/[issue_number]
        """

        # Test data
        naive_dt = datetime(2023, 1, 1, 12, 0, 0)
        aware_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        # Create SQLDB instance
        sqlDB = SQLDB(":memory:", debug=self.debug)

        # Create table and insert data
        entityInfo = sqlDB.createTable(
            [{"id": 1, "naive_date": naive_dt, "aware_date": aware_dt}],
            "test_dates",
            "id",
        )
        sqlDB.store(
            [{"id": 1, "naive_date": naive_dt, "aware_date": aware_dt}], entityInfo
        )

        # Query the data
        result = sqlDB.query("SELECT * FROM test_dates")[0]

        # Check if both datetime types are stored and retrieved correctly
        self.assertEqual(naive_dt, result["naive_date"])
        self.assertEqual(aware_dt, result["aware_date"])

        # Test with a timezone-aware datetime as the primary key
        entityInfo = sqlDB.createTable(
            [{"dt": aware_dt, "value": "test"}], "test_dates_pk", "dt"
        )
        sqlDB.store([{"dt": aware_dt, "value": "test"}], entityInfo)

        result = sqlDB.query("SELECT * FROM test_dates_pk")[0]
        self.assertEqual(aware_dt, result["dt"])

        sqlDB.close()
