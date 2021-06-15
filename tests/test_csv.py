import tempfile
from unittest import TestCase

from lodstorage.csv import CSV
from lodstorage.lod import LOD


class TestCSV(TestCase):
    '''
    Tests functionalities for the conversion between csv and list od dicts (LoD)
    '''

    def setUp(self) -> None:
        self.temp_dir=tempfile.TemporaryDirectory(prefix="test_pyLoDStorage_")
        self.testFolder=self.temp_dir.name
        self.csvStr="pageTitle,name,label\r\npage_1,Test Page 1,1\r\npage_2,Test Page 2,2\r\n"   # \r\n because the csv is in excel dialect
        self.csvLOD=[
            {"pageTitle": "page_1", "name": "Test Page 1", "label": "1"},
            {"pageTitle": "page_2", "name": "Test Page 2", "label": "2"}
        ]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_to_csv(self):
        '''tests if LoD is correctly converted to csv str'''
        expectedStr=self.csvStr
        actualStr=CSV.toCSV(self.csvLOD)
        self.assertEqual(expectedStr, actualStr)

    def test_to_csv_incomplete_dicts(self):
        '''
        tests if the LoD is correctly converted to csv even if some dicts are incomplete
        Note: incomplete dicts can lead to changes of the column orders of the csv string
        '''
        csvLOD = [
            {"pageTitle": "page_1", "label": "1"},
            {"pageTitle": "page_2", "name": "Test Page 2", "label": "2"}
        ]
        expectedStr = "pageTitle,label,name\r\npage_1,1,\r\npage_2,2,Test Page 2\r\n"
        actualStr=CSV.toCSV(csvLOD)
        self.assertEqual(expectedStr, actualStr)

    def test_store_to_csvfile(self):
        '''tests if LoD is correctly stored as csv file'''
        fileName="%s/test_store_to_csvfile.csv" % self.testFolder
        expectedStr=self.csvStr.replace("\r","")
        CSV.storeToCSVFile(self.csvLOD, fileName, True)
        actualStr=CSV.readFile(fileName)
        self.assertEqual(expectedStr, actualStr)

    def test_from_csv(self):
        '''tests if the csv is correctly parsed to an LoD'''
        expRecord=self.csvLOD[0]
        lod=CSV.fromCSV(self.csvStr)
        self.assertTrue(len(lod)==2)
        actualRecord=lod[0]
        for key, value in expRecord.items():
            self.assertTrue(key in actualRecord)
            self.assertEqual(expRecord[key], actualRecord[key])

    def test_restore_from_csvfile(self):
        '''tests if the lod is correctly restored from csv file'''
        fileName = "%s/test_restore_from_csvfile.csv" % self.testFolder
        CSV.writeFile(self.csvStr, fileName)
        lod=CSV.restoreFromCSVFile(fileName, withPostfix=True)
        self.assertEqual(self.csvLOD, lod)

    def test_round_trip(self):
        '''
        tests the csv round trip: dict -> csv -> dict
        Note: the inital dict has missing values it is expected that the final dict has the missing keys with None as value
        '''
        fileName = "%s/%s.csv" % (self.testFolder, self.test_round_trip.__name__)
        csvLOD = [
            {"pageTitle": "page_1", "name": "Test Page 1", "label": "1"},
            {"name": "Test Page 2", "label": "2"},
            {"pageTitle": "page_3", "label": "3"},
            {"pageTitle": "page_4", "name": "Test Page 4"}
        ]
        CSV.storeToCSVFile(csvLOD, fileName, withPostfix=True)
        actualLOD=CSV.restoreFromCSVFile(fileName, withPostfix=True)
        # build expected LOD
        expectedLOD=csvLOD.copy()
        fields = LOD.getFields(expectedLOD)
        LOD.setNone4List(expectedLOD, fields)
        self.assertEqual(expectedLOD, actualLOD)

    def test_from_csv_without_header(self):
        '''tests if csv string without embedded headers is parsed correctly'''
        csvStr = "page_1,Test Page 1,1\r\npage_2,Test Page 2,2\r\n"
        headerNames=["pageTitle", "name", "label"]
        actualLOD=CSV.fromCSV(csvStr, headerNames)
        self.assertEqual(self.csvLOD, actualLOD)