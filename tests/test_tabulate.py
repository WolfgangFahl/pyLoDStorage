"""
Created on 2021-06-13

@author: wf
"""

from collections import Counter

from tabulate import tabulate

from lodstorage.sample2 import Sample
from lodstorage.tabulateCounter import TabulateCounter
from tests.basetest import Basetest


class TestTabulate(Basetest):
    """
    test tabulate support/compatibility
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testIssue24_IntegrateTabulate(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/24

        test https://pypi.org/project/tabulate/ support
        """
        show = self.debug
        # show = True
        royals_lod = Sample.getRoyals()
        for fmt in ["latex", "grid", "mediawiki", "github"]:
            table = tabulate(royals_lod, headers="keys", tablefmt=fmt)
            if show:
                print(table)
            self.assertTrue("Charles III" in table)

        cities = Sample.getCities()
        counter = Counter()
        for city in cities:
            counter[city["country"]] += 1
        tabulateCounter = TabulateCounter(counter)
        for fmt in ["latex", "grid", "mediawiki", "github"]:
            table = tabulateCounter.mostCommonTable(tablefmt=fmt, limit=7)
            if show:
                print(table)
        pass
