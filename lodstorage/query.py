'''
Created on 2020-08-22

@author: wf
'''
import os
import yaml
from tabulate import tabulate
import urllib
#from wikibot.mwTable import MediaWikiTable
# redundant copy in this library to avoid dependency issues
# original is at 
from lodstorage.mwTable import MediaWikiTable


class QueryResultDocumentation():
    '''
    documentation of a query result
    '''
    
    def __init__(self,query,title:str,tryItMarkup:str,sourceCodeHeader:str,sourceCode:str,resultHeader:str,result:str):
        '''
        constructor
        
        Args:
            query(Query): the query to be documented
            title(str): the title markup
            tryItMarkup: the "try it!" markup to show
            sourceCodeHeader(str): the header title to use for the sourceCode
            sourceCode(str): the sourceCode
            resultCodeHeader(str): the header title to use for the result
            result(str): the result header
            
        '''
        self.query=query
        self.title=title
        self.tryItMarkup=f"\n{tryItMarkup}"
        self.sourceCodeHeader=sourceCodeHeader
        self.sourceCode=sourceCode
        self.resultHeader=resultHeader
        self.result=result
        
        
    def __str__(self):
        '''
        simple string representation
        '''
        text=f"{self.title}\n{self.query.description}\n{self.sourceCodeHeader}\n{self.sourceCode}{self.tryItMarkup}\n{self.resultHeader}\n{self.result}"
        return text
        
class Query(object):
    ''' a Query e.g. for SPAQRL '''
    
    def __init__(self,name:str,query:str,lang='sparql',title:str=None,description:str=None,debug=False):
        '''
        constructor 
        Args:
            name(string): the name/label of the query
            query(string): the native Query text e.g. in SPARQL
            lang(string): the language of the query e.g. SPARQL
            title(string): the header/title of the query
            description(string): the description of the query
            debug(boolean): true if debug mode should be switched on
        '''
        self.name=name
        self.query=query
        self.lang=lang
        self.title=title=name if title is None else title
        self.description="" if description is None else description
        self.debug=debug
        
    def getTryItUrl(self,baseurl:str):
        '''
        return the "try it!" url for the given baseurl
        
        Args:
            baseurl(str): the baseurl to used
            
        Returns:
            str: the "try it!" url for the given query
        '''
        quoted=urllib.parse.quote(self.query)
        quoted=f"#{quoted}"
        url=f"{baseurl}/{quoted}"
        return url
    
    def getLink(self,url,title,tablefmt):
        '''
        convert the given url and title to a link for the given tablefmt
        
        Args:
            url(str): the url to convert
            title(str): the title to show
            tablefmt(str): the table format to use
        '''
        # create a safe url
        if url is None:
            return ""
        markup=f"{title}:{url}"
        if tablefmt=="mediawiki":
            markup=f"[{url} {title}]"
        elif tablefmt=="github":
            markup=f"[{title}]({url})"
        elif tablefmt=="latex":
            markup=r"\href{%s}{%s}" % (url,title) 
        return markup
        
    def prefixToLink(self,lod:list,prefix:str,tablefmt:str):
        '''
        convert url prefixes to link according to the given table format
        
        Args:
            lod(list): the list of dicts to convert
            prefix(str): the prefix to strip 
            tablefmt(str): the tabulate tableformat to use
            
        '''
        for record in lod:
            for key in record.keys():
                value=record[key]
                if value is not None and isinstance(value,str) and value.startswith(prefix):
                    item=value.replace(prefix,"")
                    if tablefmt=="latex":
                        link=item
                    else:
                        link=self.getLink(value,item,tablefmt)
                    record[key]=link
          
        
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
    
    def documentQueryResult(self,lod:list,tablefmt:str="mediawiki",tryItUrl:str=None,withSourceCode=True,**kwArgs):
        '''
        document the given query results
        
        Args:
            lod: the list of dicts result
            tryItUrl: the "try it!" url to show
            tablefmt(str): the table format to use
            withSourceCode(bool): if True document the source code
            
        Return:
            str: the documentation tabular text for the given parameters
        '''
        sourceCode=self.query
        title=self.title
        result=tabulate(lod,headers="keys",tablefmt=tablefmt,**kwArgs)
        if withSourceCode:
            tryItMarkup=self.getLink(tryItUrl, "try it!", tablefmt)
            if tablefmt=="github":
                title=f"**{self.title}**"
                sourceCodeHeader="**query**"
                resultHeader="**result**"
                sourceCode=f"""```sql
{self.query}
```"""
                
            elif tablefmt=="mediawiki":
                title=f"== {self.title} =="
                sourceCodeHeader="=== query ==="
                resultHeader="=== result ==="
                sourceCode=f"""<source lang='{self.lang}'>
{self.query}
</source>
"""
            elif tablefmt=="latex":
                sourceCodeHeader=r"see query listing \ref{listing:%s} and result table \ref{tab:%s}" % (self.name,self.name)
                resultHeader=""
                sourceCode=r"""\begin{listing}[ht]
\caption{%s}
\label{listing:%s}
\begin{minted}{%s}
%s
\end{minted}
%s
\end{listing}
""" % (self.title,self.name,self.lang.lower(),self.query,tryItMarkup)
                tryItMarkup=""
                result=r"""\begin{table}
\caption{%s}
\label{tab:%s}
%s
\end{table}
""" % (self.title,self.name,result)
            else:
                title=f"{self.title}"
                sourceCodeHeader="query:"
                resultHeader="result:"
                sourceCode=f"{self.query}"
        if self.lang!="sparql":
            tryItMarkup=""
        queryResultDocumentation=QueryResultDocumentation(query=self,title=title,tryItMarkup=tryItMarkup,sourceCodeHeader=sourceCodeHeader,sourceCode=sourceCode,resultHeader=resultHeader,result=result)
        return queryResultDocumentation

class QueryManager(object):
    '''
    manages pre packaged Queries
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
        