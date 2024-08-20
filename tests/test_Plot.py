"""
Created on 2020-07-05

@author: wf
"""

import unittest

from lodstorage.plot import Plot
from tests.basetest import Basetest


class TestPlot(Basetest):
    """
    test the Plot helper class
    """

    def testPlot(self):
        """test a plot based on a Counter"""
        valueList = ["A", "B", "A", "C", "A", "A"]
        plot = Plot(valueList, "barchart example", xlabel="Char", ylabel="frequency")
        plot.barchart(mode="save")
        plot.title = "histogram example"
        plot.debug = True
        plot.hist(mode="save")
        pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
