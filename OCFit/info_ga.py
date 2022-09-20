# -*- coding: utf-8 -*-

#class for statistics about GA or DE fitting
#version 0.2.1
#update: 22.6.2022
# (c) Pavol Gajdos, 2018 - 2022

from pickle import load

import numpy as np

try: import matplotlib.pyplot as mpl
except:
    #import on server without graphic output
    import matplotlib
    matplotlib.use('Agg',force=True)
    import matplotlib.pyplot as mpl

def _plotsizeHelper(size):
    '''Helps to define the optimum plot size for large big-picture plots.'''
    c = 1
    r = 1
    while c * r < size:
        c += 1
        if c * r >= size: break
        else: r += 1
    return c, r

class InfoGA():
    '''statistics about GA or DE fitting from db file'''
    def __init__(self,dbfile):
        '''load db file from GA or DE'''
        f=open(dbfile,'rb')
        self.trace=load(f)
        f.close()

        path=dbfile.replace('\\','/')
        if path.rfind('/')>0: self.path=path[:path.rfind('/')+1]
        else: self.path=''

        self.chi2=self.trace['chi2']
        self.availableTrace=list(self.trace.keys())
        self.availableTrace.remove('chi2')
        self.pars=self.availableTrace
        gen=self.chi2.shape[0]
        size=self.chi2.shape[1]
        self.info={'gen':gen,'size':size}

    def Stats(self,path=None):
        '''print basic info about GA or DE'''
        text=['Number of generations: '+str(self.info['gen']),
              'Size of generation: '+str(self.info['size']),
              'Number of fitted parameters: '+str(len(self.availableTrace)),
              'Fitted parameters: '+', '.join(sorted(self.availableTrace)),
              'Minimal chi2 error: '+str(np.min(self.chi2))]
        i=np.unravel_index(np.argmin(self.chi2),self.chi2.shape)
        text.append('-------------------\nBest values of parameters:')
        for p in self.availableTrace:
            text.append(p+': '+str(self.trace[p][i]))

        if path is None: path=self.path
        f=open(path+'stat.txt','w')
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
            if log: mpl.semilogy(self.chi2)
            else: mpl.plot(self.chi2)

        if len(plot)>0:
            x=np.arange(1,self.info['gen']+1,1)
            mpl.figure()
            mpl.xlabel('Number of generations')
            mpl.ylabel(r'$\chi^2$ error')
            for pl in plot:
                if log: mpl.semilogy(x,pl[1],label=pl[0])
                else: mpl.plot(x,pl[1],label=pl[0])
            mpl.legend()
            return plot

    def Dev(self,param,new_fig=True,i_gen=None,log=True):
        '''plot deviance for given generation or for all, for given parameter'''
        val=[]
        dev=[]
        if i_gen is None:
            for gen in range(self.info['gen']):
                dev+=list(self.chi2[gen,:])
                val+=list(self.trace[param][gen,:])
        else:
            dev+=list(self.chi2[i_gen,:])
            val+=list(self.trace[param][i_gen,:])

        if new_fig: fig=mpl.figure()
        if log: mpl.semilogy(val,dev,'k.',alpha=0.2)
        else: mpl.plot(val,dev,'k.',alpha=0.2)
        mpl.xlabel(param)
        mpl.ylabel('chi2')
        #mpl.gca().ticklabel_format(useOffset=False)
        if new_fig: return fig

    def Devs(self,params=None,i_gen=None,log=True):
        '''plot deviances for multiple parameters'''
        if params is None: params=self.availableTrace

        if len(params)==1: return self.Dev(params[0],i_gen=i_gen,log=log)
        if isinstance(params,str): return self.Dev(params,i_gen=i_gen,log=log)

        fig=mpl.figure()
        cols,rows = _plotsizeHelper(len(params))
        for i,p in enumerate(params):
            mpl.subplot(rows, cols, i + 1)
            self.Dev(p,new_fig=False,i_gen=i_gen,log=log)
        fig.tight_layout()
        return fig


    def Hists(self,params=None,i_gen=-1):
        '''plot histogram for all parameters for given generation or all (i_gen=None)'''
        if params is None: params=self.availableTrace

        if len(params)==1: return self.Hist(params[0])
        if isinstance(params,str): return self.Hist(params)

        fig=mpl.figure()
        cols,rows = _plotsizeHelper(len(params))
        for i,p in enumerate(params):
            mpl.subplot(rows, cols, i + 1)
            self.Hist(p,new_fig=False,i_gen=i_gen)
        fig.tight_layout()
        return fig


    def Hist(self,param,new_fig=True,i_gen=-1):
        '''plot histogram for given generation for given parameters'''
        val=[]
        if i_gen is None:
            for gen in range(self.info['gen']): val+=list(self.trace[param][gen,:])
        else: val+=list(self.trace[param][i_gen,:])

        if new_fig: fig=mpl.figure()
        mpl.hist(val,bins=20,color='k')
        mpl.xlabel(param)
        mpl.gca().ticklabel_format(useOffset=False)
        if new_fig: return fig


    def Trace(self,par,best=True,mean=True,mini=False,maxi=False,i=None,full=False):
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
            mpl.gca().ticklabel_format(useOffset=False)

        if len(plot)>0:
            x=np.arange(1,self.info['gen']+1,1)
            mpl.figure()
            mpl.xlabel('Number of generations')
            mpl.ylabel(par)
            for pl in plot:
                mpl.plot(x,pl[1],label=pl[0])
            mpl.legend()
            mpl.gca().ticklabel_format(useOffset=False)
            return plot
