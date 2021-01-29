'''
Created on 2020-08-22

@author: wf
'''
import os
import yaml
#from wikibot.mwTable import MediaWikiTable
# redundant copy in this library to avoid dependency issues
# original is at 
from lodstorage.mwTable import MediaWikiTable
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
        