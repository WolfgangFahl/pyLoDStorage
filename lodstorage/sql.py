'''
Created on 2020-08-24

@author: wf
'''
# python standard library
import sqlite3
import datetime
import io
import time
import sys
import re
from lodstorage.lod import LOD

class SQLDB(object):
    '''
    Structured Query Language Database wrapper
    
    :ivar dbname(string): name of the database
    :ivar debug(boolean): True if debug info should be provided
    :ivar errorDebug(boolean): True if debug info should be provided on errors (should not be used for production since it might reveal data)
    '''
    RAM=":memory:"

    def __init__(self,dbname:str=':memory:',connection=None,check_same_thread=True,debug=False, errorDebug=False):
        '''
        Construct me for the given dbname and debug
        
        Args:
        
           dbname(string): name of the database - default is a RAM based database
           connection(Connection): an optional connection to be reused 
           check_same_thread(boolean): True if object handling needs to be on the same thread see https://stackoverflow.com/a/48234567/1497139
           debug(boolean): if True switch on debug
           errorDebug(boolean): True if debug info should be provided on errors (should not be used for production since it might reveal data)
        '''
        self.dbname=dbname
        self.debug=debug
        self.errorDebug=errorDebug
        if connection is None:
            self.c=sqlite3.connect(dbname,detect_types=sqlite3.PARSE_DECLTYPES,check_same_thread=check_same_thread)
        else:
            self.c=connection
        
    def close(self):
        ''' close my connection '''
        self.c.close()
                
    def execute(self,ddlCmd):
        '''
        execute the given Data Definition Command
        
        Args:
            ddlCmd(string): e.g. a CREATE TABLE or CREATE View command
        '''
        self.c.execute(ddlCmd)
        
    def createTable(self,listOfRecords,entityName,primaryKey=None,withDrop=False,sampleRecordCount=1,failIfTooFew=True):
        '''
        derive  Data Definition Language CREATE TABLE command from list of Records by examining first recorda
        as defining sample record and execute DDL command
        
        auto detect column types see e.g. https://stackoverflow.com/a/57072280/1497139
        
        Args:
           listOfRecords(list): a list of Dicts
           entityName(string): the entity / table name to use
           primaryKey(string): the key/column to use as a  primary key
           withDrop(boolean): true if the existing Table should be dropped
           sampleRecords(int): number of sampleRecords expected and to be inspected
           failIfTooFew(boolean): raise an Exception if to few sampleRecords else warn only
        Returns:
           EntityInfo: meta data information for the created table
        '''
        l= len(listOfRecords)
        if sampleRecordCount<0:
            sampleRecordCount=l
        if l<sampleRecordCount:
            msg="only %d/%d of needed sample records to createTable available" % (l,sampleRecordCount)
            if failIfTooFew:
                raise Exception(msg)
            else:
                if self.debug:
                    print(msg,file=sys.stderr,flush=True)
        sampleRecords=listOfRecords[:sampleRecordCount]
        entityInfo=EntityInfo(sampleRecords,entityName,primaryKey,debug=self.debug)
        if withDrop:
            self.c.execute(entityInfo.dropTableCmd) 
        try:
            self.c.execute(entityInfo.createTableCmd)
        except sqlite3.OperationalError as oe:
            raise Exception(f"createTable failed with error {oe} for {entityInfo.createTableCmd}")
        return entityInfo
    
    def getDebugInfo(self,record,index,executeMany):
        '''
        get the debug info for the given record at the given index depending on the state of executeMany
        
        Args:
            record(dict): the record to show
            index(int): the index of the record
            executeMany(boolean): if True the record may be valid else not
        '''
        debugInfo=""
        if not executeMany:
            # shall we shoe the details of the record (which might be a security risk)
            if self.errorDebug:
                # show details of record
                debugInfo="\nrecord  #%d=%s" % (index,repr(record))
            else:
                # show only index
                debugInfo="\nrecord #%d" % index
        return debugInfo
        
       
    def store(self,listOfRecords,entityInfo,executeMany=False,fixNone=False):
        '''
        store the given list of records based on the given entityInfo
        
        Args:
          
           listOfRecords(list): the list of Dicts to be stored
           entityInfo(EntityInfo): the meta data to be used for storing
           executeMany(bool): if True the insert command is done with many/all records at once
           fixNone(bool): if True make sure empty columns in the listOfDict are filled with "None" values
        '''
        insertCmd=entityInfo.insertCmd
        record=None
        index=0
        try:
            if executeMany:
                if fixNone:
                    LOD.setNone4List(listOfRecords, entityInfo.typeMap.keys())
                self.c.executemany(insertCmd,listOfRecords)
            else:
                for record in listOfRecords:
                    index+=1
                    if fixNone:
                        LOD.setNone(record, entityInfo.typeMap.keys())
                    self.c.execute(insertCmd,record)
            self.c.commit()
        except sqlite3.ProgrammingError as pe:
            msg=pe.args[0]
            if "You did not supply a value for binding" in msg:
                columnIndex=int(re.findall(r'\d+',msg)[0])
                columnName=list(entityInfo.typeMap.keys())[columnIndex-1]
                debugInfo=self.getDebugInfo(record, index, executeMany)
                raise Exception("%s\nfailed: no value supplied for column '%s'%s" % (insertCmd,columnName,debugInfo))
            else:
                raise pe
        except sqlite3.InterfaceError as ie:
            msg=ie.args[0]
            if "Error binding parameter" in msg:
                columnName=re.findall(r':[_a-zA-Z]\w*',msg)[0]
                debugInfo=self.getDebugInfo(record, index, executeMany)
                raise Exception("%s\nfailed: error binding column '%s'%s" % (insertCmd,columnName,debugInfo))
            else:
                raise ie
        except Exception as ex:
            debugInfo=self.getDebugInfo(record, index, executeMany)
            msg="%s\nfailed:%s%s" % (insertCmd,str(ex),debugInfo)
            raise Exception(msg)
        
    def query(self,sqlQuery,params=None):
        '''
        run the given sqlQuery and return a list of Dicts
        
        Args:
            
            sqlQuery(string): the SQL query to be executed
            params(tuple): the query params, if any
                
        Returns:
            list: a list of Dicts
        '''
        if self.debug:
            print(sqlQuery)
            if params is not None:
                print(params)
        # https://stackoverflow.com/a/13735506/1497139
        cur=self.c.cursor()
        if params is not None:
            query = cur.execute(sqlQuery,params)
        else:
            query = cur.execute(sqlQuery)
        colname = [ d[0] for d in query.description ]
        resultList=[]
        for row in query:
            record=dict(zip(colname, row))
            resultList.append(record)
        cur.close()
        return resultList
        
    def queryAll(self,entityInfo,fixDates=True):
        '''
        query all records for the given entityName/tableName
        
        Args:
           entityName(string): name of the entity/table to qury
           fixDates(boolean): True if date entries should be returned as such and not as strings
        '''  
        sqlQuery='SELECT * FROM %s' % entityInfo.name
        resultList=self.query(sqlQuery)
        if fixDates:
            entityInfo.fixDates(resultList)
        return resultList
    
    def getTableList(self,tableType='table'):
        '''
        get the schema information from this database
        
        Args:
            tableType(str): table or view
            
        Return:
            list: a list as derived from PRAGMA table_info
        '''
        tableQuery=f"SELECT name FROM sqlite_master WHERE type='{tableType}'"
        tableList=self.query(tableQuery)
        for table in tableList:
            tableName=table['name']
            columnQuery=f"PRAGMA table_info('{tableName}')" 
            columns=self.query(columnQuery)
            table['columns']=columns
        return tableList
    
    def getTableDict(self,tableType='table'):
        '''
        get the schema information from this database as a dict
        
        Args:
            tableType(str): table or view
        
        Returns:
            dict: Lookup map of tables with columns also being converted to dict
        '''
        tableDict={}
        for table in self.getTableList(tableType=tableType):
            colDict={}
            for col in table["columns"]:
                colDict[col['name']]=col
            table["columns"]=colDict
            tableDict[table['name']]=table
        return tableDict
    
    def restoreProgress(self,status,remaining,total):
        self.progress("Restore",status,remaining,total)
        
    def backupProgress(self,status,remaining,total):
        self.progress("Backup",status,remaining,total)
              
    def progress(self,action,status, remaining, total):
        '''
        show progress
        '''
        print('%s %s at %5.0f%%' % (action,"... " if status==0 else "done",(total-remaining)/total*100)) 
    
    def backup(self,backupDB,action="Backup",profile=False,showProgress:int=200,doClose=True):
        '''
        create backup of this SQLDB to the given backup db
        
        see https://stackoverflow.com/a/59042442/1497139
        
        Args:
            backupDB(string): the path to the backupdb or SQLDB.RAM for in memory
            action(string): the action to display
            profile(boolean): True if timing information shall be shown
            showProgress(int): show progress at each showProgress page (0=show no progress)
        '''
        if sys.version_info <= (3, 6):
            raise Exception("backup via stdlibrary not available in python <=3.6 use copyToDB instead")
        startTime=time.time()
        bck=sqlite3.connect(backupDB)
        if showProgress>0:
            if action=="Restore":
                progress=self.restoreProgress
            else:
                progress=self.backupProgress
        else:
            progress=None
        with bck:
            self.c.backup(bck,pages=showProgress,progress=progress)        
        elapsed=time.time()-startTime
        if profile:
            print("%s to %s took %5.1f s" % (action,backupDB,elapsed))
        if doClose:
            bck.close()
            return None
        else:
            return bck
        
    def showDump(self,dump,limit=10):
        '''
        show the given dump up to the given limit
        
        Args:
            dump(string): the SQL dump to show
            limit(int): the maximum number of lines to display
        '''
        s=io.StringIO(dump)
        index=0
        for line in s:
            if index <= limit:
                print(line)
                index+=1    
            else:
                break        
        
    def executeDump(self,connection,dump,title,maxErrors=100,errorDisplayLimit=12,profile=True):
        '''
        execute the given dump for the given connection
        
        Args:
            connection(Connection): the sqlite3 connection to use
            dump(string): the SQL commands for the dump
            title(string): the title of the dump
            maxErrors(int): maximum number of errors to be tolerated before stopping and doing a rollback
            profile(boolean): True if profiling information should be shown
        Returns:
            a list of errors
        '''
        if self.debug:
            self.showDump(dump)
        startTime=time.time()    
        if profile:
            print("dump of %s has size %4.1f MB" % (title,len(dump)/1024/1024))
        errors=[]
        index=0
        # fixes https://github.com/WolfgangFahl/ProceedingsTitleParser/issues/37
        for line in dump.split(";\n"):
            try:
                connection.execute(line)
            except  sqlite3.OperationalError as soe:
                msg="SQL error %s in line %d:\n\t%s" % (soe,index,line)
                errors.append(msg)
                if len(errors)<=errorDisplayLimit:
                    print(msg)    
                if len(errors)>=maxErrors:
                    connection.execute("ROLLBACK;")
                    break
                
            index=index+1
        if profile:    
            print("finished executing dump %s with %d lines and %d errors in %5.1f s" % (title,index,len(errors),time.time()-startTime))    
        return errors
    
    def copyTo(self,copyDB,profile=True):
        '''
        copy my content to another database
        
        Args:
            
           copyDB(Connection): the target database
           profile(boolean): if True show profile information
        '''
        startTime=time.time()
        dump="\n".join(self.c.iterdump())
        #cursor.executescript(dump)
        if profile:
            print("finished getting dump of %s in %5.1f s" % (self.dbname,time.time()-startTime))
        dumpErrors=self.executeDump(copyDB.c,dump,self.dbname,profile=profile)
        return dumpErrors
       
        
    @staticmethod
    def restore(backupDB,restoreDB,profile=False,showProgress=200,debug=False):
        '''
        restore the restoreDB from the given backup DB
        
        Args:
            backupDB(string): path to the backupDB e.g. backup.db
            restoreDB(string): path to the restoreDB or in Memory SQLDB.RAM
            profile(boolean): True if timing information should be shown
            showProgress(int): show progress at each showProgress page (0=show no progress)
        '''
        backupSQLDB=SQLDB(backupDB)
        connection=backupSQLDB.backup(restoreDB,action="Restore",profile=profile,showProgress=showProgress,doClose=False)
        restoreSQLDB=SQLDB(restoreDB,connection=connection,debug=debug)
        return restoreSQLDB
    
        
class EntityInfo(object):
    """
    holds entity meta Info 
    
    :ivar name(string): entity name = table name
    
    :ivar primaryKey(string): the name of the primary key column
    
    :ivar typeMap(dict): maps column names to python types
    
    :ivar debug(boolean): True if debug information should be shown
    
    """
        
    def __init__(self,sampleRecords,name,primaryKey=None,debug=False):
        '''
        construct me from the given name and primary key
        
        Args:
           name(string): the name of the entity
           primaryKey(string): the name of the primary key column
           debug(boolean): True if debug information should be shown
        '''
        self.sampleRecords=sampleRecords
        self.name=name
        self.primaryKey=primaryKey
        self.debug=debug
        self.typeMap={}
        self.sqlTypeMap={}
        self.createTableCmd=self.getCreateTableCmd(sampleRecords)
        self.dropTableCmd="DROP TABLE IF EXISTS %s" % self.name
        self.insertCmd=self.getInsertCmd()
        
    def getCreateTableCmd(self,sampleRecords):
        '''
        get the CREATE TABLE DDL command for the given sample records
        
        Args:
            sampleRecords(list): a list of Dicts of sample Records    
            
        Returns:
            string: CREATE TABLE DDL command for this entity info 
            
        Example:   
      
        .. code-block:: sql
            
            CREATE TABLE Person(name TEXT PRIMARY KEY,born DATE,numberInLine INTEGER,wikidataurl TEXT,age FLOAT,ofAge BOOLEAN)
    
        '''
        ddlCmd="CREATE TABLE %s(" %self.name
        delim=""
        for sampleRecord in sampleRecords:
            for key,value in sampleRecord.items():
                sqlType=None
                valueType=None
                if value is None:
                    if len(sampleRecords)==1:
                        print("Warning sampleRecord column %s is None - using TEXT as type" % key)
                        valueType=str
                else:
                    valueType=type(value)
                if valueType == str:
                    sqlType="TEXT"
                elif valueType == int:
                    sqlType="INTEGER"
                elif valueType == float:
                    sqlType="FLOAT"
                elif valueType == bool:
                    sqlType="BOOLEAN"      
                elif valueType == datetime.date:
                    sqlType="DATE"    
                elif valueType== datetime.datetime:
                    sqlType="TIMESTAMP"
                else:
                    if valueType is not None:
                        msg="warning: unsupported type %s for column %s " % (str(valueType),key)
                        print(msg)
                if sqlType is not None and valueType is not None:
                    self.addType(key,valueType,sqlType)
        for key,sqlType in self.sqlTypeMap.items():        
            ddlCmd+="%s%s %s%s" % (delim,key,sqlType," PRIMARY KEY" if key==self.primaryKey else "")
            delim=","
        ddlCmd+=")"  
        if self.debug:
            print (ddlCmd)    
        return ddlCmd
        
    def getInsertCmd(self):
        '''
        get the INSERT command for this entityInfo
        
        Returns:
            the INSERT INTO SQL command for his entityInfo e.g.
                 
        Example:   
      
        .. code-block:: sql

            INSERT INTO Person (name,born,numberInLine,wikidataurl,age,ofAge) values (?,?,?,?,?,?).

        '''
        columns =','.join(self.typeMap.keys())
        placeholders=':'+',:'.join(self.typeMap.keys())
        insertCmd="INSERT INTO %s (%s) values (%s)" % (self.name, columns,placeholders)
        if self.debug:
            print(insertCmd)
        return insertCmd
        
    def addType(self,column,valueType,sqlType):
        '''
        add the python type for the given column to the typeMap
        
        Args:
           column(string): the name of the column
           
           valueType(type): the python type of the column
        '''
        if not column in self.typeMap:
            self.typeMap[column]=valueType     
            self.sqlTypeMap[column]=sqlType          
        
    def fixDates(self,resultList):
        '''
        fix date entries in the given resultList by parsing the date content e.g.
        converting '1926-04-21' back to datetime.date(1926, 4, 21)
        
        Args:
            resultList(list): the list of records to be fixed
        '''
        for record in resultList:
            for key,valueType in self.typeMap.items():
                if valueType==datetime.date:
                    dt=datetime.datetime.strptime(record[key],"%Y-%m-%d")  
                    dateValue=dt.date()  
                    record[key]=dateValue