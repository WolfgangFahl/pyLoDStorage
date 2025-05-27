"""
Created on 2024-05-06

@author: wf
"""

from lodstorage.params import Params
from tests.basetest import Basetest


class TestParams(Basetest):
    """
    test the params handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_jinja_params(self):
        """
        test jinia_params
        """
        for sample, params_dict in [
            ("PREFIX target: <http://www.wikidata.org/entity/{{ q }}>", {"q": "Q80"})
        ]:
            params = Params(sample)
            if self.debug:
                print(params.params)
            self.assertEqual(["q"], params.params)
            self.assertTrue("q" in params.params_dict)
            params.params_dict = params_dict
            query = params.apply_parameters()
            self.assertEqual(
                "PREFIX target: <http://www.wikidata.org/entity/Q80>", query
            )

    def test_duplicate_params(self):
        """
        Test handling of duplicate parameters
        """
        sample = "Hello {{name}}, welcome to {{place}}! Nice to meet you, {{name}}."
        params_dict = {"name": "Alice", "place": "Wonderland"}

        params = Params(sample)
        if self.debug:
            print(params.params)

        self.assertEqual(["name", "place", "name"], params.params)
        self.assertTrue("name" in params.params_dict)
        self.assertTrue("place" in params.params_dict)

        params.params_dict = params_dict
        query = params.apply_parameters()

        self.assertEqual(
            "Hello Alice, welcome to Wonderland! Nice to meet you, Alice.", query
        )

        # Test apply_parameters_with_check
        result = params.apply_parameters_with_check(params_dict)
        self.assertEqual(
            "Hello Alice, welcome to Wonderland! Nice to meet you, Alice.", result
        )

        # Test error message for missing parameters
        with self.assertRaises(Exception) as context:
            params.apply_parameters_with_check()

        msg = str(context.exception)
        self.assertTrue("Query needs 2 parameters: name, place" in msg, msg)
