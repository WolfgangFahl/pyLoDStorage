"""
Created on 2020-08-14

@author: wf
"""

import datetime
import time
from sys import stderr

import requests
from SPARQLWrapper import SPARQLWrapper2
from SPARQLWrapper.Wrapper import POST, POSTDIRECTLY
from lodstorage.version import Version
from lodstorage.lod import LOD
from lodstorage.params import Params
from lodstorage.rate_limiter import RateLimiter
from lodstorage.rdf_format import RdfFormat


class SPARQL(object):
    """
    wrapper for SPARQL e.g. Apache Jena, Virtuoso, Blazegraph

    :ivar url: full endpoint url (including mode)
    :ivar mode: 'query' or 'update'
    :ivar debug: True if debugging is active
    :ivar typedLiterals: True if INSERT should be done with typedLiterals
    :ivar profile(boolean): True if profiling / timing information should be displayed
    :ivar sparql: the SPARQLWrapper2 instance to be used
    :ivar method(str): the HTTP method to be used 'POST' or 'GET'
    """

    def __init__(
        self,
        url,
        mode="query",
        debug=False,
        isFuseki=False,
        typedLiterals=False,
        profile=False,
        agent=None,
        method="POST",
        calls_per_minute: int = None,
    ):
        """
        Construct a SPARQL wrapper

        Args:
            url (string): the base URL of the endpoint - the mode query/update is going to be appended
            mode (string): 'query' or 'update'
            debug (bool): True if debugging is to be activated
            typedLiterals (bool): True if INSERT should be done with typedLiterals
            profile (boolean): True if profiling / timing information should be displayed
            agent (string): the User agent to use
            method (string): the HTTP method to be used 'POST' or 'GET'
        """
        if isFuseki:
            self.url = f"{url}/{mode}"
        else:
            self.url = url
        self.mode = mode
        self.debug = debug
        self.typedLiterals = typedLiterals
        self.profile = profile
        if agent is None:
            agent=self.get_user_agent()
        self.sparql = SPARQLWrapper2(url)
        self.sparql.agent=agent
        self.method = method
        self.rate_limiter = RateLimiter(calls_per_minute=calls_per_minute or 60)  # Default 1/sec safe for Wikidata

    @classmethod
    def get_user_agent(cls) -> str:
        """
        Constructs a User-Agent string compliant with Wikimedia policy.
        """
        version = Version()
        user_agent= f"{version.name}/{version.version}"
        return user_agent

    @classmethod
    def fromEndpointConf(cls, endpointConf) -> "SPARQL":
        """
        create a SPARQL endpoint from the given EndpointConfiguration

        Args:
            endpointConf (Endpoint): the endpoint configuration to be used
        """
        if not endpointConf:
            raise ValueError("endpointConf must be specified")
        sparql = SPARQL(
            url=endpointConf.endpoint,
            method=endpointConf.method,
            calls_per_minute=endpointConf.calls_per_minute,
        )
        if hasattr(endpointConf, "auth"):
            authMethod = None
            if endpointConf.auth == "BASIC":
                authMethod = "BASIC"
            elif endpointConf.auth == "DIGEST":
                authMethod = "DIGEST"
            sparql.addAuthentication(
                endpointConf.user, endpointConf.password, method=authMethod
            )
        return sparql

    def addAuthentication(self, username: str, password: str, method: str = "BASIC"):
        """
        Add Http Authentication credentials to the sparql wrapper
        Args:
            username: name of the user
            password: password of the user
            method: HTTP Authentication method
        """
        if method:
            self.sparql.setHTTPAuth(method)

        if username and password:
            self.sparql.setCredentials(username, password)

    def test_query(
        self,
        query: str = "SELECT * WHERE { ?s ?p ?o } LIMIT 1",
        expected_bindings: int = 1,
    ) -> Exception:
        """
        Check if the SPARQL endpoint is available using a standard SPARQL query.

        Args:
            query (str): the SPARQL query to use for testing

        Returns:
            Exception if the endpoint fails
        """
        result = None
        try:
            query_result = self.rawQuery(query, method=self.method)
            bindings = query_result.bindings
            if not len(bindings) == expected_bindings:
                raise Exception(
                    f"SPARQL query {query} returned {len(bindings)} bindings instead of {expected_bindings}"
                )
        except Exception as ex:
            result = ex
        return result

    def post_query_direct(
        self, query: str, rdf_format: str = "n3", timeout: int = 60
    ) -> str:
        """
        Fetch raw RDF response via direct HTTP POST.

        Args:
            query: SPARQL CONSTRUCT query
            rdf_format: RDF format label (e.g. 'turtle', 'rdf-xml', 'json-ld', 'n3')
            timeout: timeout in seconds (default: 60)

        Returns:
            Raw RDF content as string

        Raises:
            Exception if HTTP request fails
        """
        rdf_format = RdfFormat.by_label(rdf_format)
        mime_type = rdf_format.mime_type
        headers = {
            "Accept": mime_type,
            "User-Agent": SPARQL.get_user_agent()
        }

        # Wrap the actual HTTP call with rate limiting
        @self.rate_limiter.rate_limited
        def _do_request():
            return requests.post(
                self.url,
                data={"query": query},
                headers=headers,
                timeout=timeout,
            )

        response = _do_request()

        if response.status_code != 200:
            msg = f"HTTP {response.status_code}: {response.text}"
            raise Exception(msg)

        return response.text.strip()

    def rawQuery(self, queryString: str, method=POST):
        """
        query with the given query string

        Args:
            queryString(str): the SPARQL query to be performed
            method(str): POST or GET - POST is mandatory for update queries
        Returns:
            list: the raw query result as bindings
        """
        queryString = self.fix_comments(queryString)
        self.sparql.setQuery(queryString)
        self.sparql.method = method
        bindings = self.sparql.query()
        return bindings

    def fix_comments(self, query_string: str) -> str:
        """
        make sure broken SPARQLWrapper will find comments
        """
        if query_string is None:
            return None
        return "#\n" + query_string

    def getValue(self, sparqlQuery: str, attr: str):
        """
        get the value for the given SPARQL query using the given attr

        Args:
            sparql(SPARQL): the SPARQL endpoint to ge the value for
            sparqlQuery(str): the SPARQL query to run
            attr(str): the attribute to get
        """
        if self.debug:
            print(sparqlQuery)
        qLod = self.queryAsListOfDicts(sparqlQuery)
        return self.getFirst(qLod, attr)

    def getValues(self, sparqlQuery: str, attrList: list):
        """
        get Values for the given sparlQuery and attribute list

        Args:
            sparqlQuery(str): the query which did not return any values
            attrList(list): the list of attributes
        """
        if self.debug:
            print(sparqlQuery)
        qLod = self.queryAsListOfDicts(sparqlQuery)
        if not (len(qLod) == 1):
            msg = f"getValues for {attrList} failed for {qLod}"
            raise Exception(msg)
        record = qLod[0]
        values = ()
        for attr in attrList:
            if not attr in record:
                msg = f"getValues failed for attribute {attr} which is missing in result record {record}"
                raise Exception(msg)
            recordTuple = (record[attr],)
            values += recordTuple
        return values

    def getFirst(self, qLod: list, attr: str):
        """
        get the column attr of the first row of the given qLod list

        Args:
            qLod(list): the list of dicts (returned by a query)
            attr(str): the attribute to retrieve

        Returns:
            object: the value
        """
        if len(qLod) == 1 and attr in qLod[0]:
            value = qLod[0][attr]
            return value
        raise Exception(f"getFirst for attribute {attr} failed for {qLod}")

    def getResults(self, jsonResult):
        """
        get the result from the given jsonResult

        Args:
            jsonResult: the JSON encoded result

        Returns:
            list: the list of bindings
        """
        return jsonResult.bindings

    def insert(self, insertCommand):
        """
        run an insert

        Args:
            insertCommand(string): the SPARQL INSERT command

        Returns:
            a response
        """
        self.sparql.setRequestMethod(POSTDIRECTLY)
        response = None
        exception = None
        try:
            response = self.rawQuery(insertCommand, method=POST)
            # see https://github.com/RDFLib/sparqlwrapper/issues/159#issuecomment-674523696
            # dummy read the body
            response.response.read()
        except Exception as ex:
            exception = ex
            if self.debug:
                print(ex)
        return response, exception

    def getLocalName(self, name):
        """
        retrieve valid localname from a string based primary key
        https://www.w3.org/TR/sparql11-query/#prefNames

        Args:
            name(string): the name to convert

        Returns:
            string: a valid local name
        """
        localName = "".join(ch for ch in name if ch.isalnum())
        return localName

    def insertListOfDicts(
        self,
        listOfDicts,
        entityType,
        primaryKey,
        prefixes,
        limit=None,
        batchSize=None,
        profile=False,
    ):
        """
        insert the given list of dicts mapping datatypes

        Args:
            entityType(string): the entityType to use as a
            primaryKey(string): the name of the primary key attribute to use
            prefix(string): any PREFIX statements to be used
            limit(int): maximum number of records to insert
            batchSize(int): number of records to send per request

        Return:
            a list of errors which should be empty on full success

        datatype maping according to
        https://www.w3.org/TR/xmlschema-2/#built-in-datatypes

        mapped from
        https://docs.python.org/3/library/stdtypes.html

        compare to
        https://www.w3.org/2001/sw/rdb2rdf/directGraph/
        http://www.bobdc.com/blog/json2rdf/
        https://www.w3.org/TR/json-ld11-api/#data-round-tripping
        https://stackoverflow.com/questions/29030231/json-to-rdf-xml-file-in-python
        """
        if limit is not None:
            listOfDicts = listOfDicts[:limit]
        else:
            limit = len(listOfDicts)
        total = len(listOfDicts)
        if batchSize is None:
            return self.insertListOfDictsBatch(
                listOfDicts, entityType, primaryKey, prefixes, total=total
            )
        else:
            startTime = time.time()
            errors = []
            # store the list in batches
            for i in range(0, total, batchSize):
                recordBatch = listOfDicts[i : i + batchSize]
                batchErrors = self.insertListOfDictsBatch(
                    recordBatch,
                    entityType,
                    primaryKey,
                    prefixes,
                    batchIndex=i,
                    total=total,
                    startTime=startTime,
                )
                errors.extend(batchErrors)
            if self.profile:
                print(
                    "insertListOfDicts for %9d records in %6.1f secs"
                    % (len(listOfDicts), time.time() - startTime),
                    flush=True,
                )
            return errors

    def insertListOfDictsBatch(
        self,
        listOfDicts,
        entityType,
        primaryKey,
        prefixes,
        title="batch",
        batchIndex=None,
        total=None,
        startTime=None,
    ):
        """
        insert a Batch part of listOfDicts

        Args:
            entityType(string): the entityType to use as a
            primaryKey(string): the name of the primary key attribute to use
            prefix(string): any PREFIX statements to be used
            title(string): the title to display for the profiling (if any)
            batchIndex(int): the start index of the current batch
            total(int): the total number of records for all batches
            starttime(datetime): the start of the batch processing

        Return:
            a list of errors which should be empty on full success
        """
        errors = []
        size = len(listOfDicts)
        if batchIndex is None:
            batchIndex = 0
        batchStartTime = time.time()
        if startTime is None:
            startTime = batchStartTime
        rdfprefix = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
        insertCommand = f"{rdfprefix}{prefixes}\nINSERT DATA {{\n"
        for index, record in enumerate(listOfDicts):
            if not primaryKey in record:
                errors.append(f"missing primary key {primaryKey} in record {index}")
            else:
                primaryValue = record[primaryKey]
                if primaryValue is None:
                    errors.append(
                        f"primary key {primaryKey} value is None in record {index}"
                    )
                else:
                    encodedPrimaryValue = self.getLocalName(primaryValue)
                    tSubject = f"{entityType}__{encodedPrimaryValue}"
                    insertCommand += f'  {tSubject} rdf:type "{entityType}".\n'
                    for keyValue in record.items():
                        key, value = keyValue
                        # convert key if necessary
                        key = self.getLocalName(key)
                        valueType = type(value)
                        if self.debug:
                            print("%s(%s)=%s" % (key, valueType, value))
                        tPredicate = f"{entityType}_{key}"
                        tObject = value
                        if valueType == str:
                            escapedString = self.controlEscape(value)
                            tObject = '"%s"' % escapedString
                        elif valueType == int:
                            if self.typedLiterals:
                                tObject = (
                                    '"%d"^^<http://www.w3.org/2001/XMLSchema#integer>'
                                    % value
                                )
                            pass
                        elif valueType == float:
                            if self.typedLiterals:
                                tObject = (
                                    '"%s"^^<http://www.w3.org/2001/XMLSchema#decimal>'
                                    % value
                                )
                            pass
                        elif valueType == bool:
                            pass
                        elif valueType == datetime.date:
                            # if self.typedLiterals:
                            tObject = (
                                '"%s"^^<http://www.w3.org/2001/XMLSchema#date>' % value
                            )
                            pass
                        elif valueType == datetime.datetime:
                            tObject = (
                                '"%s"^^<http://www.w3.org/2001/XMLSchema#dateTime>'
                                % value
                            )
                            pass
                        else:
                            errors.append(
                                "can't handle type %s in record %d" % (valueType, index)
                            )
                            tObject = None
                        if tObject is not None:
                            insertRecord = "  %s %s %s.\n" % (
                                tSubject,
                                tPredicate,
                                tObject,
                            )
                            insertCommand += insertRecord
        insertCommand += "\n}"
        if self.debug:
            print(insertCommand, flush=True)
        response, ex = self.insert(insertCommand)
        if response is None and ex is not None:
            errors.append("%s for record %d" % (str(ex), index))
        if self.profile:
            print(
                "%7s for %9d - %9d of %9d %s in %6.1f s -> %6.1f s"
                % (
                    title,
                    batchIndex + 1,
                    batchIndex + size,
                    total,
                    entityType,
                    time.time() - batchStartTime,
                    time.time() - startTime,
                ),
                flush=True,
            )
        return errors

    controlChars = [chr(c) for c in range(0x20)]

    @staticmethod
    def controlEscape(s):
        """
        escape control characters

        see https://stackoverflow.com/a/9778992/1497139
        """
        escaped = "".join(
            [
                (
                    c.encode("unicode_escape").decode("ascii")
                    if c in SPARQL.controlChars
                    else c
                )
                for c in s
            ]
        )
        escaped = escaped.replace('"', '\\"')
        return escaped

    def query(self, queryString, method=POST):
        """
        get a list of results for the given query

        Args:
            queryString(string): the SPARQL query to execute
            method(string): the method eg. POST to use

        Returns:
            list: list of bindings
        """
        queryResult = self.rawQuery(queryString, method=method)
        if self.debug:
            print(queryString)
        if hasattr(queryResult, "info"):
            if "content-type" in queryResult.info():
                ct = queryResult.info()["content-type"]
                if "text/html" in ct:
                    response = queryResult.response.read().decode()
                    if not "Success" in response:
                        raise ("%s failed: %s", response)
                return None
        jsonResult = queryResult.convert()
        return self.getResults(jsonResult)

    def queryAsListOfDicts(
        self,
        queryString,
        fixNone: bool = False,
        sampleCount: int = None,
        param_dict: dict = None,
    ):
        """
        Get a list of dicts for the given query (to allow round-trip results for insertListOfDicts)

        Args:
            queryString (str): the SPARQL query to execute
            fixNone (bool): if True add None values for empty columns in Dict
            sampleCount (int): the number of samples to check
            param_dict (dict): dictionary of parameter names and values to be applied to the query

        Returns:
            list: a list of Dicts

        Raises:
            Exception: If the query requires parameters but they are not provided
        """
        params = Params(queryString)
        queryString = params.apply_parameters_with_check(param_dict)

        records = self.query(queryString, method=self.method)
        listOfDicts = self.asListOfDicts(
            records, fixNone=fixNone, sampleCount=sampleCount
        )
        return listOfDicts

    @staticmethod
    def strToDatetime(value, debug=False):
        """
        convert a string to a datetime
        Args:
            value(str): the value to convert
        Returns:
            datetime: the datetime
        """
        dateFormat = "%Y-%m-%d %H:%M:%S.%f"
        if "T" in value and "Z" in value:
            dateFormat = "%Y-%m-%dT%H:%M:%SZ"
        dt = None
        try:
            dt = datetime.datetime.strptime(value, dateFormat)
        except ValueError as ve:
            if debug:
                print(str(ve))
        return dt

    def asListOfDicts(self, records, fixNone: bool = False, sampleCount: int = None):
        """
        convert SPARQL result back to python native

        Args:
            record(list): the list of bindings
            fixNone(bool): if True add None values for empty columns in Dict
            sampleCount(int): the number of samples to check

        Returns:
            list: a list of Dicts
        """
        resultList = []
        fields = None
        if fixNone:
            fields = LOD.getFields(records, sampleCount)
        for record in records:
            resultDict = {}
            for keyValue in record.items():
                key, value = keyValue
                datatype = value.datatype
                if datatype is not None:
                    if datatype == "http://www.w3.org/2001/XMLSchema#integer":
                        resultValue = int(value.value)
                    elif datatype == "http://www.w3.org/2001/XMLSchema#decimal":
                        resultValue = float(value.value)
                    elif datatype == "http://www.w3.org/2001/XMLSchema#boolean":
                        resultValue = value.value in ["TRUE", "true"]
                    elif datatype == "http://www.w3.org/2001/XMLSchema#date":
                        dt = datetime.datetime.strptime(value.value, "%Y-%m-%d")
                        resultValue = dt.date()
                    elif datatype == "http://www.w3.org/2001/XMLSchema#dateTime":
                        dt = SPARQL.strToDatetime(value.value, debug=self.debug)
                        resultValue = dt
                    else:
                        # unsupported datatype
                        resultValue = value.value
                else:
                    resultValue = value.value
                resultDict[key] = resultValue
            if fixNone:
                for field in fields:
                    if not field in resultDict:
                        resultDict[field] = None
            resultList.append(resultDict)
        return resultList

    def printErrors(self, errors):
        """
        print the given list of errors

        Args:
            errors(list): a list of error strings

        Returns:
            boolean: True if the list is empty else false
        """
        if len(errors) > 0:
            print("ERRORS:")
            for error in errors:
                print(error, flush=True, file=stderr)
            return True
        else:
            return False
