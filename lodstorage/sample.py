'''
Created on 2020-08-24

@author: wf
'''
import urllib.request
import json
from lodstorage.jsonable import JSONAble, JSONAbleList
from datetime import date, datetime

class Sample(object):
    '''
    Sample dataset generator
    '''

    def __init__(self):
        '''
        Constructor
        '''
        
    @staticmethod         
    def getSample(size):         
        listOfDicts=[]
        for index in range(size):
            listOfDicts.append({'pkey': "index%d" %index, 'cindex': index})
        return listOfDicts    
    
    @staticmethod
    def getCountries():
        countryJsonUrl="https://gist.githubusercontent.com/erdem/8c7d26765831d0f9a8c62f02782ae00d/raw/248037cd701af0a4957cce340dabb0fd04e38f4c/countries.json"
        with urllib.request.urlopen(countryJsonUrl) as url:
            countryList=json.loads(url.read().decode())
        return countryList
    
    @staticmethod
    def getCities():
        '''
        get a list of cities
        '''
        cityJsonUrl="https://raw.githubusercontent.com/lutangar/cities.json/master/cities.json"
        with urllib.request.urlopen(cityJsonUrl) as url:
            cityList=json.loads(url.read().decode())
        for city in cityList:
            city['cityId']="%s-%s" % (city['country'],city['name'])    
        return cityList
    
    @staticmethod
    def dob(isoDateString):
        ''' get the date of birth from the given iso date state'''
        #if sys.version_info >= (3, 7):
        #    dt=datetime.fromisoformat(isoDateString)
        #else:
        dt=datetime.strptime(isoDateString,"%Y-%m-%d")  
        return dt.date()   
    
    @staticmethod
    def getRoyals():
        return Royal.getSamples()
    
    @staticmethod
    def getRoyalsInstances():
        lod=Royal.getSamples()
        royals=[]
        for record in lod:
            royal=Royal()
            royal.fromDict(record)
            royals.append(royal)
        return royals
    
class Royals(JSONAbleList):
    def __init__(self,load=False):
        super(Royals, self).__init__("royals",clazz=None)
        if load:
            self.royals=Royal.getSamples()
        else:
            self.royals=None
        
class RoyalsORMList(JSONAbleList):
    def __init__(self,load=False):
        super(RoyalsORMList, self).__init__("royals",Royal)
        if load:
            self.royals=Sample.getRoyalsInstances()
        else:
            self.royals=None
            
class Royal(JSONAble):
    '''
    i am a single Royal
    '''
    
    @classmethod
    def getSamples(cls):
        listOfDicts=[
            {'name': 'Elizabeth Alexandra Mary Windsor', 'born': Sample.dob('1926-04-21'), 'numberInLine': 0, 'wikidataurl': 'https://www.wikidata.org/wiki/Q9682' },
            {'name': 'Charles, Prince of Wales',         'born': Sample.dob('1948-11-14'), 'numberInLine': 1, 'wikidataurl': 'https://www.wikidata.org/wiki/Q43274' },
            {'name': 'George of Cambridge',              'born': Sample.dob('2013-07-22'), 'numberInLine': 3, 'wikidataurl': 'https://www.wikidata.org/wiki/Q1359041'},
            {'name': 'Harry Duke of Sussex',             'born': Sample.dob('1984-09-15'), 'numberInLine': 6, 'wikidataurl': 'https://www.wikidata.org/wiki/Q152316'}
        ]
        today=date.today()
        for person in listOfDicts:
            born=person['born']
            age=(today - born).days / 365.2425
            person['age']=age
            person['ofAge']=age>=18
            person['lastmodified']=datetime.now()
        return listOfDicts
    
class Cities(JSONAbleList):
    def __init__(self,load=False):
        super(Cities, self).__init__("cities",clazz=None)
        if load:
            self.cities=Sample.getCities()      
        else:
            self.cities=None  