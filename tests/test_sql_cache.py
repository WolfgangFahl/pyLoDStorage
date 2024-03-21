"""
Created on 2024-03-21

@author: wf
"""
import os

from sqlmodel import Field, SQLModel

from lodstorage.query import EndpointManager, QueryManager
from lodstorage.sparql import SPARQL
from lodstorage.sql_cache import Cached, SqlDB
from tests.basetest import Basetest


class City(SQLModel, table=True):
    """
    represents a city
    """

    # ugly workaround for
    # https://stackoverflow.com/questions/37908767/table-roles-users-is-already-defined-for-this-metadata-instance
    __table_args__ = {"extend_existing": True}
    city_id: str = Field(primary_key=True)
    name: str
    population: float


class TestSqlCache(Basetest):
    """
    Tests the sql cache functionality
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.qm = QueryManager(lang="sparql", debug=False)
        self.endpoints = EndpointManager.getEndpoints(lang="sparql")
        self.wikidata = self.endpoints["qlever-wikidata"]
        self.db_path = "/tmp/cities_sql_cache.db"
        if os.path.isfile(self.db_path):
            os.remove(self.db_path)
        self.sql_db = SqlDB(self.db_path, debug=False)

    def testSqlCache(self):
        """
        test SQL cache handling
        """
        query = self.qm.queriesByName["cities"]
        sparql = SPARQL(self.wikidata.endpoint)
        qlod = sparql.queryAsListOfDicts(query.query)
        if self.debug:
            print(f"found {len(qlod)} records")
            limit = 10
            for i in range(limit):
                print(qlod[i])
        cache = Cached(
            City,
            sparql,
            sql_db=self.sql_db,
            query_name="cities",
            max_errors=1,
            debug=self.debug,
        )
        for force_query in [True, False]:
            cache.fetch_or_query(self.qm, force_query=force_query)
