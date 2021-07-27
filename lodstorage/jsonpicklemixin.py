# Json persistence
import jsonpickle
import os


class JsonPickleMixin(object):
    ''' 
    allow reading and writing derived objects from a jsonpickle file
    '''
    debug = False
    
    @staticmethod
    def checkExtension(jsonFile:str,extension:str=".json")->str:
        '''
        make sure the jsonFile has the given extension e.g. ".json"
        
        Args:
            jsonFile(str): the jsonFile name - potentially without ".json" suffix
        
        Returns:
            str: the jsonFile name with ".json" as an extension guaranteed
        '''
        if not jsonFile.endswith(extension):
            jsonFile=f"{jsonFile}{extension}" 
        return jsonFile    

    # read me from a json pickle file
    @staticmethod
    def readJsonPickle(jsonFileName,extension=".jsonpickle"):
        '''
        Args:
            jsonFileName(str): name of the file (optionally without ".json" postfix)
            extension(str): default file extension
        '''
        jsonFileName=JsonPickleMixin.checkExtension(jsonFileName, extension)
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
        
    def asJsonPickle(self)->str:
        '''
        convert me to JSON
        
        Returns:
            str: a JSON String with my JSON representation
        '''
        json = jsonpickle.encode(self)
        return json    

    def writeJsonPickle(self, jsonFileName:str, extension:str=".jsonpickle"):
        '''
        write me to the json file with the given name (optionally without postfix)
        
        Args:
            jsonFileName(str): name of the file (optionally without ".json" postfix)
            extension(str): default file extension
        '''
        jsonFileName=JsonPickleMixin.checkExtension(jsonFileName, extension)  
        json = self.asJsonPickle()
        if JsonPickleMixin.debug:
            print("writing %s" % (jsonFileName))
            print(json)
            print(self)
        jsonFile = open(jsonFileName, "w")
        jsonFile.write(json)
        jsonFile.close()
