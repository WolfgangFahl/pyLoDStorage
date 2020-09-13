'''
Created on 2020-09-12

@author: wf
'''
import unittest
import json
from lodstorage.sample import Royals,Cities
from lodstorage.jsonable import JSONAble
from lodstorage.types import Types
import time

class TestJsonAble(unittest.TestCase):
    '''
    test JSON serialization with JsonAble mixin
    '''

    def setUp(self):
        self.profile=True
        pass

    def tearDown(self):
        pass
    
    def testSingleToDoubleQuote(self):
        jsonStr='''
        {
            "cities": [
            {
                "name": "Upper Hell's Gate"
            },
            {
                 "name": "N'zeto"
            }
            ]
        }
        '''
        listOfDicts=json.loads(jsonStr)
        dictStr=str(listOfDicts)   
        if self.debug:
            print(dictStr)
        jsonStr2=JSONAble.singleQuoteToDoubleQuote(dictStr)
        if self.debug:
            print(jsonStr2)
        self.assertEqual('''{"cities": [{"name": "Upper Hell's Gate"}, {"name": "N'zeto"}]}''',jsonStr2)
        
    def testSingleQuoteToDoubleQuoteStackoverflow(self):
        """
        see 
            - https://stackoverflow.com/a/63862387/1497139 
            - https://stackoverflow.com/a/50257217/1497139
        """
        singleQuotedExamples=[
            '''{'cities': [{'name': "Upper Hell's Gate"}, {'name': "N'zeto"}]''']
        for example in singleQuotedExamples:
            print (example)
            for useRegex in [False,True]:
                doubleQuoted=JSONAble.singleQuoteToDoubleQuote(example,useRegex=useRegex)
                print(doubleQuoted)
            print
            
    def testJsonAble(self):
        '''
        test JSONAble
        '''
        examples=[{
            'manager': Royals(),
            'listName': 'royals'
        }, {
            'manager': Cities(),
            'listName': 'cities'
        }
        ]
        index=0
        for useToJson in [True,False]:
            for example in examples:
                starttime=time.time()
                manager=example['manager']
                listName=example['listName']
                if useToJson:
                    jsonStr=manager.toJSON()
                else:
                    jsonStr=manager.asJSON()
                if self.debug:
                    print(jsonStr[:500])
                    #print(jsonStr,file=open('/tmp/example%d.json' %index,'w'))
                index+=1
                if self.profile:
                    print("->JSON for %d took %7.3f s" % (index, (time.time()-starttime)))
                self.assertTrue(isinstance(jsonStr,str))
                starttime=time.time()
                jsonDict=json.loads(jsonStr)
                self.assertTrue(isinstance(jsonDict,dict))
                if self.debug:
                    print(str(jsonDict)[:500])
                if self.profile:
                    print("<-JSON for %d took %7.3f s" % (index, time.time()-starttime))
                cls=manager.__class__
                types=Types(cls.__name__)
                types.getTypes(listName,manager.__dict__[listName])
                example1=cls()
                example1.fromJson(jsonStr,types=types)
                print(example1.__dict__)
                #self.assertEqual(example,example1)    
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()