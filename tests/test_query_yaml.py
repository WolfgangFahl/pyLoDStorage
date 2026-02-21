"""
Created on 2025-06-12

@author: wf
"""

import os

from lodstorage.params import Param
from lodstorage.query import Query, QueryManager
from tests.basetest import Basetest


class TestQueryYaml(Basetest):
    """
    Test query yaml serialization handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.wikidata_queries_path = (
            f"{os.path.dirname(__file__)}/../sampledata/wikidata.yaml"
        )

    def testRead(self):
        """
        test reading a yaml file
        """
        qm = QueryManager(
            queriesPath=self.wikidata_queries_path,
            with_default=False,
            lang="sparql",
            debug=False,
        )
        self.assertTrue(len(qm.queriesByName) > 8)
        pass

    def testApplyParametersWithDefaultValues(self):
        """
        Test that apply_parameters_with_check falls back to default_value from
        param_list when param_dict is empty or None (issue #158).
        """
        from lodstorage.params import Params

        param = Param(name="limit", type="int", default_value="10")
        query_str = "SELECT * FROM foo LIMIT {{ limit }}"
        params = Params(query_str)

        # Empty dict — should use default, not raise
        result = params.apply_parameters_with_check(param_dict={}, param_list=[param])
        self.assertEqual("SELECT * FROM foo LIMIT 10", result)

        # None — should use default, not raise
        result = params.apply_parameters_with_check(param_dict=None, param_list=[param])
        self.assertEqual("SELECT * FROM foo LIMIT 10", result)

        # Explicit override takes precedence over default
        result = params.apply_parameters_with_check(
            param_dict={"limit": "25"}, param_list=[param]
        )
        self.assertEqual("SELECT * FROM foo LIMIT 25", result)

        # No default and no param_dict — must raise
        param_no_default = Param(name="limit", type="int")
        params2 = Params(query_str)
        with self.assertRaises(Exception) as ctx:
            params2.apply_parameters_with_check(
                param_dict=None, param_list=[param_no_default]
            )
        self.assertIn("limit", str(ctx.exception))

    def testQuerySerialization(self):
        """
        Test YAML serialization of Query objects with parameters
        """
        debug = self.debug
        debug = True

        # Create a Query with parameters manually
        input_param = Param(name="qids", type="str", description="Wikidata QIDs")
        output_param = Param(name="label", type="str", description="Entity label")

        query = Query(
            name="TestQuery",
            query="SELECT ?entity ?label WHERE { VALUES ?entity { {{qids}} } ?entity rdfs:label ?label }",
            param_list=[input_param],
            output=[output_param],
        )

        # Test serialization
        yaml_str = query.to_yaml()

        if debug:
            print("Query YAML:")
            print(yaml_str)

        # Should not contain Python object references
        self.assertNotIn("!!python/object:", yaml_str)

        # Test deserialization
        restored_query = Query.from_yaml(yaml_str)  # @UndefinedVariable
        self.assertEqual(restored_query.name, "TestQuery")
        self.assertEqual(len(restored_query.param_list), 1)
        self.assertEqual(len(restored_query.output), 1)
