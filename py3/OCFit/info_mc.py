# -*- coding: utf-8 -*-

#class for statistics about GA fitting
#version 0.1.1
#update: 14.6.2017
# (c) Pavol Gajdos, 2018

import gc #cleaning var from RAM

from PyAstronomy.funcFit import TraceAnalysis

try: import pymc
except: 
    import warnings
    warnings.warn('Module pymc not found! Using FitMC will not be possible!')

import numpy as np

try: import matplotlib.pyplot as mpl
except:
    #import on server without graphic output
    import matplotlib
    matplotlib.use('Agg',force=True)
    import matplotlib.pyplot as mpl
    

class InfoMC():
    '''statistics about MC fitting from db file'''
    def __init__(self,dbfile):
        '''load db file'''
        self.dbfile=dbfile
        self.ta=TraceAnalysis(dbfile)
        path=dbfile.replace('\\','/')
        if path.rfind('/')>0: self.path=path[:path.rfind('/')+1]
        else: self.path=''
        self.pars=self.ta.availableParameters()
    
    def AllParams(self,eps=False):
        '''statistics about MCMC fitting for all params'''
        #summary plots
        if len(self.pars)>1:
            try: self.ta.plotCorr(point=True)
            except: self.ta.plotCorr()
            mpl.savefig(self.path+'corr.png')
            if eps: mpl.savefig(self.path+'corr.eps')
            mpl.close('all')
            self.ConfidInt(points=self.ta.db.trace(self.pars[0])().shape[0]<1000)
            mpl.savefig(self.path+'conf.png')
            if eps: mpl.savefig(self.path+'conf.eps')
            mpl.close('all')
        self.ta.plotHist()
        mpl.savefig(self.path+'hist.png')
        if eps: mpl.savefig(self.path+'hist.eps')
        mpl.close('all')
        self.ta.plotDeviance()
        mpl.savefig(self.path+'dev.png')
        if eps: mpl.savefig(self.path+'dev.eps')
        mpl.close('all')

        #correlation table
        if len(self.pars)>1:
            f=open(self.path+'corr.tbl','w')
            colWidth = {}
            for p in self.pars: colWidth[p]=max(len(p),9)
            head=(" "*(max(colWidth.values())+1))+"|"
            for p in self.pars: head+=(" %"+str(colWidth[p])+"s |")%p
            f.write(head+'\n')
            f.write("-"*len(head)+'\n')
            for p2 in self.pars:
                f.write(("%"+str(max(colWidth.values()))+"s |")%(p2))
                for p1 in self.pars:
                    coe=self.ta.pearsonr(p1,p2)[0]
                    f.write(" % 8.6f |"%coe)
                f.write('\n')
            f.write("-" * len(head))
            f.close()
        gc.collect()  #cleaning RAM...

    def Geweke(self,eps=False):
        '''plot geweke diagnostics'''
        db=pymc.database.pickle.load(self.dbfile)
        for p in self.pars:
            exec('gw=pymc.geweke(db.%s())' %p)
            if self.path=='': pymc.Matplot.geweke_plot(gw,p,suffix='_geweke')
            else: pymc.Matplot.geweke_plot(gw,p,path=self.path,suffix='_geweke')
            if eps: mpl.savefig(self.path+p+'_geweke.eps')
            mpl.close('all')
        del db
        gc.collect()  #cleaning RAM...


    def OneParam(self,name,eps=False):
        '''plots and info-files for one parameter from MCMC fitting'''
        f=open(self.path+name+'.stat','w')
        f.write('iter: '+str(self.ta.stateDic['sampler']['_iter'])+'\n')
        f.write('burn: '+str(self.ta.stateDic['sampler']['_burn'])+'\n')
        f.write('thin: '+str(self.ta.stateDic['sampler']['_thin'])+'\n\n')

        f.write(name+'\n')
        m=self.ta['deviance'].argmin()
        f.write('min chi2: '+str(self.ta[name][m])+'\n')
        f.write('mean: '+str(self.ta.mean(name))+'\n')
        f.write('median: '+str(self.ta.median(name))+'\n')
        f.write('STD: '+str(self.ta.std(name))+'\n')
        f.write('1sigma - 68%: '+str(self.ta.hpd(name,cred=0.682))+'\n')
        f.write('2sigma - 95%: '+str(self.ta.hpd(name,cred=0.955))+'\n')
        f.write('3sigma - 99%: '+str(self.ta.hpd(name,cred=0.997))+'\n')
        f.close()

        self.ta.plotTrace(name)
        mpl.savefig(self.path+name+'_trace.png')
        if eps: mpl.savefig(self.path+name+'_trace.eps')
        mpl.close('all')
        self.ta.plotTraceHist(name)
        mpl.savefig(self.path+name+'_traceHist.png')
        if eps: mpl.savefig(self.path+name+'_traceHist.eps')
        mpl.close('all')

        gc.collect() #cleaning RAM...


    def ConfidInt(self,nbins=20,points=True,levels=None,params=None):
        '''plot of Confidence Regions for 1 sigma=0.6827 and 2 sigma = 0.9545 (or 3 sigma = 0.9973)'''
        if params is None: params=self.ta.availableParameters()
        if levels is None: levels=[0.6827,0.9545]
        traces={}
        for p in params: traces[p]=self.ta[p]
        fontmap={1:10,2:8,3:6,4:5,5:4}
        k=1
        n=len(traces)
        for j in range(n):
            for i in range(n):
                if i>j:
                    tr1=traces[params[j]]
                    tr2=traces[params[i]]

                    L,xbins,ybins=np.histogram2d(tr1,tr2,nbins)
                    L[L==0]=1e-16
                    shape=L.shape
                    L=L.ravel()
                    i_sort=np.argsort(L)[::-1]
                    i_unsort=np.argsort(i_sort)
                    L_cumsum=L[i_sort].cumsum()
                    L_cumsum/=L_cumsum[-1]
                    xbins=0.5*(xbins[1:]+xbins[:-1])
                    ybins=0.5*(ybins[1:]+ybins[:-1])
                    sigma=L_cumsum[i_unsort].reshape(shape)

                    x_s=tr1.mean()
                    y_s=tr2.mean()

                    mpl.subplot(n-1,n-1,k)
                    mpl.xlabel(params[j],fontsize='x-small')
                    mpl.ylabel(params[i],fontsize='x-small')
                    tlabels=mpl.gca().get_xticklabels()
                    if n>6:
                        mpl.setp(tlabels,'fontsize',3)
                        tlabels=mpl.gca().get_yticklabels()
                        mpl.setp(tlabels,'fontsize',3)
                    else:
                        mpl.setp(tlabels,'fontsize',fontmap[n-1])
                        tlabels=mpl.gca().get_yticklabels()
                        mpl.setp(tlabels,'fontsize',fontmap[n-1])
                    mpl.contour(xbins,ybins,sigma.T,levels=levels)
                    if points: mpl.plot(tr1,tr2,'k.',ms=2)
                    mpl.plot(x_s,y_s,'r.',ms=10)
                if not i==j: k+=1
                gc.collect() #cleaning RAM...
