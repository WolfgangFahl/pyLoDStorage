"""
Created on 2024-01-28

@author: wf
"""
from tests.basetest import Basetest
from lodstorage.linkml import Schema
import json

class TestLinkMLSchema(Basetest):
    """
    test LinkML Schema compatibility
    """

    def test_linkml_types(self):
        """
        test reading official LinkML types
        """
        uri = "https://raw.githubusercontent.com/linkml/linkml-runtime/main/linkml_runtime/linkml_model/model/schema/types.yaml"
        schema=Schema.load_from_yaml_url(uri)
        debug=True
        if debug:
            print(json.dumps(schema.to_dict(),indent=2,default=str))
            print(schema.to_yaml())
