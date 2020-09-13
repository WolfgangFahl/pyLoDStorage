'''
Created on 2020-09-12

@author: wf
'''
import datetime
import sys
class Types(object):
    '''
    Types
    
    holds entity meta Info 
    
    :ivar name(string): entity name = table name
    '''

    def __init__(self,name):
        '''
        Constructor
        '''
        self.name=name
        self.typeMap={}
        
    def addType(self,listName,field,valueType):
        '''
        add the python type for the given field to the typeMap
        
        Args:
           listName(string): the name of the list of the field
           field(string): the name of the field
           
           valueType(type): the python type of the field
        '''
        if listName not in self.typeMap:
            self.typeMap[listName]={}
        typeMap=self.typeMap[listName]    
        if not field in typeMap:
            typeMap[field]=valueType
            
    def getTypes(self,listName,sampleRecords,limit=10):   
        '''
        determine the types for the given sample records
        '''     
        for sampleRecord in sampleRecords[:limit]:
            for key,value in sampleRecord.items():
                valueType=None
                if value is None:
                    if len(sampleRecords)==1:
                        print("Warning sampleRecord field %s is None - using string as type" % key)
                        valueType=str
                else:
                    valueType=type(value)
                if valueType == str:
                    pass
                elif valueType == int:
                    pass
                elif valueType == float:
                    pass
                elif valueType == bool:
                    pass      
                elif valueType == datetime.date:
                    pass    
                elif valueType== datetime.datetime:
                    pass
                else:
                    if valueType is not None:
                        msg="warning: unsupported type %s for field %s " % (str(valueType),key)
                        print(msg)
                if valueType is not None:
                    self.addType(listName,key,valueType) 
                    
    def fixTypes(self,data):
        '''
        fix the types in the given data structure
        
        Args:
            data(dict): a dict representation returned from storage
            with list of Dicts as entries
        '''
        for listName in self.typeMap:
            if listName in data:
                self.fixListOfDicts(self.typeMap[listName],data[listName])
    
    def fixListOfDicts(self,typeMap,listOfDicts):
        '''
        fix the type in the given list of Dicts
        '''
        for record in listOfDicts:
            for keyValue in record.items():
                key,value=keyValue
                if key in typeMap:
                    valueType=typeMap[key]
                    if valueType==bool:
                        b= value in ['True','TRUE','true']
                        record[key]=b
                    elif valueType==datetime.date:
                        dt=datetime.datetime.strptime(value,"%Y-%m-%d") 
                        record[key]=dt.date()
                    elif valueType==datetime.datetime:
                        # see https://stackoverflow.com/questions/127803/how-do-i-parse-an-iso-8601-formatted-date
                        if sys.version_info >= (3, 7):
                            dtime=datetime.datetime.fromisoformat(value)
                        else:
                            dtime=datetime.datetime.strptime(value,"%Y-%m-%dT%H:%M:%S.%f")  
                        record[key]=dtime

                        
        