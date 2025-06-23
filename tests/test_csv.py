"""
Created 2021

@author: wf
"""

import csv
import tempfile

from lodstorage.lod import LOD
from lodstorage.lod_csv import CSV
from lodstorage.sample2 import Sample
from tests.basetest import Basetest


class TestCSV(Basetest):
    """
    Tests functionalities for the conversion between csv and list od dicts (LoD)
    """

    def setUp(self):
        super().setUp(debug=False)
        self.csv_converter = CSV.get_instance()
        self.temp_dir = tempfile.TemporaryDirectory(prefix="test_pyLoDStorage_")
        self.testFolder = self.temp_dir.name
        self.csvStr = '"pageTitle","name","label"\r\n"page_1","Test Page 1","1"\r\n"page_2","Test Page 2","2"\r\n'
        self.csvStrMinimal = (
            "pageTitle,name,label\r\npage_1,Test Page 1,1\r\npage_2,Test Page 2,2\r\n"
        )
        self.csvLOD = [
            {"pageTitle": "page_1", "name": "Test Page 1", "label": "1"},
            {"pageTitle": "page_2", "name": "Test Page 2", "label": "2"},
        ]
        self.quoting_configs = [(csv.QUOTE_MINIMAL, self.csvStrMinimal)]

    def tearDown(self) -> None:
        super().tearDown()
        self.temp_dir.cleanup()

    def testRoyals(self):
        """test conversion of royals with different quoting modes"""
        inlod = Sample.getRoyals()
        for quoting, _ in self.quoting_configs:
            with self.subTest(quoting=quoting):
                csv_output = self.csv_converter.toCSV(inlod, quoting=quoting)
                if self.debug:
                    print(f"Quoting {quoting}: {csv_output}")
                outlod = self.csv_converter.fromCSV(csv_output, quoting=quoting)
                if self.debug:
                    print(f"Parsed: {outlod}")

    def test_to_csv(self):
        """tests if LoD is correctly converted to csv str with various quoting"""
        for quoting, expected in self.quoting_configs:
            with self.subTest(quoting=quoting):
                actual = self.csv_converter.toCSV(self.csvLOD, quoting=quoting)
                self.assertEqual(expected, actual)

    def test_to_csv_incomplete_dicts(self):
        """tests if LoD is correctly converted to csv even if some dicts are incomplete"""
        csvLOD = [
            {"pageTitle": "page_1", "label": "1"},
            {"pageTitle": "page_2", "name": "Test Page 2", "label": "2"},
        ]
        expected_cases = [
            (
                csv.QUOTE_MINIMAL,
                "pageTitle,label,name\r\npage_1,1,\r\npage_2,2,Test Page 2\r\n",
            )
        ]
        for quoting, expected in expected_cases:
            with self.subTest(quoting=quoting):
                actual = self.csv_converter.toCSV(csvLOD, quoting=quoting)
                self.assertEqual(expected, actual)

    def test_store_to_csvfile(self):
        """tests if LoD is correctly stored as csv file"""
        for quoting, expected_content in self.quoting_configs:
            with self.subTest(quoting=quoting):
                fileName = f"{self.testFolder}/test_store_{quoting}.csv"
                expected = expected_content.replace("\r", "")
                csvStr = self.csv_converter.toCSV(self.csvLOD, quoting=quoting)
                self.csv_converter.writeFile(csvStr, fileName)
                actual = self.csv_converter.readFile(fileName)
                self.assertEqual(expected, actual)

    def test_from_csv(self):
        """tests if csv is correctly parsed to LoD"""
        for quoting, csv_content in self.quoting_configs:
            with self.subTest(quoting=quoting):
                lod = self.csv_converter.fromCSV(csv_content, quoting=quoting)
                self.assertEqual(len(lod), 2)
                for key, value in self.csvLOD[0].items():
                    self.assertIn(key, lod[0])
                    self.assertEqual(value, lod[0][key])

    def test_restore_from_csvfile(self):
        """tests if lod is correctly restored from csv file"""
        for quoting, csv_content in self.quoting_configs:
            with self.subTest(quoting=quoting):
                fileName = f"{self.testFolder}/test_restore_{quoting}.csv"
                self.csv_converter.writeFile(csv_content, fileName)
                lod = self.csv_converter.fromCSV(
                    self.csv_converter.readFile(fileName), quoting=quoting
                )
                self.assertEqual(self.csvLOD, lod)

    def test_round_trip(self):
        """tests csv round trip: dict -> csv -> dict"""
        csvLOD = [
            {"pageTitle": "page_1", "name": "Test Page 1", "label": "1"},
            {"name": "Test Page 2", "label": "2"},
            {"pageTitle": "page_3", "label": "3"},
            {"pageTitle": "page_4", "name": "Test Page 4"},
        ]
        for quoting, _ in self.quoting_configs:
            with self.subTest(quoting=quoting):
                fileName = f"{self.testFolder}/round_trip_{quoting}.csv"
                csvStr = self.csv_converter.toCSV(csvLOD, quoting=quoting)
                self.csv_converter.writeFile(csvStr, fileName)
                actualLOD = self.csv_converter.fromCSV(
                    self.csv_converter.readFile(fileName), quoting=quoting
                )
                expectedLOD = csvLOD.copy()
                fields = LOD.getFields(expectedLOD)
                LOD.setNone4List(expectedLOD, fields)
                self.assertEqual(expectedLOD, actualLOD)

    def test_from_csv_without_header(self):
        """tests if csv string without embedded headers is parsed correctly"""
        test_cases = [
            (csv.QUOTE_MINIMAL, "page_1,Test Page 1,1\r\npage_2,Test Page 2,2\r\n")
        ]
        headerNames = ["pageTitle", "name", "label"]
        for quoting, csv_content in test_cases:
            with self.subTest(quoting=quoting):
                actualLOD = self.csv_converter.fromCSV(
                    csv_content, headerNames, quoting=quoting
                )
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
        for quoting, _ in self.quoting_configs:
            with self.subTest(quoting=quoting):
                actualCSVStr = self.csv_converter.toCSV(csvLOD, quoting=quoting)
                actualLOD = self.csv_converter.fromCSV(actualCSVStr, quoting=quoting)
                self.assertEqual(csvLOD, actualLOD)
