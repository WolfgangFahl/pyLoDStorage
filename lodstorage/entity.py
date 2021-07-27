'''
Created on 2020-08-19

@author: wf
'''
from lodstorage.yamlablemixin import YamlAbleMixin
from lodstorage.jsonpicklemixin import JsonPickleMixin
from lodstorage.storageconfig import StorageConfig, StoreMode
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB
from lodstorage.lod import LOD
from lodstorage.jsonable import JSONAbleList
import os
import time

class EntityManager(YamlAbleMixin, JsonPickleMixin,JSONAbleList):
    '''
    generic entity manager
    '''

    def __init__(self,name,entityName,entityPluralName:str,listName:str=None,clazz=None,tableName:str=None,primaryKey:str=None,config=None,debug=False):
        '''
        Constructor
        
        Args:
            name(string): name of this eventManager
            entityName(string): entityType to be managed e.g. Country
            entityPluralName(string): plural of the the entityType e.g. Countries
            config(StorageConfig): the configuration to be used if None a default configuration will be used
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
        self.config=config
        if config is None:
            config=StorageConfig.getDefault()
            if debug:
                config.debug=debug
        super(EntityManager, self).__init__(listName,clazz,tableName)
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
        if config is not None:
            cachedir=config.getCachePath() 
            if config.cacheFile is not None:
                return config.cacheFile
        ''' get the path to the file for my cached data '''  
        if mode is StoreMode.JSON or mode is StoreMode.JSONPICKLE:  
            extension=f".{mode.name.lower()}"
            cachepath=f"{cachedir}/{self.name}-{self.listName}{extension}" 
        elif mode is StoreMode.SPARQL:
            cachepath=f"SPQRL {config.endpoint}"    
        elif mode is StoreMode.SQL:
            cachepath=f"{cachedir}/{self.tableName}.db"
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
                sqlQuery="SELECT COUNT(*) AS count FROM %s" % config.tableName
                try:
                    sqlDB=self.getSQLDB(cacheFile)
                    countResult=sqlDB.query(sqlQuery)
                    count=countResult[0]['count']
                    result=count>100
                except Exception as ex:
                    # e.g. sqlite3.OperationalError: no such table: Event_crossref
                    pass      
        else:
            raise Exception("unsupported mode %s" % self.mode)            
        return result     
    
    def fromCache(self):
        '''
        get my entries from the cache
        
        Returns:
            the list of Dicts and as a side effect setting self.cacheFile
        '''
        if not self.isCached():
            listOfDicts=self.getListOfDicts()
            self.cacheFile=self.store(listOfDicts)
        else:
            # fromStore also sets self.cacheFile
            self.fromStore()
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
        
    def store(self,listOfDicts,limit=10000000,batchSize=250,cacheFile=None,fixNone=True,sampleRecordCount=1):
        ''' 
        store my entities 
        
        Args:
            listOfDicts(list): the list of dicts to store
            limit(int): maximumn number of records to store
            batchSize(int): size of batch for storing
            cacheFile(string): the name of the storage e.g path to JSON or sqlite3 file
            sampleRecordCount(int): the number of records to analyze for type information
        '''
        config=self.config
        mode=config.mode
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
            # @ FIXME make abstract 
            self.showProgress ("storing %d events for %s to %s" % (len(self.events),self.name,self.mode))    
            entityType="cr:Event"
            prefixes="PREFIX cr: <http://cr.bitplan.com/>"
            primaryKey="eventId"
            self.sparql.insertListOfDicts(listOfDicts, entityType, primaryKey, prefixes,limit=limit,batchSize=batchSize)
            self.showProgress ("store for %s done after %5.1f secs" % (self.name,time.time()-startTime))
        elif mode is StoreMode.SQL:
            startTime=time.time()
            if cacheFile is None:
                cacheFile=self.getCacheFile(config=self.config,mode=self.config.mode)
            sqldb=self.getSQLDB(cacheFile)
            self.showProgress ("storing %d %s for %s to %s:%s" % (len(listOfDicts),self.entityPluralName,self.name,config.mode,cacheFile)) 
            entityInfo=sqldb.createTable(listOfDicts, self.tableName, primaryKey=self.primaryKey,withDrop=True,sampleRecordCount=sampleRecordCount)   
            self.sqldb.store(listOfDicts, entityInfo,executeMany=self.executeMany,fixNone=fixNone)
            self.showProgress ("store for %s done after %5.1f secs" % (self.name,time.time()-startTime))
        else:
            raise Exception("unsupported store mode %s" % self.mode)  
        return cacheFile