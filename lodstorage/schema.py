'''
Created on 2021-01-26

@author: wf
'''
from collections import Counter

class SchemaManager(object,):
    '''
    a manager for schemas
    '''
    def __init__(self,schemaDefs=None,baseUrl:str=None):
        '''
        constructor
            Args:
                schemaDefs(dict): a dictionary of schema names
                baseUrl(str): the base url to use for links
        '''
        self.baseUrl=baseUrl
        self.schemasByName={}
        if schemaDefs is None:
            schemaDefs={}
        for key,name in schemaDefs.items():
            self.schemasByName[key]=Schema(key,name) 
        pass

class Schema(object):
    '''
    a relational Schema
    '''

    def __init__(self,name:str,title:str):
        '''
        Constructor
        
        Args:
            name(str): the name of the schema
            title(str): the title of the schema
        '''
        self.name=name
        self.title=title
        self.propsByName={}
        
    @staticmethod    
    def generalizeColumn(tableList,colName:str):
        ''' 
        remove the column with the given name from all tables in the tablelist and
        return it
        
        Args:
            tableList(list): a list of Tables
            colName(string): the name of the column to generalize
        
        Returns:
            string: the column having been generalized and removed
        '''
        gCol=None
        for table in tableList:
            for col in table['columns']: 
                if col['name']==colName:
                    gCol=col.copy()
                    # no linking yet @FIXME - will need this later
                    if 'link' in gCol:
                        gCol.pop('link')
                    # is generalization protected for this column?
                    if not 'special' in col or not col['special']:
                        table['columns'].remove(col)
        return gCol                
        
    @staticmethod    
    def getGeneral(tableList,name:str,debug:bool=False):
        '''
        derive a general table from the given table list
        Args:
            tableList(list): a list of tables
            name(str): name of the general table
            debug(bool): True if column names should be shown
            
        Returns:
            at table dict for the generalized table
        '''
        general={'name':name,'columns':[]}
        colCount=Counter()
        for table in tableList:
            for col in table['columns']:
                columnId="%s.%s" % (col['name'],col['type'])
                if debug:
                    print (columnId) 
                colCount[columnId]+=1
        for columnId,count in colCount.items():
            if count==len(tableList): 
                colName=columnId.split('.')[0]
                generalCol=Schema.generalizeColumn(tableList, colName)
                general['columns'].append(generalCol)    
        return general
    
    @staticmethod
    def getGeneralViewDDL(tableList,name:str,debug=False)->str:
        ''' 
        get the DDL statement to create a general view
        
        Args:
            tableList: the list of tables
            name(str): the name of the view
            debug(bool): True if debug should be set
        '''
        general=Schema.getGeneral(tableList, name, debug)
        cols=""
        delim=""
        for col in general['columns']:
            cols+="%s%s" % (delim,col['name'])
            delim=","
        ddl="CREATE VIEW %s AS \n" % name
        delim=""
        for table in tableList:
            ddl+="%s  SELECT %s FROM %s" % (delim,cols,table['name'])
            delim="\nUNION\n"
        return ddl
        