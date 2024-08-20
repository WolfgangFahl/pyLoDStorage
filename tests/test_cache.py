"""
Created on 2024-03-09

@author: wf
"""

from lodstorage.cache import CacheManager
from lodstorage.sample2 import Royals, Sample
from tests.basetest import Basetest


class TestCache(Basetest):
    """
    Tests the cache functionality
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testCache(self):
        """
        test cache handling
        """
        caches = {}
        cm = CacheManager("test_cache")
        cm.base_dir = "/tmp/"
        royals = Sample.get("royals")["QE2 heirs up to number in line 5"]
        royals_lod = []
        for royal in royals.members:
            royals_lod.append(royal.to_dict())
        cache = cm.store("royals_lod", royals_lod)
        caches[str(cache.path)] = cache
        for ext in [".json", ".yaml"]:
            cache = cm.store("royals", royals, ext, count_attr="members")
            caches[cache.path] = cache
        for path, cache in caches.items():
            if self.debug:
                print(cache)
            cls = Royals if not "_lod" in str(path) else None
            loaded_data = cm.load(cache.name, cache.extension, cls, cache.count_attr)
            loaded_count = None
            if isinstance(loaded_data, list) and len(loaded_data) > 0:
                loaded_count = len(loaded_data)
            elif isinstance(loaded_data, cls):
                loaded_count = len(getattr(loaded_data, cache.count_attr))
            if loaded_count:
                print(
                    f"Successfully loaded data from {path} with {loaded_count} items."
                )
            else:
                print(f"Failed to load or empty data from {path}.")
