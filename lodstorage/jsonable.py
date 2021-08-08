'''This module has a class JSONAble for serialization of tables/list of dicts to and from JSON encoding

Created on 2020-09-03

@author: wf
'''
import json
import datetime
import sys
import re

from lodstorage.lod import LOD


class JSONAbleSettings():
    '''
    settings for JSONAble - put in a separate class so they would not be
    serialized
    '''
    indent=4
    '''
    regular expression to be used for conversion from singleQuote to doubleQuote
    see https://stackoverflow.com/a/50257217/1497139
    '''
    singleQuoteRegex = re.compile('(?<!\\\\)\'')
    
class JSONAble(object):
    '''
    mixin to allow classes to be JSON serializable see
    
    - https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
    
    '''    
 
    def __init__(self):
        '''
        Constructor
        '''
        
    @classmethod
    def getPluralname(cls):
        return "%ss" % cls.__name__  
        
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
        doubleQuoted=JSONAbleSettings.singleQuoteRegex.sub('\"', singleQuoted)
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
    
    def getJsonTypeSamples(self):
        '''
        does my class provide a "getSamples" method?
        '''
        if hasattr(self, '__class__'):
            cls=self.__class__
            if isinstance(self, JSONAbleList) and not hasattr(cls, 'getSamples'):
                cls=self.clazz
            if hasattr(cls, 'getSamples'):
                getSamples=getattr(cls,'getSamples');
                if callable(getSamples):
                    return getSamples()
        return None
    
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
            
    def checkExtension(self,jsonFile:str,extension:str=".json")->str:
        '''
        make sure the jsonFile has the given extension e.g. ".json"
        
        Args:
            jsonFile(str): the jsonFile name - potentially without ".json" suffix
        
        Returns:
            str: the jsonFile name with ".json" as an extension guaranteed
        '''
        if not jsonFile.endswith(extension):
            jsonFile=f"{jsonFile}{extension}" 
        return jsonFile    
            
    def storeToJsonFile(self,jsonFile:str,extension:str=".json",limitToSampleFields:bool=False):
        '''
        store me to the given jsonFile
        
        Args:
            jsonFile(str): the JSON file name (optionally without extension)
            exension(str): the extension to use if not part of the jsonFile name
            limitToSampleFields(bool): If True the returned JSON is limited to the attributes/fields that are present in the samples. Otherwise all attributes of the object will be included. Default is False.
        '''
        jsonFile=self.checkExtension(jsonFile,extension)
        JSONAble.storeJsonToFile(self.toJSON(limitToSampleFields), jsonFile)

    def restoreFromJsonFile(self,jsonFile:str):
        '''
        restore me from the given jsonFile
        
        Args:
            jsonFile(string): the jsonFile to restore me from
        '''
        jsonFile=self.checkExtension(jsonFile)
        jsonStr=JSONAble.readJsonFromFile(jsonFile)
        self.fromJson(jsonStr)
        
    def fromJson(self,jsonStr):
        '''
        initialize me from the given JSON string
        
        Args:
            jsonStr(str): the JSON string
        '''
        jsonMap=json.loads(jsonStr) 
        self.fromDict(jsonMap) 
    
            
    def fromDict(self,data):
        '''
        initialize me from the given data
        
        Args:
            data: the dictionary to initalize me from
        '''        
        # https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-in-python-taking-union-o                 
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
        
    def toJSON(self, limitToSampleFields:bool=False):
        '''

        Args:
            limitToSampleFields(bool): If True the returned JSON is limited to the attributes/fields that are present in the samples. Otherwise all attributes of the object will be included. Default is False.

        Returns:
            a recursive JSON dump of the dicts of my objects
        '''
        data={}
        if limitToSampleFields:
            samples=self.getJsonTypeSamples()
            sampleFields = LOD.getFields(samples)
            if isinstance(self, JSONAbleList):
                limitedRecords=[]
                for record in self.__dict__[self.listName]:
                    limitedRecord={}
                    for key, value in record.__dict__.items():
                        if key in sampleFields:
                            limitedRecord[key] = value
                    limitedRecords.append(limitedRecord)
                data[self.listName]=limitedRecords
            else:
                for key,value in self.__dict__.items():
                    if key in sampleFields:
                        data[key]=value
        else:
            data=self
        jsonStr=json.dumps(data, default=lambda v: self.toJsonAbleValue(v),
            sort_keys=True, indent=JSONAbleSettings.indent)
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
    
    def asJSON(self,asString=True,data=None):
        '''
        recursively return my dict elements
        
        Args:
            asString(boolean): if True return my result as a string
        '''
        if data is None: 
            data=self.__dict__
        jsonDict=self.reprDict(data)
        if asString:
            jsonStr=str(jsonDict)
            jsonStr = JSONAble.singleQuoteToDoubleQuote(jsonStr)
            return jsonStr
        return jsonDict

    
class JSONAbleList(JSONAble):
    '''
    Container class 
    '''
    
    def __init__(self,listName:str=None,clazz=None,tableName:str=None,initList:bool=True,handleInvalidListTypes=False,filterInvalidListTypes=False):
        '''
        Constructor
        
        Args:
            listName(str): the name of the list attribute to be used for storing the List
            clazz(class): a class to be used for Object relational mapping (if any) 
            tableName(str): the name of the "table" to be used
            initList(bool): True if the list should be initialized
            handleInvalidListTypes(bool): True if invalidListTypes should be converted or filtered
            filterInvalidListTypes(bool): True if invalidListTypes should be deleted
        '''
        self.clazz=clazz
        self.handleInvalidListTypes=handleInvalidListTypes
        self.filterInvalidListTypes=filterInvalidListTypes
        if listName is None:
            if self.clazz is not None:
                listName=self.clazz.getPluralname()
            else:
                listName=self.__class__.name.lower()
        self.listName=listName
        if tableName is None:
            self.tableName=listName
        else:
            self.tableName=tableName
        if initList:
            self.__dict__[self.listName]=[]
            
    def getList(self):
        '''
        get my list
        '''
        return self.__dict__[self.listName]
    
    def setListFromLoD(self,lod:list)->list:
        '''
        set my list from the given list of dicts
        
        Args:
            lod(list) a raw record list of dicts
            
        Returns:
            list: a list of dicts if no clazz is set
                otherwise a list of objects
        '''
        # non OO mode
        if self.clazz is None:
            result = lod
            self.__dict__[self.listName] = result
        else:
            # ORM mode
            # TODO - handle errors
            self.fromLoD(lod,append=False)
        return self.getList()
    
    def getLoDfromJson(self,jsonStr:str,types=None,listName:str=None):
        '''
        get a list of Dicts form the given JSON String
        
        Args:
            jsonStr(str): the JSON string
            fixType(Types): the types to be fixed
        Returns:
            list: a list of dicts
        '''
        # read a data structe from the given JSON string
        lodOrDict=json.loads(jsonStr)       
        # it should be a list only of dict with my list
        if not isinstance(lodOrDict,dict) and listName is not None:
            lod=lodOrDict
        else:
            if self.listName in lodOrDict:
                # get the relevant list of dicts
                lod=lodOrDict[self.listName]
            else:
                msg=f"invalid JSON for getLoD from Json\nexpecting a list of dicts or a dict with '{self.listName}' as list\nfound a dict with keys: {lodOrDict.keys()} instead"
                raise Exception(msg)
        if types is not None:
            types.fixTypes(lod,self.listName)   
        return lod 

    def fromLoD(self,lod,append:bool=True,debug:bool=False):
        '''
        load my entityList from the given list of dicts
        
        Args:
            lod(list): the list of dicts to load
            append(bool): if True append to my existing entries
            
        Return:
            list: a list of errors (if any)
        
        '''
        errors=[]
        entityList=self.getList()
        if not append:
            del entityList[:]
        if self.handleInvalidListTypes:
            LOD.handleListTypes(lod=lod,doFilter=self.filterInvalidListTypes)

        for record in lod:
            # call the constructor to get a new instance
            try:
                entity=self.clazz()
                entity.fromDict(record)
                entityList.append(entity)
            except Exception as ex:
                error={
                    self.listName:record,
                    "error": ex
                }
                errors.append(error)
                if debug:
                    print(error)
        return errors
    
    def getLookup(self,attrName:str,withDuplicates:bool=False):
        '''
        create a lookup dictionary by the given attribute name
        
        Args:
            attrName(str): the attribute to lookup
            withDuplicates(bool): whether to retain single values or lists
        
        Return:
            a dictionary for lookup or a tuple dictionary,list of duplicates depending on withDuplicates
        '''
        return LOD.getLookup(self.getList(), attrName, withDuplicates)  
            
    def getJsonData(self):    
        '''
        get my Jsondata
        '''
        jsonData={
                self.listName:self.__dict__[self.listName]
            }
        return jsonData    
            
    def toJsonAbleValue(self,v):
        '''
        make sure we don't store our meta information
        clazz, tableName and listName but just the list we are holding
        '''
        if v==self:
            return self.getJsonData()
        else:
            return super().toJsonAbleValue(v)   
        
        
    def fromJson(self,jsonStr,types=None):
        '''
        initialize me from the given JSON string
        
        Args:
            jsonStr(str): the JSON string
            fixType(Types): the types to be fixed
        '''    
        lod=self.getLoDfromJson(jsonStr, types,listName=self.listName)
        self.setListFromLoD(lod)
          
        
    def asJSON(self,asString=True):
        jsonData=self.getJsonData()
        return super().asJSON(asString, data=jsonData)
    
    def restoreFromJsonFile(self,jsonFile:str)->list:
        '''
        read my list of dicts and restore it
        '''
        lod=self.readLodFromJsonFile(jsonFile)
        return self.setListFromLoD(lod)
        
        
    def restoreFromJsonStr(self,jsonStr:str)->list:
        '''
        restore me from the given jsonStr
        
        Args:
            jsonStr(str): the json string to restore me from
        '''
        lod=self.readLodFromJsonStr(jsonStr)
        return self.setListFromLoD(lod)
        
               
    def readLodFromJsonFile(self,jsonFile:str,extension:str=".json"):
        '''
        read the list of dicts from the given jsonFile
        
        Args:
            jsonFile(string): the jsonFile to read from
            
        Returns:
            list: a list of dicts
        '''
        jsonFile=self.checkExtension(jsonFile,extension)
        jsonStr=JSONAble.readJsonFromFile(jsonFile)
        lod=self.readLodFromJsonStr(jsonStr)
        return lod

    def readLodFromJsonStr(self, jsonStr)->list:
        '''
        restore me from the given jsonStr

        Args:
            storeFilePrefix(string): the prefix for the JSON file name
        '''
        if self.clazz is None:
            typeSamples = self.getJsonTypeSamples()
        else:
            typeSamples = self.clazz.getSamples()
        if typeSamples is None:
            types = None
        else:
            types = Types(self.listName)
            types.getTypes(self.listName, typeSamples, len(typeSamples))
        lod = self.getLoDfromJson(jsonStr, types,listName=self.listName)
        return lod

    
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
            items=sampleRecord.items()
            self.getTypesForItems(listName,items,warnOnNone=len(sampleRecords)==1)
          
    def getTypesForItems(self,listName,items,warnOnNone=False):  
            for key,value in items:
                valueType=None
                if value is None:
                    if warnOnNone:
                        if self.debug:
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
                    
    def fixTypes(self,lod:list,listName:str):
        '''
        fix the types in the given data structure
        
        Args:
            lod(list): a list of dicts
            listName(str): the types to lookup by list name
        '''
        for listName in self.typeMap:
            self.fixListOfDicts(self.typeMap[listName],lod)
    
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
                if value is None:
                    record[key]=None
                elif key in typeMap:
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
                        if isinstance(value,str):
                            if sys.version_info >= (3, 7):
                                dtime=datetime.datetime.fromisoformat(value)
                            else:
                                dtime=datetime.datetime.strptime(value,"%Y-%m-%dT%H:%M:%S.%f")  
                        else:
                            # TODO: error handling
                            dtime=None    
                        record[key]=dtime