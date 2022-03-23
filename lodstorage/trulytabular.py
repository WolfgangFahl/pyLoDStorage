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
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT ?property ?propertyLabel WHERE {
  VALUES ?propertyLabel {
%s
  }
  ?property rdf:type wikibase:Property;
  rdfs:label ?propertyLabel.
  FILTER((LANG(?propertyLabel)) = "%s")
}""" % (valuesClause,lang)
        cls.addPropertiesForQuery(wdProperties,sparql,query)
        return wdProperties
    
    @classmethod
    def getPropertiesByIds(cls,sparql,propertyIds:list,lang:str="en"):
        '''
        get a list of Wikidata properties by the given id list
        
        Args:
            sparql(SPARQL): the SPARQL endpoint to use
            propertyIds(list): a list of ids of the properties 
            lang(str): the language of the label
        '''
        # the result dict
        wdProperties={}
        valuesClause=""
        for propertyId in propertyIds:
            valuesClause+=f'   wd:{propertyId}\n'
        query="""
# get the property for the given property Ids
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX wikibase: <http://wikiba.se/ontology#>
SELECT ?property ?propertyLabel WHERE {
  VALUES ?property {
%s
  }
  ?property rdf:type wikibase:Property;
  rdfs:label ?propertyLabel.
  FILTER((LANG(?propertyLabel)) = "%s")
}""" % (valuesClause,lang)
        cls.addPropertiesForQuery(wdProperties,sparql,query)
        return wdProperties
        
    @classmethod    
    def addPropertiesForQuery(cls,wdProperties:list,sparql,query):  
        '''
          add properties from the given query's result to the given
          wdProperties list using the given sparql endpoint
        Args:
          wdProperties(list): the list of wikidata properties
          sparql(SPARQL): the SPARQL endpoint to use
          query(str): the SPARQL query to perform
        '''
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
    '''
    a wikidata Item
    '''
    def __init__(self,qid:str,lang:str="en",sparql:SPARQL=None):
        '''
        construct me with the given item id, language and optional SPARQL access
        
        Args:
            qid(str): the item Id
            lang(str): the language to use
            sparql(SPARQL): the sparql access to use
        '''
        self.qid=qid
        self.lang=lang
        self.sparql=sparql
        if sparql is not None:
            self.qlabel,self.description=WikidataItem.getLabelAndDescription(sparql, self.qid, self.lang)
    
    def __str__(self):
                
        return self.asText(long=False)
    
    def asText(self,long:bool=True):
        '''
        returns my content as a text representation
        
        Args:
            long(bool): True if a long format including url is wished
            
        Returns:
            str: a text representation of my content
        '''
        text=self.qid
        if hasattr(self, "qlabel"):
            text=f"{self.qlabel} ({self.qid})"  
        if hasattr(self,"description"):
            text+=f":{self.description}"
        if long:
            text+=f"-> https://www.wikidata.org/wiki/{self.qid}"
        return text
    
    @classmethod
    def getLabelAndDescription(self,sparql:SPARQL, itemId:str,lang:str="en"):
        '''
        get  the label for the given item and language
        
        Args:
            itemId(str): the wikidata Q/P id
            lang(str): the language of the label 
            
        Returns:
            (str,str): the label and description as a tuple
        '''
        query="""
# get the label for the given item
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX schema: <http://schema.org/>
SELECT ?itemLabel ?itemDescription
WHERE
{
  VALUES ?item {
    wd:%s
  }
  ?item rdfs:label ?itemLabel.
  filter (lang(?itemLabel) = "%s").
  ?item schema:description ?itemDescription.
  FILTER((LANG(?itemDescription)) = "%s")
}""" % (itemId,lang,lang)
        return sparql.getValues(query, ["itemLabel","itemDescription"])
        
    @classmethod
    def getItemsByLabel(cls,sparql:SPARQL,itemLabel:str,lang:str="en")->list:
        '''
        get a Wikidata items by the given label
        
        Args:
            sparql(SPARQL): the SPARQL endpoint to use
            itemLabel(str): the label of the items
            lang(str): the language of the label
            
        Returns:
            a list of potential items
        '''
        valuesClause=f'   "{itemLabel}"@{lang}\n'
        query="""# get the items that have the given label in the given language
# e.g. we'll find human=Q5 as the oldest type for the label "human" first
# and then the newer ones such as "race in Warcraft"
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
SELECT ?itemId ?item ?itemLabel ?itemDescription
WHERE { 
  VALUES ?itemLabel {
%s
  }
  BIND (xsd:integer(SUBSTR(STR(?item),33)) AS ?itemId)
  ?item rdfs:label ?itemLabel. 
  ?item schema:description ?itemDescription
  FILTER(LANG(?itemDescription)="%s")
} ORDER BY ?itemId""" % (valuesClause,lang)

        qLod=sparql.queryAsListOfDicts(query)
        items=[]
        for record in qLod:
            url=record["item"] 
            qid=re.sub(r"http://www.wikidata.org/entity/(.*)",r"\1",url)
            item=WikidataItem(qid)
            item.url=url
            item.qlabel=record["itemLabel"]
            item.description=record["itemDescription"]
            items.append(item)
        return items
        
class TrulyTabular(object):
    '''
    truly tabular SPARQL/RDF analysis
    
    checks "how tabular" a query based on a list of properties of an itemclass is
    '''
    endpoint="https://query.wikidata.org/sparql"

    def __init__(self, itemQid, propertyLabels:list=[],propertyIds:list=[],where:str=None,endpoint=None,method="POST",lang="en",debug=False):
        '''
        Constructor
        
        Args:
            itemQid(str): wikidata id of the type to analyze 
            propertyLabels(list): a list of labels of properties to be considered
            propertyIds(list): a list of ids of properties to be considered
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
        self.item=WikidataItem(itemQid,sparql=self.sparql,lang=lang)
        self.queryManager=TrulyTabular.getQueryManager(debug=self.debug)
        self.properties=WikidataProperty.getPropertiesByIds(self.sparql,propertyIds,lang)
        self.properties.update(WikidataProperty.getPropertiesByLabels(self.sparql, propertyLabels, lang))
    
        
    def __str__(self):
        '''
        Returns:
            str: my text representation
        '''
        return self.asText(long=False)
    
    def count(self):
        '''
        get my count
        '''
        query=f"""# Count all items with the given 
# type {self.item.asText(long=True)}
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT (COUNT (DISTINCT ?item) AS ?count)
WHERE
{{
  # instance of {self.item.qlabel}
  ?item wdt:P31 wd:{self.item.qid}.{self.where}
}}"""
        return self.sparql.getValue(query, "count")
    
    def asText(self,long:bool=True):
        '''
        returns my content as a text representation
        
        Args:
            long(bool): True if a long format including url is wished
            
        Returns:
            str: a text representation of my content
        '''
        text=self.item.asText(long)
        return text
    
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
    
    def mostFrequentPropertiesQuery(self):
        '''
        get the most frequently used properties
        '''
        query=self.queryManager.queriesByName["mostFrequentProperties"]
        query.title=f"most frequently used properties for {self.asText(long=True)}"
        query.query=query.query % (self.item.asText(long=True),self.itemQid,self.lang)
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
  # instance of {self.item.qlabel}
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
        query=Query(query=sparql,name=f"NonTabular {self.item.qlabel}/{propertyLabel}:{freqDesc}",title=f"non tabular entries for {self.item.qlabel}/{propertyLabel}:{freqDesc}")
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
        
    def genWdPropertyStatistic(self,wdProperty:WikidataProperty,itemCount:int,withQuery=True)->dict:
        '''
        generate a property Statistics Row for the given wikidata Property
        
        Args:
            wdProperty(WikidataProperty): the property to get the statistics for
            itemCount(int): the total number of items to check
            withQuery(bool): if true include the sparql query
            
        Returns:
            dict: a statistics row
        '''
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
        if withQuery:
            statsRow["queryf"]=self.noneTabularQuery(wdProperty).query
            statsRow["queryex"]=self.noneTabularQuery(wdProperty,asFrequency=False).query
        self.addStatsColWithPercent(statsRow,"total",total,itemCount)
        self.addStatsColWithPercent(statsRow,"non tabular",nttotal,total)
        return statsRow
        
    def genPropertyStatistics(self):
        '''
        generate the property Statistics
        
        Returns:
            generator: a generator of statistic dict rows
        '''
        itemCount=self.count()
        for wdProperty in self.properties.values():
            statsRow=self.genWdPropertyStatistic(wdProperty, itemCount)
            yield statsRow
    
    def getPropertyStatistics(self):
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
            statsRow=self.genWdPropertyStatistic(wdProperty, itemCount)
            lod.append(statsRow)
        return lod
    

        