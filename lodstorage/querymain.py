'''
Created on 2022-02-13

@author: wf
'''
from lodstorage.version import Version
__version__ = Version.version
__date__ = Version.date
__updated__ = Version.updated

DEBUG = 0

import json
import requests
import sys
import traceback
import os
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from lodstorage.query import QueryManager, QueryResultDocumentation, EndpointManager, Format, ValueFormatter
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB
from lodstorage.csv import CSV

class QueryMain:
    '''
    Commandline handler
    '''
    @classmethod
    def main(cls,args):
        '''
        command line activation with parsed args
        
        Args:
            args(list): the command line arguments
        '''
        debug=args.debug
        endpoints=EndpointManager.getEndpoints(args.endpointPath)
        qm=QueryManager(lang=args.language,debug=debug,queriesPath=args.queriesPath)
        # preload ValueFormatter
        ValueFormatter.getFormats(args.formatsPath)
        if args.list:
            for name,query in qm.queriesByName.items():
                print(f"{name}:{query.title}")
        elif args.listEndpoints:
            for endpoint in endpoints.values():
                if hasattr(endpoint, "lang") and endpoint.lang==args.language:
                    print(endpoint)

        elif args.queryName is not None:
            if debug or args.showQuery:
                print(f"named query {args.queryName}:")
            if args.queryName not in qm.queriesByName:
                raise Exception(f"named query {args.queryName} not available")
            query=qm.queriesByName[args.queryName]
            if debug or args.showQuery:
                if hasattr(query, "description") and query.description is not None:
                    print(query.description)
                print(f"{args.language}:\n{query.query}")
            if args.endpointName:
                endpointConf=endpoints.get(args.endpointName)                
            if args.language=="sparql":
                method='POST'
                if args.endpointName:
                    endPointUrl=endpointConf.endpoint
                    method=endpointConf.method
                else:
                    endPointUrl=query.endpoint
                if args.method:
                    method=method
                sparql=SPARQL(endPointUrl,method=method)
                if args.prefixes:
                    query.query = f"{endpointConf.prefixes}\n{query.query}"
                if args.raw:
                    qres = cls.rawQuery(endPointUrl, query=query.query, resultFormat=args.format, mimeType=args.mimeType)
                    print(qres)
                    return
                if "wikidata" in args.endpointName and query.formats is None:
                    query.formats=["*:wikidata"]
                qlod=sparql.queryAsListOfDicts(query.query)
            elif args.language=="sql":
                sqlDB=SQLDB(endpointConf.endpoint)
                qlod=sqlDB.query(query.query)
            else:
                raise Exception(f"language {args.language} not known/supported")    
            if args.format is Format.csv:
                csv=CSV.toCSV(qlod)
                print(csv)
            elif args.format in [Format.latex,Format.github, Format.mediawiki]:
                doc=query.documentQueryResult(qlod, tablefmt=str(args.format),floatfmt=".0f")
                docstr=doc.asText()
                print (docstr)
            elif args.format in [Format.json]:
                print(json.dumps(qlod))

    @staticmethod
    def rawQuery(endpoint, query, resultFormat, mimeType):
        """
        returns raw result of the endpoint

        Args:
            endpoint: url of the endpoint
            query(str): query
            resultFormat(str): format of the result
            mimeType(str): mimeType

        Returns:
            raw result of the query
        """
        params={
            "query":query,
            "format": resultFormat
        }
        payload = {}
        if mimeType:
            headers = {
                'Accept': mimeType
            }
        else:
            headers={}

        response = requests.request("GET", endpoint, headers=headers, data=payload, params=params)
        return response.text
                
def mainSQL(argv=None):
    '''
    commandline for SQL queries
    '''
    main(argv,lang='sql')
    
def mainSPARQL(argv=None):
    '''
    commandline for SPARQL queries
    '''
    main(argv,lang='sparql')
    
def main(argv=None,lang=None): # IGNORE:C0111
    '''
    main program.
    
    commandline access to List of Dicts / Linked Open Data Queries
    '''
    if argv is None:
        argv=sys.argv[1:]
        
    program_name = os.path.basename(__file__)
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = "commandline query of endpoints in diverse languages such as SPARQL/SQL"
    user_name="Wolfgang Fahl"
    program_license = '''%s

  Created by %s on %s.
  Copyright 2020-2022 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc,user_name, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug", dest="debug",   action="store_true", help="set debug [default: %(default)s]")
        parser.add_argument('-ep', '--endpointPath', default=None, help="path to yaml file to configure endpoints to use for queries")
        parser.add_argument('-fp', '--formatsPath', default=ValueFormatter.formatsPath, help="path to yaml file to configure formats to use for querie result documentation")
        parser.add_argument('-en', '--endpointName', default="wikidata", help=f"Name of the endpoint to use for queries. Available by default: {EndpointManager.getEndpointNames()}")
        parser.add_argument('--method',help="method to be used for SPARQL queries")
        parser.add_argument('-f','--format', type=Format, choices=list(Format))
        parser.add_argument('-li','--list',action="store_true",help="show the list of available queries")
        parser.add_argument('-le','--listEndpoints',action="store_true",help="show the list of available endpoints") 
        parser.add_argument("-m", "--mimeType",help="MIME-type to use for the raw query")
        parser.add_argument("-p", "--prefixes",action="store_true",help="add predefined prefixes for endpoint")
        parser.add_argument('-sq','--showQuery',action="store_true",help="show the query") 
        parser.add_argument('-qp', '--queriesPath',help="path to YAML file with query definitions")
        parser.add_argument("-q", "--query",help="the query to run")
        parser.add_argument("-qn","--queryName",help="run a named query")
        parser.add_argument("-raw",action="store_true", help="return the raw query result from the endpoint. (MIME type defined over -f or -m)")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        if lang is None:
            parser.add_argument('-l','--language',help="the query language to use",required=True)
        args = parser.parse_args(argv)
        if lang is not None:
            args.language=lang
        QueryMain.main(args)
  
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if args.debug:
            print(traceback.format_exc())
        return 2     

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())