'''
Created on 2020-08-19

@author: wf
'''
from lodstorage.yamlablemixin import YamlAbleMixin
from lodstorage.jsonpicklemixin import JsonPickleMixin
from lodstorage.jsonable import JSONAble
from lodstorage.storageconfig import StorageConfig, StoreMode
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB
from lodstorage.lod import LOD
from lodstorage.jsonable import JSONAbleList
import sys
import os
import time

class EntityManager(YamlAbleMixin, JsonPickleMixin,JSONAbleList):
    '''
    generic entity manager
    '''

    def __init__(self,name,entityName,entityPluralName:str,listName:str=None,clazz=None,tableName:str=None,primaryKey:str=None,config=None,handleInvalidListTypes=False,filterInvalidListTypes=False,debug=False):
        '''
        Constructor
        
        Args:
            name(string): name of this eventManager
            entityName(string): entityType to be managed e.g. Country
            entityPluralName(string): plural of the the entityType e.g. Countries
            config(StorageConfig): the configuration to be used if None a default configuration will be used
            handleInvalidListTypes(bool): True if invalidListTypes should be converted or filtered
            filterInvalidListTypes(bool): True if invalidListTypes should be deleted
            debug(boolean): override debug setting when default of config is used via config=None
        '''
        self.name=name
        self.entityName=entityName
        self.entityPluralName=entityPluralName
        if listName is None:
            listName=entityPluralName
        if tableName is None:
            tableName=entityName
        self.primaryKey=primaryKey
        if config is None:
            config=StorageConfig.getDefault()
            if debug:
                config.debug=debug
        self.config=config
        super(EntityManager, self).__init__(listName=listName,clazz=clazz,tableName=tableName,handleInvalidListTypes=handleInvalidListTypes,filterInvalidListTypes=filterInvalidListTypes)
        cacheFile=self.getCacheFile(config=config,mode=config.mode)
        self.showProgress ("Creating %smanager(%s) for %s using cache %s" % (self.entityName,config.mode,self.name,cacheFile))
        if config.mode is StoreMode.SPARQL:
            if config.endpoint is None:
                raise Exception("no endpoint set for mode sparql") 
            self.endpoint=config.endpoint   
            self.sparql=SPARQL(config.endpoint,debug=config.debug,profile=config.profile)
        elif config.mode is StoreMode.SQL:
            self.executeMany=False # may be True when issues are fixed
            
    def storeMode(self):
        '''
        return my store mode
        '''
        return self.config.mode

    def showProgress(self,msg):
        ''' display a progress message 
            
            Args:
              msg(string): the message to display
        '''
        if self.config.withShowProgress:
            print (msg,flush=True)      
     
    def getCacheFile(self,config=None,mode=StoreMode.SQL):
        '''
        get the cache file for this event manager
        Args:
            config(StorageConfig): if None get the cache for my mode
            mode(StoreMode): the storeMode to use
        '''
        if config is None:
            config=self.config
        cachedir=config.getCachePath() 
        if config.cacheFile is not None:
            return config.cacheFile
        ''' get the path to the file for my cached data '''  
        if mode is StoreMode.JSON or mode is StoreMode.JSONPICKLE:  
            extension=f".{mode.name.lower()}"
            cachepath=f"{cachedir}/{self.name}-{self.listName}{extension}" 
        elif mode is StoreMode.SPARQL:
            cachepath=f"SPAQRL {self.name}:{config.endpoint}"    
        elif mode is StoreMode.SQL:
            cachepath=f"{cachedir}/{self.name}.db"
        else:
            cachepath=f"undefined cachepath for StoreMode {mode}"
        return cachepath     
    
    def removeCacheFile(self):
        '''  remove my cache file '''
        mode=self.config.mode
        if mode is StoreMode.JSON or mode is StoreMode.JSONPICKLE:
            cacheFile=self.getCacheFile(mode=mode)
            if os.path.isfile(cacheFile):
                os.remove(cacheFile)
                    
    def getSQLDB(self,cacheFile):
        '''
        get the SQL database for the given cacheFile
        
        Args:
            cacheFile(string): the file to get the SQL db from
        '''
        config=self.config
        sqldb=self.sqldb=SQLDB(cacheFile,debug=config.debug,errorDebug=config.errorDebug)
        return sqldb
    
    def initSQLDB(self,sqldb,listOfDicts=None,withCreate:bool=True,withDrop:bool=True,sampleRecordCount=-1):
        '''
        initialize my sql DB  
        
        Args:
            listOfDicts(list): the list of dicts to analyze for type information
            withDrop(boolean): true if the existing Table should be dropped
            withCreate(boolean): true if the create Table command should be executed - false if only the entityInfo should be returned
            sampleRecordCount(int): the number of records to analyze for type information
        Return:
            EntityInfo: the entity information such as CREATE Table command
        '''
        if listOfDicts is None:
            listOfDicts=JSONAble.getJsonTypeSamplesForClass(self.clazz)
        entityInfo=sqldb.createTable(listOfDicts, self.tableName, primaryKey=self.primaryKey,withCreate=withCreate,withDrop=withDrop,sampleRecordCount=sampleRecordCount) 
        return entityInfo
    
    def setNone(self,record,fields):
        '''
        make sure the given fields in the given record are set to none
        Args:
            record(dict): the record to work on
            fields(list): the list of fields to set to None 
        '''
        LOD.setNone(record,fields)
            
    def isCached(self):
        ''' check whether there is a file containing cached 
        data for me '''
        result=False
        config=self.config
        mode=self.config.mode
        if mode is StoreMode.JSON or mode is StoreMode.JSONPICKLE:
            result=os.path.isfile(self.getCacheFile(config=self.config,mode=mode))
        elif mode is StoreMode.SPARQL:
            # @FIXME - make abstract
            query=config.prefix+"""
SELECT  ?source (COUNT(?source) AS ?sourcecount)
WHERE { 
   ?event cr:Event_source ?source.
}
GROUP by ?source
"""                                 
            sourceCountList=self.sparql.queryAsListOfDicts(query)
            for sourceCount in sourceCountList:
                source=sourceCount['source'];
                recordCount=sourceCount['sourcecount']
                if source==self.name and recordCount>100:
                    result=True
        elif mode is StoreMode.SQL:
            cacheFile=self.getCacheFile(config=self.config,mode=StoreMode.SQL)
            if os.path.isfile(cacheFile):
                sqlQuery=f"SELECT COUNT(*) AS count FROM {self.tableName}" 
                try:
                    sqlDB=self.getSQLDB(cacheFile)
                    countResults=sqlDB.query(sqlQuery)
                    countResult=countResults[0]
                    count=countResult['count']
                    result=count>=0
                except Exception as ex:
                    msg=str(ex)
                    if self.debug:
                        print(msg,file=sys.stderr)
                        sys.stderr.flush()
                    # e.g. sqlite3.OperationalError: no such table: Event_crossref
                    pass      
        else:
            raise Exception("unsupported mode %s" % self.mode)            
        return result     
    
    def fromCache(self,force:bool=False,getListOfDicts=None,append=False,sampleRecordCount=-1):
        '''
        get my entries from the cache or from the callback provided
        
        Args:
            force(bool): force ignoring the cache
            getListOfDicts(callable): a function to call for getting the data 
            append(bool): True if records should be appended
            sampleRecordCount(int): the number of records to analyze for type information
            
        Returns:
            the list of Dicts and as a side effect setting self.cacheFile
        '''
        if not self.isCached() or force:
            startTime=time.time()
            self.showProgress(f"getting {self.entityPluralName} for {self.name} ...")
            if getListOfDicts is None:
                if hasattr(self, "getListOfDicts"):
                    getListOfDicts=self.getListOfDicts
                else:
                    raise  Exception("from Cache failed and no secondary cache via getListOfDicts specified")
            listOfDicts=getListOfDicts()
            duration=time.time()-startTime
            self.showProgress(f"got {len(listOfDicts)} {self.entityPluralName} in {duration:5.1f} s")   
            self.cacheFile=self.storeLoD(listOfDicts,append=append,sampleRecordCount=sampleRecordCount)
            self.setListFromLoD(listOfDicts)
        else:
            # fromStore also sets self.cacheFile
            listOfDicts=self.fromStore()
        return listOfDicts
        
    def fromStore(self,cacheFile=None,setList:bool=True)->list:
        '''
        restore me from the store
        Args:
            cacheFile(String): the cacheFile to use if None use the pre configured cachefile
            setList(bool): if True set my list with the data from the cache file
            
        Returns:
            list: list of dicts or JSON entitymanager
        '''
        startTime=time.time()
        if cacheFile is None:
            cacheFile=self.getCacheFile(config=self.config,mode=self.config.mode)
        self.cacheFile=cacheFile
        self.showProgress("reading %s for %s from cache %s" % (self.entityPluralName,self.name,cacheFile))
        mode=self.config.mode
        if mode is StoreMode.JSONPICKLE:   
            JSONem=JsonPickleMixin.readJsonPickle(cacheFile)
            if self.clazz is not None:
                listOfDicts=JSONem.getLoD()
            else:
                listOfDicts=JSONem.getList()
        elif mode is StoreMode.JSON:
            listOfDicts=self.readLodFromJsonFile(cacheFile)
            pass
        elif mode is StoreMode.SPARQL:
            # @FIXME make abstract
            eventQuery="""
PREFIX cr: <http://cr.bitplan.com/>
SELECT ?eventId ?acronym ?series ?title ?year ?country ?city ?startDate ?endDate ?url ?source WHERE { 
   OPTIONAL { ?event cr:Event_eventId ?eventId. }
   OPTIONAL { ?event cr:Event_acronym ?acronym. }
   OPTIONAL { ?event cr:Event_series ?series. }
   OPTIONAL { ?event cr:Event_title ?title. }
   OPTIONAL { ?event cr:Event_year ?year.  }
   OPTIONAL { ?event cr:Event_country ?country. }
   OPTIONAL { ?event cr:Event_city ?city. }
   OPTIONAL { ?event cr:Event_startDate ?startDate. }
   OPTIONAL { ?event cr:Event_endDate ?endDate. }
   OPTIONAL { ?event cr:Event_url ?url. }
   ?event cr:Event_source ?source FILTER(?source='%s').
}
""" % self.name        
            listOfDicts=self.sparql.queryAsListOfDicts(eventQuery)
        elif mode is StoreMode.SQL:
            sqlQuery="SELECT * FROM %s" % self.tableName
            sqlDB=self.getSQLDB(cacheFile)
            listOfDicts=sqlDB.query(sqlQuery)
            sqlDB.close()
            pass
        else:
            raise Exception("unsupported store mode %s" % self.mode)
          
        self.showProgress("read %d %s from %s in %5.1f s" % (len(listOfDicts),self.entityPluralName,self.name,time.time()-startTime))
        if setList:
            self.setListFromLoD(listOfDicts)
        return listOfDicts
    
    def getLoD(self):
        """
        Return the LoD of the entities in the list
        
        Return:
            list: a list of Dicts
            
        """
        lod= []
        for entity in self.getList():
            # TODO - optionally filter by samples
            lod.append(entity.__dict__)
        return lod
    
    def store(self,limit=10000000,batchSize=250,append=False,fixNone=True,sampleRecordCount=-1)->str:
        '''
        store my list of dicts
        
        Args:
            limit(int): maximum number of records to store per batch
            batchSize(int): size of batch for storing
            append(bool): True if records should be appended
            fixNone(bool): if True make sure the dicts are filled with None references for each record
            sampleRecordCount(int): the number of records to analyze for type information
        
        Return:
            str: The cachefile being used
        '''
        lod=self.getLoD()
        return self.storeLoD(lod,limit=limit,batchSize=batchSize,append=append,fixNone=fixNone,sampleRecordCount=sampleRecordCount)
        
    def storeLoD(self,listOfDicts,limit=10000000,batchSize=250,cacheFile=None,append=False,fixNone=True,sampleRecordCount=1)->str:
        ''' 
        store my entities 
        
        Args:
            listOfDicts(list): the list of dicts to store
            limit(int): maximum number of records to store
            batchSize(int): size of batch for storing
            cacheFile(string): the name of the storage e.g path to JSON or sqlite3 file
            append(bool): True if records should be appended
            fixNone(bool): if True make sure the dicts are filled with None references for each record
            sampleRecordCount(int): the number of records to analyze for type information
            
        Return:
            str: The cachefile being used
        '''
        config=self.config
        mode=config.mode
        if self.handleInvalidListTypes:
            LOD.handleListTypes(lod=listOfDicts,doFilter=self.filterInvalidListTypes)
        if mode is StoreMode.JSON or mode is StoreMode.JSONPICKLE:    
            if cacheFile is None:
                cacheFile=self.getCacheFile(config=self.config,mode=mode)
            self.showProgress (f"storing {len(listOfDicts)} {self.entityPluralName} for {self.name} to cache {cacheFile}")
            if mode is StoreMode.JSONPICKLE:
                self.writeJsonPickle(cacheFile)
            if mode is StoreMode.JSON:
                self.storeToJsonFile(cacheFile)
                pass
        elif mode is StoreMode.SPARQL:
            startTime=time.time()
            msg=f"storing {len(listOfDicts)} {self.entityPluralName} to {self.config.mode} ({self.config.endpoint})"
            self.showProgress (msg) 
            # @ FIXME make abstract /configurable
            entityType="cr:Event"
            prefixes=self.config.prefix
            self.sparql.insertListOfDicts(listOfDicts, entityType, self.primaryKey, prefixes,limit=limit,batchSize=batchSize)
            self.showProgress ("store for %s done after %5.1f secs" % (self.name,time.time()-startTime))
        elif mode is StoreMode.SQL:
            startTime=time.time()
            if cacheFile is None:
                cacheFile=self.getCacheFile(config=self.config,mode=self.config.mode)
            sqldb=self.getSQLDB(cacheFile)
            self.showProgress ("storing %d %s for %s to %s:%s" % (len(listOfDicts),self.entityPluralName,self.name,config.mode,cacheFile)) 
            if append:
                withDrop=False
                withCreate=False
            else:
                withDrop=True
                withCreate=True
            entityInfo=self.initSQLDB(sqldb,listOfDicts,withCreate=withCreate,withDrop=withDrop,sampleRecordCount=sampleRecordCount)
            self.sqldb.store(listOfDicts, entityInfo,executeMany=self.executeMany,fixNone=fixNone)
            self.showProgress ("store for %s done after %5.1f secs" % (self.name,time.time()-startTime))
        else:
            raise Exception("unsupported store mode %s" % self.mode)  
        return cacheFile