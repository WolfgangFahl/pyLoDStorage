"""
Created on 2025-11-23

@author: wf
"""

import os

from lodstorage.yaml_path import YamlPath
from tests.basetest import Basetest


class TestYamlPath(Basetest):
    """
    Tests YamlPath
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_yaml_path(self):
        """
        test yaml_path handling
        """
        yaml_files = [
            "dblp.yaml",
            "royals.yaml",
            "endpoints.yaml",
            "endpoints_qlever.yaml",
            "formats.yaml",
            "got.yaml",
            "prefixes.yaml",
            "queries.yaml",
            "royals_linkml_schema.yaml",
            "scholia.yaml",
            "trulytabular.yaml",
            "wf.yaml",
            "wikidata.yaml",
        ]

        for yamlFileName in yaml_files:
            # Test getSamplePath: sample file should exist
            sample_path = YamlPath.getSamplePath(yamlFileName)
            self.assertTrue(
                os.path.exists(sample_path),
                f"Sample file {yamlFileName} does not exist at {sample_path}",
            )

            # Test getDefaultPath: if it exists, basename should match
            default_path = YamlPath.getDefaultPath(yamlFileName)
            if default_path is not None:
                self.assertEqual(
                    os.path.basename(default_path),
                    yamlFileName,
                    f"Default path basename does not match for {yamlFileName}",
                )
