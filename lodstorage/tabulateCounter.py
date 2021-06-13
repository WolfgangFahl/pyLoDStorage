'''
Created on 2021-06-13

@author: wf
'''
from tabulate import tabulate

class TabulateCounter(object):
    '''
    helper for tabulating Counters
    '''


    def __init__(self, counter):
        '''
        Constructor
        '''
        self.counter=counter
    
    def mostCommonTable(self,headers=["#","key","count","%"],tablefmt='pretty',limit=50):
        '''
        get the most common Table
        '''
        bins=len(self.counter.keys())
        limit=min(bins,limit)
        total=sum(self.counter.values())
        binTable=[("total",bins,total)]
        for i,bintuple in enumerate(self.counter.most_common(limit)):
            key,count=bintuple
            binTable.append((i+1,key,count,count/total*100.0))
        
        table=tabulate(binTable,headers=headers,tablefmt=tablefmt,floatfmt=".2f")
        return table