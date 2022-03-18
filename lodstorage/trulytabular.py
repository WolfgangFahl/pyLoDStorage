'''
Created on 2022-04-14

@author: wf
'''
from lodstorage.sparql import SPARQL
from lodstorage.query import Query,QueryManager,YamlPath
import os
import re


class WikidataProperty():
    '''
    a WikidataProperty
    '''
    
    def __init__(self,pid:str):
        '''
        construct me with the given property id
        
        Args:
            pid(str): the property Id
        '''
        self.pid=pid
        self.reverse=False
    
    def getPredicate(self):
        '''
        get me as a Predicate
        '''
        reverseToken="^" if self.reverse else ""
        pLabel=f"{reverseToken}wdt:{self.pid}"
        return pLabel
    
    def __str__(self):
        text=self.pid
        if hasattr(self, "label"):
            text=f"{self.label} ({self.pid})"
        return text
      
    @classmethod
    def getPropertiesByLabels(cls,sparql,propertyLabels:list,lang:str="en"):
        '''
        get a list of Wikidata properties by the given label list
        
        Args:
            sparql(SPARQL): the SPARQL endpoint to use
            propertyLabels(list): a list of labels of the properties 
            lang(str): the language of the label
        '''
        # the result dict
        wdProperties={}
        valuesClause=""
        for propertyLabel in propertyLabels:
            valuesClause+=f'   "{propertyLabel}"@{lang}\n'
        query="""
# get the property for the given labels
SELECT ?property ?propertyLabel WHERE {
  VALUES ?propertyLabel {
%s
  }
  ?property rdf:type wikibase:Property;
  rdfs:label ?propertyLabel.
  FILTER((LANG(?propertyLabel)) = "en")
}""" % valuesClause
        qLod=sparql.queryAsListOfDicts(query)
        for record in qLod:
            url=record["property"]
            pid=re.sub(r"http://www.wikidata.org/entity/(.*)",r"\1",url)
            prop=WikidataProperty(pid)
            prop.pLabel=record["propertyLabel"]
            prop.url=url
            wdProperties[prop.pLabel]=prop
            pass
        return wdProperties
    
class WikidataItem:
    def __init__(self,qid:str):
        '''
        construct me with the given item id
        
        Args:
            qid(str): the item Id
        '''
        self.qid=qid
        
        
    def __str__(self):
        text=self.qid
        if hasattr(self, "qlabel"):
            text=f"{self.qlabel} ({self.qid})"
        return text
        
    @classmethod
    def getItemsByLabel(cls,sparql,itemLabels:list,lang:str="en"):
        '''
        get a list of Wikidata items by the given label list
        
        Args:
            sparql(SPARQL): the SPARQL endpoint to use
            itemLabels(list): a list of labels of items
            lang(str): the language of the label
        '''
        items={}
        valuesClause=""
        for itemLabel in itemLabels:
            valuesClause+=f'   "{itemLabel}"@{lang}\n'
        query="""# get the lowest item that has the given label 
# e.g. we'll find human=Q5 instead of the newer human entries in wikidata
SELECT (MIN(?itemValue) as ?item) ?itemLabel
WHERE { 
  VALUES ?itemLabel {
%s
  }
  ?itemValue rdfs:label ?itemLabel. 
} GROUP BY ?itemLabel""" % valuesClause

        qLod=sparql.queryAsListOfDicts(query)
        for record in qLod:
            url=record["item"] 
            qid=re.sub(r"http://www.wikidata.org/entity/(.*)",r"\1",url)
            item=WikidataItem(qid)
            item.url=url
            item.qlabel=record["itemLabel"]
            items[item.qlabel]=item
        return items
        
class TrulyTabular(object):
    '''
    truly tabular SPARQL/RDF analysis
    
    checks "how tabular" a query based on a list of properties of an itemclass is
    '''
    endpoint="https://query.wikidata.org/sparql"

    def __init__(self, itemQid, propertyLabels:list=[],where:str=None,endpoint=None,method="POST",lang="en",debug=False):
        '''
        Constructor
        
        Args:
            itemQid(str): wikidata id of the type to analyze 
            popertyLabels(list) the list of labels of properties to be considered
            where(str): extra where clause for instance selection (if any)
            endpoint(str): the url of the SPARQL endpoint to be used
        '''
        self.itemQid=itemQid
        self.debug=debug
        if endpoint is None:
            endpoint=TrulyTabular.endpoint
        self.endpoint=endpoint
        self.sparql=SPARQL(endpoint,method=method)
        self.where=f"\n  {where}" if where is not None else ""
        self.lang=lang
        self.label=self.getLabel(itemQid,lang=self.lang)
        self.queryManager=TrulyTabular.getQueryManager(debug=self.debug)
        self.properties=WikidataProperty.getPropertiesByLabels(self.sparql, propertyLabels, lang)
        
    def __str__(self):
        '''
        Returns:
            str: my text representation
        '''
        return self.asText(long=False)
    
    def asText(self,long:bool=True):
        '''
        returns my content as a text representation
        
        Args:
            long(bool): True if a long format including url is wished
            
        Returns:
            str: a text representation of my content
        '''
        if long:
            return f"{self.label}({self.itemQid}) https://www.wikidata.org/wiki/{self.itemQid}"
        else:
            return f"{self.label}({self.itemQid})"
    
    @classmethod
    def getQueryManager(cls,lang='sparql',name="trulytabular",debug=False):
        '''
        get the query manager for the given language and fileName
        
        Args:
            lang(str): the language of the queries to extract
            name(str): the name of the manager containing the query specifications
            debug(bool): if True set debugging on
        '''
        qYamlFileName=f"{name}.yaml"
        for qYamlFile in YamlPath.getPaths(qYamlFileName):
            if os.path.isfile(qYamlFile):
                qm=QueryManager(lang=lang,debug=debug,queriesPath=qYamlFile)
                return qm
        return None
    
        
    def getValue(self,sparqlQuery:str,attr:str):
        '''
        get the value for the given SPARQL query using the given attr
        
        Args:
            sparqlQuery(str): the SPARQL query to run
            attr(str): the attribute to get
        '''
        if self.debug:
            print(sparqlQuery)
        qLod=self.sparql.queryAsListOfDicts(sparqlQuery)
        return self.getFirst(qLod, attr)
        
    def getFirst(self,qLod:list,attr:str):
        '''
        get the column attr of the first row of the given qLod list
        
        Args:
            qLod(list): the list of dicts (returned by a query)
            attr(str): the attribute to retrieve
            
        Returns:
            object: the value
        '''
        if len(qLod)==1 and attr in qLod[0]:
            value=qLod[0][attr]
            return value
        raise Exception(f"getFirst for attribute {attr} failed for {qLod}")
        
    def getLabel(self,itemId:str,lang:str="en"):
        '''
        get  the label for the given item
        
        Args:
            itemId(str): the wikidata Q/P id
            lang(str): the language of the label 
            
        Returns:
            str: the label
        '''
        query="""
# get the label for the given item
SELECT ?itemLabel
WHERE
{
  VALUES ?item {
    wd:%s
  }
  ?item rdfs:label ?itemLabel.
  filter (lang(?itemLabel) = "%s").
}""" % (itemId,lang)
        return self.getValue(query, "itemLabel")
        
    def count(self):
        '''
        get my count
        '''
        query=f"""# Count all items with the given 
# type {self.asText(long=True)}
SELECT (COUNT (DISTINCT ?item) AS ?count)
WHERE
{{
  # instance of {self.label}
  ?item wdt:P31 wd:{self.itemQid}.{self.where}
}}"""
        return self.getValue(query, "count")
    
    def mostFrequentIdentifiersQuery(self):
        '''
        get the most frequently used identifiers
        '''
        query=self.queryManager.queriesByName["mostFrequentIdentifiers"]
        query.title=f"most frequently used identifiers for {self.asText(long=True)}"
        query.query=query.query % self.itemQid
        return query
    
    def noneTabularQuery(self,wdProperty:WikidataProperty,asFrequency:bool=True):
        '''
        get the none tabular entries for the given property
        
        Args:
            wdProperty(WikidataProperty): the property to analyze
            asFrequency(bool): if true do a frequency analysis
        '''
        propertyLabel=wdProperty.pLabel
        propertyId=wdProperty.pid
        # work around https://github.com/RDFLib/sparqlwrapper/issues/211
        if "described at" in propertyLabel:
            propertyLabel=propertyLabel.replace("described at","describ'd at")
        sparql=f"""
# Count all {self.asText(long=True)} items
# with the given {propertyLabel}({propertyId}) https://www.wikidata.org/wiki/Property:{propertyId} 
SELECT ?item ?itemLabel (COUNT (?value) AS ?count)
WHERE
{{
  # instance of {self.label}
  ?item wdt:P31 wd:{self.itemQid}.{self.where}
  ?item rdfs:label ?itemLabel.
  filter (lang(?itemLabel) = "en").
  # {propertyLabel}
  ?item {wdProperty.getPredicate()} ?value.
}} GROUP by ?item ?itemLabel
"""
        if asFrequency:
            freqDesc="frequencies"
            sparql=f"""SELECT ?count (COUNT(?count) AS ?frequency) WHERE {{{{
{sparql}
}}}}
GROUP BY ?count
ORDER BY DESC (?frequency)"""
        else:
            freqDesc="records"
            sparql=f"""{sparql}
HAVING (COUNT (?value) > 1)
ORDER BY DESC(?count)"""
        query=Query(query=sparql,name=f"NonTabular {self.label}/{propertyLabel}:{freqDesc}",title=f"non tabular entries for {self.label}/{propertyLabel}:{freqDesc}")
        return query

    def noneTabular(self,wdProperty:WikidataProperty):
        '''
        get the none tabular result for the given Wikidata property
        
        Args:
            wdProperty(WikidataProperty): the Wikidata property
        '''
        query=self.noneTabularQuery(wdProperty)
        if self.debug:
            print(query.query)
        qlod=self.sparql.queryAsListOfDicts(query.query)
        return qlod
    
    def addStatsColWithPercent(self,m,col,value,total): 
        '''
        add a statistics Column
        '''
        m[col]=value
        m[f"{col}%"]=float(f"{value/total*100:.1f}")
    
    def getPropertyStatics(self):
        '''
        get the property Statistics
        '''
        itemCount=self.count()
        lod=[{
            "property": "∑",
            "total": itemCount,
            "total%": 100.0
        }]
        for wdProperty in self.properties.values():
            ntlod=self.noneTabular(wdProperty)
            statsRow={"property":wdProperty.pLabel}
            total=0
            nttotal=0
            maxCount=0
            for record in ntlod:
                f=record["frequency"]
                count=record["count"]
                #statsRow[f"f{count}"]=f
                if count>1:
                    nttotal+=f
                else:
                    statsRow["1"]=f
                if count>maxCount:
                    maxCount=count     
                total+=f
            statsRow["max"]=maxCount
            self.addStatsColWithPercent(statsRow,"total",total,itemCount)
            self.addStatsColWithPercent(statsRow,"non tabular",nttotal,total)
            lod.append(statsRow)
        return lod
    

        