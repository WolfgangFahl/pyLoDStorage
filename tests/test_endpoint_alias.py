"""
Created on 2026-09-30

@author: wf
"""

import os
import tempfile
from unittest.mock import patch

from lodstorage.query import Endpoint, EndpointManager
from lodstorage.yaml_path import YamlPath
from tests.basetest import Basetest


class TestEndpointAlias(Basetest):
    """
    test abstract endpoint names resolved to concrete endpoints
    see https://github.com/WolfgangFahl/pyLoDStorage/issues/169
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def get_endpoints(self) -> dict:
        """
        get a set of concrete and abstract endpoints
        """
        endpoints = {
            "qlever-local": Endpoint(
                name="qlever-local",
                lang="sparql",
                database="qlever",
                endpoint="https://qlever.example.org/api",
            ),
            "wikidata": Endpoint(name="wikidata", alias="qlever-local"),
            "wd": Endpoint(name="wd", alias="wikidata"),
        }
        return endpoints

    def test_alias_resolves(self):
        """
        an alias and an alias chain resolve to the concrete endpoint
        """
        resolved = EndpointManager.resolve_aliases(self.get_endpoints())
        for name in ["wikidata", "wd"]:
            endpoint = resolved[name]
            if self.debug:
                print(endpoint)
            self.assertEqual(name, endpoint.name)
            self.assertEqual("qlever-local", endpoint.alias)
            self.assertEqual("https://qlever.example.org/api", endpoint.endpoint)
            self.assertEqual("qlever", endpoint.database)
            self.assertTrue(str(endpoint).startswith(f"{name} → qlever-local:"))
        self.assertIsNone(resolved["qlever-local"].alias)

    def test_alias_cycle(self):
        """
        an alias cycle raises
        """
        endpoints = {
            "a": Endpoint(name="a", alias="b"),
            "b": Endpoint(name="b", alias="a"),
        }
        with self.assertRaises(ValueError) as context:
            EndpointManager.resolve_aliases(endpoints)
        self.assertIn("cycle", str(context.exception))

    def test_alias_missing_target(self):
        """
        an alias to a missing endpoint raises
        """
        endpoints = {"wikidata": Endpoint(name="wikidata", alias="nowhere")}
        with self.assertRaises(ValueError) as context:
            EndpointManager.resolve_aliases(endpoints)
        self.assertIn("wikidata → nowhere", str(context.exception))

    def test_alias_from_yaml(self):
        """
        an alias in an endpoints.yaml file resolves via getEndpoints
        """
        yaml_text = """endpoints:
  'qlever-local':
    endpoint: https://qlever.example.org/api
    database: qlever
    method: POST
    lang: sparql
  'wikidata':
    alias: qlever-local
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_path = os.path.join(tmpdir, "endpoints.yaml")
            with open(yaml_path, "w") as yaml_file:
                yaml_file.write(yaml_text)
            endpoints = EndpointManager.getEndpoints(
                endpointPath=yaml_path, lang="sparql", with_default=False
            )
        self.assertIn("wikidata", endpoints)
        endpoint = endpoints["wikidata"]
        self.assertEqual("https://qlever.example.org/api", endpoint.endpoint)
        self.assertEqual("qlever-local", endpoint.alias)
        self.assertFalse(endpoint.local)

    def test_local_layer(self):
        """
        entries of the local ~/.pylodstorage layer are marked local,
        an abstract name redefined there is local as well
        """
        packaged_yaml = """endpoints:
  'wikidata':
    endpoint: https://query.example.org/sparql
    lang: sparql
  'dblp':
    endpoint: https://dblp.example.org/sparql
    lang: sparql
"""
        local_yaml = """endpoints:
  'qlever-local':
    endpoint: https://qlever.example.org/api
    database: qlever
    lang: sparql
  'wikidata':
    alias: qlever-local
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            packaged_path = os.path.join(tmpdir, "endpoints.yaml")
            local_path = os.path.join(tmpdir, "local_endpoints.yaml")
            for yaml_path, yaml_text in [
                (packaged_path, packaged_yaml),
                (local_path, local_yaml),
            ]:
                with open(yaml_path, "w") as yaml_file:
                    yaml_file.write(yaml_text)
            with patch.object(YamlPath, "getDefaultPath", return_value=local_path):
                endpoints = EndpointManager.getEndpoints(
                    endpointPath=packaged_path, lang="sparql", with_default=True
                )
        self.assertFalse(endpoints["dblp"].local)
        self.assertTrue(endpoints["qlever-local"].local)
        self.assertTrue(endpoints["wikidata"].local)
        self.assertEqual(
            "https://qlever.example.org/api", endpoints["wikidata"].endpoint
        )
