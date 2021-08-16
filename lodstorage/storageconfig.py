'''
Created on 2020-08-29

@author: wf
'''
from enum import Enum
from pathlib import Path
import os
class StoreMode(Enum):
    '''
    possible supported storage modes
    '''
    JSONPICKLE = 1      # JSON Pickle
    JSON = 2
    SQL = 3
    SPARQL = 4
    YAML = 5    
    
class StorageConfig(object):
    '''
    a storage configuration
    '''
           
    def getCachePath(self,ensureExists=True)->str:
        '''
        get the path to the default cache
        
        Args:
            name(str): the name of the cache to use
        '''
        
        cachedir=f"{self.cacheRootDir}/.{self.cacheDirName}"
        
        if ensureExists:
            if not os.path.exists(cachedir):
                os.makedirs(cachedir)
        return cachedir

    def __init__(self, mode=StoreMode.SQL,cacheRootDir:str=None,cacheDirName:str="lodstorage",cacheFile=None,withShowProgress=True,profile=True,debug=False,errorDebug=True):
        '''
        Constructor
        
        Args:
            mode(StoreMode): the storage mode e.g. sql
            cacheRootDir(str): the cache root directory to use - if None the home directory will be used
            cacheFile(string): the common cacheFile to use (if any)
            withShowProgress(boolean): True if progress should be shown
            profile(boolean): True if timing / profiling information should be shown
            debug(boolean): True if debugging information should be shown
            errorDebug(boolean): True if debug info should be provided on errors (should not be used for production since it might reveal data)
        '''
        if cacheRootDir is None:
            home = str(Path.home())
            self.cacheRootDir=f"{home}"
        else:
            self.cacheRootDir=cacheRootDir
        self.cacheDirName=cacheDirName
        self.mode=mode
        self.cacheFile=cacheFile
        self.profile=profile
        self.withShowProgress=withShowProgress
        self.debug=debug
        self.errorDebug=errorDebug
        
    @staticmethod
    def getDefault(debug=False):
        return StorageConfig.getSQL(debug)    
        
    @staticmethod
    def getSQL(debug=False):
        config=StorageConfig(mode=StoreMode.SQL,debug=debug)
        config.tableName=None
        return config
    
    @staticmethod
    def getJSON(debug=False):
        config=StorageConfig(mode=StoreMode.JSON,debug=debug)
        return config
    
    @staticmethod
    def getJsonPickle(debug=False):
        config=StorageConfig(mode=StoreMode.JSONPICKLE,debug=debug)
        return config
    
    @staticmethod
    def getSPARQL(prefix,endpoint,host,debug=False):
        config=StorageConfig(mode=StoreMode.SPARQL,debug=debug)
        config.prefix=prefix
        config.host=host
        config.endpoint=endpoint
        return config
    
    @staticmethod
    def getYaml(debug=False):
        config=StorageConfig(mode=StoreMode.YAML,debug=debug)
        return config
    
    