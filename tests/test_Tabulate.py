"""
Created on 2021-06-13

@author: wf
"""
import unittest
from collections import Counter

from tabulate import tabulate

from lodstorage.sample import Royals, Sample
from lodstorage.tabulateCounter import TabulateCounter
from tests.basetest import Basetest


class TestTabulate(Basetest):
    """
    test tabulate support/compatibility
    """

    def testIssue24_IntegrateTabulate(self):
        """
        https://github.com/WolfgangFahl/pyLoDStorage/issues/24

        test https://pypi.org/project/tabulate/ support
        """
        show = self.debug
        # show=True
        royals = Royals(load=True)
        for fmt in ["latex", "grid", "mediawiki", "github"]:
            table = tabulate(royals.royals, headers="keys", tablefmt=fmt)
            if show:
                print(table)

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


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
