"""
Created on 2025-06-04

@author: wf
"""

import json
from typing import Dict

from lodstorage.prefixes import Prefixes
from lodstorage.query import EndpointManager

from omnigraph.ominigraph_paths import OmnigraphPaths
from omnigraph.prefix_config import PrefixConfigs
from tests.basetest import Basetest


class TestPrefixConfig(Basetest):
    """
    Test Prefix Configuration
    """

    def setUp(self, debug=False, profile=True):
        """
        setUp the test environment
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.ogp = OmnigraphPaths()
        self.prefixes_yaml_path = self.ogp.examples_dir / "prefixes.yaml"
        self.pfix_configs = PrefixConfigs.ofYaml(self.prefixes_yaml_path)

    def get_all_prefixes(self) -> Dict[str, str]:
        """
        Get all prefixes from all prefix sets combined

        Returns:
            Dict[str, str]: Combined dictionary of all prefix mappings
        """
        all_prefixes = {}
        for prefix_config in self.pfix_configs.prefix_sets.values():
            all_prefixes.update(prefix_config.prefixes)
        return all_prefixes

    def test_load_prefixes(self):
        """
        test loading prefix configurations
        """
        pfix_configs = self.pfix_configs
        if self.debug:
            for set_name, pfix_config in pfix_configs.prefix_sets.items():
                print(f"{set_name}:{pfix_config.description}")
                print(json.dumps(pfix_config.prefixes, indent=2, default=str))
        self.assertTrue("wikidata" in pfix_configs.prefix_sets)
        self.assertTrue("wdt" in pfix_configs.prefix_sets["wikidata"].prefixes)

    def test_complete(self):
        """
        test we have references all PREFIX definitions of all default endpoints
        """
        endpoints = EndpointManager.getEndpoints(lang="sparql")
        all_config_prefixes = self.get_all_prefixes()
        missing_prefixes = set()

        for name, endpoint in endpoints.items():

            if hasattr(endpoint, "prefixes") and endpoint.prefixes:
                if self.debug:
                    pf_list = endpoint.prefixes.split("\n")
                    print(f"checking {len(pf_list)} prefixes of endpoint {name}")
                endpoint_prefixes = Prefixes.extract_prefixes(endpoint.prefixes)

                for prefix_name, prefix_uri in endpoint_prefixes.items():
                    if prefix_name not in all_config_prefixes:
                        missing_prefixes.add(f"{prefix_name}: {prefix_uri}")
                        if self.debug:
                            print(f"  Missing prefix: {prefix_name} -> {prefix_uri}")
        self.assertEqual(len(missing_prefixes), 0, f"Missing {len(missing_prefixes)} prefixes: {missing_prefixes}")

    def test_get_declarations(self):
        """
        test getting declarations works
        """
        prefix_sets = ["rdf", "blazegraph", "gov"]
        declarations = self.pfix_configs.get_selected_declarations(prefix_sets)

        if self.debug:
            print(f"Selected declarations for {prefix_sets}:")
            print(declarations)
        expected_prefixes = ["rdf", "bd", "gov"]
        for prefix in expected_prefixes:
            self.assertIn(prefix, declarations)
