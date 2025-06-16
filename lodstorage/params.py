"""
Created on 2024-05-06

@author: wf
"""

import argparse
import re
from dataclasses import field
from typing import Dict, Optional

from basemkit.yamlable import lod_storable


@lod_storable
class Param:
    """
    a parameter  (input or output) for a query
    """

    name: str
    type: str  # python type
    default_value: Optional[str] = None  # for input parameters only
    range: Optional[list] = field(default=None)  # for output only
    description: Optional[str] = None  # optional for doc/UI


class Params:
    """
    parameter handling
    """

    def __init__(
        self, query: str, illegal_chars: str = """"[;<>&|]"'""", with_audit: bool = True
    ):
        """
        constructor

        Args:
            query (str): the query to analyze for parameters
            illegal_chars (str): chars that may not be in the values
            with_audit (bool): if True audit parameters
        """
        self.illegal_chars = illegal_chars
        self.query = query
        self.with_audit = with_audit
        self.pattern = re.compile(r"{{\s*(\w+)\s*}}")
        self.params = self.pattern.findall(query)
        self.params_dict = {param: "" for param in self.params}
        self.has_params = len(self.params) > 0

    def set(self, params_dict: Dict):
        """
        set my params
        """
        self.params_dict = params_dict

    def audit(self) -> None:
        """
        Audit the usage of parameters in the query.

        Raises:
            ValueError: If potentially malicious values are detected in the parameter dictionary.
        """
        for param, value in self.params_dict.items():
            if isinstance(value, str):
                for char in self.illegal_chars:
                    if char in value:
                        raise ValueError(
                            f"Potentially malicious value detected for parameter '{param}'"
                        )

    def apply_parameters(self) -> str:
        """
        Replace Jinja templates in the query with corresponding parameter values.

        Returns:
            str: The query with Jinja templates replaced by parameter values.
        """
        if self.with_audit:
            self.audit()
        query = self.query
        for param, value in self.params_dict.items():
            pattern = re.compile(r"{{\s*" + re.escape(param) + r"\s*\}\}")
            value_str = str(value)
            query = re.sub(pattern, value_str, query)
        return query

    def apply_parameters_with_check(self, param_dict: dict = None) -> str:
        """
        Apply parameters to the query string with parameter checking.

        This method checks if the query requires parameters. If parameters are required
        but not provided, it raises an exception with a descriptive message. If parameters
        are provided, it applies them to the query.

        Args:
            param_dict (dict, optional): A dictionary of parameter names and values.

        Returns:
            str: The query string with parameters applied, if applicable.

        Raises:
            Exception: If parameters are required but not provided.
        """
        query = self.query
        if self.has_params:
            if not param_dict:
                param_names = list(
                    dict.fromkeys(self.params)
                )  # remove duplicates while preserving order
                if len(param_names) > 3:
                    displayed_params = ", ".join(param_names[:3]) + ", ..."
                else:
                    displayed_params = ", ".join(param_names)
                plural_suffix = "s" if len(param_names) > 1 else ""
                msg = f"Query needs {len(param_names)} parameter{plural_suffix}: {displayed_params}"
                raise Exception(msg)
            else:
                self.set(param_dict)
                query = self.apply_parameters()
        return query


class StoreDictKeyPair(argparse.Action):
    """
    Custom argparse action to store key-value pairs as a dictionary.

    This class implements an argparse action to parse and store command-line
    arguments in the form of key-value pairs. The pairs should be separated by
    a comma and each key-value pair should be separated by an equals sign.

    Example:
        --option key1=value1,key2=value2,key3=value3

    Reference:
        https://stackoverflow.com/a/42355279/1497139
    """

    def __call__(
        self,
        _parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        _option_string: Optional[str] = None,
    ) -> None:
        """
        Parse key-value pairs and store them as a dictionary in the namespace.

        Args:
            parser (argparse.ArgumentParser): The argument parser object.
            namespace (argparse.Namespace): The namespace to store the parsed values.
            values (str): The string containing key-value pairs separated by commas.
            option_string (Optional[str]): The option string, if provided.
        """
        my_dict = {}
        for kv in values.split(","):
            k, v = kv.split("=")
            my_dict[k] = v
        setattr(namespace, self.dest, my_dict)
