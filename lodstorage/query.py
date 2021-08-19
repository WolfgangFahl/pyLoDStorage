'''
Created on 2020-08-22

@author: wf
'''
import os
import yaml
from tabulate import tabulate
#from wikibot.mwTable import MediaWikiTable
# redundant copy in this library to avoid dependency issues
# original is at 
from lodstorage.mwTable import MediaWikiTable


class QueryResultDocumentation():
    '''
    documentation of a query result
    '''
    
    def __init__(self,title,sourceCode,sourceCodeHeader,resultHeader,result):
        '''
        constructor
        
        Args:
            title(str): the title markup
            
        '''
        self.title=title
        self.sourceCodeHeader=sourceCodeHeader
        self.sourceCode=sourceCode
        self.resultHeader=resultHeader
        self.result=result
        
    def __str__(self):
        text=f"{self.title}\n{self.sourceCodeHeader}\n{self.sourceCode}\n{self.resultHeader}\n{self.result}"
        return text
        
class Query(object):
    ''' a Query e.g. for SPAQRL '''
    
    def __init__(self,name,query,lang='sparql',debug=False):
        '''
        constructor 
        Args:
            name(string): the name of the query
            query(string): the native Query text e.g. in SPARQL
            lang(string): the language of the query e.g. SPARQL
            debug(boolean): true if debug mode should be switched on
        '''
        self.name=name
        self.lang=lang
        self.query=query
        self.debug=debug
        
    def asWikiSourceMarkup(self):
        '''
        convert me to Mediawiki markup for syntax highlighting using the "source" tag
        
        
        Returns:
            string: the Markup
        '''
        markup="<source lang='%s'>\n%s\n</source>\n" %(self.lang,self.query)
        return markup
        
    def asWikiMarkup(self,listOfDicts):
        '''
        convert the given listOfDicts result to MediaWiki markup
        
        Args:
            listOfDicts(list): the list of Dicts to convert to MediaWiki markup
        
        Returns:
            string: the markup
        '''
        if self.debug:
            print(listOfDicts)
        mwTable=MediaWikiTable()
        mwTable.fromListOfDicts(listOfDicts)
        markup=mwTable.asWikiMarkup()        
        return markup
    
    def documentQueryResult(self,lod:list,tablefmt:str="mediawiki",withSourceCode=True,**kwArgs):
        '''
        document the given query results
        
        Args:
            lod: the list of dicts result
            tablefmt(str): the table format to use
            withSourceCode(bool): if True document the source code
            
        Return:
            str(
        '''
        sourceCode=self.query
        title=self.name
        if withSourceCode:
            sourceCodeHeader="**query**"
            resultHeader="**result**"
            if tablefmt=="github":
                title=f"**{self.name}**"
                sourceCode=f"""**query**
```sql
{self.query}
```"""
            if tablefmt=="mediawiki":
                title=f"== {self.name} =="
                sourceCodeHeader="=== query ==="
                resultHeader="=== result ==="
                sourceCode=f"""<source lang='sql'>
{self.query}
</source>
"""
        tab=tabulate(lod,headers="keys",tablefmt=tablefmt,**kwArgs)
        queryResultDocumentation=QueryResultDocumentation(title=title,sourceCode=sourceCode,sourceCodeHeader=sourceCodeHeader,resultHeader=resultHeader,result=tab)
        return queryResultDocumentation

class QueryManager(object):
    '''
    manages prepackaged Queries
    '''

    def __init__(self,lang='sql',debug=False,path=None):
        '''
        Constructor
        Args:
            lang(string): the language to use for the queries sql or sparql
            debug(boolean): True if debug information should be shown
        '''
        self.queriesByName={}
        self.lang=lang
        self.debug=debug
        queries=QueryManager.getQueries(path=path)
        for name,queryDict in queries.items():
            if self.lang in queryDict:
                queryText=queryDict[self.lang]
                query=Query(name,queryText,lang=self.lang,debug=self.debug)
                self.queriesByName[name]=query
    
    @staticmethod
    def getQueries(path=None):
        if path is None:
            path=os.path.dirname(__file__)+"/.."
        queriesPath=path+"/queries.yaml"
        with open(queriesPath, 'r') as stream:
            examples = yaml.safe_load(stream)
        return examples
        