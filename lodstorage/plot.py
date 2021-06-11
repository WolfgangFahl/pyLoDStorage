'''
Created on 2020-07-05

@author: wf
'''
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np
import os

class Plot(object):
    '''
    create Plot based on counters
    see https://stackoverflow.com/questions/19198920/using-counter-in-python-to-build-histogram
    '''
    def __init__(self, valueList,title,xlabel=None,ylabel=None,gformat='.png',fontsize=12,plotdir=None,debug=False):
        '''
        Constructor
        '''
        self.counter=Counter(valueList)
        self.valueList=valueList
        self.title=title
        self.xlabel=xlabel
        self.ylabel=ylabel
        self.fontsize=fontsize
        self.gformat=gformat
        self.debug=debug
        path=os.path.dirname(__file__)
        if plotdir is not None:
            self.plotdir=plotdir
        else:
            self.plotdir=path+"/../plots/"
            os.makedirs(self.plotdir,exist_ok=True)
            
    def titleMe(self):   
        ''' set my title and labels '''     
        plt.title(self.title, fontsize=self.fontsize)
        if self.xlabel is not None:
            plt.xlabel(self.xlabel)
        if self.ylabel is not None:    
            plt.ylabel(self.ylabel)
            
    def showMe(self,mode='show',close=True):
        ''' show me in the given mode '''
        if mode=="show":
            plt.show() 
        else:
            plt.savefig(self.plotdir+self.title+self.gformat)
        if close:    
            plt.close()    
            
    def barchart(self,mode='show'):
        ''' barchart based histogram for the given counter '''
        labels, values = zip(*self.counter.items())
        indexes = np.arange(len(labels))
        width = 1
        self.titleMe()
        plt.bar(indexes, values, width)
        plt.xticks(indexes + width * 0.5, labels)
        plt.yticks(np.arange(1,max(values)+1,step=1))
        self.showMe(mode)
        
    def showDebug(self):    
        print("   value  list: ",self.valueList)
        print("counter  items: ",self.counter.items())
        print("counter values: ",self.counter.values())
        print("counter   keys: ",self.counter.keys())
        
    def hist(self,mode="show"):
        ''' create histogram for the given counter '''
        if self.debug:
            self.showDebug()
        self.titleMe()
        # see https://stackoverflow.com/a/2162045/1497139
        plt.hist(self.valueList,bins=len(self.counter.keys()))
        self.showMe(mode)
        pass
            
        