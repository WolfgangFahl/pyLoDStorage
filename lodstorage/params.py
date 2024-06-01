"""
Created on 2024-05-06

@author: wf
"""
import argparse
import re
from typing import Dict, Optional


class Params:
    """
    parameter handling
    """

    def __init__(self, query: str, illegal_chars: str = """"[;<>&|]"'"""):
        """
        constructor

        Args:
            query(str): the query to analyze for parameters
            illegal_chars: chars that may not be in the values
        """
        self.illegal_chars = illegal_chars
        self.query = query
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
        self.audit()
        query = self.query
        for param, value in self.params_dict.items():
            pattern = re.compile(r"{{\s*" + re.escape(param) + r"\s*\}\}")
            query = re.sub(pattern, value, query)
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
