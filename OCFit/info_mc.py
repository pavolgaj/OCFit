# -*- coding: utf-8 -*-

#class for statistics about MC fitting from emcee package
#version 0.2.1
#update: 22.6.2022
# (c) Pavol Gajdos, 2018-2022

import gc #cleaning var from RAM

import warnings

try: import emcee
except ModuleNotFoundError: warnings.warn('Module emcee not found! Using FitMC will not be possible!')

import numpy as np
from scipy.stats import pearsonr

try: import corner
except ModuleNotFoundError: warnings.warn('Module corner not found! Ploting corner plot will not be possible!')

try:
    import matplotlib.pyplot as mpl
    fig=mpl.figure()
    mpl.close(fig)
except:
    #import on server without graphic output
    try: mpl.switch_backend('Agg')
    except:
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

class InfoMC():
    '''statistics about MC fitting from db file'''
    def __init__(self,dbfile):
        '''load db file'''
        self.ta=np.load(dbfile,allow_pickle=True)
        path=dbfile.replace('\\','/')
        if path.rfind('/')>0: self.path=path[:path.rfind('/')+1]
        else: self.path=''
        self.pars=list(self.ta['pnames'])

        self.flat=self.ta['chain'].reshape((self.ta['chain'].shape[0]*self.ta['chain'].shape[1],self.ta['chain'].shape[2]),order='F')
        self.flatprob=self.ta['lnp'].reshape((self.ta['lnp'].shape[0]*self.ta['lnp'].shape[1]),order='F')


    def AllParams(self,eps=False):
        '''statistics about MCMC fitting for all params'''
        #summary plots
        if len(self.pars)>1:
            try:
                self.Corner()
                mpl.savefig(self.path+'corner.png')
                if eps: mpl.savefig(self.path+'corner.eps')
                mpl.close('all')
            except NameError: warnings.warn('Ploting corner plot is not be possible!')

            self.Corr()
            mpl.savefig(self.path+'corr.png')
            if eps: mpl.savefig(self.path+'corr.eps')
            mpl.close('all')

            self.ConfidInt(points=self.flat.shape[0]<1000)  #only if not many points
            mpl.savefig(self.path+'conf.png')
            if eps: mpl.savefig(self.path+'conf.eps')
            mpl.close('all')

        self.Hists()
        mpl.savefig(self.path+'hist.png')
        if eps: mpl.savefig(self.path+'hist.eps')
        mpl.close('all')
        self.Devs()
        mpl.savefig(self.path+'dev.png')
        if eps: mpl.savefig(self.path+'dev.eps')
        mpl.close('all')

        self.CorrTab()

        gc.collect()  #cleaning RAM...

    def CorrTab(self,path=None):
        #correlation table
        if path is None: path=self.path
        if len(self.pars)>1:
            f=open(path+'corr.tbl','w')
            colWidth = {}
            for p in self.pars: colWidth[p]=max(len(p),9)
            head=(" "*(max(colWidth.values())+1))+"|"
            for p in self.pars: head+=(" %"+str(colWidth[p])+"s |")%p
            f.write(head+'\n')
            f.write("-"*len(head)+'\n')
            for i2,p2 in enumerate(self.pars):
                f.write(("%"+str(max(colWidth.values()))+"s |")%(p2))
                for i1,p1 in enumerate(self.pars):
                    coe=pearsonr(self.flat[:,i1],self.flat[:,i2])[0]
                    f.write(" % 8.6f |"%coe)
                f.write('\n')
            f.write("-" * len(head))
            f.close()


    def OneParam(self,name,eps=False):  #todo
        '''plots and info-files for one parameter from MCMC fitting'''
        self.Stats(name)

        self.Trace(name)
        mpl.savefig(self.path+name+'_trace.png')
        if eps: mpl.savefig(self.path+name+'_trace.eps')
        mpl.close('all')

        self.MultiPlot(name)
        mpl.savefig(self.path+name+'_all.png')
        if eps: mpl.savefig(self.path+name+'_all.eps')
        mpl.close('all')

        gc.collect() #cleaning RAM...

    def Stats(self,name,path=None):
        if path is None: path=self.path
        f=open(path+name+'_stat.txt','w')

        sampleArgs=self.ta['sampleArgs'].item()

        f.write('iter: '+str(sampleArgs['iters'])+'\n')
        f.write('burn: '+str(sampleArgs['burn'])+'\n')
        f.write('thin: '+str(sampleArgs['binn'])+'\n')
        f.write('walkers: '+str(sampleArgs['nwalker'])+'\n\n')

        f.write(name+'\n')
        i=self.pars.index(name)
        m=np.argmax(self.flatprob)
        f.write('max. prob.: '+str(self.flat[m,i])+'\n')
        f.write('mean: '+str(np.mean(self.flat[:,i]))+'\n')
        f.write('median: '+str(np.median(self.flat[:,i]))+'\n')
        f.write('STD: '+str(np.std(self.flat[:,i]))+'\n')
        f.write('1sigma - 68%: '+str(np.quantile(self.flat[:,i],1-0.6827))+' ... '+str(np.quantile(self.flat[:,i],0.6827))+'\n')
        f.write('2sigma - 95%: '+str(np.quantile(self.flat[:,i],1-0.9545))+' ... '+str(np.quantile(self.flat[:,i],0.9545))+'\n')
        f.write('3sigma - 99%: '+str(np.quantile(self.flat[:,i],1-0.9973))+' ... '+str(np.quantile(self.flat[:,i],0.9973))+'\n')
        f.close()


    def Corner(self,params=None):
        '''plot corner plot'''
        values=[]
        tr=[]
        if params is None: params=self.pars
        for p in params:
            i=self.pars.index(p)
            values.append(np.median(self.flat[:,i]))
            tr.append(self.flat[:,i])
        fig=corner.corner(np.array(tr).transpose(),labels=params,truths=values,quantiles=[1-0.6827,0.6827],show_titles=True)
        return fig

    def Hist(self,param,new_fig=True,label=True):
        '''plot histogram for one parameter'''
        i=self.pars.index(param)
        if new_fig: fig=mpl.figure()
        mpl.hist(self.flat[:,i],bins=20,color='k')
        if label: mpl.xlabel(param)
        mpl.gca().ticklabel_format(useOffset=False)
        if new_fig: return fig

    def Hists(self,params=None):
        '''plot histograms for multiple parameters'''
        if params is None: params=self.pars

        if len(params)==1: return self.Hist(params[0])
        if isinstance(params,str): return self.Hist(params)

        fig=mpl.figure()
        cols,rows = _plotsizeHelper(len(params))
        for i,p in enumerate(params):
            mpl.subplot(rows, cols, i + 1)
            self.Hist(p,new_fig=False)
        fig.tight_layout()
        return fig

    def Dev(self,param,new_fig=True,label=True):
        '''plot deviance for one parameter'''
        i=self.pars.index(param)
        if new_fig: fig=mpl.figure()
        mpl.plot(self.flat[:,i],self.flatprob,'k.',alpha=0.2)
        if label:
            mpl.xlabel(param)
            mpl.ylabel('log probability')
        mpl.gca().invert_yaxis()
        mpl.gca().ticklabel_format(useOffset=False)
        if new_fig: return fig

    def Devs(self,params=None):
        '''plot deviances for multiple parameters'''
        if params is None: params=self.pars

        if len(params)==1: return self.Dev(params[0])
        if isinstance(params,str): return self.Dev(params)

        fig=mpl.figure()
        cols,rows = _plotsizeHelper(len(params))
        for i,p in enumerate(params):
            mpl.subplot(rows, cols, i + 1)
            self.Dev(p,new_fig=False)
        fig.tight_layout()
        return fig

    def Acorr(self,param,new_fig=True,label=True):
        '''autocorrelation plot for one parameter'''
        i=self.pars.index(param)
        if new_fig: fig=mpl.figure()
        acorr=emcee.autocorr.function_1d(self.flat[:,i])
        x=np.arange(-len(acorr),len(acorr))
        acorr=np.append(acorr[::-1],acorr)
        mpl.plot(x,acorr,'k-',lw=1)
        mpl.plot([x[0],x[-1]],[0,0],'k-')
        if label: mpl.title(param)
        mpl.xlim(-200,200)
        mpl.gca().ticklabel_format(useOffset=False)
        if new_fig: return fig

    def Trace(self,param,new_fig=True,label=True):
        '''plot traces for one param'''
        i=self.pars.index(param)
        if new_fig: fig=mpl.figure()
        for j in range(self.ta['chain'].shape[0]):
            mpl.plot(self.ta['chain'][j,:,i],'k-',alpha=0.2)
        if label: mpl.ylabel(param)
        mpl.gca().ticklabel_format(useOffset=False)
        if new_fig: return fig

    def MultiPlot(self,param):
        '''plot trace, acorr, hist and deviance for one param'''
        fig=mpl.figure()
        mpl.subplot(2,2,1)
        self.Trace(param,new_fig=False,label=False)
        mpl.title('trace')
        mpl.subplot(2,2,2)
        self.Hist(param,new_fig=False,label=False)
        mpl.title('hist')
        mpl.subplot(2,2,3)
        self.Acorr(param,new_fig=False,label=False)
        mpl.title('acorr')
        mpl.subplot(2,2,4)
        self.Dev(param,new_fig=False,label=False)
        mpl.title('log prob.')
        fig.suptitle(param)
        fig.tight_layout()
        return fig

    def Corr(self,params=None):
        '''plot of Correlations between params'''
        if params is None: params=self.pars
        traces={}
        for p in params: traces[p]=self.flat[:,self.pars.index(p)]
        fontmap={1:10,2:8,3:6,4:5,5:4}
        k=1
        n=len(traces)

        fig=mpl.figure()
        for j in range(n):
            for i in range(n):
                if i>j:
                    tr1=traces[params[j]]
                    tr2=traces[params[i]]

                    x_s=tr1.mean()
                    y_s=tr2.mean()

                    mpl.subplot(n-1,n-1,k)
                    mpl.xlabel(params[j],fontsize='x-small')
                    mpl.ylabel(params[i],fontsize='x-small')
                    tlabels=mpl.gca().get_xticklabels()
                    mpl.title("Pearson's R: %1.5f" % pearsonr(tr1,tr2)[0],fontsize='x-small')
                    if n>6:
                        mpl.setp(tlabels,'fontsize',3)
                        tlabels=mpl.gca().get_yticklabels()
                        mpl.setp(tlabels,'fontsize',3)
                    else:
                        mpl.setp(tlabels,'fontsize',fontmap[n-1])
                        tlabels=mpl.gca().get_yticklabels()
                        mpl.setp(tlabels,'fontsize',fontmap[n-1])
                    mpl.plot(tr1,tr2,'k.',ms=2,zorder=-10)
                    mpl.plot(x_s,y_s,'r.',ms=10)
                if not i==j: k+=1
                gc.collect() #cleaning RAM...
        fig.tight_layout()
        return fig


    def ConfidInt(self,nbins=20,points=True,levels=None,params=None):
        '''plot of Confidence Regions for 1 sigma=0.6827 and 2 sigma = 0.9545 (or 3 sigma = 0.9973)'''
        if params is None: params=self.pars
        if levels is None: levels=[0.6827,0.9545]
        traces={}
        for p in params: traces[p]=self.flat[:,self.pars.index(p)]
        fontmap={1:10,2:8,3:6,4:5,5:4}
        k=1
        n=len(traces)

        fig=mpl.figure()
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
                    mpl.contour(xbins,ybins,sigma.T,levels=levels,colors=['lime','magenta'])
                    if points: mpl.plot(tr1,tr2,'k.',ms=2,zorder=-10)
                    mpl.plot(x_s,y_s,'r.',ms=10)
                if not i==j: k+=1
                gc.collect() #cleaning RAM...
        fig.tight_layout()
        return fig
