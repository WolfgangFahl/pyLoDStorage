"""
Created on 2024-03-09

@author: wf

refactored from https://github.com/WolfgangFahl/pyCEURmake/blob/main/ceurws/utils/json_cache.py
by Tim Holzheim
"""

import os
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from orjson import orjson

from lodstorage.yamlable import YamlAble, lod_storable


@lod_storable
class Cache:
    """
    Represents cache metadata and its file extension.

    Attributes:
        name: The name of the cache.
        extension: The file extension for the cache (e.g., 'json', 'csv').
        size: The size of the cache file in bytes.
        count: Optional; the number of items in the cache, if applicable.
        count_attr: the name of the attribute to determine the number of items, if applicable
        last_accessed: Optional; the last accessed timestamp of the cache.
    """

    name: str
    extension: str
    count_attr: str = None
    count: Optional[int] = None

    def set_path(self, base_path: str):
        """
        Set my path based on the given base_path and ensure the parent directory is created.

        Args:
            base_path (str): The base path where the directory should be created.
        """
        self.path = Path(f"{base_path}/{self.name}{self.extension}")
        # Ensure parent directory is created
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def is_stored(self) -> bool:
        """Determines if the cache file exists and is not empty."""
        return self.path.is_file() and self.path.stat().st_size > 1

    @property
    def size(self) -> int:
        cache_size = os.path.getsize(self.path) if os.path.isfile(self.path) else 0
        return cache_size

    @property
    def last_accessed(self) -> datetime:
        cache_last_accessed = (
            datetime.fromtimestamp(os.path.getmtime(self.path))
            if os.path.isfile(self.path)
            else None
        )
        return cache_last_accessed


@lod_storable
class CacheManager:
    """Manages multiple cache files with various extensions.

    Attributes:
        name: The name used for the base directory where cache files are stored.
        caches: A dictionary to track each cache's metadata.
    """

    name: str
    caches: Dict[str, Cache] = field(default_factory=dict)

    def __post_init__(self):
        self.base_dir = None

    def base_path(self) -> str:
        """Fetches the base path for this cache manager.

        Args:
            cache: The cache for which to generate the file path.

        Returns:
            The base path
        """
        if self.base_dir is None:
            self.base_dir = os.path.expanduser("~")
        base_path = os.path.join(self.base_dir, f".{self.name}")
        os.makedirs(base_path, exist_ok=True)
        return base_path

    def get_cache_by_name(self, lod_name, ext=".json") -> Cache:
        """
        Retrieves or creates a cache object by name and extension.

        Args:
            cache_name (str): The name of the cache to retrieve or create.
            ext (str): The file extension for the cache.

        Returns:
            Cache: An existing or newly created Cache object.
        """
        if lod_name in self.caches:
            cache = self.caches[lod_name + ext]
        else:
            cache = Cache(lod_name, ext)
            self.caches[lod_name + ext] = cache
        base_path = self.base_path()
        cache.set_path(base_path)
        return cache

    def load(
        self,
        lod_name: str,
        ext: str = ".json",
        cls: Optional[Type[YamlAble]] = None,
        count_attr: str = None,
    ) -> Union[List, Dict, None]:
        """
        Load data from a cache file. This method supports JSON and, if a relevant class is provided, other formats like YAML.

        Args:
            lod_name (str): The name of the list of dicts or class instances to read from cache.
            ext (str): The extension of the cache file, indicating the format (default is ".json").
            cls (Optional[Type[YamlAble]]): The class type for deserialization. This class must have from_json() or from_yaml()
                                             class methods for deserialization, depending on the file extension.
            count_attr(str): the name of attribute data_to_store for updating the cache.count s
        Returns:
            Union[List, Dict, None]: A list of dicts, a list of class instances, a single dict, or None if the cache is not stored.
        """
        cache = self.get_cache_by_name(lod_name, ext)
        cache.count_attr = count_attr
        result = None
        if cache.is_stored:
            if ext == ".json":
                if cls and hasattr(cls, "load_from_yaml_file"):
                    result = cls.load_from_json_file(
                        cache.path
                    )  # Adjusted for class method
                else:
                    with open(cache.path, encoding="utf-8") as json_file:
                        result = orjson.loads(json_file.read())
            elif ext == ".yaml":
                if cls and hasattr(cls, "load_from_yaml_file"):
                    result = cls.load_from_yaml_file(
                        cache.path
                    )  # Adjusted for class method
                else:
                    raise ValueError(
                        "YAML deserialization requires a cls parameter that is a subclass of YamlAble."
                    )
            else:
                raise ValueError(f"Unsupported file extension {ext} for loading.")

            # Dynamic count update based on count_attr if applicable
            if count_attr and hasattr(result, count_attr):
                cache.count = len(getattr(result, count_attr))
            elif isinstance(result, list):
                cache.count = len(result)

        return result

    def store(
        self,
        cache_name: str,
        data_to_store: Union[List, Dict],
        ext: str = ".json",
        count_attr: str = None,
    ) -> Cache:
        """
        Stores data into a cache file, handling serialization based on the specified file extension.
        Supports JSON and YAML formats, and custom serialization for classes that provide specific
        serialization methods.

        Args:
            cache_name (str): The identifier for the cache where the data will be stored.
            data_to_store (Union[List, Dict]): The data to be stored in the cache. This can be a list of dictionaries,
                                               a single dictionary, or instances of data classes if `cls` is provided.
            ext (str): The file extension indicating the serialization format (e.g., '.json', '.yaml').
                       Defaults to '.json'.
            count_attr(str): the name of attribute data_to_store for updating the cache.count s

        Raises:
            ValueError: If the file extension is unsupported or if required methods for serialization are not implemented in `cls`.
        """
        cache = self.get_cache_by_name(cache_name, ext)
        cache.count_attr = count_attr
        cache.set_path(self.base_path())

        if ext == ".json":
            # Check if  cls has a method `save_to_json_file`
            # that accepts a file path and data to store
            if isinstance(data_to_store, list):
                json_str = orjson.dumps(data_to_store, option=orjson.OPT_INDENT_2)
                with cache.path.open("wb") as json_file:
                    json_file.write(json_str)
            else:
                if hasattr(data_to_store, "save_to_json_file"):
                    data_to_store.save_to_json_file(str(cache.path))
                else:
                    raise ValueError(
                        "JSON serialization requires a 'save_to_json_file' method"
                    )
        elif ext == ".yaml":
            if hasattr(data_to_store, "save_to_yaml_file"):
                # Assuming cls has a method `save_to_yaml_file` that accepts a file path and data to store
                data_to_store.save_to_yaml_file(str(cache.path))
            else:
                raise ValueError(
                    "YAML serialization requires a 'save_to_yaml_file' method."
                )
        else:
            raise ValueError(f"Unsupported file extension {ext}.")

        # Update cache metadata post storing
        if count_attr and hasattr(data_to_store, count_attr):
            cache.count = len(getattr(data_to_store, count_attr))
        elif isinstance(data_to_store, list):
            cache.count = len(data_to_store)

        return cache
