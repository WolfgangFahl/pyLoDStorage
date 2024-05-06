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
