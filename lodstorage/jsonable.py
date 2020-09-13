'''This module has a class JSONAble for serialization of tables/list of dicts to and from JSON encoding

Created on 2020-09-03

@author: wf
'''
import json
import datetime
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