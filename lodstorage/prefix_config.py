"""
Created on 2025-06-04

@author: wf
"""

import os
from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Optional

from basemkit.yamlable import lod_storable

from lodstorage.yaml_path import YamlPath


@dataclass
class PrefixConfig:
    """
    Configuration for SPARQL prefixes
    """

    name: str
    wikidata_id: Optional[str] = None
    url: Optional[str] = None
    prefix_prefix: Optional[str] = None

    description: Optional[str] = None
    prefixes: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """
        Set default values after initialization
        """
        # nothing to do yet
        pass

    def as_text(self) -> str:
        """
        Get prefixes as formatted text block.

        Returns:
            str: Newline-separated prefix declarations
        """
        text = "\n".join(self.prefixes.values())
        return text


@lod_storable
class PrefixConfigs:
    """Collection of prefix configurations loaded from YAML."""

    # ClassVars: IGNORED by @dataclass
    # Enables singleton
    _instance: ClassVar[Optional["PrefixConfigs"]] = None
    _prefixes_path: ClassVar[Optional[str]] = None

    prefix_sets: Dict[str, PrefixConfig] = field(default_factory=dict)

    @classmethod
    def get_instance(cls) -> "PrefixConfigs":
        """Get singleton PrefixConfigs (loads prefixes.yaml via YamlPath if needed)."""
        if cls._instance is None:
            cls._instance = cls.of_yaml()
        return cls._instance

    @classmethod
    def preload(cls, prefixes_path: str) -> "PrefixConfigs":
        """Preload singleton with specific prefixes path."""
        cls._instance = cls.of_yaml(prefixes_path)
        cls._prefixes_path = prefixes_path
        return cls._instance

    @classmethod
    def of_yaml(cls, yaml_path: str = None) -> "PrefixConfigs":
        """Load from YAML (uses prefixes.yaml via YamlPath if yaml_path=None)."""
        if yaml_path is None:
            paths = YamlPath.getPaths("prefixes.yaml")
            yaml_path = paths[0] if paths else None
        if yaml_path and os.path.exists(yaml_path):
            prefix_configs = cls.load_from_yaml_file(yaml_path)
        else:
            prefix_configs = cls()  # Empty if no file
        return prefix_configs

    def __post_init__(self):
        """
        initialize all prefixes and test prefix prefix for all prefix configs
        """
        self.all_prefixes = {}
        for key, prefix_config in self.prefix_sets.items():
            if prefix_config.prefix_prefix is None:
                prefix_config.prefix_prefix = key
        self.all_prefixes.update(prefix_config.prefixes)
        pass

    def get_selected_declarations(self, prefix_set: List[str]) -> str:
        """
        Get PREFIX declarations for selected prefix sets.

        Args:
            prefix_set: List of prefix set names to include

        Returns:
            str: Combined PREFIX declarations
        """
        selected_prefixes = {}
        for prefix_set_name in prefix_set:
            if prefix_set_name in self.prefix_sets:
                prefix_config = self.prefix_sets[prefix_set_name]
                selected_prefixes.update(prefix_config.prefixes)
        declarations = self.get_prefix_declarations(selected_prefixes)
        return declarations

    def get_prefix_declarations(self, prefixes: Dict[str, str] = None) -> str:
        """
        Convert prefixes to PREFIX declarations.

        Args:
            prefixes: Dictionary of prefix mappings, defaults to all_prefixes

        Returns:
            str: Newline-separated PREFIX declarations
        """
        if prefixes is None:
            prefixes = self.all_prefixes
        prefix_lines = []
        for prefix_name, prefix_uri in prefixes.items():
            prefix_lines.append(f"PREFIX {prefix_name}: <{prefix_uri}>")
            declarations = "\n".join(prefix_lines)
        return declarations
