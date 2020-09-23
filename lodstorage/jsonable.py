'''This module has a class JSONAble for serialization of tables/list of dicts to and from JSON encoding

Created on 2020-09-03

@author: wf
'''
import json
import datetime
import sys
import re

class JSONAble(object):
    '''
    mixin to allow classes to be JSON serializable see
    
    - https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
    
    '''
    indent=4
    
    '''
    regular expression to be used for conversion from singleQuote to doubleQuote
    see https://stackoverflow.com/a/50257217/1497139
    '''
    singleQuoteRegex = re.compile('(?<!\\\\)\'')
 
    def __init__(self):
        '''
        Constructor
        '''
        
    @staticmethod 
    def singleQuoteToDoubleQuote(singleQuoted,useRegex=False):
        '''
        convert a single quoted string to a double quoted one
        
        Args:
            singleQuoted (str): a single quoted string e.g.
            
                .. highlight:: json
                
                {'cities': [{'name': "Upper Hell's Gate"}]}
                
            useRegex (boolean): True if a regular expression shall be used for matching
            
        Returns:
            string: the double quoted version of the string 
        
        Note:
            see
            - https://stackoverflow.com/questions/55600788/python-replace-single-quotes-with-double-quotes-but-leave-ones-within-double-q 

        '''
        if useRegex:
            doubleQuoted=JSONAble.singleQuoteToDoubleQuoteUsingRegex(singleQuoted)
        else:
            doubleQuoted=JSONAble.singleQuoteToDoubleQuoteUsingBracketLoop(singleQuoted)
        return doubleQuoted
    
    @staticmethod
    def singleQuoteToDoubleQuoteUsingRegex(singleQuoted):
        """
        convert a single quoted string to a double quoted one using a regular expression
        
        Args:
            singleQuoted(string): a single quoted string e.g. {'cities': [{'name': "Upper Hell's Gate"}]}
            useRegex(boolean): True if a regular expression shall be used for matching
        Returns:
            string: the double quoted version of the string e.g. 
        Note:
            see https://stackoverflow.com/a/50257217/1497139
        """
        doubleQuoted=JSONAble.singleQuoteRegex.sub('\"', singleQuoted)
        return doubleQuoted
    
    @staticmethod    
    def singleQuoteToDoubleQuoteUsingBracketLoop(singleQuoted):  
        """
        convert a single quoted string to a double quoted one using a regular expression
        
        Args:
            singleQuoted(string): a single quoted string e.g. {'cities': [{'name': "Upper Hell's Gate"}]}
            useRegex(boolean): True if a regular expression shall be used for matching
        Returns:
            string: the double quoted version of the string e.g. 
        Note:
            see https://stackoverflow.com/a/63862387/1497139
        
        """
        cList=list(singleQuoted)
        inDouble=False;
        inSingle=False;
        for i,c in enumerate(cList):
            #print ("%d:%s %r %r" %(i,c,inSingle,inDouble))
            if c=="'":
                if not inDouble:
                    inSingle=not inSingle
                    cList[i]='"'
            elif c=='"':
                inDouble=not inDouble
                inSingle=False
        doubleQuoted="".join(cList)    
        return doubleQuoted
    
    def storeToJsonFile(self,storeFilePrefix,tableName):
        '''
        store me with the given storeFilePrefix
        
        Args:
            storeFilePrefix(string): the prefix for the JSON file name
            tableName(string): the name of the attribute for which to store the type information
        '''
        JSONAble.storeJsonToFile(self.toJSON(), "%s.json" % storeFilePrefix)
        types=Types.forTable(self, tableName)
        JSONAble.storeJsonToFile(types.toJSON(), "%s-types.json" % storeFilePrefix)
       
    def restoreFromJsonFile(self,storeFilePrefix):
        '''
        restore me from the given storeFilePrefix
        
        Args:
            storeFilePrefix(string): the prefix for the JSON file name
        '''
        jsonStr=JSONAble.readJsonFromFile("%s.json" % storeFilePrefix)
        typesJson=JSONAble.readJsonFromFile("%s-types.json" % storeFilePrefix)
        types=Types(type(self).__name__)
        types.fromJson(typesJson)
        self.fromJson(jsonStr, types)
    
    @staticmethod
    def readJsonFromFile(jsonFilePath):
        '''
        read json string from the given jsonFilePath
        
        Args:
            jsonFilePath(string): the path of the file where to read the result from
             
        Returns:
            the JSON string read from the file
        '''
        with open(jsonFilePath,"r") as jsonFile:
            jsonStr=jsonFile.read()
        return jsonStr
        
    @staticmethod
    def storeJsonToFile(jsonStr,jsonFilePath):
        '''
        store the given json string to the given jsonFilePath
        
        Args:
            jsonStr(string): the string to store
            jsonFilePath(string): the path of the file where to store the result
            
        '''
        with open(jsonFilePath,"w") as jsonFile:
            jsonFile.write(jsonStr) 
    
    def fromJson(self,jsonStr,types=None):
        '''
        initialize me from the given JSON string
        
        Args:
            jsonStr(str): the JSON string
            fixType(Types): the types to be fixed
        '''
        data=json.loads(jsonStr)       
        if types is not None:
            types.fixTypes(data)                      
        self.__dict__=data
    
    def toJsonAbleValue(self,v):
        '''
        return the JSON able value of the given value v
        Args:
            v(object): the value to convert
        '''
        # objects have __dict__ hash tables which can be JSON-converted
        if (hasattr(v, "__dict__")):
            return v.__dict__
        elif isinstance(v,datetime.datetime):
            return v.isoformat()
        elif isinstance(v,datetime.date):
            return v.isoformat()
        else:
            return ""
        
    def toJSON(self):
        '''
        Returns:
            a recursive JSON dump of the dicts of my objects
        '''
        jsonStr=json.dumps(self, default=lambda v: self.toJsonAbleValue(v), 
            sort_keys=True, indent=JSONAble.indent)
        return jsonStr
        
    def getJSONValue(self,v):
        '''
        get the value of the given v as JSON
        
        Args:
            v(object): the value to get
            
        Returns:
            the the value making sure objects are return as dicts
        '''
        if (hasattr(v, "asJSON")):
            return v.asJSON(asString=False)
        elif type(v) is dict:
            return self.reprDict(v)
        elif type(v) is list:
            vlist=[]
            for vitem in v:
                vlist.append(self.getJSONValue(vitem))
            return vlist
        elif isinstance(v,datetime.datetime):
            return v.isoformat()
        elif isinstance(v,datetime.date):
            return v.isoformat()
        elif isinstance(v,bool):
            # convert True,False to -> true,false
            return str(v).lower()
        else:   
            return v
    
    def reprDict(self,srcDict):
        '''
        get the given srcDict as new dict with fields being converted with getJSONValue
        
        Args:
            scrcDict(dict): the source dictionary
        
        Returns
            dict: the converted dictionary
        '''
        d = dict()
        for a, v in srcDict.items():
            d[a]=self.getJSONValue(v)
        return d
    
    def asJSON(self,asString=True):
        '''
        recursively return my dict elements
        
        Args:
            asString(boolean): if True return my result as a string
        '''
        jsonDict=self.reprDict(self.__dict__)
        if asString:
            jsonStr=str(jsonDict)
            jsonStr = JSONAble.singleQuoteToDoubleQuote(jsonStr)
            return jsonStr
        return jsonDict
    
class Types(JSONAble):
    '''
    Types
    
    holds entity meta Info 
    
    :ivar name(string): entity name = table name
    '''

    typeName2Type={
    'bool': bool,
    'date': datetime.date,
    'datetime': datetime.datetime,
    'float': float,
    'int': int,
    'str': str
    
    }
    
    def __init__(self,name,debug=False):
        '''
        Constructor
        
        Args:
            name(str): the name of the type map
        '''
        self.name=name
        self.debug=debug
        self.typeMap={}
        
    @staticmethod
    def forTable(instance,listName,debug=False):
        '''
        get the types for the list of Dicts (table) in the given instance with the given listName
        Args:
            instance(object): the instance to inspect
            listName(string): the list of dicts to inspect
            debug(bool): True if debuggin information should be shown
        
        Returns:
            Types: a types object 
        '''
        clazz=type(instance)
        types=Types(clazz.__name__,debug=debug)
        types.getTypes(listName,instance.__dict__[listName])
        return types
        
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
                    self.addType(listName,key,valueType.__name__) 
                    
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
    
    def getType(self,typeName):
        '''
        get the type for the given type name
        '''
        if typeName in Types.typeName2Type:
            return Types.typeName2Type[typeName]
        else:
            if self.debug:
                print("Warning unsupported type %s" %typeName)
            return None
        
    def fixListOfDicts(self,typeMap,listOfDicts):
        '''
        fix the type in the given list of Dicts
        '''
        for record in listOfDicts:
            for keyValue in record.items():
                key,value=keyValue
                if key in typeMap:
                    valueType=self.getType(typeMap[key])
                    if valueType==bool:
                        if type(value)==str:
                            b=value in ['True','TRUE','true']
                        else:
                            b= value 
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