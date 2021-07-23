# Json persistence
import jsonpickle
import os


class JsonPickleMixin(object):
    ''' 
    allow reading and writing derived objects from a jsonpickle file
    '''
    debug = False

    # read me from a yaml file
    @staticmethod
    def readJson(name, postfix=".json"):
        jsonFileName = name
        if not name.endswith(postfix):
            jsonFileName = name + postfix
        # is there a jsonFile for the given name
        if os.path.isfile(jsonFileName):
            if JsonPickleMixin.debug:
                print("reading %s" % (jsonFileName))
            with open(jsonFileName) as jsonFile:    
                json = jsonFile.read()
            result = jsonpickle.decode(json)
            if (JsonPickleMixin.debug):
                print (json)
                print (result)
            return result
        else:
            return None
        
    def asJson(self)->str:
        '''
        convert me to JSON
        
        Returns:
            str: a JSON String with my JSON representation
        '''
        json = jsonpickle.encode(self)
        return json    

    def writeJson(self, name:str, postfix:str=".json"):
        '''
        write me to the json file with the given name (optionally without postfix)
        
        name(str): name of the file (optionally without ".json" postfix)
        postfix(str): default file extension
        '''
        if not name.endswith(postfix):
            jsonFileName = name + postfix
        else:
            jsonFileName = name    
        json = self.asJson()
        if JsonPickleMixin.debug:
            print("writing %s" % (jsonFileName))
            print(json)
            print(self)
        jsonFile = open(jsonFileName, "w")
        jsonFile.write(json)
        jsonFile.close()
