# -*- coding: utf-8 -*-

#class for statistics about GA fitting
#version 0.1.1
#update: 5.4.2017
# (c) Pavol Gajdos, 2018

from pickle import load

import numpy as np

try: import matplotlib.pyplot as mpl
except:
    #import on server without graphic output
    import matplotlib
    matplotlib.use('Agg',force=True)
    import matplotlib.pyplot as mpl


class InfoGA():
    '''statistics about GA fitting from db file'''
    def __init__(self,dbfile):
        '''load db file from GA'''    
        f=open(dbfile,'rb')
        self.trace=load(f)
        f.close()
                
        self.chi2=self.trace['chi2']
        self.availableTrace=self.trace.keys()
        self.availableTrace.remove('chi2')
        gen=self.chi2.shape[0]
        size=self.chi2.shape[1]
        self.info={'gen':gen,'size':size}
        
    def Info(self,name=None):
        '''print basic info about GA'''
        text=['Number of generations: '+str(self.info['gen']),
              'Size of generation: '+str(self.info['size']),
              'Number of fitted parameters: '+str(len(self.availableTrace)),
              'Fitted parameters: '+', '.join(sorted(self.availableTrace)),
              'Minimal chi2 error: '+str(np.min(self.chi2))]
        i=np.unravel_index(np.argmin(self.chi2),self.chi2.shape)
        text.append('-------------------\nBest values of parameters:')
        for p in self.availableTrace:
            text.append(p+': '+str(self.trace[p][i]))
            
        if name is None:
            print '------------------------------------'
            for t in text: print t
            print '------------------------------------'
        else:
            f=open(name,'w')
            for t in text: f.write(t+'\n')
            f.close()
            
        
    def PlotChi2(self,best=True,mean=True,besti=False,mini=False,maxi=False,i=None,full=False,log=True):
        '''plot chi2 error for best (Global), mean, best, minimal or maximal value in each generation or for selected individual or for all individuals'''
        plot=[]
        
        if best:
            chi_min=1e20
            temp=[]
            for gen in range(self.info['gen']):
                gen_min=np.min(self.chi2[gen,:])
                if gen_min<chi_min: chi_min=gen_min
                temp.append(chi_min)
            plot.append(['Global best solution',temp])
        
        if mean:
            temp=[]
            for gen in range(self.info['gen']):
                mean=np.mean(self.chi2[gen,:])
                temp.append(mean)
            plot.append(['Mean value',temp])            
                        
        if besti:
            temp=[]
            for gen in range(self.info['gen']):
                temp.append(np.min(self.chi2[gen,:]))
            plot.append(['Best solution',temp])
        
        if mini:
            temp=[]
            for gen in range(self.info['gen']):
                x=np.min(self.chi2[gen,:])
                temp.append(x)
            plot.append(['Minimal value',temp])
            
        if maxi:
            temp=[]
            for gen in range(self.info['gen']):
                x=np.max(self.chi2[gen,:])
                temp.append(x)
            plot.append(['Maximal value',temp])
            
        if i is not None:
            plot.append(['Individual '+str(i),self.chi2[:,i]])
            
        if full:
            plot=[]
            mpl.figure()
            mpl.xlabel('Number of generations')
            mpl.ylabel(r'$\chi^2$ error') 
            if log:  mpl.semilogy(self.chi2)
            else: mpl.plot(self.chi2)
            
        if len(plot)>0:
            x=np.arange(1,self.info['gen']+1,1)
            mpl.figure()
            mpl.xlabel('Number of generations')
            mpl.ylabel(r'$\chi^2$ error')            
            for pl in plot: 
                if log:  mpl.semilogy(x,pl[1],label=pl[0])
                else: mpl.plot(x,pl[1],label=pl[0])
            mpl.legend()
            return plot
            
    def Deviance(self,i=None,par=None):
        '''plot deviance for given generation or for all, for given parameters'''
        if par is None: par=self.availableTrace
        if not isinstance(par,list): par=[par]
        
        val={}
        for p in par: val[p]=[]
        dev=[]
        if i is None:
            for gen in range(self.info['gen']):
                dev+=list(self.chi2[gen,:])
                for p in par: val[p]+=list(self.trace[p][gen,:])
        else:
            dev+=list(self.chi2[i,:])
            for p in par: val[p]+=list(self.trace[p][i,:])                   
        
        n=len(par)
        mpl.figure()
        for j in range(n):
            mpl.subplot(2,int(np.ceil(n/2.)),j+1)
            mpl.plot(val[par[j]],dev,'.')
            mpl.xlabel(par[j])
            mpl.ylabel('chi2')
        return val,dev
    
    
    def GlobHist(self,par=None):
        '''plot histogram for given parameters for all generations'''
        if par is None: par=self.availableTrace
        if not isinstance(par,list): par=[par]        
        
        val={}
        for p in par: val[p]=[]
        for gen in range(self.info['gen']):
            for p in par: val[p]+=list(self.trace[p][gen,:])
               
        n=len(par)
        mpl.figure()
        for j in range(n):
            mpl.subplot(2,int(np.ceil(n/2.)),j+1)
            mpl.hist(val[par[j]])
            mpl.xlabel(par[j])
            
        return val
    
    def Hist(self,i=-1,par=None):
        '''plot histogram for given generation for given parameters'''
        if par is None: par=self.availableTrace
        if not isinstance(par,list): par=[par]
        
        n=len(par)
        mpl.figure()
        for j in range(n):
            mpl.subplot(2,int(np.ceil(n/2.)),j+1)
            mpl.hist(self.trace[par[j]][i])
            mpl.xlabel(par[j])
        

    def Plot(self,par,best=True,mean=True,mini=False,maxi=False,i=None,full=False):
        '''plot parameter trace for best, mean, minimal or maximal value in each generation or for selected individual or for all individuals'''
        if not par in self.availableTrace:
            raise KeyError('Parameter "'+par+'" is not available!')
        plot=[]

        if best:
            chi_min=1e20
            par_min=1e20
            temp=[]
            for gen in range(self.info['gen']):
                gen_min=np.argmin(self.chi2[gen,:])
                if self.chi2[gen,gen_min]<chi_min: 
                    chi_min=self.chi2[gen,gen_min]
                    par_min=self.trace[par][gen,gen_min]
                temp.append(par_min)
            plot.append(['Best solution',temp])
        
        if mean:
            temp=[]
            for gen in range(self.info['gen']):
                mean=np.mean(self.trace[par][gen,:])
                temp.append(mean)
            plot.append(['Mean value',temp])
        
        if mini:
            temp=[]
            for gen in range(self.info['gen']):
                x=np.min(self.trace[par][gen,:])
                temp.append(x)
            plot.append(['Minimal value',temp])
            
        if maxi:
            temp=[]
            for gen in range(self.info['gen']):
                x=np.max(self.trace[par][gen,:])
                temp.append(x)
            plot.append(['Maximal value',temp])
            
        if i is not None:
            plot.append(['Individual '+str(i),self.chi2[:,i]])
            
        if full:
            plot=[]
            mpl.figure()
            mpl.xlabel('Number of generations')
            mpl.ylabel(par) 
            mpl.plot(self.trace[par])
            
        if len(plot)>0:
            x=np.arange(1,self.info['gen']+1,1)
            mpl.figure()
            mpl.xlabel('Number of generations')
            mpl.ylabel(par)            
            for pl in plot: 
                mpl.plot(x,pl[1],label=pl[0])
            mpl.legend()
            return plot
            
        
