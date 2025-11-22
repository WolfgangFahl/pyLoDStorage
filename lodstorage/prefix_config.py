"""
Created on 2025-06-04

@author: wf
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from basemkit.yamlable import lod_storable


@dataclass
class PrefixConfig:
    """
    Configuration for SPARQL prefixes
    """

    name: str
    url: Optional[str] = None
    prefix_prefix: Optional[str] = None

    description: Optional[str] = None
    prefixes: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """
        Set default values after initialization
        """
        if self.prefix_prefix is None:
            self.prefix_prefix = self.name


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

    prefix_sets: Dict[str, PrefixConfig] = field(default_factory=dict)

    @classmethod
    def ofYaml(cls, yaml_path: str) -> "PrefixConfigs":
        """Load prefix configurations from YAML file."""
        prefix_configs = cls.load_from_yaml_file(yaml_path)
        return prefix_configs

    def __post_init__(self):
        """ """
        self.all_prefixes = {}
        for prefix_config in self.prefix_sets.values():
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
