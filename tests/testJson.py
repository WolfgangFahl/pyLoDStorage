'''
Created on 2020-09-12

@author: wf
'''
import unittest
import json
from lodstorage.sample import Royals,Cities
from lodstorage.jsonable import JSONAble
import time
import re

class TestJsonAble(unittest.TestCase):
    '''
    test JSON serialization with JsonAble mixin
    '''

    def setUp(self):
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
        
    def testJsonAble(self):
        '''
        test JSONAble
        '''
        examples=[Royals(),Cities()]
        index=0
        for useToJson in [True,False]:
            for example in examples:
                starttime=time.time()
                if useToJson:
                    jsonStr=example.toJSON()
                else:
                    jsonStr=example.asJSON()
                print(jsonStr[:500])
                print(jsonStr,file=open('/tmp/example%d.json' %index,'w'))
                index+=1
                print("->JSON took %7.3f s" % (time.time()-starttime))
                self.assertTrue(isinstance(jsonStr,str))
                starttime=time.time()
                jsonDict=json.loads(jsonStr)
                self.assertTrue(isinstance(jsonDict,dict))
                print(str(jsonDict)[:500])
                print("<-JSON took %7.3f s" % (time.time()-starttime))
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()