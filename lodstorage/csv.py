import csv
import io

from lodstorage.jsonable import JSONAble
from lodstorage.lod import LOD


class CSV(LOD):
    '''
    helper for converting data in csv format to list of dicts (LoD) and vice versa
    '''

    @staticmethod
    def restoreFromCSVFile(filePath:str, headerNames:list=None, withPostfix:bool=False):
        '''
        restore LOD from given csv file

        Args:
            filePath(str): file name
            headerNames(list): Names of the headers that should be used. If None it is assumed that the header is given.
            withPostfix(bool): If False the file type is appended to given filePath. Otherwise file type MUST be given with filePath.

        Returns:
            list of dicts (LoD) containing the content of the given csv file
        '''
        if not withPostfix:
            filePath += ".csv"
        csvStr = CSV.readFile(filePath)
        lod = CSV.fromCSV(csvStr, headerNames)
        return lod

    @staticmethod
    def fromCSV(csvString:str, fields:list=None, delimiter=",",quoting=csv.QUOTE_NONNUMERIC, **kwargs):
        '''
        convert given csv string to list of dicts (LOD)

        Args:
            csvStr(str): csv string that should be converted to LOD
            headerNames(list): Names of the headers that should be used. If None it is assumed that the header is given.

        Returns:
            list of dicts (LoD) containing the content of the given csv string
        '''
        csvStream=io.StringIO(csvString)
        reader = csv.DictReader(csvStream, fieldnames=fields, delimiter=delimiter, quoting=quoting, **kwargs)
        lod=list(reader)
        CSV.fixTypes(lod)
        return lod

    @staticmethod
    def storeToCSVFile(lod:list, filePath:str, withPostfix:bool=False):
        '''
            converts the given lod to CSV file.

            Args:
                lod(list): lod that should be converted to csv file
                filePath(str): file name the csv should be stored to
                withPostfix(bool): If False the file type is appended to given filePath. Otherwise file type MUST be given with filePath.
            Returns:
                csv string of the given lod
        '''
        if not withPostfix:
            filePath += ".csv"
        csvStr=CSV.toCSV(lod)
        CSV.writeFile(csvStr, filePath)

    @staticmethod
    def toCSV(lod:list, includeFields:list=None, excludeFields:list=None, delimiter=",",quoting=csv.QUOTE_NONNUMERIC, **kwargs):
        '''
        converts the given lod to CSV string.
        For details about the csv dialect parameters see https://docs.python.org/3/library/csv.html#csv-fmt-params

        Args:
            lod(list): lod that should be converted to csv string
            includeFields(list): list of fields that should be included in the csv (positive list)
            excludeFields(list): list of fields that should be excluded from the csv (negative list)
            kwargs: csv dialect parameters
        Returns:
            csv string of the given lod
        '''
        if lod is None:
            return ''
        if isinstance(lod[0], JSONAble):
            lod=[vars(d) for d in lod]
        if excludeFields is not None:
            lod=LOD.filterFields(lod, excludeFields)
        if includeFields is None:
            fields = LOD.getFields(lod)
        else:
            fields=includeFields
            lod=LOD.filterFields(lod, includeFields, reverse=True)
        csvStream = io.StringIO()
        dict_writer = csv.DictWriter(csvStream, fieldnames=fields, delimiter=delimiter, quoting=quoting, **kwargs)
        dict_writer.writeheader()
        dict_writer.writerows(lod)
        csvString = csvStream.getvalue()
        return csvString

    @staticmethod
    def readFile(filename: str) -> str:
        """
        Reads the given filename and returns it as string
        Args:
            filename: Name of the file that should be returned as string

        Returns:
            Content of the file as string
        """
        with open(filename, 'r') as file:
            content = file.read()
        return content

    @staticmethod
    def writeFile(content:str, filename: str) -> str:
        """
        Write the given str to the given filename
        Args:
            content(str): string that should be written into the file
            filename: Name of the file the given str should be written to
        Returns:
            Nothing
        """
        with open(filename, 'w') as file:
            file.write(content)

    @staticmethod
    def fixTypes(lod:list):
        """
        fixes the types of the given LoD.

        """
        for record in lod:
            for key, value in record.items():
                # fix empty csv value: "cell1,,cell3" converts the second value to empty string instead of None
                if value == '':
                    record[key] = None

