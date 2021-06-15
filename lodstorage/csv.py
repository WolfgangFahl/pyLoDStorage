import csv
import io

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
    def fromCSV(csvString:str, headerNames:list=None):
        '''
        convert given csv string to list of dicts (LOD)

        Args:
            csvStr(str): csv string that should be converted to LOD
            headerNames(list): Names of the headers that should be used. If None it is assumed that the header is given.

        Returns:
            list of dicts (LoD) containing the content of the given csv string
        '''
        reader = csv.DictReader(io.StringIO(csvString), headerNames)
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
    def toCSV(lod:list):
        '''
        converts the given lod to CSV string.

        Args:
            lod(list): lod that should be converted to csv string

        Returns:
            csv string of the given lod
        '''
        fields = LOD.getFields(lod)
        keys=fields
        csvString = ""
        csvStream = io.StringIO(csvString)
        dict_writer = csv.DictWriter(csvStream, keys)
        dict_writer.writeheader()
        dict_writer.writerows(lod)
        csvStream.seek(0)
        csvString = csvStream.read()
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
        content = ""
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

