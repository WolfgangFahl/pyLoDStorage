'''
Created on 2020-08-24

@author: wf
'''
import unittest
from datetime import datetime
import time
import os
import sys
from lodstorage.sample import Sample
from lodstorage.uml import UML
from lodstorage.sql import SQLDB, EntityInfo


class TestSQLDB(unittest.TestCase):
    '''
    Test the SQLDB database wrapper
    '''

    def setUp(self):
        self.debug=True
        pass

    def tearDown(self):
        pass
    
    def checkListOfRecords(self,listOfRecords,entityName,primaryKey=None,executeMany=True,fixDates=False,debug=False,doClose=True):
        '''
        check the handling of the given list of Records
        
        Args:
          
           listOfRecords(list): a list of dicts that contain the data to be stored
           entityName(string): the name of the entity type to be used as a table name
           primaryKey(string): the name of the key / column to be used as a primary key
           executeMany(boolean): True if executeMany mode of sqlite3 should be used
           debug(boolean): True if debug information e.g. CREATE TABLE and INSERT INTO commands should be shown
           doClose(boolean): True if the connection should be closed
      
        '''     
        size=len(listOfRecords)
        print("%s size is %d fixDates is: %r" % (entityName,size,fixDates))
        self.sqlDB=SQLDB(debug=debug,errorDebug=True)
        entityInfo=self.sqlDB.createTable(listOfRecords[:10],entityName,primaryKey)
        startTime=time.time()
        self.sqlDB.store(listOfRecords,entityInfo,executeMany=executeMany)
        elapsed=time.time()-startTime
        print ("adding %d %s records took %5.3f s => %5.f records/s" % (size,entityName,elapsed,size/elapsed)) 
        resultList=self.sqlDB.queryAll(entityInfo,fixDates=fixDates)    
        print ("selecting %d %s records took %5.3f s => %5.f records/s" % (len(resultList),entityName,elapsed,len(resultList)/elapsed)) 
        if doClose:
            self.sqlDB.close()
        return resultList
    
    def testEntityInfo(self):
        '''
        test creating entityInfo from the sample record
        '''
        listOfRecords=Sample.getRoyals()
        entityInfo=EntityInfo(listOfRecords[:3],'Person','name',debug=True)
        self.assertEqual("CREATE TABLE Person(name TEXT PRIMARY KEY,born DATE,numberInLine INTEGER,wikidataurl TEXT,age FLOAT,ofAge BOOLEAN,lastmodified TIMESTAMP)",entityInfo.createTableCmd)
        self.assertEqual("INSERT INTO Person (name,born,numberInLine,wikidataurl,age,ofAge,lastmodified) values (:name,:born,:numberInLine,:wikidataurl,:age,:ofAge,:lastmodified)",entityInfo.insertCmd)
        self.sqlDB=SQLDB(debug=self.debug,errorDebug=True)
        entityInfo=self.sqlDB.createTable(listOfRecords[:10],entityInfo.name,entityInfo.primaryKey)
        tableList=self.sqlDB.getTableList()
        if self.debug:
            print (tableList)
        self.assertEqual(1,len(tableList))
        personTable=tableList[0]
        self.assertEqual("Person",personTable['name'])
        self.assertEqual(7,len(personTable['columns']))
        uml=UML()
        plantUml=uml.tableListToPlantUml(tableList,packageName="Royals",withSkin=False)
        if self.debug:
            print(plantUml)
        expected="""package Royals {
  class Person << Entity >> {
   age : FLOAT 
   born : DATE 
   lastmodified : TIMESTAMP 
   name : TEXT <<PK>>
   numberInLine : INTEGER 
   ofAge : BOOLEAN 
   wikidataurl : TEXT 
  }
}
"""
        self.assertEqual(expected,plantUml)
        
        # testGeneralization
        listOfRecords=[{'name': 'Royal family', 'country': 'UK', 'lastmodified':datetime.now()}]
        entityInfo=self.sqlDB.createTable(listOfRecords[:10],'Family','name')
        tableList=self.sqlDB.getTableList()
        self.assertEqual(2,len(tableList))
        uml=UML()
        plantUml=uml.tableListToPlantUml(tableList,generalizeTo="PersonBase",withSkin=False)
        print(plantUml)
        expected='''class PersonBase << Entity >> {
 lastmodified : TIMESTAMP 
 name : TEXT <<PK>>
}
class Person << Entity >> {
 age : FLOAT 
 born : DATE 
 numberInLine : INTEGER 
 ofAge : BOOLEAN 
 wikidataurl : TEXT 
}
class Family << Entity >> {
 country : TEXT 
}
PersonBase <|-- Person
PersonBase <|-- Family
'''
        self.assertEqual(expected,plantUml)
        
    def testUniqueConstraint(self):
        '''
        test for https://github.com/WolfgangFahl/pyLoDStorage/issues/4
        sqlite3.IntegrityError: UNIQUE constraint failed: ... show debug info
        '''
        listOfDicts=[
            {"name": "John Doe"},
            {"name": "Frank Doe"}, 
            {"name": "John Doe"}, 
            {"name":"Tim Doe"}]
        sqlDB=SQLDB(debug=self.debug,errorDebug=True)
        entityInfo=sqlDB.createTable(listOfDicts[:10],'Does','name')
        try:
            sqlDB.store(listOfDicts,entityInfo,executeMany=False)
            self.fail("There should be an exception")
        except Exception as ex:
            expected="""INSERT INTO Does (name) values (:name)
failed:UNIQUE constraint failed: Does.name
record  #3={'name': 'John Doe'}"""
            errMsg=str(ex)
            self.assertEqual(expected,errMsg)
            
    def testSqlite3(self):
        '''
        test sqlite3 with a few records from the royal family
        '''
        listOfRecords=Sample.getRoyals()
        resultList=self.checkListOfRecords(listOfRecords, 'Person', 'name',debug=True)
        if self.debug:
            print(resultList)
        self.assertEquals(listOfRecords,resultList)
        
    def testBindingError(self):
        '''
        test list of Records with incomplete record leading to
        "You did not supply a value for binding 2"
        see https://bugs.python.org/issue41638
        '''
        listOfRecords=[{'name':'Pikachu', 'type':'Electric'},{'name':'Raichu' }]
        for executeMany in [True,False]:
            try:
                self.checkListOfRecords(listOfRecords,'Pokemon','name',executeMany=executeMany)
                self.fail("There should be an exception")
            except Exception as ex:
                if self.debug:
                    print(str(ex))
                self.assertTrue('no value supplied for column' in str(ex))                                                         
        
    def testListOfCities(self):
        '''
        test sqlite3 with some 120000 city records
        '''
        listOfRecords=Sample.getCities()
        for fixDates in [True,False]:
            retrievedList=self.checkListOfRecords(listOfRecords,'City',fixDates=fixDates)
            self.assertEqual(len(listOfRecords),len(retrievedList))
        
    def testSqllite3Speed(self):
        '''
        test sqlite3 speed with some 100000 artificial sample records
        consisting of two columns with a running index
        '''
        limit=100000
        listOfRecords=Sample.getSample(limit)
        self.checkListOfRecords(listOfRecords, 'Sample', 'pKey')     

    def testBackup(self):
        '''
        test creating a backup of the SQL database
        '''
        if sys.version_info >= (3, 7):
            listOfRecords=Sample.getCities()
            self.checkListOfRecords(listOfRecords,'City',fixDates=True,doClose=False)
            backupDB="/tmp/testSqlite.db"
            self.sqlDB.backup(backupDB,profile=True,showProgress=200)
            size=os.stat(backupDB).st_size
            print ("size of backup DB is %d" % size)
            self.assertTrue(size>600000)
            self.sqlDB.close()
            # restore
            ramDB=SQLDB.restore(backupDB, SQLDB.RAM, profile=True)
            entityInfo=EntityInfo(listOfRecords[:50],'City',debug=True)
            allCities=ramDB.queryAll(entityInfo)
            self.assertEqual(len(allCities),len(listOfRecords))
            
    def testCopy(self):
        '''
        test copying databases into another database
        '''
        dbFile="/tmp/DAWT_Sample3x1000.db"
        copyDB=SQLDB(dbFile)
        for sampleNo in range(3):
            listOfRecords=Sample.getSample(1000)
            self.checkListOfRecords(listOfRecords, 'Sample_%d_1000' %sampleNo, 'pKey',doClose=False)  
            self.sqlDB.copyTo(copyDB)
        size=os.stat(dbFile).st_size
        print ("size of copy DB is %d" % size)
        self.assertTrue(size>70000)
        tableList=copyDB.getTableList()
        print(tableList)
        for sampleNo in range(3):
            self.assertEqual('Sample_%d_1000' %sampleNo,tableList[sampleNo]['name'])
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSqllit3']
    unittest.main()