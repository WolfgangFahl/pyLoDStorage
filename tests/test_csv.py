import tempfile

from lodstorage.csv import CSV
from lodstorage.jsonable import JSONAble, JSONAbleList
from lodstorage.lod import LOD
from lodstorage.sample import Sample
from tests.basetest import Basetest


class TestCSV(Basetest):
    """
    Tests functionalities for the conversion between csv and list od dicts (LoD)
    """

    def setUp(self):
        super().setUp(debug=False)
        self.temp_dir = tempfile.TemporaryDirectory(prefix="test_pyLoDStorage_")
        self.testFolder = self.temp_dir.name
        self.csvStr = '"pageTitle","name","label"\r\n"page_1","Test Page 1","1"\r\n"page_2","Test Page 2","2"\r\n'  # \r\n because the csv is in excel dialect
        self.csvLOD = [
            {"pageTitle": "page_1", "name": "Test Page 1", "label": "1"},
            {"pageTitle": "page_2", "name": "Test Page 2", "label": "2"},
        ]

    def tearDown(self) -> None:
        super().tearDown()
        self.temp_dir.cleanup()

    def testRoyals(self):
        """
        test conversion of royals
        """
        return
        # TODO - fix me
        inlod = Sample.getRoyals()
        csv = CSV.toCSV(inlod)
        if self.debug:
            print(csv)
        # https://stackoverflow.com/questions/3717785/what-is-a-convenient-way-to-store-and-retrieve-boolean-values-in-a-csv-file
        outlod = CSV.fromCSV(csv)
        if self.debug:
            print(outlod)

    def test_to_csv(self):
        """tests if LoD is correctly converted to csv str"""
        expectedStr = self.csvStr
        actualStr = CSV.toCSV(self.csvLOD)
        self.assertEqual(expectedStr, actualStr)

    def test_to_csv_incomplete_dicts(self):
        """
        tests if the LoD is correctly converted to csv even if some dicts are incomplete
        Note: incomplete dicts can lead to changes of the column orders of the csv string
        """
        csvLOD = [
            {"pageTitle": "page_1", "label": "1"},
            {"pageTitle": "page_2", "name": "Test Page 2", "label": "2"},
        ]
        expectedStr = '"pageTitle","label","name"\r\n"page_1","1",""\r\n"page_2","2","Test Page 2"\r\n'
        actualStr = CSV.toCSV(csvLOD)
        self.assertEqual(expectedStr, actualStr)

    def test_store_to_csvfile(self):
        """tests if LoD is correctly stored as csv file"""
        fileName = "%s/test_store_to_csvfile.csv" % self.testFolder
        expectedStr = self.csvStr.replace("\r", "")
        CSV.storeToCSVFile(self.csvLOD, fileName, True)
        actualStr = CSV.readFile(fileName)
        self.assertEqual(expectedStr, actualStr)

    def test_from_csv(self):
        """tests if the csv is correctly parsed to an LoD"""
        expRecord = self.csvLOD[0]
        lod = CSV.fromCSV(self.csvStr)
        self.assertTrue(len(lod) == 2)
        actualRecord = lod[0]
        for key, value in expRecord.items():
            self.assertTrue(key in actualRecord)
            self.assertEqual(expRecord[key], actualRecord[key])

    def test_restore_from_csvfile(self):
        """tests if the lod is correctly restored from csv file"""
        fileName = "%s/test_restore_from_csvfile.csv" % self.testFolder
        CSV.writeFile(self.csvStr, fileName)
        lod = CSV.restoreFromCSVFile(fileName, withPostfix=True)
        self.assertEqual(self.csvLOD, lod)

    def test_round_trip(self):
        """
        tests the csv round trip: dict -> csv -> dict
        Note: the inital dict has missing values it is expected that the final dict has the missing keys with None as value
        """
        fileName = "%s/%s.csv" % (self.testFolder, self.test_round_trip.__name__)
        csvLOD = [
            {"pageTitle": "page_1", "name": "Test Page 1", "label": "1"},
            {"name": "Test Page 2", "label": "2"},
            {"pageTitle": "page_3", "label": "3"},
            {"pageTitle": "page_4", "name": "Test Page 4"},
        ]
        CSV.storeToCSVFile(csvLOD, fileName, withPostfix=True)
        actualLOD = CSV.restoreFromCSVFile(fileName, withPostfix=True)
        # build expected LOD
        expectedLOD = csvLOD.copy()
        fields = LOD.getFields(expectedLOD)
        LOD.setNone4List(expectedLOD, fields)
        self.assertEqual(expectedLOD, actualLOD)

    def test_from_csv_without_header(self):
        """tests if csv string without embedded headers is parsed correctly"""
        csvStr = '"page_1","Test Page 1","1"\r\n"page_2","Test Page 2","2"\r\n'
        headerNames = ["pageTitle", "name", "label"]
        actualLOD = CSV.fromCSV(csvStr, headerNames)
        self.assertEqual(self.csvLOD, actualLOD)

    def test_to_csv_delimiter_in_value(self):
        """tests if delimiter in dict value will not result in incorrect values"""
        csvLOD = [
            {
                "pageTitle": "page_1",
                "name": "Test Page 1, delimiter in value",
                "label": "1,000",
            }
        ]
        actualCSVStr = CSV.toCSV(csvLOD)
        actualLOD = CSV.fromCSV(actualCSVStr)
        self.assertEqual(csvLOD, actualLOD)

    def testCsvFromJSONAble(self):
        """
        tests generation of csv from list of JSONAble object
        """
        lod = [
            {"name": "Test", "label": 1},
            {"name": "Test 2", "label": 2},
            {"name": "Different", "location": "Munich"},
        ]
        jsonAbleList = JSONAbleList(clazz=JSONAble)
        jsonAbleList.fromLoD(lod)
        actualCsvString = CSV.toCSV(jsonAbleList.getList())
        expectedCsvString = '"name","label","location"\r\n"Test",1,""\r\n"Test 2",2,""\r\n"Different","","Munich"\r\n'
        self.assertEqual(actualCsvString, expectedCsvString)

    def testCsvFromJSONAbleExcludeFields(self):
        """
        tests generation of csv from list of JSONAble object with excluding specific fields (negative list)
        """
        lod = [
            {"name": "Test", "label": 1},
            {"name": "Test 2", "label": 2},
            {"name": "Different", "location": "Munich"},
        ]
        jsonAbleList = JSONAbleList(clazz=JSONAble)
        jsonAbleList.fromLoD(lod)
        actualCsvString = CSV.toCSV(jsonAbleList.getList(), excludeFields=["label"])
        expectedCsvString = (
            '"name","location"\r\n"Test",""\r\n"Test 2",""\r\n"Different","Munich"\r\n'
        )
        self.assertEqual(actualCsvString, expectedCsvString)

    def testCsvFromJSONAbleIncludeFields(self):
        """
        tests generation of csv from list of JSONAble object with including only specified fields (positive list)
        """
        lod = [
            {"name": "Test", "label": 1},
            {"name": "Test 2", "label": 2},
            {"name": "Different", "location": "Munich"},
        ]
        jsonAbleList = JSONAbleList(clazz=JSONAble)
        jsonAbleList.fromLoD(lod)
        actualCsvString = CSV.toCSV(
            jsonAbleList.getList(), includeFields=["name", "location"]
        )
        expectedCsvString = (
            '"name","location"\r\n"Test",""\r\n"Test 2",""\r\n"Different","Munich"\r\n'
        )
        self.assertEqual(actualCsvString, expectedCsvString)
