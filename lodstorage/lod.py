'''
Created on 2021-01-31

@author: wf
'''

class LOD(object):
    '''
    list of Dict aka Table
    '''

    def __init__(self,name):
        '''
        Constructor
        '''
        self.name=name
        pass
    
    @staticmethod
    def getFields(listOfDicts,sampleCount:int=None):
        if sampleCount is None:
            sampleCount=len(listOfDicts)
        fields=[]
        for row in listOfDicts:
            for key in row.keys():
                if not key in fields:
                    fields.append(key)
        return fields
        
    @staticmethod    
    def setNone4List(listOfDicts,fields):
        '''
        set the given fields to None for the records in the given listOfDicts
        if they are not set
        Args:
            listOfDicts(list): the list of records to work on
            fields(list): the list of fields to set to None 
        '''
        for record in listOfDicts:
            LOD.setNone(record, fields)
    
    @staticmethod
    def setNone(record,fields):
        '''
        make sure the given fields in the given record are set to none
        Args:
            record(dict): the record to work on
            fields(list): the list of fields to set to None 
        '''
        for field in fields:
            if not field in record:
                record[field]=None