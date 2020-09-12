'''
Created on 2020-09-12

@author: wf
'''
import datetime
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
        
    def addType(self,field,valueType):
        '''
        add the python type for the given field to the typeMap
        
        Args:
           field(string): the name of the field
           
           valueType(type): the python type of the field
        '''
        if not field in self.typeMap:
            self.typeMap[field]=valueType
            
    def getTypes(self,sampleRecords,limit=10):   
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
                    self.addType(key,valueType)            
        