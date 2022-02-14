'''
Created on 2022-02-13

@author: wf
'''
__version__ = "0.1.6"
__date__ = '2020-09-10'
__updated__ = '2022-02-14'   
DEBUG = 0

from enum import Enum 
import sys
import os
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from lodstorage.query import QueryManager, QueryResultDocumentation
from lodstorage.sparql import SPARQL
from lodstorage.csv import CSV

class Format(Enum):
    csv = 'csv'
    json = 'json'
    xml = 'xml'
    tsv = 'tsv'
    latex = 'latex'
    mediawiki= 'mediawiki'
    github = 'github'
 
    def __str__(self):
        return self.value

class QueryMain:
    '''
    Commandline handler
    '''
    @classmethod
    def main(cls,args):
        '''
        command line activation with parsed args
        '''
        debug=args.debug
        if args.list:
            qm=QueryManager(lang=args.language,debug=debug,queriesPath=args.queriesPath)
            for name,query in qm.queriesByName.items():
                print(f"{name}:{query.title}")
        elif args.queryName is not None:
            if debug:
                print(f"named query {args.queryName}:")
            qm=QueryManager(lang=args.language,debug=debug,queriesPath=args.queriesPath)
            if args.queryName not in qm.queriesByName:
                raise Exception(f"named query {args.queryName} not available")
            query=qm.queriesByName[args.queryName]
            if args.language=="sparql":
                endpoint=SPARQL(query.endpoint)
                if "wikidata" in query.endpoint:
                    query.addFormatCallBack(QueryResultDocumentation.wikiDataLink)  
                qlod=endpoint.queryAsListOfDicts(query.query)
            if args.format is Format.csv:
                csv=CSV.toCSV(qlod)
                print(csv)
            elif args.format is Format.latex or args.format is Format.github or args.format is Format.mediawiki:
                doc=query.documentQueryResult(qlod, tablefmt=str(args.format),floatfmt=".0f")
                docstr=doc.asText()
                print (docstr)
                


def mainSQL(argv=None):
    main(argv,lang='SQL')
    
def mainSPARQL(argv=None):
    main(argv,lang='SPARQL')
    
def main(argv=None,lang=None): # IGNORE:C0111
    '''main program.'''

    if argv is None:
        argv=sys.argv[1:]
        
    program_name = os.path.basename(__file__)
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = "script to read event metadata from http://wikicfp.com"
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
        parser.add_argument('-e', '--endpoint', default="https://query.wikidata.org/sparql", help="SPARQL endpoint to use for queries")
        parser.add_argument('-f','--format', type=Format, choices=list(Format))
        parser.add_argument('-li','--list',action="store_true",help="show the list of available queries")
        parser.add_argument('-qp', '--queriesPath',help="path to YAML file with query definitions")
        parser.add_argument("-q", "--query",help="the query to run")
        parser.add_argument("-qn","--queryName",help="run a named query")
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
        return 2     

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())