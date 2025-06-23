"""
Created 2021

@author: wf
"""

import csv
import io
from typing import Any, Dict, List

from lodstorage.lod import LOD


class CSV:
    """
    helper for converting data in csv format to list of dicts (LoD) and vice versa
    """

    _instance = None

    def __new__(cls, dialect: str = "excel", quoting: int = csv.QUOTE_NONNUMERIC):
        """
        constructor to set dialect and quoting defaults
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.dialect = dialect
            cls._instance.quoting = quoting
        return cls._instance

    @classmethod
    def get_instance(cls, dialect: str = "excel", quoting: int = csv.QUOTE_NONNUMERIC):
        """Get singleton instance of CSV class"""
        return cls(dialect, quoting)

    def restoreFromCSVFile(
        self, filePath: str, headerNames: List[str] = None, withPostfix: bool = False
    ) -> List[Dict[str, Any]]:
        """
        restore LOD from given csv file

        Args:
            filePath(str): file name
            headerNames(List[str]): Names of the headers that should be used. If None it is assumed that the header is given.
            withPostfix(bool): If False the file type is appended to given filePath. Otherwise file type MUST be given with filePath.

        Returns:
            List[Dict[str, Any]]: list of dicts (LoD) containing the content of the given csv file
        """
        if not withPostfix:
            filePath += ".csv"
        csvStr = self.readFile(filePath)
        lod = self.fromCSV(csvStr, headerNames)
        return lod

    def fromCSV(
        self,
        csvString: str,
        fields: List[str] = None,
        dialect: str = None,
        quoting: int = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        convert given csv string to list of dicts (LOD)

        Args:
            csvString(str): csv string that should be converted to LOD
            fields(List[str]): Names of the headers that should be used. If None it is assumed that the header is given.
            dialect(str): CSV dialect to use
            quoting(int): CSV quoting behavior

        Returns:
            List[Dict[str, Any]]: list of dicts (LoD) containing the content of the given csv string
        """
        if dialect is None:
            dialect = self.dialect
        if quoting is None:
            quoting = self.quoting
        csvStream = io.StringIO(csvString)
        reader = csv.DictReader(
            csvStream, fieldnames=fields, dialect=dialect, quoting=quoting, **kwargs
        )
        lod = list(reader)
        self.fixTypes(lod)
        return lod

    def storeToCSVFile(
        self, lod: List[Dict[str, Any]], filePath: str, withPostfix: bool = False
    ):
        """
        converts the given lod to CSV file.

        Args:
            lod(List[Dict[str, Any]]): lod that should be converted to csv file
            filePath(str): file name the csv should be stored to
            withPostfix(bool): If False the file type is appended to given filePath. Otherwise file type MUST be given with filePath.
        """
        if not withPostfix:
            filePath += ".csv"
        csvStr = self.toCSV(lod)
        self.writeFile(csvStr, filePath)

    def toCSV(
        self,
        lod: List[Dict[str, Any]],
        includeFields: List[str] = None,
        excludeFields: List[str] = None,
        dialect: str = None,
        quoting: int = None,
        **kwargs,
    ) -> str:
        """
        converts the given lod to CSV string.

        Args:
            lod(List[Dict[str, Any]]): lod that should be converted to csv string
            includeFields(List[str]): list of fields that should be included in the csv
            excludeFields(List[str]): list of fields that should be excluded from the csv
            dialect(str): CSV dialect to use
            quoting(int): CSV quoting behavior

        Returns:
            str: csv string of the given lod
        """
        if dialect is None:
            dialect = self.dialect
        if quoting is None:
            quoting = self.quoting
        if lod is None:
            return ""
        if excludeFields is not None:
            lod = LOD.filterFields(lod, excludeFields)
        if includeFields is None:
            fields = LOD.getFields(lod)
        else:
            fields = includeFields
            lod = LOD.filterFields(lod, includeFields, reverse=True)
        csvStream = io.StringIO()
        dict_writer = csv.DictWriter(
            csvStream, fieldnames=fields, dialect=dialect, quoting=quoting, **kwargs
        )
        dict_writer.writeheader()
        dict_writer.writerows(lod)
        csvString = csvStream.getvalue()
        return csvString

    def readFile(self, filename: str) -> str:
        """
        Reads the given filename and returns it as string

        Args:
            filename(str): Name of the file that should be returned as string

        Returns:
            str: Content of the file as string
        """
        with open(filename, "r") as file:
            content = file.read()
        return content

    def writeFile(self, content: str, filename: str):
        """
        Write the given str to the given filename

        Args:
            content(str): string that should be written into the file
            filename(str): Name of the file the given str should be written to
        """
        with open(filename, "w") as file:
            file.write(content)

    def fixTypes(self, lod: List[Dict[str, Any]]) -> None:
        """
        fixes the types of the given LoD.

        Args:
            lod(List[Dict[str, Any]]): List of dictionaries to fix types for
        """
        for record in lod:
            for key, value in record.items():
                if value == "":
                    record[key] = None
