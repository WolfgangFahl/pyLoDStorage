# pyLoDStorage
python List of Dict (Table) Storage library

| | |
| :--- | :--- |
| **PyPi** | [![PyPI Status](https://img.shields.io/pypi/v/pyLodStorage.svg)](https://pypi.python.org/pypi/pyLodStorage/) [![License](https://img.shields.io/github/license/WolfgangFahl/pyLoDStorage.svg)](https://www.apache.org/licenses/LICENSE-2.0) [![pypi](https://img.shields.io/pypi/pyversions/pyLodStorage)](https://pypi.org/project/pyLodStorage/) [![format](https://img.shields.io/pypi/format/pyLodStorage)](https://pypi.org/project/pyLodStorage/) [![downloads](https://img.shields.io/pypi/dd/pyLodStorage)](https://pypi.org/project/pyLodStorage/) |
| **GitHub** | [![Github Actions Build](https://github.com/WolfgangFahl/pyLoDStorage/actions/workflows/build.yml/badge.svg)](https://github.com/WolfgangFahl/pyLoDStorage/actions/workflows/build.yml) [![Release](https://img.shields.io/github/v/release/WolfgangFahl/pyLoDStorage)](https://github.com/WolfgangFahl/pyLoDStorage/releases) [![Contributors](https://img.shields.io/github/contributors/WolfgangFahl/pyLoDStorage)](https://github.com/WolfgangFahl/pyLoDStorage/graphs/contributors) [![Last Commit](https://img.shields.io/github/last-commit/WolfgangFahl/pyLoDStorage)](https://github.com/WolfgangFahl/pyLoDStorage/commits/) [![GitHub issues](https://img.shields.io/github/issues/WolfgangFahl/pyLoDStorage.svg)](https://github.com/WolfgangFahl/pyLoDStorage/issues) [![GitHub closed issues](https://img.shields.io/github/issues-closed/WolfgangFahl/pyLoDStorage.svg)](https://github.com/WolfgangFahl/pyLoDStorage/issues/?q=is%3Aissue+is%3Aclosed) |
| **Code** | [![style-black](https://img.shields.io/badge/%20style-black-000000.svg)](https://github.com/psf/black) [![imports-isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/) |
| **Docs** | [![API Docs](https://img.shields.io/badge/API-Documentation-blue)](https://WolfgangFahl.github.io/pyLoDStorage/) [![formatter-docformatter](https://img.shields.io/badge/%20formatter-docformatter-fedcba.svg)](https://github.com/PyCQA/docformatter) [![style-google](https://img.shields.io/badge/%20style-google-3666d6.svg)](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) |
[![DOI](https://zenodo.org/badge/294325156.svg)](https://doi.org/10.5281/zenodo.17805335)

What it is
==========
pyLoDStorage allows to store table like data (List of Dicts) via

- Sqlite3
- JSON
- SPARQL

Installation
============
```bash
pip install pylodstorage
```

Get Sources
===========
```bash
git clone https://github.com/WolfgangFahl/pyLoDStorage
cd pyLodStorage
scripts/install
```

Testing
=======
```bash
scripts/test
```

Usage
=====
see [test cases](https://github.com/WolfgangFahl/pyLoDStorage/tree/master/tests)

Command Line Interface
======================
sparqlquery
```bash
sparqlquery -h
usage: sparqlquery [-h] [-d] [-ep ENDPOINTPATH] [-fp FORMATSPATH] [-li]
                   [--limit LIMIT] [--params PARAMS] [-le] [-sq]
                   [-qp QUERIESPATH] [-q QUERY] [-qf QUERYFILE]
                   [-qn QUERYNAME] [-en ENDPOINTNAME] [--method METHOD]
                   [-f {csv,json,html,xml,tsv,latex,mediawiki,raw,github}]
                   [-m MIMETYPE] [-p] [-raw] [-V]

commandline query of endpoints in diverse languages such as SPARQL/SQL

  Created by Wolfgang Fahl on 2020-09-10.
  Copyright 2020-2025 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE

options:
  -h, --help            show this help message and exit
  -d, --debug           set debug [default: False]
  -ep ENDPOINTPATH, --endpointPath ENDPOINTPATH
                        path to yaml file to configure endpoints to use for
                        queries
  -fp FORMATSPATH, --formatsPath FORMATSPATH
                        path to yaml file to configure formats to use for
                        query result documentation
  -li, --list           show the list of available queries
  --limit LIMIT         set limit parameter of query
  --params PARAMS       query parameters as Key-value pairs in the format
                        key1=value1,key2=value2
  -le, --listEndpoints  show the list of available endpoints
  -sq, --showQuery      show the query
  -qp QUERIESPATH, --queriesPath QUERIESPATH
                        path to YAML file with query definitions
  -q QUERY, --query QUERY
                        the query to run
  -qf QUERYFILE, --queryFile QUERYFILE
                        the query file to run
  -qn QUERYNAME, --queryName QUERYNAME
                        run a named query
  -en ENDPOINTNAME, --endpointName ENDPOINTNAME
                        Name of the endpoint to use for queries. Available by
                        default: ['wikidata', 'wikidata-main', 'wikidata-
                        scholarly', 'wikidata-legacy-full', 'wikidata-dbis',
                        'wikidata-qlever', ...]
  --method METHOD       method to be used for SPARQL queries
  -f {csv,json,html,xml,tsv,latex,mediawiki,raw,github}, --format {csv,json,html,xml,tsv,latex,mediawiki,raw,github}
  -m MIMETYPE, --mimeType MIMETYPE
                        MIME-type to use for the raw query
  -p, --prefixes        add predefined prefixes for endpoint
  -raw                  return the raw query result from the endpoint. (MIME
                        type defined over -f or -m)
  -V, --version         show program's version number and exit
```

## Documentation
[Wiki](http://wiki.bitplan.com/index.php/PyLoDStorage)

### Authors
* [Wolfgang Fahl](http://www.bitplan.com/Wolfgang_Fahl)
* [Tim Holzheim](https://www.semantic-mediawiki.org/wiki/Tim_Holzheim)
