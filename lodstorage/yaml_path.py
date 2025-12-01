"""
Created on 2025-11-23

@author: wf
"""

import os
from pathlib import Path


class YamlPath:
    """
    provide path to loading configuration or data files by checking:
    - a provided path or an optional user-specific location (~/.pylodstorage).
    """

    @classmethod
    def getSamplePath(cls, yamlFileName: str) -> str:
        """
        Get the path to the sample YAML file usually located in ../sampledata relative to this script.

        Args:
            yamlFileName (str): The name of the YAML file.

        Returns:
            str: The absolute path to the sample file.
        """
        base_dir = os.path.dirname(__file__)
        sample_path = os.path.abspath(
            os.path.join(base_dir, "..", "sampledata", yamlFileName)
        )
        return sample_path

    @classmethod
    def getDefaultPath(cls, yamlFileName: str) -> str:
        """
        Get the path to the YAML file in the default user home location (.pylodstorage).

        Args:
            yamlFileName (str): The name of the YAML file.

        Returns:
            str: The full path to the file in the user's home directory.
        """
        home = str(Path.home())
        default_path = f"{home}/.pylodstorage/{yamlFileName}"
        return default_path

    @classmethod
    def getPaths(
        cls, yamlFileName: str, yamlPath: str = None, with_default: bool = True
    ):
        """
        Get a list of YAML file paths to be used for loading configuration/data.

        Args:
            yamlFileName (str): The name of the YAML file.
            yamlPath (str, optional): The full path to read from. Defaults to None (uses getSamplePath).
            with_default (bool, optional): Whether to include paths from the default location .pylodstorage in the Home directory. Defaults to True.

        Returns:
            list: A list of file paths found.
        """
        if yamlPath is None:
            yamlPath = cls.getSamplePath(yamlFileName)

        yamlPaths = [yamlPath]

        if with_default:
            homepath = cls.getDefaultPath(yamlFileName)
            if os.path.isfile(homepath):
                yamlPaths.append(homepath)

        return yamlPaths
