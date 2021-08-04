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
            if listOfDicts is None:
                return None
            sampleCount=len(listOfDicts)
        fields=[]
        from lodstorage.jsonable import JSONAble
        for row in listOfDicts:
            if isinstance(row, JSONAble):
                row=vars(row)
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
                
    '''
    https://stackoverflow.com/questions/33542997/python-intersection-of-2-lists-of-dictionaries/33543164
    '''
    @staticmethod  
    def sortKey(d,key=None):
        ''' get the sort key for the given dict d with the given key
        '''
        if key is None:
            # https://stackoverflow.com/a/60765557/1497139
            return hash(tuple(d.items()))
        else:
            return d[key] 
        
    @staticmethod            
    def intersect(listOfDict1,listOfDict2,key=None):
        '''
        get the  intersection of the two lists of Dicts by the given key 
        '''
        i1=iter(sorted(listOfDict1, key=lambda k: LOD.sortKey(k, key)))
        i2=iter(sorted(listOfDict2, key=lambda k: LOD.sortKey(k, key)))
        c1=next(i1)
        c2=next(i2)
        lr=[]
        while True:
            try:
                val1=LOD.sortKey(c1,key)
                val2=LOD.sortKey(c2,key)
                if val1<val2:
                    c1=next(i1)
                elif val1>val2:
                    c2=next(i2)
                else:
                    lr.append(c1)
                    c1=next(i1)
                    c2=next(i2)
            except StopIteration:
                break     
        return lr    
    
    @staticmethod
    def addLookup(lookup,duplicates,record,value,withDuplicates:bool):
        '''
        add a single lookup result
        
        Args:
            lookup(dict): the lookup map
            duplicates(list): the list of duplicates
            record(dict): the current record
            value(object): the current value to lookup
            withDuplicates(bool): if True duplicates should be allowed and lists returned if False a separate duplicates
            list is created 
        '''
        if value in lookup:
            if withDuplicates:
                lookupResult=lookup[value]
                lookupResult.append(record)
            else:
                duplicates.append(record)
                return
        else:
            if withDuplicates:
                lookupResult=[record]
            else:
                lookupResult=record
        lookup[value]=lookupResult  
    
    @staticmethod
    def getLookup(lod:list,attrName:str,withDuplicates:bool=False):
        '''
        create a lookup dictionary by the given attribute name for the given list of dicts
        
        Args:
            lod(list): the list of dicts to get the lookup dictionary for
            attrName(str): the attribute to lookup
            withDuplicates(bool): whether to retain single values or lists
        
        Return:
            a dictionary for lookup
        '''
        lookup={}
        duplicates=[]
        for record in lod:
            value=None
            if isinstance(record,dict):
                if attrName in record:
                    value=record[attrName]
            else:
                if hasattr(record, attrName):
                    value=getattr(record,attrName)
            if value is not None:
                if isinstance(value,list):
                    for listValue in value:
                        LOD.addLookup(lookup,duplicates,record,listValue,withDuplicates)    
                else:
                    LOD.addLookup(lookup,duplicates,record,value,withDuplicates)    
        if withDuplicates:
            return lookup  
        else:
            return lookup,duplicates
    
    @classmethod
    def handleListTypes(cls,lod,doFilter=False,separator=","):
        '''
        handle list types in the given list of dicts
        
        Args:
            cls: this class
            lod(list): a list of dicts
            doFilter(bool): True if records containing lists value items should be filtered
            separator(str): the separator to use when converting lists
        '''
        # see https://stackoverflow.com/a/1207485/1497139
        for i in range(len(lod) - 1, -1, -1):
            record=lod[i]
            if isinstance(record,dict):
                for key in record:
                    value=record[key]
                    if isinstance(value,list):
                        if doFilter:
                            del lod[i]
                            continue
                        else:
                            newValue=separator.join(value)   
                            record[key]=newValue
        
    @staticmethod
    def filterFields(lod:list, fields:list, reverse:bool=False):
        '''
        filter the given LoD with the given list of fields by either limiting the LoD to the fields or removing the
        fields contained in the list depending on the state of the reverse parameter

        Args:
            lod(list): list of dicts from which the fields should be excluded
            fields(list): list of fields that should be excluded from the lod
            reverse(bool): If True limit dict to the list of given fields. Otherwise exclude the fields from the dict.

        Returns:
            LoD
        '''
        res=[]
        for record in lod:
            if reverse:
                recordReduced={d: record[d] for d in record if d in fields}
            else:
                recordReduced = {d: record[d] for d in record if d not in fields}
            res.append(recordReduced)
        return res