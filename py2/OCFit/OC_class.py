# -*- coding: utf-8 -*-

#main classes of OCFit package
#version 0.1.4
#update: 3.4.2020
# (c) Pavol Gajdos, 2018-2020

from time import time
import sys
import os
import threading
import warnings

import pickle

#import matplotlib
try: 
    import matplotlib.pyplot as mpl
    fig=mpl.figure()
    mpl.close(fig)
except:
    #import on server without graphic output
    try: mpl.switch_backend('Agg')
    except:
        import matplotlib
        matplotlib.reload(matplotlib)    
        matplotlib.use('Agg',force=True)
        import matplotlib.pyplot as mpl

from matplotlib import gridspec
mpl.style.use('classic')

import numpy as np

try: import pymc
except: warnings.warn('Module pymc not found! Using FitMC will not be possible!')

from .ga import TPopul
from .info_ga import InfoGA as InfoGAClass
from .info_mc import InfoMC as InfoMCClass

#some constants
AU=149597870700 #astronomical unit in meters
c=299792458     #velocity of light in meters per second
day=86400.    #number of seconds in day
minutes=1440. #number of minutes in day

def GetMax(x,n):
    '''return n max values in array x'''
    temp=[]
    x=np.array(x)
    for i in range(n):
        temp.append(np.argmax(x))
        x[temp[-1]]=0
    return np.array(temp)


class SimpleFit():
    '''class with common function for FitLinear and FitQuad'''
    def __init__(self,t,t0,P,oc=None,err=None):
        '''input: observed time, time of zeros epoch, period, (O-C values, errors)'''
        self.t=np.array(t)     #times
        
        #linear ephemeris of binary
        self.P=P
        self.t0=t0
        self._t0P=[t0,P]   #given linear ephemeris of binary
        
        if oc is None:
            #calculate O-C
            self.Epoch()
            tC=t0+P*self.epoch
            self.oc=self.t-tC
        else: self.oc=np.array(oc)
        
        if err is None:
            #errors not given
            self.err=np.ones(self.t.shape)
            self._set_err=False
        else:
            #errors given
            self.err=np.array(err)
            self._set_err=True
        self._corr_err=False
        self._calc_err=False
        self._old_err=[]
        
        #sorting data...
        self._order=np.argsort(self.t)
        self.t=self.t[self._order]      #times
        self.oc=self.oc[self._order]    #O-Cs
        self.err=self.err[self._order]  #errors
        
        self.Epoch()
        self.params={}         #values of parameters
        self.params_err={}     #errors of fitted parameters
        self.model=[]          #model O-C 
        self.new_oc=[]         #new O-C (residue)
        self.chi=0
        self._robust=False
        self._mcmc=False
        self.tC=[]

    def Epoch(self):
        '''calculate epoch'''
        self.epoch=np.round((self.t-self.t0)/self.P*2)/2.
        return self.epoch
        
    def PhaseCurve(self,P,t0,plot=False):
        '''create phase curve'''
        f=np.mod(self.t-t0,P)/float(P)    #phase
        order=np.argsort(f)
        f=f[order]
        oc=self.oc[order]
        if plot:
            mpl.figure()
            if self._set_err: mpl.errorbar(f,oc,yerr=self.err,fmt='o')
            else: mpl.plot(f,oc,'.')
        return f,oc
   
    def Summary(self,name=None):
        '''parameters summary, writting to file "name"'''
        params=self.params.keys()
        units={'t0':'JD','P':'d','Q':'d'}

        text=['parameter'.ljust(15,' ')+'unit'.ljust(10,' ')+'value'.ljust(30,' ')+'error']
        for p in sorted(params):
            text.append(p.ljust(15,' ')+units[p].ljust(10,' ')+str(self.params[p]).ljust(30,' ')
                        +str(self.params_err[p]).ljust(20,' '))
        text.append('')
        if self._robust: text.append('Fitting method: Robust regression')
        elif self._mcmc: text.append('Fitting method: MCMC')
        else: text.append('Fitting method: Standard regression')
        g=len(params)
        n=len(self.t)
        text.append('chi2 = '+str(self.chi))
        text.append('chi2_r = '+str(self.chi/(n-g)))
        text.append('AIC = '+str(self.chi+2*g))
        text.append('AICc = '+str(self.chi+2*g*n/(n-g-1)))
        text.append('BIC = '+str(self.chi+g*np.log(n)))
        if name is None:
            print '------------------------------------'
            for t in text: print t
            print '------------------------------------'
        else:
            f=open(name,'w')
            for t in text: f.write(t+'\n')
            f.close()
            
    def InfoMCMC(self,db,eps=False,geweke=False):
        '''statistics about GA fitting'''
        info=InfoMCClass(db)
        info.AllParams(eps)
        
        for p in info.pars: info.OneParam(p,eps)
        if geweke: info.Geweke(eps)

    def CalcErr(self):
        '''calculate errors according to current model'''
        n=len(self.model)
        err=np.sqrt(sum((self.oc-self.model)**2)/(n*(n-1)))
        errors=err*np.ones(self.model.shape)*np.sqrt(n-len(self.params))
        chi=sum(((self.oc-self.model)/errors)**2)
        print 'New chi2:',chi,chi/(n-len(self.params))
        self._calc_err=True
        self._set_err=False
        self.err=errors
        return errors

    def CorrectErr(self):
        '''scaling errors according to current model'''
        n=len(self.model)
        chi0=sum(((self.oc-self.model)/self.err)**2)
        alfa=chi0/(n-2)
        err=self.err*np.sqrt(alfa)
        chi=sum(((self.oc-self.model)/err)**2)
        print 'New chi2:',chi,chi/(n-len(self.params))
        if self._set_err and len(self._old_err)==0: self._old_err=self.err
        self.err=err
        self._corr_err=True
        return err        

    def AddWeight(self,weight):
        '''adding weight to data + scaling according to current model
        warning: weights have to be in same order as input date!        
        '''
        if not len(weight)==len(self.t):
            print 'incorrect length of "w"!'
            return
        weight=np.array(weight)[self._order]
        err=1./weight
        n=len(self.t)
        chi0=sum(((self.oc-self.model)/err)**2)
        alfa=chi0/(n-len(self.params))
        err*=np.sqrt(alfa)
        chi=sum(((self.oc-self.model)/err)**2)
        print 'New chi2:',chi,chi/(n-len(self.params))
        self._calc_err=True
        self._set_err=False
        self.err=err
        return err
        
        
    def SaveOC(self,name,weight=None):
        '''saving O-C calculated from given ephemeris to file
        name - name of file
        weight - weight of data 
        warning: weights have to be in same order as input date!
        '''
        f=open(name,'w')
        if weight is not None:
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.oc,np.array(weight)[self._order])),
                       fmt=["%14.7f",'%10.3f',"%+12.10f","%.10f"],delimiter="    ",
                       header='Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    '+'O-C'.ljust(12,' ')+'    '+'Weight')  
        elif self._set_err:
            if self._corr_err: err=self._old_err
            else: err=self.err
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.oc,err)),
                       fmt=["%14.7f",'%10.3f',"%+12.10f","%.10f"],delimiter="    ",
                       header='Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    '+'O-C'.ljust(12,' ')+'    '+'Error')          
        else:
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.oc)),
                       fmt=["%14.7f",'%10.3f',"%+12.10f"],delimiter="    ",
                       header='Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    '+'O-C')
        f.close()
     
     
    def SaveRes(self,name,weight=None):
        '''saving residue (new O-C) to file
        name - name of file
        weight - weight of data 
        warning: weights have to be in same order as input date!
        '''
        f=open(name,'w')
        if self._set_err:
            if self._corr_err: err=self._old_err
            else: err=self.err
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.new_oc,err)),
                       fmt=["%14.7f",'%10.3f',"%+12.10f","%.10f"],delimiter="    ",
                       header='Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    '+'new O-C'.ljust(12,' ')+'    Error')
        elif weight is not None:
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.new_oc,np.array(weight)[self._order])),
                       fmt=["%14.7f",'%10.3f',"%+12.10f","%.10f"],delimiter="    ",
                       header='Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    '+'new O-C'.ljust(12,' ')+'    Weight')            
        else:
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.new_oc)),
                       fmt=["%14.7f",'%10.3f',"%+12.10f"],delimiter="    ",
                       header='Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    new O-C')
        f.close()

    def PlotRes(self,name=None,no_plot=0,no_plot_err=0,eps=False,oc_min=True,
                time_type='JD',offset=2400000,trans=True,title=None,epoch=False,
                min_type=False,weight=None,trans_weight=False,bw=False,double_ax=False,
                fig_size=None):
        '''plotting residue (new O-C)
        name - name of file to saving plot (if not given -> show graph)
        no_plot - count of outlier point which will not be plot
        no_plot_err - count of errorful point which will not be plot
        eps - save also as eps file
        oc_min - O-C in minutes (if False - days)
        time_type - type of JD in which is time (show in x label)
        offset - offset of time
        trans - transform time according to offset
        title - name of graph
        epoch - x axis in epoch
        min_type - distinction of type of minimum
        weight - weight of data (shown as size of points)
        trans_weight - transform weights to range (1,10)
        bw - Black&White plot
        double_ax - two axes -> time and epoch
        fig_size - custom figure size - e.g. (12,6)
        
        warning: weights have to be in same order as input data!
        '''

        if fig_size:
            fig=mpl.figure(figsize=fig_size)
        else:
            fig=mpl.figure()
            
        ax1=fig.add_subplot(111)
        #setting labels
        if epoch and not double_ax:
            ax1.set_xlabel('Epoch')
            x=self.epoch
        elif offset>0:
            ax1.set_xlabel('Time ('+time_type+' - '+str(offset)+')')
            if not trans: offset=0
            x=self.t-offset
        else:
            ax1.set_xlabel('Time ('+time_type+')')
            offset=0
            x=self.t

        if oc_min:
            ax1.set_ylabel('Residue O - C (min)')
            k=minutes
        else:
            ax1.set_ylabel('Residue O - C (d)')
            k=1

        if title is not None: 
            if double_ax: fig.subplots_adjust(top=0.85)
            fig.suptitle(title,fontsize=20)

        #primary / secondary minimum
        if min_type:
            prim=np.where(np.round(self.epoch)==self.epoch)
            sec=np.where(np.round(self.epoch)<>self.epoch)
        else:
            prim=np.arange(0,len(self.epoch),1)
            sec=np.array([])

        #set weight
        set_w=False
        if weight is not None:
            weight=np.array(weight)[self._order]
            if trans_weight:
                w_min=min(weight)
                w_max=max(weight)
                weight=9./(w_max-w_min)*(weight-w_min)+1
            if weight.shape==self.t.shape:
                w=[]
                levels=[0,3,5,7.9,10]
                size=[3,4,5,7]
                for i in range(len(levels)-1):
                    w.append(np.where((weight>levels[i])*(weight<=levels[i+1])))
                w[-1]=np.append(w[-1],np.where(weight>levels[-1]))  #if some weight is bigger than max. level
                set_w=True
            else:
                warnings.warn('Shape of "weight" is different to shape of "time". Weight will be ignore!')

        if bw: color='k'
        else: color='b'
        errors=GetMax(abs(self.new_oc),no_plot)
        if set_w:
            #using weights
            prim=np.delete(prim,np.where(np.in1d(prim,errors)))
            sec=np.delete(sec,np.where(np.in1d(sec,errors)))
            if not len(prim)==0:
                for i in range(len(w)):
                    ax1.plot(x[prim[np.where(np.in1d(prim,w[i]))]],
                             (self.new_oc*k)[prim[np.where(np.in1d(prim,w[i]))]],color+'o',markersize=size[i])
            if not len(sec)==0:
                for i in range(len(w)):
                    ax1.plot(x[sec[np.where(np.in1d(sec,w[i]))]],
                             (self.new_oc*k)[sec[np.where(np.in1d(sec,w[i]))]],color+'o',markersize=size[i],
                             fillstyle='none',markeredgewidth=1,markeredgecolor=color)

        else:
            #without weight
            if self._set_err:
                #using errors
                if self._corr_err: err=self._old_err
                else: err=self.err
                errors=np.append(errors,GetMax(err,no_plot_err))
                prim=np.delete(prim,np.where(np.in1d(prim,errors)))
                sec=np.delete(sec,np.where(np.in1d(sec,errors)))
                if not len(prim)==0:
                    ax1.errorbar(x[prim],(self.new_oc*k)[prim],yerr=(err*k)[prim],fmt=color+'o',markersize=5)
                if not len(sec)==0:
                    ax1.errorbar(x[sec],(self.new_oc*k)[sec],yerr=(err*k)[sec],fmt=color+'o',markersize=5,
                                 fillstyle='none',markeredgewidth=1,markeredgecolor=color)

            else:
                #without errors
                prim=np.delete(prim,np.where(np.in1d(prim,errors)))
                sec=np.delete(sec,np.where(np.in1d(sec,errors)))
                if not len(prim)==0:
                    ax1.plot(x[prim],(self.new_oc*k)[prim],color+'o',zorder=2)
                if not len(sec)==0:
                    ax1.plot(x[sec],(self.new_oc*k)[sec],color+'o',
                             mfc='none',markeredgewidth=1,markeredgecolor=color,zorder=2)
        
        if double_ax:
            #setting secound axis                        
            ax2=ax1.twiny() 
            #generate plot to obtain correct axis in epoch
            l=ax2.plot(self.epoch,self.oc*k)
            ax2.set_xlabel('Epoch')
            l.pop(0).remove()
            lims=np.array(ax1.get_xlim())
            epoch=np.round((lims-self.t0)/self.P*2)/2.
            ax2.set_xlim(epoch)
        
        if name is None: mpl.show()
        else:
            mpl.savefig(name+'.png')
            if eps: mpl.savefig(name+'.eps')
            mpl.close(fig)

    def Plot(self,name=None,no_plot=0,no_plot_err=0,eps=False,oc_min=True,
             time_type='JD',offset=2400000,trans=True,title=None,epoch=False,
             min_type=False,weight=None,trans_weight=False,bw=False,double_ax=False,
             fig_size=None):
        '''plotting original O-C with linear fit
        name - name of file to saving plot (if not given -> show graph)
        no_plot - count of outlier point which will not be plot
        no_plot_err - count of errorful point which will not be plot
        eps - save also as eps file
        oc_min - O-C in minutes (if False - days)
        time_type - type of JD in which is time (show in x label)
        offset - offset of time
        trans - transform time according to offset
        title - name of graph
        epoch - x axis in epoch
        min_type - distinction of type of minimum
        weight - weight of data (shown as size of points)
        trans_weight - transform weights to range (1,10)
        bw - Black&White plot
        double_ax - two axes -> time and epoch
        fig_size - custom figure size - e.g. (12,6)
        
        warning: weights have to be in same order as input data!
        '''

        if fig_size:
            fig=mpl.figure(figsize=fig_size)
        else:
            fig=mpl.figure()

        ax1=fig.add_subplot(111)
        #setting labels
        if epoch and not double_ax:
            ax1.set_xlabel('Epoch')
            x=self.epoch
        elif offset>0:
            ax1.set_xlabel('Time ('+time_type+' - '+str(offset)+')')
            if not trans: offset=0
            x=self.t-offset
        else:
            ax1.set_xlabel('Time ('+time_type+')')
            offset=0
            x=self.t

        if oc_min:
            ax1.set_ylabel('O - C (min)')
            k=minutes
        else:
            ax1.set_ylabel('O - C (d)')
            k=1
            
        if title is not None: 
            if double_ax: fig.subplots_adjust(top=0.85)
            fig.suptitle(title,fontsize=20)

        if not len(self.model)==len(self.t):
            no_plot=0

        #primary / secondary minimum
        if min_type:
            prim=np.where(np.round(self.epoch)==self.epoch)
            sec=np.where(np.round(self.epoch)<>self.epoch)
        else:
            prim=np.arange(0,len(self.epoch),1)
            sec=np.array([])

        #set weight
        set_w=False
        if weight is not None:
            weight=np.array(weight)[self._order]
            if trans_weight:
                w_min=min(weight)
                w_max=max(weight)
                weight=9./(w_max-w_min)*(weight-w_min)+1
            if weight.shape==self.t.shape:
                w=[]
                levels=[0,3,5,7.9,10]
                size=[3,4,5,7]
                for i in range(len(levels)-1):
                    w.append(np.where((weight>levels[i])*(weight<=levels[i+1])))
                w[-1]=np.append(w[-1],np.where(weight>levels[-1]))  #if some weight is bigger than max. level
                set_w=True
            else:
                warnings.warn('Shape of "weight" is different to shape of "time". Weight will be ignore!')
        
        if bw: color='k'
        else: color='b'
        if len(self.new_oc)==len(self.oc): errors=GetMax(abs(self.new_oc),no_plot)  #remove outlier points
        else: errors=np.array([])
        if set_w:
            #using weights
            prim=np.delete(prim,np.where(np.in1d(prim,errors)))
            sec=np.delete(sec,np.where(np.in1d(sec,errors)))
            if not len(prim)==0:
                for i in range(len(w)):
                    ax1.plot(x[prim[np.where(np.in1d(prim,w[i]))]],
                             (self.oc*k)[prim[np.where(np.in1d(prim,w[i]))]],color+'o',markersize=size[i],zorder=1)
            if not len(sec)==0:
                for i in range(len(w)):
                    ax1.plot(x[sec[np.where(np.in1d(sec,w[i]))]],
                             (self.oc*k)[sec[np.where(np.in1d(sec,w[i]))]],color+'o',markersize=size[i],
                             fillstyle='none',markeredgewidth=1,markeredgecolor=color,zorder=1)

        else:
            #without weight
            if self._set_err:
                #using errors
                if self._corr_err: err=self._old_err
                else: err=self.err
                errors=np.append(errors,GetMax(err,no_plot_err))  #remove errorful points
                prim=np.delete(prim,np.where(np.in1d(prim,errors)))
                sec=np.delete(sec,np.where(np.in1d(sec,errors)))
                if not len(prim)==0:
                    ax1.errorbar(x[prim],(self.oc*k)[prim],yerr=(err*k)[prim],fmt=color+'o',markersize=5,zorder=1)
                if not len(sec)==0:
                    ax1.errorbar(x[sec],(self.oc*k)[sec],yerr=(err*k)[sec],fmt=color+'o',markersize=5,
                                 fillstyle='none',markeredgewidth=1,markeredgecolor=color,zorder=1)

            else:
                #without errors
                prim=np.delete(prim,np.where(np.in1d(prim,errors)))
                sec=np.delete(sec,np.where(np.in1d(sec,errors)))
                if not len(prim)==0:
                    ax1.plot(x[prim],(self.oc*k)[prim],color+'o',zorder=1)
                if not len(sec)==0:
                    ax1.plot(x[sec],(self.oc*k)[sec],color+'o',
                             mfc='none',markeredgewidth=1,markeredgecolor=color,zorder=1)

        #plot linear model
        if bw: 
            color='k'
            lw=2
        else: 
            color='r'
            lw=1
            
        if len(self.model)==len(self.t):
            #model was calculated
            if len(self.t)<1000:
                dE=(self.epoch[-1]-self.epoch[0])/1000.
                E=np.linspace(self.epoch[0]-50*dE,self.epoch[-1]+50*dE,1100)
            else:
                dE=(self.epoch[-1]-self.epoch[0])/len(self.epoch)
                E=np.linspace(self.epoch[0]-0.05*len(self.epoch)*dE,self.epoch[-1]+0.05*len(self.epoch)*dE,1.1*len(self.epoch))                
            tC=self._t0P[0]+self._t0P[1]*E
            p=[]
            if 'Q' in self.params:
                #Quad Model
                p.append(self.params['Q'])
            p+=[self.params['P']-self._t0P[1],self.params['t0']-self._t0P[0]]
            new=np.polyval(p,E)
            
            if epoch and not double_ax: ax1.plot(E,new*k,color,linewidth=lw)
            else: ax1.plot(tC+new-offset,new*k,color,linewidth=lw)
        
        if double_ax:
            #setting secound axis
            ax2=ax1.twiny() 
            #generate plot to obtain correct axis in epoch
            if len(self.model)==len(self.t): l=ax2.plot(E,new*k,zorder=2)
            else: l=ax2.plot(self.epoch,self.oc*k,zorder=2)
            ax2.set_xlabel('Epoch')
            l.pop(0).remove()
            lims=np.array(ax1.get_xlim())
            epoch=np.round((lims-self.t0)/self.P*2)/2.
            ax2.set_xlim(epoch)
        

        if name is None: mpl.show()
        else:
            mpl.savefig(name+'.png')
            if eps: mpl.savefig(name+'.eps')
            mpl.close(fig)

class FitLinear(SimpleFit):
    '''fitting of O-C diagram with linear function'''
    
    def FitRobust(self,n_iter=10):
        '''robust regresion
        return: new O-C'''
        self.FitLinear()
        for i in range(n_iter): self.FitLinear(robust=True)
        self._robust=True
        self._mcmc=False
        return self.new_oc

    def FitLinear(self,robust=False):
        '''simple linear regresion
        return: new O-C'''
        if robust:
            err=self.err*np.exp(((self.oc-self.model)/(5*self.err))**4)
            k=1
            while np.inf in err:
                k*=10
                err=self.err*np.exp(((self.oc-self.model)/(5*k*self.err))**4)
        else: err=self.err
        w=1./err

        p,cov=np.polyfit(self.epoch,self.oc,1,cov=True,w=w)
        
        self.P=p[0]+self._t0P[1]
        self.t0=p[1]+self._t0P[0]
        
        self.params['P']=p[0]+self._t0P[1]
        self.params['t0']=p[1]+self._t0P[0]

        self.Epoch()
        self.model=np.polyval(p,self.epoch)
        self.chi=sum(((self.oc-self.model)/self.err)**2)

        if robust:
            n=len(self.t)*1.06*sum(1./err)/sum(1./self.err)
            chi_m=1.23*sum(((self.oc-self.model)/err)**2)/(n-2)
        else: chi_m=self.chi/(len(self.t)-2)
        
        err=np.sqrt(chi_m*cov.diagonal())
        self.params_err['P']=err[0]
        self.params_err['t0']=err[1]        

        self.tC=self.t0+self.P*self.epoch
        self.new_oc=self.oc-self.model

        self._robust=False
        self._mcmc=False
        return self.new_oc
        
    def FitMCMC(self,n_iter,limits,steps,fit_params=None,burn=0,binn=1,visible=True,db=None):
        '''fitting with Markov chain Monte Carlo
        n_iter - number of MC iteration - should be at least 1e5
        limits - limits of parameters for fitting
        steps - steps (width of normal distibution) of parameters for fitting
        fit_params - list of fitted parameters
        burn - number of removed steps before equilibrium - should be approx. 0.1-1% of n_iter
        binn - binning size - should be around 10
        visible - display status of fitting
        db - name of database to save MCMC fitting details (could be analysed later using InfoMCMC function)
        '''

        #setting pymc sampling for fitted parameters
        if fit_params is None: fit_params=['P','t0']
        vals0={'P': self._t0P[1], 't0': self._t0P[0]}
        vals={}        
        pars={}
        for p in ['P','t0']:
            if p in self.params: vals[p]=self.params[p]
            else: vals[p]=vals0[p]                
            if p in fit_params:
                pars[p]=pymc.Uniform(p,lower=limits[p][0],upper=limits[p][1],value=vals[p])

        def model_fun(**arg):
            '''model function for pymc'''
            if 'P' in arg: P=arg['P']
            else: P=vals['P']
            if 't0' in arg: t0=arg['t0'] 
            else: t0=vals['t0']
            return t0+P*self.epoch        

        #definition of pymc model
        model=pymc.Deterministic(
            eval=model_fun,
            doc='model',
            name='Model',
            parents=pars,
            trace=True,
            plot=False)

        #final distribution
        if self._set_err or self._calc_err:
            #if known errors of data -> normal/Gaussian distribution
            y=pymc.Normal('y',mu=model,tau=1./self.err**2,value=self.t,observed=True)
        else:
            #if unknown errors of data -> Poisson distribution
            #note: should cause wrong performance of fitting, rather use function CalcErr for obtained errors
            y=pymc.Poisson('y',mu=model,value=self.t,observed=True)

        #adding final distribution and sampling of parameters to model
        Model=[y]
        for v in pars.itervalues():
            Model.append(v)

        #create pymc object
        if db is None: R=pymc.MCMC(Model)
        else:
            #saving MCMC fitting details
            path=db.replace('\\','/')   #change dirs in path (for Windows)
            if path.rfind('/')>0:
                path=path[:path.rfind('/')+1]  #find current dir of db file
                if not os.path.isdir(path): os.mkdir(path) #create dir of db file, if not exist
            R=pymc.MCMC(Model,db='pickle',dbname=db)

        #setting pymc method - distribution and steps
        for p in pars:
            R.use_step_method(pymc.Metropolis,pars[p],proposal_sd=steps[p],
                              proposal_distribution='Normal')

        if not visible: 
            #hidden output
            f = open(os.devnull, 'w')
            out=sys.stdout            
            sys.stdout=f 
            
        R.sample(iter=n_iter,burn=burn,thin=binn)  #MCMC fitting/simulation

        self.params_err={} #remove errors of parameters
            
        for p in ['P','t0']:
            #calculate values and errors of parameters and save them
            if p in pars:
                self.params[p]=R.stats()[p]['mean']
                self.params_err[p]=R.stats()[p]['standard deviation']
            else: 
                self.params[p]=vals[p]
                self.params_err[p]='---'

        print ''
        R.summary() #summary of MCMC fitting
        
        if not visible: 
            #hidden output
            sys.stdout=out
            f.close()
        
        self.Epoch()
        self.tC=self.params['t0']+self.params['P']*self.epoch
        self.new_oc=self.t-self.tC
        self.model=self.oc+self.new_oc    
        
        self.chi=sum(((self.oc-self.model)/self.err)**2)     
        
        self._robust=False
        self._mcmc=True

        return self.new_oc


class FitQuad(SimpleFit):
    '''fitting of O-C diagram with quadratic function'''

    def FitRobust(self,n_iter=10):
        '''robust regresion
        return: new O-C'''
        self.FitQuad()
        for i in range(n_iter): self.FitQuad(robust=True)
        self._robust=True
        self._mcmc=False
        return self.new_oc

    def FitQuad(self,robust=False):
        '''simple linear regresion
        return: new O-C'''
        if robust:
            err=self.err*np.exp(((self.oc-self.model)/(5*self.err))**4)
            k=1
            while np.inf in err:
                k*=10
                err=self.err*np.exp(((self.oc-self.model)/(5*k*self.err))**4)
        else: err=self.err
        p,cov=np.polyfit(self.epoch,self.oc,2,cov=True,w=1./err)

        self.Q=p[0]      
        self.P=p[1]+self._t0P[1]
        self.t0=p[2]+self._t0P[0]
        
        self.params['Q']=p[0]
        self.params['P']=p[1]+self._t0P[1]
        self.params['t0']=p[2]+self._t0P[0]

        self.Epoch()
        self.model=np.polyval(p,self.epoch)
        self.chi=sum(((self.oc-self.model)/self.err)**2)

        if robust:
            n=len(self.t)*1.06*sum(1./err)/sum(1./self.err)
            chi_m=1.23*sum(((self.oc-self.model)/err)**2)/(n-3)
        else: chi_m=self.chi/(len(self.t)-3)
        
        err=np.sqrt(chi_m*cov.diagonal())
        self.params_err['Q']=err[0]
        self.params_err['P']=err[1]
        self.params_err['t0']=err[2]

        self.tC=self.t0+self.P*self.epoch+self.Q*self.epoch**2
        self.new_oc=self.oc-self.model

        self._robust=False
        self._mcmc=False
        return self.new_oc
        
    def FitMCMC(self,n_iter,limits,steps,fit_params=None,burn=0,binn=1,visible=True,db=None):
        '''fitting with Markov chain Monte Carlo
        n_iter - number of MC iteration - should be at least 1e5
        limits - limits of parameters for fitting
        steps - steps (width of normal distibution) of parameters for fitting
        fit_params - list of fitted parameters
        burn - number of removed steps before equilibrium - should be approx. 0.1-1% of n_iter
        binn - binning size - should be around 10
        visible - display status of fitting
        db - name of database to save MCMC fitting details (could be analysed later using InfoMCMC function)
        '''

        #setting pymc sampling for fitted parameters
        if fit_params is None: fit_params=['Q','P','t0']
        vals0={'P': self._t0P[1], 't0': self._t0P[0], 'Q':0}
        vals={}        
        pars={}
        for p in ['P','t0','Q']:
            if p in self.params: vals[p]=self.params[p]
            else: vals[p]=vals0[p]                
            if p in fit_params:
                pars[p]=pymc.Uniform(p,lower=limits[p][0],upper=limits[p][1],value=vals[p])

        def model_fun(**arg):
            '''model function for pymc'''
            if 'Q' in arg: Q=arg['Q']
            else: Q=vals['Q']
            if 'P' in arg: P=arg['P']
            else: P=vals['P']
            if 't0' in arg: t0=arg['t0'] 
            else: t0=vals['t0']
            return t0+P*self.epoch+Q*self.epoch**2        

        #definition of pymc model
        model=pymc.Deterministic(
            eval=model_fun,
            doc='model',
            name='Model',
            parents=pars,
            trace=True,
            plot=False)

        #final distribution
        if self._set_err or self._calc_err:
            #if known errors of data -> normal/Gaussian distribution
            y=pymc.Normal('y',mu=model,tau=1./self.err**2,value=self.t,observed=True)
        else:
            #if unknown errors of data -> Poisson distribution
            #note: should cause wrong performance of fitting, rather use function CalcErr for obtained errors
            y=pymc.Poisson('y',mu=model,value=self.t,observed=True)

        #adding final distribution and sampling of parameters to model
        Model=[y]
        for v in pars.itervalues():
            Model.append(v)

        #create pymc object
        if db is None: R=pymc.MCMC(Model)
        else:
            #saving MCMC fitting details
            path=db.replace('\\','/')   #change dirs in path (for Windows)
            if path.rfind('/')>0:
                path=path[:path.rfind('/')+1]  #find current dir of db file
                if not os.path.isdir(path): os.mkdir(path) #create dir of db file, if not exist
            R=pymc.MCMC(Model,db='pickle',dbname=db)

        #setting pymc method - distribution and steps
        for p in pars:
            R.use_step_method(pymc.Metropolis,pars[p],proposal_sd=steps[p],
                              proposal_distribution='Normal')

        if not visible: 
            #hidden output
            f = open(os.devnull, 'w')
            out=sys.stdout            
            sys.stdout=f 
            
        R.sample(iter=n_iter,burn=burn,thin=binn)  #MCMC fitting/simulation

        self.params_err={} #remove errors of parameters
            
        for p in ['Q','P','t0']:
            #calculate values and errors of parameters and save them
            if p in pars:
                self.params[p]=R.stats()[p]['mean']
                self.params_err[p]=R.stats()[p]['standard deviation']
            else: 
                self.params[p]=vals[p]
                self.params_err[p]='---'

        print ''
        R.summary() #summary of MCMC fitting
        
        if not visible: 
            #hidden output
            sys.stdout=out
            f.close()
        
        self.Epoch()
        self.tC=self.t0+self.P*self.epoch+self.Q*self.epoch**2
        self.new_oc=self.t-self.tC
        self.model=self.oc+self.new_oc           
        self.chi=sum(((self.oc-self.model)/self.err)**2)     
        
        self._robust=False
        self._mcmc=True

        return self.new_oc


class ComplexFit():
    '''class with common function for OCFit and RVFit'''
    def KeplerEQ(self,M,e,eps=1e-10):
        '''solving Kepler Equation using Newton-Raphson method
        with starting formula S9 given by Odell&Gooding (1986)
        M - Mean anomaly (np.array, float or list) [rad]
        e - eccentricity
        (eps - accurancy)
        output in rad in same format as M
        '''
        #if input is not np.array
        len1=False
        if isinstance(M,int) or isinstance(M,float):
            #M is float
            if M==0.: return 0.
            M=np.array(M)
            len1=True
        lst=False
        if isinstance(M,list):
            #M is list
            lst=True
            M=np.array(M)

        E0=M+e*np.sin(M)/np.sqrt(1-2*e*np.cos(M)+e**2)  #starting formula S9
        E=E0-(E0-e*np.sin(E0)-M)/(1-e*np.cos(E0))
        while (abs(E-E0)>eps).any():
            E0=E
            E=E-(E-e*np.sin(E)-M)/(1-e*np.cos(E))
        while (E<0).any(): E[np.where(E<0)]+=2*np.pi
        while (E>2*np.pi).any(): E[np.where(E>2*np.pi)]-=2*np.pi
        if len1: return E[0]  #output is float
        if lst: return list(E)  #output is list
        return E


    def KeplerEQMarkley(self,M,e):
        '''solving Kepler Equation - Markley (1995): Kepler Equation Solver
        M - Mean anomaly (np.array, float or list) [rad]
        e - eccentricity
        output in rad in same format as M
        '''
        #if input is not np.array
        len1=False
        if isinstance(M,int) or isinstance(M,float):
            #M is float
            if M==0.: return 0.
            M=np.array(M)
            len1=True
        lst=False
        if isinstance(M,list):
            #M is list
            lst=True
            M=np.array(M)

        pi2=np.pi**2
        pi=np.pi

        #if somewhere is M=0 or M=pi
        M=M-(np.floor(M/(2*pi))*2*pi)
        flip=np.where(M>pi)
        M[flip]=2*pi-M[flip]
        M_0=np.where(np.round_(M,14)==0)
        M_pi=np.where(np.round_(M,14)==np.round_(pi,14))

        alpha=(3.*pi2+1.6*pi*(pi-abs(M))/(1.+e))/(pi2-6.)
        d=3*(1-e)+alpha*e
        r=3*alpha*d*(d-1+e)*M+M**3
        q=2*alpha*d*(1-e)-M**2
        w=(abs(r)+np.sqrt(q**3+r**2))**(2./3.)
        E1=(2*r*w/(w**2+w*q+q**2)+M)/d
        s=e*np.sin(E1)
        f0=E1-s-M
        f1=1-e*np.cos(E1)
        f2=s
        f3=1-f1
        f4=-f2
        d3=-f0/(f1-0.5*f0*f2/f1)
        d4=-f0/(f1+0.5*d3*f2+(d3**2)*f3/6.)
        d5=-f0/(f1+0.5*d4*f2+d4**2*f3/6.+d4**3*f4/24.)
        E=E1+d5
        E[flip]=2*pi-E[flip]
        E[M_0]=0.
        E[M_pi]=pi
        if len1: return E[0]  #output is float
        if lst: return list(E)  #output is list
        return E

    def Epoch(self,t0,P,t=None):
        '''convert time to epoch'''
        if t is None: t=self.t
        epoch=np.round((t-t0)/P*2)/2.
        self.epoch=epoch
        self._t0P=[t0,P]
        self._min_type=np.abs((2*(epoch-epoch.astype('int'))).astype('int'))
        return epoch        
            
    def InfoGA(self,db,eps=False):
        '''statistics about GA fitting'''
        info=InfoGAClass(db)
        path=db.replace('\\','/')
        if path.rfind('/')>0: path=path[:path.rfind('/')+1]
        else: path=''
        info.Info(path+'ga-info.txt')
        info.PlotChi2()
        mpl.savefig(path+'ga-chi2.png')
        if eps: mpl.savefig(path+'ga-chi2.eps')
        for p in info.availableTrace:
            info.Plot(p)
            mpl.savefig(path+'ga-'+p+'.png')
            if eps: mpl.savefig(path+'ga-'+p+'.eps')
        mpl.close('all')
        
    def InfoMCMC(self,db,eps=False,geweke=False):
        '''statistics about GA fitting'''
        info=InfoMCClass(db)
        info.AllParams(eps)
        
        for p in info.pars: info.OneParam(p,eps)
        if geweke: info.Geweke(eps)        
        
                
    def LiTE(self,t,a_sin_i3,e3,w3,t03,P3):
        '''model of O-C by Light-Time effect given by Irwin (1952)
        t - times of minima (np.array or float) [days]
        a_sin_i3 - semimayor axis original binary around center of mass of triple system [AU]
        e3 - eccentricity of 3rd body
        w3 - longitude of pericenter of 3rd body [rad]
        P3 - period of 3rd body [days]
        t03 - time of pericenter passage of 3rd body [days]
        output in days
        '''

        M=2*np.pi/P3*(t-t03)  #mean anomally
        if e3<0.9: E=self.KeplerEQ(M,e3)   #eccentric anomally
        else: E=self.KeplerEQMarkley(M,e3)
        nu=2*np.arctan(np.sqrt((1+e3)/(1-e3))*np.tan(E/2))  #true anomally
        dt=a_sin_i3*AU/c*((1-e3**2)/(1+e3*np.cos(nu))*np.sin(nu+w3)+e3*np.sin(w3))
        return dt/day
              

class OCFit(ComplexFit):
    '''class for fitting O-C diagrams'''
    def __init__(self,t,oc,err=None):
        '''loading times, O-Cs, (errors)'''
        self.t=np.array(t)
        self.oc=np.array(oc)
        if err is None:
            #errors not given
            self.err=np.ones(self.t.shape)
            self._set_err=False
        else:
            #errors given
            self.err=np.array(err)
            self._set_err=True
        
        #sorting data...
        self._order=np.argsort(self.t)
        self.t=self.t[self._order]    #times
        self.oc=self.oc[self._order]  #O-Cs
        self.err=self.err[self._order]   #errors
        
        self.limits={}          #limits of parameters for fitting
        self.steps={}           #steps (width of normal distibution) of parameters for fitting
        self.params={}          #values of parameters, fixed values have to be set here
        self.params_err={}      #errors of fitted parameters
        self.paramsMore={}      #values of parameters calculated from model params
        self.paramsMore_err={}  #errors of calculated parameters
        self.fit_params=[]      #list of fitted parameters
        self._calc_err=False    #errors were calculated
        self._corr_err=False    #errors were corrected
        self._old_err=[]        #given errors 
        self.model='LiTE3'      #used model of O-C
        self._t0P=[]            #linear ephemeris of binary
        self.epoch=[]           #epoch of binary
        self.res=[]             #residua = new O-C
        self._min_type=[]        #type of minima (primary=0 / secondary=1)
        self.availableModels=['LiTE3','LiTE34','LiTE3Quad','LiTE34Quad',\
                              'AgolInPlanet','AgolInPlanetLin','AgolExPlanet',\
                              'AgolExPlanetLin','Apsidal']   #list of available models

    
    def AvailableModels(self):
        '''print available models for fitting O-Cs'''
        print 'Available Models:'
        for s in self.availableModels: print s
            
    def ModelParams(self,model=None,allModels=False):
        '''display parameters of model'''
        
        def Display(model):
            s=model+': '
            if 'Quad' in model: s+='t0, P, Q, '
            if 'Lin' in model: s+='t0, '
            if 'LiTE' in model: s+='a_sin_i3, e3, w3, t03, P3, '
            if '4' in model: s+='a_sin_i4, e4, w4, t04, P4, ' 
            if 'InPlanet' in model: s+='P, a, w, e, mu3, r3, w3, t03, P3, '    
            if 'ExPlanet' in model: s+='P, mu3, e3, t03, P3, '
            if 'Apsidal' in model: s+='t0, P, w0, dw, e, '
            print s[:-2]
            
        if model is None: model=self.model
        if allModels:
            for m in self.availableModels: Display(m)
        else: Display(model)
                
    
    def Save(self,path):
        '''saving data, model, parameters... to file'''
        data={}
        data['t']=self.t
        data['oc']=self.oc
        data['err']=self.err
        data['order']=self._order
        data['set_err']=self._set_err
        data['calc_err']=self._calc_err
        data['corr_err']=self._corr_err
        data['old_err']=self._old_err
        data['limits']=self.limits
        data['steps']=self.steps
        data['params']=self.params
        data['params_err']=self.params_err
        data['paramsMore']=self.paramsMore
        data['paramsMore_err']=self.paramsMore_err
        data['fit_params']=self.fit_params
        data['model']=self.model   
        data['t0P']=self._t0P
        data['epoch']=self.epoch
        data['min_type']=self._min_type
        
        path=path.replace('\\','/')   #change dirs in path (for Windows)
        if path.rfind('.')<=path.rfind('/'): path+='.ocf'   #without extesion
        f=open(path,'wb') 
        pickle.dump(data,f,protocol=2)
        f.close()
        
    def Load(self,path):
        '''loading data, model, parameters... from file'''
        path=path.replace('\\','/')   #change dirs in path (for Windows)
        if path.rfind('.')<=path.rfind('/'): path+='.ocf'   #without extesion
        f=open(path,'rb')
        data=pickle.load(f) 
        f.close()
        
        self.t=data['t']
        self.oc=data['oc']
        self.err=data['err']
        self._order=data['order']
        self._set_err=data['set_err']
        self._corr_err=data['corr_err']
        self._calc_err=data['calc_err']
        self._old_err=data['old_err']
        self.limits=data['limits']
        self.steps=data['steps']
        self.params=data['params']
        self.params_err=data['params_err']
        self.paramsMore=data['paramsMore']
        self.paramsMore_err=data['paramsMore_err']
        self.fit_params=data['fit_params']
        self.model=data['model']
        self._t0P=data['t0P']
        self.epoch=data['epoch']
        self._min_type=data['min_type']


    def AgolInPlanet(self,t,P,a,w,e,mu3,r3,w3,t03,P3):
        '''model TTV - inner planet (Agol et al., 2005 - sec. 3)
        t - times of minima = transits (np.array alebo float) [days]
        P - period of transiting exoplanet [days]
        a - semimayor axis of transiting exoplanet [AU]
        w - longitude of periastrum of transiting exoplanet [rad]
        e - eccentricity of transiting exoplanet
        mu3 - reduced mass of 3rd body; mu3 = M3/(M12+M3)
        r3 - radius of orbit of 3rd body [AU]
        w3 -longitude of periastrum of 3rd. body [rad]
        t03 - time of pericenter passage of 3rd body [days]
        P3 - period of 3rd body [days]
        output in days
        '''

        nu=2*np.pi/P3*(t-t03)
        dt=-P*mu3*r3*np.cos(nu+w3)*np.sqrt(1-e**2)/(2*np.pi*a*(1-e*np.sin(w)))
        return dt

    def AgolInPlanetLin(self,t,t0,P,a,w,e,mu3,r3,w3,t03,P3):
        '''model TTV - inner planet (Agol et al., 2005 - sec. 3) with linear model
        t - times of minima = transits (np.array alebo float) [days]
        t0 - time of refernce transit [days]
        P - period of transiting exoplanet [days]
        a - semimayor axis of transiting exoplanet [AU]
        w - longitude of periastrum of transiting exoplanet [rad]
        e - eccentricity of transiting exoplanet
        mu3 - reduced mass of 3rd body; mu3 = M3/(M12+M3)
        r3 - radius of orbit of 3rd body [AU]
        w3 -longitude of periastrum of 3rd body [rad]
        t03 - time of pericenter passage of 3rd body [days]
        P3 - period of 3rd body [days]
        output in days
        '''

        if not len(self.epoch)==len(t):
            raise NameError('Epoch not callculated! Run function "Epoch" before it.')
        dt=t0+P*self.epoch-(self._t0P[0]+self._t0P[1]*self.epoch) #linear model

        dt3=self.AgolInPlanet(t,P,a,w,e,mu3,r3,w3,t03,P3)  #AgolInPlanet model
        return dt+dt3

    def AgolExPlanet(self,t,P,mu3,e3,t03,P3):
        '''model TTV - exterior planet (Agol et al., 2005 - sec. 4)
        t - times of minima = transits (np.array alebo float) [days]
        P - period of transiting exoplanet [days]
        mu3 - reduced mass of 3rd body; mu3 = M3/(M12+M3)
        e3 - eccentricity of 3rd exoplanet
        t03 - time of pericenter passage of 3rd body [days]
        P3 - period of 3rd body [days]
        output in days        
        '''

        M=2*np.pi/P3*(t-t03)
        while (M>2*np.pi).any(): M[np.where(M>2*np.pi)]-=2*np.pi
        while (M<0).any(): M[np.where(M<0)]+=2*np.pi
        if e3<0.9: E=self.KeplerEQ(M,e3)
        else: E=self.KeplerEQMarkley(M,e3)
        nu=2*np.arctan(np.sqrt((1+e3)/(1-e3))*np.tan(E/2))
        while (nu>2*np.pi).any(): nu[np.where(nu>2*np.pi)]-=2*np.pi
        while (nu<0).any(): nu[np.where(nu<0)]+=2*np.pi
        dt=mu3/(2*np.pi*(1-mu3))*P**2/P3*(1-e3**2)**(-3./2.)*(nu-M+e3*np.sin(nu))
        return dt

    def AgolExPlanetLin(self,t,t0,P,mu3,e3,t03,P3):
        '''model TTV - exterior planet (Agol et al., 2005 - sec. 4) with linear model
        t - times of minima = transits (np.array alebo float) [days]
        t0 - time of refernce transit [days]
        P - period of transiting exoplanet [days]
        mu3 - reduced mass of 3rd body; mu3 = M3/(M12+M3)
        e3 - eccentricity of 3rd exoplanet
        t03 - time of pericenter passage of 3rd body [days]
        P3 - period of 3rd body [days]
        output in days  
        '''

        if not len(self.epoch)==len(t):
            raise NameError('Epoch not callculated! Run function "Epoch" before it.')
        dt=t0+P*self.epoch
        
        dt3=self.AgolExPlanet(t,P,mu3,e3,t03,P3)
        return dt+dt3-(self._t0P[0]+self._t0P[1]*self.epoch)    
    
    def LiTE3(self,t,a_sin_i3,e3,w3,t03,P3):
        '''model of O-C by Light-Time effect caused by 3rd body given by Irwin (1952)
        t - times of minima (np.array or float) [days]
        a_sin_i3 - semimayor axis of eclipsing binary around center of mass of triple system [AU]
        e3 - eccentricity of 3rd body
        w3 - longitude of pericenter of 3rd body [rad]
        P3 - period of 3rd body [days]
        t03 - time of pericenter passage of 3rd body [days]
        output in days
        '''

        dt3=self.LiTE(t,a_sin_i3,e3,w3,t03,P3)
        return dt3     
    
    def LiTE34(self,t,a_sin_i3,e3,w3,t03,P3,a_sin_i4,e4,w4,t04,P4):
        '''model of O-C by Light-Time effect caused by 3rd and 4th body given by Irwin (1952)
        t - times of minima (np.array or float) [days]
        a_sin_i3, a_sin_i4 - semimayor axis of eclipsing binary around center of mass of multiple system [AU]
        e3, e4 - eccentricity of 3rd/4th body
        w3, w4 - longitude of pericenter of 3rd/4th body [rad]
        P3, P4 - period of 3rd/4th body [days]
        t03, t04 - time of pericenter passage of 3rd/4th body [days]
        output in days
        '''

        dt3=self.LiTE(t,a_sin_i3,e3,w3,t03,P3)
        dt4=self.LiTE(t,a_sin_i4,e4,w4,t04,P4)
        return dt3+dt4    
        
    def LiTE3Quad(self,t,t0,P,Q,a_sin_i3,e3,w3,t03,P3):
        '''model of O-C by Light-Time effect caused by 3rd body given by Irwin (1952) \
        with quadratic model of O-C         
        t - times of minima (np.array or float) [days]
        t0 - time of refernce minima [days]
        P - period of eclipsing binary [days]
        Q - quadratic term [days]
        a_sin_i3 - semimayor axis of eclipsing binary around center of mass of triple system [AU]
        e3 - eccentricity of 3rd body
        w3 - longitude of pericenter of 3rd body [rad]
        P3 - period of 3rd body [days]
        t03 - time of pericenter passage of 3rd body [days]
        output in days
        '''

        if not len(self.epoch)==len(t):
            raise NameError('Epoch not callculated! Run function "Epoch" before it.')
        dt=t0+P*self.epoch+Q*self.epoch**2

        dt3=self.LiTE(t,a_sin_i3,e3,w3,t03,P3)
        return dt+dt3-(self._t0P[0]+self._t0P[1]*self.epoch)


    def LiTE34Quad(self,t,t0,P,Q,a_sin_i3,e3,w3,t03,P3,a_sin_i4,e4,w4,t04,P4):
        '''model of O-C by Light-Time effect caused by 3rd and 4th body given by Irwin (1952)\
        with quadratic model of O-C
        t - times of minima (np.array or float) [days]
        t0 - time of refernce minima [days]
        P - period of eclipsing binary [days]
        Q - quadratic term [days]
        a_sin_i3, a_sin_i4 - semimayor axis of eclipsing binary around center of mass of multiple system [AU]
        e3, e4 - eccentricity of 3rd/4th body
        w3, w4 - longitude of pericenter of 3rd/4th body [rad]
        P3, P4 - period of 3rd/4th body [days]
        t03, t04 - time of pericenter passage of 3rd/4th body [days]
        output in days
        '''

        if not len(self.epoch)==len(t):
            raise NameError('Epoch not callculated! Run function "Epoch" before it.')
        dt=t0+P*self.epoch+Q*self.epoch**2

        dt3=self.LiTE(t,a_sin_i3,e3,w3,t03,P3)
        dt4=self.LiTE(t,a_sin_i4,e4,w4,t04,P4)
        return dt+dt3+dt4-(self._t0P[0]+self._t0P[1]*self.epoch)
    
    def Apsidal(self,t,t0,P,w0,dw,e,min_type):
        '''Apsidal motion on O-C diagram (Gimenez&Bastero,1995)
        t0 - time of refernce minima [days]
        P - period of eclipsing binary [days]
        w0 - initial position of pericenter [rad]
        dw - angular velocity of line of apsides [rad/period]
        e - eccentricity
        min_type - type of minimas [0 or 1]
        
        output in days
        '''
        
        if not len(self.epoch)==len(t):
            raise NameError('Epoch not callculated! Run function "Epoch" before it.')
        
        w=w0+dw*self.epoch   #position of pericenter
        nu=-w+np.pi/2       #true anomaly
        b=e/(1+np.sqrt(1-e**2))
        
        sum1=0
        sum2=0
        tmp=0
        for n in range(1,10):
            tmp=(-b)**n*(1/n+np.sqrt(1-e**2))*np.sin(n*nu)
            #primary
            sum1+=tmp
            #secondary
            if n%2: sum2-=tmp
            else: sum2+=tmp
            
        oc1=P/np.pi*sum1
        oc2=P/np.pi*sum2
        
        dt=np.zeros(t.shape)
        dt[np.where(min_type==0)[0]]=oc1[np.where(min_type==0)[0]]  #primary
        dt[np.where(min_type==1)[0]]=oc2[np.where(min_type==1)[0]]  #secondary
                
        return dt+(t0+P*self.epoch)-(self._t0P[0]+self._t0P[1]*self.epoch)
        
    
    def PhaseCurve(self,P,t0,plot=False):
        '''create phase curve'''
        f=np.mod(self.t-t0,P)/float(P)    #phase
        order=np.argsort(f)
        f=f[order]
        oc=self.oc[order]
        if plot:
            mpl.figure()
            if self._set_err: mpl.errorbar(f,oc,yerr=self.err,fmt='o')
            else: mpl.plot(f,oc,'.')
        return f,oc

    def Chi2(self,params):
        '''calculate chi2 error (used as Objective Function for GA fitting) based on given parameters (in dict)'''
        param=dict(params)
        for x in self.params:
            #add fixed parameters
            if not x in param: param[x]=self.params[x]
        model=self.Model(param=param)   #calculate model
        return sum(((model-self.oc)/self.err)**2)

    def FitGA(self,generation,size,mut=0.5,SP=2,plot_graph=False,visible=True,
              n_thread=1,db=None):
        '''fitting with Genetic Algorithms
        generation - number of generations - should be approx. 100-200 x number of free parameters
        size - number of individuals in one generation (size of population) - should be approx. 100-200 x number of free parameters
        mut - proportion of mutations
        SP - selection pressure (see Razali&Geraghty (2011) for details)
        plot_graph - plot figure of best and mean solution found in each generation
        visible - display status of fitting
        n_thread - number of threads for multithreading
        db - name of database to save GA fitting details (could be analysed later using InfoGA function)
        '''

        def Thread(subpopul):
            #thread's function for multithreading
            for i in subpopul: objfun[i]=self.Chi2(popul.p[i])

        limits=self.limits
        steps=self.steps

        popul=TPopul(size,self.fit_params,mut,steps,limits,SP)  #init GA Class
        min0=1e15  #large number for comparing -> for finding min. value
        p={}     #best set of parameters
        if plot_graph:
            graph=[]
            graph_mean=[]
            
        objfun=[]   #values of Objective Function
        for i in range(size): objfun.append(0)
        
        if db is not None:
            #saving GA fitting details
            save_dat={}
            save_dat['chi2']=[]
            for par in self.fit_params: save_dat[par]=[]  
            path=db.replace('\\','/')   #change dirs in path (for Windows)
            if path.rfind('/')>0:
                path=path[:path.rfind('/')+1]  #find current dir of db file
                if not os.path.isdir(path): os.mkdir(path) #create dir of db file, if not exist
    
        if not visible: 
            #hidden output
            f = open(os.devnull, 'w')
            out=sys.stdout            
            sys.stdout=f 
            
        tic=time()
        for gen in range(generation):
            #main loop of GA
            threads=[]
            sys.stdout.write('gen: '+str(gen+1)+' / '+str(generation)+' in '+str(np.round(time()-tic,1))+' sec  ')
            sys.stdout.flush()
            for t in range(n_thread):
                #multithreading
                threads.append(threading.Thread(target=Thread,args=[range(int(t*size/float(n_thread)),
                                                                          int((t+1)*size/float(n_thread)))]))
            #waiting for all threads and joining them
            for t in threads: t.start()
            for t in threads: t.join()

            #finding best solution in population and compare with global best solution            
            i=np.argmin(objfun)
            if objfun[i]<min0:
                min0=objfun[i]
                p=dict(popul.p[i])
            
            if plot_graph:
                graph.append(min0)
                graph_mean.append(np.mean(np.array(objfun)))                
            
            if db is not None:
                save_dat['chi2'].append(list(objfun)) 
                for par in self.fit_params:
                    temp=[]
                    for x in popul.p: temp.append(x[par])
                    save_dat[par].append(temp)  
            
            popul.Next(objfun)  #generate new generation
            sys.stdout.write('\r')
            sys.stdout.flush()
            
        sys.stdout.write('\n')
        if not visible: 
            #hidden output
            sys.stdout=out
            f.close()
            
        if plot_graph:
            mpl.figure()
            mpl.plot(graph,'-')
            mpl.xlabel('Number of generations')
            mpl.ylabel(r'Minimal $\chi^2$')
            mpl.plot(graph_mean,'--')
            mpl.legend(['Best solution',r'Mean $\chi^2$ in generation'])

        if db is not None:
            #saving GA fitting details to file
            for x in save_dat: save_dat[x]=np.array(save_dat[x])
            f=open(db,'wb')
            pickle.dump(save_dat,f,protocol=2)
            f.close()
            
        for param in p: self.params[param]=p[param]   #save found parameters 
        self.params_err={}   #remove errors of parameters
        #remove some values calculated from old parameters
        self.paramsMore={}
        self.paramsMore_err={}

        return self.params


    def FitMCMC(self,n_iter,burn=0,binn=1,visible=True,db=None):
        '''fitting with Markov chain Monte Carlo
        n_iter - number of MC iteration - should be at least 1e5
        burn - number of removed steps before equilibrium - should be approx. 0.1-1% of n_iter
        binn - binning size - should be around 10
        visible - display status of fitting
        db - name of database to save MCMC fitting details (could be analysed later using InfoMCMC function)
        '''

        #setting pymc sampling for fitted parameters        
        pars={}
        for p in self.fit_params:
            pars[p]=pymc.Uniform(p,lower=self.limits[p][0],upper=self.limits[p][1],value=self.params[p])

        def model_fun(**vals):
            '''model function for pymc'''
            param=dict(vals)
            for x in self.params:
                #add fixed parameters
                if not x in param: param[x]=self.params[x]
            return self.Model(param=param)        

        #definition of pymc model
        model=pymc.Deterministic(
            eval=model_fun,
            doc='model',
            name='Model',
            parents=pars,
            trace=True,
            plot=False)

        #final distribution
        if self._set_err or self._calc_err:
            #if known errors of data -> normal/Gaussian distribution
            y=pymc.Normal('y',mu=model,tau=1./self.err**2,value=self.oc,observed=True)
        else:
            #if unknown errors of data -> Poisson distribution
            #note: should cause wrong performance of fitting, rather use function CalcErr for obtained errors
            y=pymc.Poisson('y',mu=model,value=self.oc,observed=True)

        #adding final distribution and sampling of parameters to model
        Model=[y]
        for v in pars.itervalues():
            Model.append(v)

        #create pymc object
        if db is None: R=pymc.MCMC(Model)
        else:
            #saving MCMC fitting details
            path=db.replace('\\','/')   #change dirs in path (for Windows)
            if path.rfind('/')>0:
                path=path[:path.rfind('/')+1]  #find current dir of db file
                if not os.path.isdir(path): os.mkdir(path) #create dir of db file, if not exist
            R=pymc.MCMC(Model,db='pickle',dbname=db)

        #setting pymc method - distribution and steps
        for p in pars:
            R.use_step_method(pymc.Metropolis,pars[p],proposal_sd=self.steps[p],
                              proposal_distribution='Normal')

        if not visible: 
            #hidden output
            f = open(os.devnull, 'w')
            out=sys.stdout            
            sys.stdout=f 
            
        R.sample(iter=n_iter,burn=burn,thin=binn)  #MCMC fitting/simulation

        self.params_err={} #remove errors of parameters
        #remove some values calculated from old parameters
        self.paramsMore={}
        self.paramsMore_err={}
            
        for p in pars:
            #calculate values and errors of parameters and save them
            self.params[p]=R.stats()[p]['mean']
            self.params_err[p]=R.stats()[p]['standard deviation']

        print ''
        R.summary() #summary of MCMC fitting
        
        if not visible: 
            #hidden output
            sys.stdout=out
            f.close()

        return self.params,self.params_err


    def Summary(self,name=None):
        '''summary of parameters, output to file "name"'''
        params=[]
        unit=[]
        vals=[]
        err=[]
        for x in sorted(self.params.keys()):
            #names, units, values and errors of model params
            params.append(x)
            vals.append(str(self.params[x]))
            if not len(self.params_err)==0:
                #errors calculated
                if x in self.params_err: err.append(str(self.params_err[x]))
                elif x in self.fit_params: err.append('---')   #errors not calculated
                else: err.append('fixed')  #fixed params
            elif x in self.fit_params: err.append('---')  #errors not calculated
            else: err.append('fixed')   #fixed params
            #add units
            if x[0]=='a' or x[0]=='r': unit.append('AU')
            elif x[0]=='P':
                unit.append('d')
                #also in years
                params.append(x)
                vals.append(str(self.params[x]/365.2425))
                try: err.append(str(float(err[-1])/365.2425)) #error calculated
                except: err.append(err[-1])  #error not calculated
                unit.append('y')
            elif x[0]=='Q': unit.append('d')
            elif x[0]=='t': unit.append('JD')
            elif x[0]=='e' or x[0]=='m': unit.append('')
            elif x[0]=='w' or x[1]=='w':
                #transform to deg
                vals[-1]=str(np.rad2deg(float(vals[-1])))
                try: err[-1]=str(np.rad2deg(float(err[-1]))) #error calculated
                except: pass  #error not calculated
                unit.append('deg')
        
        #calculate some more parameters, if not calculated
        self.MassFun()
        self.Amplitude()
        self.ParamsApsidal()
        
        #make blank line        
        params.append('')
        vals.append('')
        err.append('')
        unit.append('')
        for x in sorted(self.paramsMore.keys()):
            #names, units, values and errors of more params
            params.append(x)
            vals.append(str(self.paramsMore[x]))
            if not len(self.paramsMore_err)==0:
                #errors calculated
                if x in self.paramsMore_err:
                    err.append(str(self.paramsMore_err[x]))
                else: err.append('---')   #errors not calculated
            else: err.append('---')  #errors not calculated
            #add units
            if x[0]=='f' or x[0]=='M': unit.append('M_sun')
            elif x[0]=='a': unit.append('AU')
            elif x[0]=='P' or x[0]=='U':
                unit.append('d')
                #also in years
                params.append(x)
                vals.append(str(self.paramsMore[x]/365.2425))
                try: err.append(str(float(err[-1])/365.2425)) #error calculated
                except: err.append(err[-1])  #error not calculated
                unit.append('y')
            elif x[0]=='K': 
                unit.append('s')
                #also in minutes
                params.append(x)
                vals.append(str(self.paramsMore[x]/60.))
                try: err.append(str(float(err[-1])/60.)) #error calculated
                except: err.append(err[-1])  #error not calculated
                unit.append('m')
        
        #generate text output
        text=['parameter'.ljust(15,' ')+'unit'.ljust(10,' ')+'value'.ljust(30,' ')+'error']
        for i in range(len(params)):
            text.append(params[i].ljust(15,' ')+unit[i].ljust(10,' ')+vals[i].ljust(30,' ')+err[i].ljust(20,' '))
        text.append('')
        text.append('Model: '+self.model)
        if len(self.params_err)==0: text.append('Fitting method: GA')
        else: text.append('Fitting method: MCMC')
        chi=self.Chi2(self.params)
        n=len(self.t)
        g=len(self.fit_params)
        #calculate some stats
        text.append('chi2 = '+str(chi))
        text.append('chi2_r = '+str(chi/(n-g)))
        text.append('AIC = '+str(chi+2*g))
        text.append('AICc = '+str(chi+2*g*n/(n-g-1)))
        text.append('BIC = '+str(chi+g*np.log(n)))
        if name is None:
            #output to screen
            print '------------------------------------'
            for t in text: print t
            print '------------------------------------'
        else:
            #output to file
            f=open(name,'w')
            for t in text: f.write(t+'\n')
            f.close()
            
            
    def Amplitude(self):
        '''calculate amplitude of O-C in seconds'''
        output={}  
        if 'LiTE3' in self.model:
            #LiTE3 and LiTE3Quad models
            if 'K4' in self.paramsMore: 
                #remove values calculated before
                del self.paramsMore['K4']
                if 'K4' in self.paramsMore_err: del self.paramsMore_err['K4']
                    
            self.paramsMore['K3']=self.params['a_sin_i3']*AU/c*np.sqrt(1-self.params['e3']**2*np.cos(self.params['w3'])**2)
            output['K3']=self.paramsMore['K3']              
            if len(self.params_err)>0:
                #calculate error of Amplitude
                #get errors of params of 3rd body
                if 'e3' in self.params_err: e_err=self.params_err['e3']
                else: e_err=0
                if 'a_sin_i3' in self.params_err: a_err=self.params_err['a_sin_i3']*AU
                else: a_err=0
                if 'w3' in self.params_err: w_err=self.params_err['w3']
                else: w_err=0
                #partial derivations
                sqrt=np.sqrt(1-self.params['e3']*np.cos(self.params['w3']))
                da=sqrt/c  #dK3/d(a_sin_i3)
                de=-self.params['a_sin_i3']*AU*self.params['e3']*np.cos(self.params['w3'])/(c*sqrt) #dK3/de3
                dw=self.params['a_sin_i3']*AU*self.params['e3']**2*np.sin(self.params['w3'])*np.cos(self.params['w3'])/(c*sqrt) #dK3/dw3
                self.paramsMore_err['K3']=np.sqrt((da*a_err)**2+(de*e_err)**2+(dw*w_err)**2)
                
                #if some errors = 0, del them; and return only non-zero errors           
                if self.paramsMore_err['K3']==0: del self.paramsMore_err['K3']                
                else: output['K3_err']=self.paramsMore_err['K3']
            
            
        if 'LiTE34' in self.model:
            #LiTE34 and LiTE34Quad models
            self.paramsMore['K4']=self.params['a_sin_i4']*AU/c*np.sqrt(1-self.params['e4']**2*np.cos(self.params['w4'])**2)
            output['K4']=self.paramsMore['K4']            
            if len(self.params_err)>0:                 
                #calculate error of Amplitude            
                #get errors of params of 4th body
                if 'e4' in self.params_err: e_err=self.params_err['e4']
                else: e_err=0
                if 'a_sin_i4' in self.params_err: a_err=self.params_err['a_sin_i4']*AU
                else: a_err=0
                if 'w4' in self.params_err: w_err=self.params_err['w4']
                else: w_err=0
                #partial derivations
                sqrt=np.sqrt(1-self.params['e4']*np.cos(self.params['w4']))
                da=sqrt/c  #dK4/d(a_sin_i4)
                de=-self.params['a_sin_i4']*AU*self.params['e4']*np.cos(self.params['w4'])/(c*sqrt) #dK4/de4
                dw=self.params['a_sin_i4']*AU*self.params['e4']**2*np.sin(self.params['w4'])*np.cos(self.params['w4'])/(c*sqrt) #dK4/dw4
                self.paramsMore_err['K4']=np.sqrt((da*a_err)**2+(de*e_err)**2+(dw*w_err)**2)
    
                #if some errors = 0, del them; and return only non-zero errors           
                if self.paramsMore_err['K4']==0: del self.paramsMore_err['K4']                
                else: output['K4_err']=self.paramsMore_err['K4']        
                    
        
        if 'ExPlanet' in self.model:
            #AgolExPlanet and AgolExPlanetLin models
            if 'K4' in self.paramsMore: 
                #remove values calculated before
                del self.paramsMore['K4']
                if 'K4' in self.paramsMore_err: del self.paramsMore_err['K4']
            
            self.paramsMore['K3']=day*self.params['mu3']/(2*np.pi*(1-self.params['mu3']))*self.params['P']**2/self.params['P3']*\
                                  (1-self.params['e3']**2)**(-3./2.)*2*(np.arctan(self.params['e3']/(1+np.sqrt(1-self.params['e3']**2)))+self.params['e3'])
            
            output['K3']=self.paramsMore['K3']
            if len(self.params_err)>0: 
                #calculate error of Amplitude
                #get errors of params of 3rd body
                if 'e3' in self.params_err: e_err=self.params_err['e3']
                else: e_err=0
                if 'P3' in self.params_err: P3_err=self.params_err['P3']*day
                else: P3_err=0
                if 'mu3' in self.params_err: mu_err=self.params_err['mu3']
                else: mu_err=0
                if 'P' in self.params_err: P_err=self.params_err['P']*day
                else: P_err=0
                #partial derivations
                K=self.paramsMore['K3']
                dmu=K/(1-self.params['mu3'])  #dK3/dmu3
                dP=2*K/self.params['P']/day   #dK3/dP
                dP3=-K/self.params['P3']/day   #dK3/dP3
                e=self.params['e3']
                de=day*self.params['mu3']/(2*np.pi*(1-self.params['mu3']))*self.params['P']**2/self.params['P3']*\
                   ((4*np.sqrt(1-e**2))*e**2+2*np.sqrt(1-e**2)+6*np.sqrt(1-e**2)*e*np.arctan(e/(np.sqrt(1-e**2)+1))+1)/(e**2-1)**3           #dK3/de3
                self.paramsMore_err['K3']=np.sqrt((dmu*mu_err)**2+(dP*P_err)**2+(dP3*P3_err)**2+(de*e_err)**2)
                
                #if some errors = 0, del them; and return only non-zero errors           
                if self.paramsMore_err['K3']==0: del self.paramsMore_err['K3']                
                else: output['K3_err']=self.paramsMore_err['K3']
            
            
        if 'InPlanet' in self.model:
            #AgolInPlanet and AgolInPlanetLin models
            if 'K4' in self.paramsMore: 
                #remove values calculated before
                del self.paramsMore['K4']
                if 'K4' in self.paramsMore_err: del self.paramsMore_err['K4']
            
            self.paramsMore['K3']=day*self.params['P']*self.params['mu3']*self.params['r3']*np.sqrt(1-self.params['e']**2)/\
                                  (2*np.pi*self.params['a']*(1-self.params['e']*np.sin(self.params['w'])))
            
            output['K3']=self.paramsMore['K3']
            if len(self.params_err)>0:           
                #calculate error of Amplitude
                #get errors of params of 3rd body
                if 'e' in self.params_err: e_err=self.params_err['e']
                else: e_err=0
                if 'mu3' in self.params_err: mu_err=self.params_err['mu3']
                else: mu_err=0
                if 'P' in self.params_err: P_err=self.params_err['P']*day
                else: P_err=0
                if 'r3' in self.params_err: r_err=self.params_err['r3']*AU                
                else: r_err=0
                if 'a' in self.params_err: a_err=self.params_err['a']*AU
                else: a_err=0
                if 'w' in self.params_err: w_err=self.params_err['w']
                else: w_err=0
                #partial derivations
                K=self.paramsMore['K3']
                dmu=K/self.params['mu3']  #dK3/dmu3
                dP=K/self.params['P']/day   #dK3/dP
                dr=K/self.params['r3']/AU   #dK3/dr3
                da=K/self.params['a']/AU   #dK3/da
                e=self.params['e']
                w=self.params['w']
                de=-K*np.sqrt(1+e)*(e-np.sin(w))/(1-e*np.sin(w))          #dK3/de
                dw=K*e*np.cos(w)/(1-e*np.sin(w))          #dK3/dw
                self.paramsMore_err['K3']=np.sqrt((dmu*mu_err)**2+(dP*P_err)**2+(dr*r_err)**2
                                                  +(de*e_err)**2+(da*a_err)**2+(dw*w_err)**2)
                
                #if some errors = 0, del them; and return only non-zero errors           
                if self.paramsMore_err['K3']==0: del self.paramsMore_err['K3']                
                else: output['K3_err']=self.paramsMore_err['K3']
                
        if 'Apsid' in self.model:
            #Apsidal motion
            if 'K4' in self.paramsMore: 
                #remove values calculated before
                del self.paramsMore['K4']
                if 'K4' in self.paramsMore_err: del self.paramsMore_err['K4']
            self.paramsMore['K3']=day*self.params['P']*self.params['e']/np.pi
            
            output['K3']=self.paramsMore['K3']
            if len(self.params_err)>0:           
                #calculate error of Amplitude
                #get errors of params of 3rd body
                if 'e' in self.params_err: e_err=self.params_err['e']
                else: e_err=0
                if 'P' in self.params_err: P_err=self.params_err['P']
                else: P_err=0
                self.paramsMore_err['K3']=self.paramsMore['K3']*np.sqrt((P_err/self.params['P'])**2+\
                                          (e_err/self.params['e'])**2)
                
                #if some errors = 0, del them; and return only non-zero errors           
                if self.paramsMore_err['K3']==0: del self.paramsMore_err['K3']                
                else: output['K3_err']=self.paramsMore_err['K3']            
            
        return output
    
    def ParamsApsidal(self):
        '''calculate some params for model of apsidal motion'''
        output={}
        if not 'Apsidal' in self.model: return output
        self.paramsMore['Ps']=self.params['P']*(1-self.params['dw']/(2*np.pi))
        self.paramsMore['U']=self.paramsMore['Ps']*2*np.pi/self.params['dw']
        output['Ps']=self.paramsMore['Ps']
        output['U']=self.paramsMore['U']
            
        if len(self.params_err)>0: 
            #calculate error of params
            #get errors of params of model
            if 'P' in self.params_err: P_err=self.params_err['P']
            else: P_err=0            
            if 'dw' in self.params_err: dw_err=self.params_err['dw']
            else: dw_err=0
            
            self.paramsMore_err['Ps']=np.sqrt((1-self.params['dw']/(2*np.pi))**2*P_err**2+\
                                      (self.params['P']/(2*np.pi)*dw_err)**2)
            self.paramsMore_err['U']=self.paramsMore['U']*np.sqrt((P_err/self.params['P'])**2+\
                                      (dw_err/self.params['dw'])**2)
            
            #if some errors = 0, del them; and return only non-zero errors           
            if self.paramsMore_err['Ps']==0: del self.paramsMore_err['Ps']
            else: output['Ps_err']=self.paramsMore_err['Ps']
            if self.paramsMore_err['U']==0: del self.paramsMore_err['U']
            else: output['U_err']=self.paramsMore_err['U']
            return output
            
            
    def MassFun(self):
        '''calculate Mass Function for LiTE models'''
        output={}
        if 'LiTE3' in self.model:
            #LiTE3 and LiTE3Quad models
            if 'f_m4' in self.paramsMore: 
                #remove values calculated before
                del self.paramsMore['f_m4']
                if 'f_m4' in self.paramsMore_err: del self.paramsMore_err['f_m4']
                
            self.paramsMore['f_m3']=self.params['a_sin_i3']**3/(self.params['P3']/365.2425)**2
            output['f_m3']=self.paramsMore['f_m3']            
            if len(self.params_err)>0: 
                #calculate error of Mass Function
                #get errors of params of 3rd body
                if 'P3' in self.params_err: P3_err=self.params_err['P3']
                else: P3_err=0            
                if 'a_sin_i3' in self.params_err: a_err=self.params_err['a_sin_i3']
                else: a_err=0
                self.paramsMore_err['f_m3']=self.paramsMore['f_m3']*np.sqrt(9*(a_err/self.params['a_sin_i3'])**2+\
                                             4*(P3_err/self.params['P3'])**2) 
                #if some errors = 0, del them; and return only non-zero errors           
                if self.paramsMore_err['f_m3']==0: del self.paramsMore_err['f_m3']
                else: output['f_m3_err']=self.paramsMore_err['f_m3']
            
            
        if 'LiTE34' in self.model:
            #LiTE34 and LiTE34Quad models
            self.paramsMore['f_m4']=self.params['a_sin_i4']**3/(self.params['P4']/365.2425)**2
            output['f_m4']=self.paramsMore['f_m4']            
            if len(self.params_err)>0: 
                #calculate error of Mass Function
                #get errors of params of 4th body
                if 'P4' in self.params_err: P4_err=self.params_err['P4']
                else: P4_err=0            
                if 'a_sin_i4' in self.params_err: a_err=self.params_err['a_sin_i4']
                else: a_err=0
                self.paramsMore_err['f_m4']=self.paramsMore['f_m4']*np.sqrt(9*(a_err/self.params['a_sin_i4'])**2+\
                                            4*(P4_err/self.params['P4'])**2)
                
                #if some errors = 0, del them; and return only non-zero errors           
                if self.paramsMore_err['f_m4']==0: del self.paramsMore_err['f_m4']
                else: output['f_m4_err']=self.paramsMore_err['f_m4']
        return output
        


    def AbsoluteParam(self,M,i=90,M_err=0,i_err=0):
        '''calculate mass and semi-mayor axis of 3rd body from mass of binary and inclination'''
        self.MassFun() 
        output={}
        if 'LiTE3' in self.model:
            #LiTE3 and LiTE3Quad models
            self.paramsMore['a12']=self.params['a_sin_i3']/np.sin(np.deg2rad(i))
            f=self.paramsMore['f_m3']/np.sin(np.deg2rad(i))**3   #Mass function of 3rd body/sin(i)**3
            root=(2*f**3+18*f**2*M+3*np.sqrt(3)*np.sqrt(4*f**3*M**3+27*f**2*M**4)+27*f*M**2)**(1./3.)
            self.paramsMore['M3']=root/(3.*2.**(1./3.))-2.**(1./3.)*(-f**2-6.*f*M)/(3.*root)+f/3.
            self.paramsMore['a3']=self.paramsMore['a12']*M/self.paramsMore['M3']
            self.paramsMore['a']=self.paramsMore['a12']+self.paramsMore['a3']
            
            output['M3']=self.paramsMore['M3']
            output['a12']=self.paramsMore['a12']
            output['a3']=self.paramsMore['a3']
            output['a']=self.paramsMore['a']
            if len(self.params_err)>0:
                #calculate error of params
                #get errors of params of 3rd body
                if 'a_sin_i3' in self.params_err: a_err=self.params_err['a_sin_i3']
                else: a_err=0
                if 'f_m3' in self.paramsMore_err: f3_err=self.paramsMore_err['f_m3']
                else: f3_err=0
                f_err=f*np.sqrt((f3_err/self.paramsMore['f_m3'])**2+9*(np.deg2rad(i_err)/np.tan(np.deg2rad(i)))**2)
    
                #some strange partial derivations... (calculated using Wolfram Mathematica)
                #dM3/dM            
                dM=-((2**(1/3.)*(f**2+6*f*M)*(54*f*M+(3*np.sqrt(3)*(8*f**3*M+108*f**2*M**3))/(2*np.sqrt(4*f**3*M**2+27*f**2*M**4))))/(9*(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*M**2+\
                    27*f**2*M**4))**(4/3.)))+(54*f*M+(3*np.sqrt(3)*(8*f**3*M+108*f**2*M**3))/(2*np.sqrt(4*f**3*M**2+27*f**2*M**4)))/(9*2**(1/3.)*(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*\
                    M**2+27*f**2*M**4))**(2/3.))+(2*2**(1/3.)*f)/(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*M**2+27*f**2*M**4))**(1/3.)

                #dM3/df
                df=1/3.-(2**(1/3.)*(f**2+6*f*M)*(36*f+6*f**2+27*M**2+(3*np.sqrt(3)*(12*f**2*M**2+54*f*M**4))/(2*np.sqrt(4*f**3*M**2+27*f**2*M**4))))/(9*(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*\
                    np.sqrt(4*f**3*M**2+27*f**2*M**4))**(4/3.))+(36*f+6*f**2+27*M**2+(3*np.sqrt(3)*(12*f**2*M**2+54*f*M**4))/(2*np.sqrt(4*f**3*M**2+27*f**2*M**4)))/(9*2**(1/3.)*(18*f**2+2*f**3+\
                    27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*M**2+27*f**2*M**4))**(2/3.))+(2**(1/3.)*(2*f+6*M))/(3*(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*M**2+27*f**2*M**4))**(1/3.))
                
                #calculate errors of params
                self.paramsMore_err['a12']=self.paramsMore['a12']*np.sqrt((a_err/self.params['a_sin_i3'])**2+(np.deg2rad(i_err)/np.tan(np.deg2rad(i)))**2)
                self.paramsMore_err['M3']=np.sqrt((dM*M_err)**2+(df*f_err)**2)
                self.paramsMore_err['a3']=self.paramsMore['a3']*np.sqrt((self.paramsMore_err['a12']/self.paramsMore['a12'])**2+\
                                        (M_err/M)**2+(self.paramsMore_err['M3']/self.paramsMore['M3'])**2)
                self.paramsMore_err['a']=self.paramsMore_err['a12']+self.paramsMore_err['a3']
                
                #if some errors = 0, del them; and return only non-zero errors 
                if self.paramsMore_err['M3']==0: del self.paramsMore_err['M3']
                else: output['M3_err']=self.paramsMore_err['M3']
                if self.paramsMore_err['a12']==0: del self.paramsMore_err['a12']
                else: output['a12_err']=self.paramsMore_err['a12']
                if self.paramsMore_err['a3']==0: del self.paramsMore_err['a3']
                else: output['a3_err']=self.paramsMore_err['a3']
                if self.paramsMore_err['a']==0: del self.paramsMore_err['a']
                else: output['a_err']=self.paramsMore_err['a']
                
                
        if 'LiTE34' in self.model:
            #Lite34 a Lite34Quad models
            self.paramsMore['a12-3']=self.paramsMore['a']
            output['a12-3']=self.paramsMore['a']
            if 'a' in self.paramsMore_err: 
                self.paramsMore_err['a12-3']=self.paramsMore_err['a']
                output['a_err']=self.paramsMore_err['a']
            
            self.paramsMore['a123']=self.params['a_sin_i4']/np.sin(np.deg2rad(i))
            f=self.paramsMore['f_m4']/np.sin(np.deg2rad(i))**3   #Mass function of 4th body/sin(i)**3

            root=(2*f**3+18*f**2*M+3*np.sqrt(3)*np.sqrt(4*f**3*M**3+27*f**2*M**4)+27*f*M**2)**(1./3.)
            self.paramsMore['M4']=root/(3*2**(1./3.))-2**(1./3.)*(-f**2-6*f*M)/(3*root)+f/3.
            self.paramsMore['a4']=self.paramsMore['a12']*M/self.paramsMore['M4']
            self.paramsMore['a']=self.paramsMore['a12']+self.paramsMore['a4']

            output['M4']=self.paramsMore['M4']
            output['a123']=self.paramsMore['a123']
            output['a4']=self.paramsMore['a4']
            output['a']=self.paramsMore['a']
            if len(self.params_err)>0:
                #calculate error of params
                #get errors of params of 3rd body
                if 'a_sin_i4' in self.params_err: a_err=self.params_err['a_sin_i4']
                else: a_err=0
                if 'f_m4' in self.paramsMore_err: f4_err=self.paramsMore_err['f_m4']
                else: f4_err=0
                f_err=f*np.sqrt((f4_err/self.paramsMore['f_m4'])**2+9*(np.deg2rad(i_err)/np.tan(np.deg2rad(i)))**2)
    
                #some strange partial derivations... (calculated using Derive6)
                #dM4/dM            
                #some strange partial derivations... (calculated using Wolfram Mathematica)
                #dM3/dM            
                dM=-((2**(1/3.)*(f**2+6*f*M)*(54*f*M+(3*np.sqrt(3)*(8*f**3*M+108*f**2*M**3))/(2*np.sqrt(4*f**3*M**2+27*f**2*M**4))))/(9*(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*M**2+\
                    27*f**2*M**4))**(4/3.)))+(54*f*M+(3*np.sqrt(3)*(8*f**3*M+108*f**2*M**3))/(2*np.sqrt(4*f**3*M**2+27*f**2*M**4)))/(9*2**(1/3.)*(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*\
                    M**2+27*f**2*M**4))**(2/3.))+(2*2**(1/3.)*f)/(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*M**2+27*f**2*M**4))**(1/3.)

                #dM3/df
                df=1/3.-(2**(1/3.)*(f**2+6*f*M)*(36*f+6*f**2+27*M**2+(3*np.sqrt(3)*(12*f**2*M**2+54*f*M**4))/(2*np.sqrt(4*f**3*M**2+27*f**2*M**4))))/(9*(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*\
                    np.sqrt(4*f**3*M**2+27*f**2*M**4))**(4/3.))+(36*f+6*f**2+27*M**2+(3*np.sqrt(3)*(12*f**2*M**2+54*f*M**4))/(2*np.sqrt(4*f**3*M**2+27*f**2*M**4)))/(9*2**(1/3.)*(18*f**2+2*f**3+\
                    27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*M**2+27*f**2*M**4))**(2/3.))+(2**(1/3.)*(2*f+6*M))/(3*(18*f**2+2*f**3+27*f*M**2+3*np.sqrt(3)*np.sqrt(4*f**3*M**2+27*f**2*M**4))**(1/3.))
                
                #calculate errors of params
                self.paramsMore_err['a123']=self.paramsMore['a123']*np.sqrt((a_err/self.params['a_sin_i4'])**2+(np.deg2rad(i_err)/np.tan(np.deg2rad(i)))**2)
                self.paramsMore_err['M4']=np.sqrt((dM*M_err)**2+(df*f_err)**2)
                self.paramsMore_err['a4']=self.paramsMore['a4']*np.sqrt((self.paramsMore_err['a123']/self.paramsMore['a123'])**2+\
                                        (M_err/M)**2+(self.paramsMore_err['M4']/self.paramsMore['M4'])**2)
                self.paramsMore_err['a']=self.paramsMore_err['a123']+self.paramsMore_err['a4']

                #if some errors = 0, del them; and return only non-zero errors 
                if self.paramsMore_err['M4']==0: del self.paramsMore_err['M4']
                else: output['M4_err']=self.paramsMore_err['M4']
                if self.paramsMore_err['a123']==0: del self.paramsMore_err['a123']
                else: output['a123_err']=self.paramsMore_err['a123']
                if self.paramsMore_err['a4']==0: del self.paramsMore_err['a4']
                else: output['a4_err']=self.paramsMore_err['a4']
                if self.paramsMore_err['a']==0: del self.paramsMore_err['a']
                else: output['a_err']=self.paramsMore_err['a']
            
        
        if 'Agol' in self.model:
            #AgolInPlanet, AgolInPlanetLin, AgolExPlanet, AgolExPlanetLin
            self.paramsMore['M3']=M*self.params['mu3']/(1-self.params['mu3'])
            self.paramsMore['a']=((self.params['P3']/365.2425)**2*(M+self.paramsMore['M3']))**(1./3.)
            
            output['M3']=self.paramsMore['M3']
            output['a']=self.paramsMore['a']            
            if len(self.params_err)>0:
                #calculate error of params
                #get errors of params of 3rd body
                if 'mu3' in self.params_err: mu3_err=self.params_err['mu3']
                else: mu3_err=0
                if 'P3' in self.params_err: P3_err=self.params_err['P3']
                else: P3_err=0
                
                #calculate error of params
                self.paramsMore_err['M3']=self.paramsMore['M3']*np.sqrt((M_err/M)**2+\
                                    (mu3_err/(self.params['mu3']*(1-self.params['mu3'])))**2)
                self.paramsMore_err['a']=self.paramsMore['a']/3.*np.sqrt(((M_err+self.paramsMore_err['M3'])/\
                                    (M+self.paramsMore['M3']))**2+(2*P3_err/self.params['P3'])**2)
    
                #if some errors = 0, del them; and return only non-zero errors 
                if self.paramsMore_err['M3']==0: del self.paramsMore_err['M3']
                else: output['M3_err']=self.paramsMore_err['M3']
                if self.paramsMore_err['a']==0: del self.paramsMore_err['a']
                else: output['a_err']=self.paramsMore_err['a']
        return output


    def Model(self,t=None,param=None,min_type=None):
        ''''calculate model curve of O-C in given times based on given set of parameters'''
        if t is None: t=self.t          
        if param is None: param=self.params        
        if self.model=='LiTE3':
            model=self.LiTE3(t,param['a_sin_i3'],param['e3'],param['w3'],param['t03'],param['P3'])
        elif self.model=='LiTE34':
            model=self.LiTE34(t,param['a_sin_i3'],param['e3'],param['w3'],param['t03'],param['P3'],
                              param['a_sin_i4'],param['e4'],param['w4'],param['t04'],param['P4'])
        elif self.model=='LiTE3Quad':
            model=self.LiTE3Quad(t,param['t0'],param['P'],param['Q'],param['a_sin_i3'],param['e3'],
                                 param['w3'],param['t03'],param['P3'])
        elif self.model=='LiTE34Quad':
            model=self.LiTE34Quad(t,param['t0'],param['P'],param['Q'],
                                  param['a_sin_i3'],param['e3'],param['w3'],param['t03'],param['P3'],
                                  param['a_sin_i4'],param['e4'],param['w4'],param['t04'],param['P4'])
        elif self.model=='AgolInPlanet':
            model=self.AgolInPlanet(t,param['P'],param['a'],param['w'],param['e'],
                                    param['mu3'],param['r3'],param['w3'],param['t03'],param['P3'])
        elif self.model=='AgolInPlanetLin':
            model=self.AgolInPlanetLin(t,param['t0'],param['P'],param['a'],param['w'],param['e'],
                                       param['mu3'],param['r3'],param['w3'],param['t03'],param['P3'])
        elif self.model=='AgolExPlanet':
            model=self.AgolExPlanet(t,param['P'],param['mu3'],param['e3'],param['t03'],param['P3'])
        elif self.model=='AgolExPlanetLin':
            model=self.AgolExPlanetLin(t,param['t0'],param['P'],param['mu3'],param['e3'],param['t03'],param['P3']) 
        elif self.model=='Apsidal':
            if min_type is None: min_type=self._min_type    
            model=self.Apsidal(t,param['t0'],param['P'],param['w0'],param['dw'],param['e'],min_type)
        else:
            raise ValueError('The model "'+self.model+'" does not exist!')
        return model


    def CalcErr(self):
        '''estimate errors of input data based on current model (useful before using FitMCMC)'''
        model=self.Model(self.t,self.params)  #calculate model values

        n=len(model)   #number of data points
        err=np.sqrt(sum((self.oc-model)**2)/(n-1))   #calculate corrected sample standard deviation 
        err*=np.ones(model.shape)  #generate array of errors
        chi=sum(((self.oc-model)/err)**2)   #calculate new chi2 error -> chi2_r = 1
        print 'New chi2:',chi,chi/(n-len(self.fit_params))
        self._calc_err=True
        self._set_err=False
        self.err=err
        return err

    def CorrectErr(self):
        '''correct scale of given errors of input data based on current model 
        (useful if FitMCMC gives worse results like FitGA and chi2_r is not approx. 1)'''
        model=self.Model(self.t,self.params)     #calculate model values

        n=len(model)   #number of data points
        chi0=sum(((self.oc-model)/self.err)**2)    #original chi2 error
        alfa=chi0/(n-len(self.fit_params))         #coefficient between old and new errors -> chi2_r = 1
        err=self.err*np.sqrt(alfa)          #new errors
        chi=sum(((self.oc-model)/err)**2)   #calculate new chi2 error
        print 'New chi2:',chi,chi/(n-len(self.fit_params))
        if self._set_err and len(self._old_err)==0: self._old_err=self.err    #if errors were given, save old values
        self.err=err
        self._corr_err=True
        return err

    def AddWeight(self,weight):
        '''adding weight of input data + scaling according to current model
        warning: weights have to be in same order as input date!'''
        if not len(weight)==len(self.t):
            #if wrong length of given weight array
            print 'incorrect length of "w"!'
            return
            
        weight=np.array(weight)
        err=1./weight[self._order]   #transform to errors and change order according to order of input data
        n=len(self.t)   #number of data points
        model=self.Model(self.t,self.params)   #calculate model values

        chi0=sum(((self.oc-model)/err)**2)    #original chi2 error
        alfa=chi0/(n-len(self.fit_params))    #coefficient between old and new errors -> chi2_r = 1
        err*=np.sqrt(alfa)              #new errors
        chi=sum(((self.oc-model)/err)**2)   #calculate new chi2 error
        print 'New chi2:',chi,chi/(n-len(self.fit_params))
        self._calc_err=True
        self._set_err=False
        self.err=err
        return err



    def Plot(self,name=None,no_plot=0,no_plot_err=0,params=None,eps=False,oc_min=True,
             time_type='JD',offset=2400000,trans=True,title=None,epoch=False,
             min_type=False,weight=None,trans_weight=False,model2=False,with_res=False,
             bw=False,double_ax=False,legend=None,fig_size=None):
        '''plotting original O-C with model O-C based on current parameters set
        name - name of file to saving plot (if not given -> show graph)
        no_plot - number of outlier point which will not be plot
        no_plot_err - number of errorful point which will not be plot
        params - set of params of current model (if not given -> current parameters set)
        eps - save also as eps file
        oc_min - O-C in minutes (if False - days)
        time_type - type of JD in which is time (show in x label)
        offset - offset of time
        trans - transform time according to offset
        title - name of graph
        epoch - x axis in epoch
        min_type - distinction of type of minimum
        weight - weight of data (shown as size of points)
        trans_weight - transform weights to range (1,10)
        model2 - plot 2 model O-Cs - current params set and set given in "params"
        with_res - common plot with residue
        bw - Black&White plot
        double_ax - two axes -> time and epoch
        legend - labels for data and model(s) - give '' if no show label, 2nd model given in "params" is the last
        fig_size - custom figure size - e.g. (12,6)
        
        warning: weights have to be in same order as input data!
        '''            
        
        if epoch:
            if not len(self.epoch)==len(self.t):
                raise NameError('Epoch not callculated! Run function "Epoch" before it.')

        if model2:
            if params is None:
                raise ValueError('Parameters set for 2nd model not given!')
            params_model=dict(params)
            params=self.params
        if params is None: params=self.params
        if legend is None: 
            legend=['','','']
            show_legend=False
        else: show_legend=True
        
        if fig_size:
            fig=mpl.figure(figsize=fig_size)
        else:
            fig=mpl.figure()
            
        #2 plots - for residue
        if with_res:    
            gs=gridspec.GridSpec(2,1,height_ratios=[4,1])
            ax1=fig.add_subplot(gs[0])
            ax2=fig.add_subplot(gs[1],sharex=ax1)
        else: 
            ax1=fig.add_subplot(1,1,1)
            ax2=ax1
        ax1.yaxis.set_label_coords(-0.11,0.5)
        
        #setting labels
        if epoch and not double_ax:
            ax2.set_xlabel('Epoch')
            x=self.epoch
        elif offset>0:
            ax2.set_xlabel('Time ('+time_type+' - '+str(offset)+')')
            if not trans: offset=0
            x=self.t-offset
        else:
            ax2.set_xlabel('Time ('+time_type+')')
            offset=0
            x=self.t

        if oc_min:
            ax1.set_ylabel('O - C (min)')
            k=minutes
        else:
            ax1.set_ylabel('O - C (d)')
            k=1
            
        if title is not None: 
            if double_ax: fig.subplots_adjust(top=0.85)
            fig.suptitle(title,fontsize=20)                
            
        model=self.Model(self.t,params)
        self.res=self.oc-model

        #primary / secondary minimum
        if min_type:
            if not len(self.epoch)==len(self.t):
                raise NameError('Epoch not callculated! Run function "Epoch" before it.')
            prim=np.where(self._min_type==0)
            sec=np.where(self._min_type==1)
        else:
            prim=np.arange(0,len(self.t),1)
            sec=np.array([])

        #set weight
        set_w=False
        if weight is not None:
            weight=np.array(weight)[self._order]
            if trans_weight:
                w_min=min(weight)
                w_max=max(weight)
                weight=9./(w_max-w_min)*(weight-w_min)+1
            if weight.shape==self.t.shape:
                w=[]
                levels=[0,3,5,7.9,10]
                size=[3,4,5,7]
                for i in range(len(levels)-1):
                    w.append(np.where((weight>levels[i])*(weight<=levels[i+1])))
                w[-1]=np.append(w[-1],np.where(weight>levels[-1]))  #if some weight is bigger than max. level
                set_w=True                
            else:
                warnings.warn('Shape of "weight" is different to shape of "time". Weight will be ignore!')

        errors=GetMax(abs(model-self.oc),no_plot)  #remove outlier points
        if bw: color='k'
        else: color='b'
        if set_w:
            #using weights
            prim=np.delete(prim,np.where(np.in1d(prim,errors)))
            sec=np.delete(sec,np.where(np.in1d(sec,errors)))
            if not len(prim)==0:
                for i in range(len(w)):
                    ax1.plot(x[prim[np.where(np.in1d(prim,w[i]))]],
                             (self.oc*k)[prim[np.where(np.in1d(prim,w[i]))]],color+'o',markersize=size[i],label=legend[0],zorder=1)
            if not len(sec)==0:
                for i in range(len(w)):
                    ax1.plot(x[sec[np.where(np.in1d(sec,w[i]))]],
                             (self.oc*k)[sec[np.where(np.in1d(sec,w[i]))]],color+'o',markersize=size[i],
                             fillstyle='none',markeredgewidth=1,markeredgecolor=color,label=legend[0],zorder=1)

        else:
            #without weight
            if self._set_err:
                #using errors
                if self._corr_err: err=self._old_err
                else: err=self.err
                errors=np.append(errors,GetMax(err,no_plot_err))  #remove errorful points
                prim=np.delete(prim,np.where(np.in1d(prim,errors)))
                sec=np.delete(sec,np.where(np.in1d(sec,errors)))
                if not len(prim)==0:
                    ax1.errorbar(x[prim],(self.oc*k)[prim],yerr=(err*k)[prim],fmt=color+'o',markersize=5,label=legend[0],zorder=1)
                if not len(sec)==0:
                    ax1.errorbar(x[sec],(self.oc*k)[sec],yerr=(err*k)[sec],fmt=color+'o',markersize=5,
                                 fillstyle='none',markeredgewidth=1,markeredgecolor=color,label=legend[0],zorder=1)

            else:
                #without errors
                prim=np.delete(prim,np.where(np.in1d(prim,errors)))
                sec=np.delete(sec,np.where(np.in1d(sec,errors)))
                if not len(prim)==0:
                    ax1.plot(x[prim],(self.oc*k)[prim],color+'o',label=legend[0],zorder=1)
                if not len(sec)==0:
                    ax1.plot(x[sec],(self.oc*k)[sec],color+'o',label=legend[0],
                             mfc='none',markeredgewidth=1,markeredgecolor=color,zorder=1)

        #expand time interval for model O-C
        if len(self.t)<1000:
            if 't0' in params:
                old_epoch=self.epoch
                dE=(self.epoch[-1]-self.epoch[0])/1000.
                E=np.linspace(self.epoch[0]-50*dE,self.epoch[-1]+50*dE,1100)
                t1=params['t0']+params['P']*E
                self.epoch=E
            elif epoch:
                dE=(self.epoch[-1]-self.epoch[0])/1000.
                E=np.linspace(self.epoch[0]-50*dE,self.epoch[-1]+50*dE,1100)
                t1=self._t0P[0]+self._t0P[1]*E
            else:
                dt=(self.t[-1]-self.t[0])/1000.
                t1=np.linspace(self.t[0]-50*dt,self.t[-1]+50*dt,1100)
        else:
            if 't0' in params:
                old_epoch=self.epoch
                dE=(self.epoch[-1]-self.epoch[0])/len(self.epoch)
                E=np.linspace(self.epoch[0]-0.05*len(self.epoch)*dE,self.epoch[-1]+0.05*len(self.epoch)*dE,1.1*len(self.epoch))
                t1=params['t0']+params['P']*E
                self.epoch=E
            elif epoch:
                dE=(self.epoch[-1]-self.epoch[0])/len(self.epoch)
                E=np.linspace(self.epoch[0]-0.05*len(self.epoch)*dE,self.epoch[-1]+0.05*len(self.epoch)*dE,1.1*len(self.epoch))
                t1=self._t0P[0]+self._t0P[1]*E
            else:
                dt=(self.t[-1]-self.t[0])/len(self.t)
                t1=np.linspace(self.t[0]-0.05*len(self.t)*dt,self.t[-1]+0.05*len(self.t)*dt,1.1*len(self.t))


        if bw: 
            color='k'
            lw=2
        else: 
            color='r'
            lw=1
                
        if self.model=='Apsidal':
            #primary
            model_long=self.Model(t1,params,min_type=np.zeros(t1.shape))
            if epoch and not double_ax: ax1.plot(E,model_long*k,color,linewidth=lw,label=legend[1],zorder=2)
            else: ax1.plot(t1-offset,model_long*k,color,linewidth=lw,label=legend[1],zorder=2)
            #secondary
            model_long=self.Model(t1,params,min_type=np.ones(t1.shape))
            if epoch and not double_ax: ax1.plot(E,model_long*k,color,linewidth=lw,label=legend[1],zorder=2)
            else: ax1.plot(t1-offset,model_long*k,color,linewidth=lw,label=legend[1],zorder=2)
        else:
            model_long=self.Model(t1,params)            
            if epoch and not double_ax: ax1.plot(E,model_long*k,color,linewidth=lw,label=legend[1],zorder=2)
            else: ax1.plot(t1-offset,model_long*k,color,linewidth=lw,label=legend[1],zorder=2)
        
        if model2:
            #plot second model
            if bw: 
                color='k'
                lt='--'
            else: 
                color='g'
                lt='-'
            model_set=self.Model(t1,params_model)
            if epoch and not double_ax: ax1.plot(E,model_set*k,color+lt,linewidth=lw,label=legend[2],zorder=3)
            else: ax1.plot(t1-offset,model_set*k,color+lt,linewidth=lw,label=legend[2],zorder=3)
        
        if show_legend: ax1.legend() 
        
        if 't0' in params: self.epoch=old_epoch
        
        if double_ax:
            #setting secound axis
            if not len(self.epoch)==len(self.t):
                raise NameError('Epoch not callculated! Run function "Epoch" before it.')
            ax3=ax1.twiny() 
            #generate plot to obtain correct axis in epoch
            #expand time interval for model O-C
            if len(self.t)<1000:
                dE=(self.epoch[-1]-self.epoch[0])/1000.
                E=np.linspace(self.epoch[0]-50*dE,self.epoch[-1]+50*dE,1100)
            else:
                dE=(self.epoch[-1]-self.epoch[0])/len(self.epoch)
                E=np.linspace(self.epoch[0]-0.05*len(self.epoch)*dE,self.epoch[-1]+0.05*len(self.epoch)*dE,1.1*len(self.epoch))
            l=ax3.plot(E,model_long*k)
            ax3.set_xlabel('Epoch')
            l.pop(0).remove()
            lims=np.array(ax1.get_xlim())
            epoch=np.round((lims-self._t0P[0])/self._t0P[1]*2)/2.
            ax3.set_xlim(epoch)     
                    
        if with_res:
            #plot residue
            if bw: color='k'
            else: color='b'
            if oc_min: ax2.set_ylabel('Residue (min)')
            else: ax2.set_ylabel('Residue (d)')
            ax2.yaxis.set_label_coords(-0.1,0.5)
            m=round(abs(max(-min(self.res),max(self.res)))*k,2)
            ax2.set_autoscale_on(False)
            ax2.set_ylim([-m,m])
            ax2.yaxis.set_ticks(np.array([-m,0,m]))
            ax2.plot(x,self.res*k,color+'o')
            ax2.xaxis.labelpad=15
            ax2.yaxis.labelpad=15
            mpl.subplots_adjust(hspace=.07)
            mpl.setp(ax1.get_xticklabels(),visible=False)

        if name is None: mpl.show()
        else:
            mpl.savefig(name+'.png')
            if eps: mpl.savefig(name+'.eps')
            mpl.close(fig)


    def PlotRes(self,name=None,no_plot=0,no_plot_err=0,params=None,eps=False,oc_min=True,
                time_type='JD',offset=2400000,trans=True,title=None,epoch=False,
                min_type=False,weight=None,trans_weight=False,bw=False,double_ax=False,
                fig_size=None):
        '''plotting residue (new O-C)
        name - name of file to saving plot (if not given -> show graph)
        no_plot - count of outlier point which will not be plot
        no_plot_err - count of errorful point which will not be plot
        params - set of params of current model (if not given -> current parameters set)
        eps - save also as eps file
        oc_min - O-C in minutes (if False - days)
        time_type - type of JD in which is time (show in x label)
        offset - offset of time
        trans - transform time according to offset
        title - name of graph
        epoch - x axis in epoch
        min_type - distinction of type of minimum
        weight - weight of data (shown as size of points)
        trans_weight - transform weights to range (1,10)
        bw - Black&White plot
        double_ax - two axes -> time and epoch
        fig_size - custom figure size - e.g. (12,6)
        
        warning: weights have to be in same order as input data!
        '''

        if epoch:
            if not len(self.epoch)==len(self.t):
                raise NameError('Epoch not callculated! Run function "Epoch" before it.')

        if params is None: params=self.params

        if fig_size:
            fig=mpl.figure(figsize=fig_size)
        else:
            fig=mpl.figure()
            
        ax1=fig.add_subplot(1,1,1)
        ax1.yaxis.set_label_coords(-0.11,0.5)
        
        #setting labels
        if epoch and not double_ax:
            ax1.set_xlabel('Epoch')
            x=self.epoch
        elif offset>0:
            ax1.set_xlabel('Time ('+time_type+' - '+str(offset)+')')
            if not trans: offset=0
            x=self.t-offset
        else:
            ax1.set_xlabel('Time ('+time_type+')')
            offset=0
            x=self.t

        if oc_min:
            ax1.set_ylabel('Residue O - C (min)')
            k=minutes
        else:
            ax1.set_ylabel('Residue O - C (d)')
            k=1
        if title is not None: 
            if double_ax: fig.subplots_adjust(top=0.85)
            fig.suptitle(title,fontsize=20)

        model=self.Model(self.t,params)
        self.res=self.oc-model

        #primary / secondary minimum
        if min_type:
            if not len(self.epoch)==len(self.t):
                raise NameError('Epoch not callculated! Run function "Epoch" before it.')
            prim=np.where(self._min_type==0)
            sec=np.where(self._min_type==1)
        else:
            prim=np.arange(0,len(self.t),1)
            sec=np.array([])

        #set weight
        set_w=False
        if weight is not None:
            weight=np.array(weight)[self._order]
            if trans_weight:
                w_min=min(weight)
                w_max=max(weight)
                weight=9./(w_max-w_min)*(weight-w_min)+1
            if weight.shape==self.t.shape:
                w=[]
                levels=[0,3,5,7.9,10]
                size=[3,4,5,7]
                for i in range(len(levels)-1):
                    w.append(np.where((weight>levels[i])*(weight<=levels[i+1])))
                w[-1]=np.append(w[-1],np.where(weight>levels[-1]))  #if some weight is bigger than max. level
                set_w=True
            else:
                warnings.warn('Shape of "weight" is different to shape of "time". Weight will be ignore!')


        errors=GetMax(abs(self.res),no_plot)  #remove outlier points   
        if bw: color='k'
        else: color='b'
        if set_w:
            #using weights
            prim=np.delete(prim,np.where(np.in1d(prim,errors)))
            sec=np.delete(sec,np.where(np.in1d(sec,errors)))
            if not len(prim)==0:
                for i in range(len(w)):
                    mpl.plot(x[prim[np.where(np.in1d(prim,w[i]))]],
                             (self.res*k)[prim[np.where(np.in1d(prim,w[i]))]],color+'o',markersize=size[i])
            if not len(sec)==0:
                for i in range(len(w)):
                    mpl.plot(x[sec[np.where(np.in1d(sec,w[i]))]],
                             (self.res*k)[sec[np.where(np.in1d(sec,w[i]))]],color+'o',markersize=size[i],
                             fillstyle='none',markeredgewidth=1,markeredgecolor=color)

        else:
            #without weight
            if self._set_err:
                #using errors
                if self._corr_err: err=self._old_err
                else: err=self.err
                errors=np.append(errors,GetMax(err,no_plot_err))  #remove errorful points
                prim=np.delete(prim,np.where(np.in1d(prim,errors)))
                sec=np.delete(sec,np.where(np.in1d(sec,errors)))
                if not len(prim)==0:
                    mpl.errorbar(x[prim],(self.res*k)[prim],yerr=(err*k)[prim],fmt=color+'o',markersize=5)
                if not len(sec)==0:
                    mpl.errorbar(x[sec],(self.res*k)[sec],yerr=(err*k)[sec],fmt=color+'o',markersize=5,
                                 fillstyle='none',markeredgewidth=1,markeredgecolor=color)

            else:
                #without errors
                prim=np.delete(prim,np.where(np.in1d(prim,errors)))
                sec=np.delete(sec,np.where(np.in1d(sec,errors)))
                if not len(prim)==0:
                    mpl.plot(x[prim],(self.res*k)[prim],color+'o')
                if not len(sec)==0:
                    mpl.plot(x[sec],(self.res*k)[sec],color+'o',
                             mfc='none',markeredgewidth=1,markeredgecolor=color)
        
        if double_ax:
            #setting secound axis
            if not len(self.epoch)==len(self.t):
                raise NameError('Epoch not callculated! Run function "Epoch" before it.')
            ax2=ax1.twiny() 
            #generate plot to obtain correct axis in epoch
            l=ax2.plot(self.epoch,self.res*k)
            ax2.set_xlabel('Epoch')
            l.pop(0).remove()
            lims=np.array(ax1.get_xlim())
            epoch=np.round((lims-self._t0P[0])/self._t0P[1]*2)/2.
            ax2.set_xlim(epoch)        
                    
        if name is None: mpl.show()
        else:
            mpl.savefig(name+'.png')
            if eps: mpl.savefig(name+'.eps')
            mpl.close(fig)
            
            

    def SaveModel(self,name,E_min=None,E_max=None,n=1000,params=None,t0=None,P=None):
        '''save model curve of O-C to file
        name - name of output file
        E_min - minimal value of epoch
        E_max - maximal value of epoch
        n - number of data points
        params - parameters of model (if not given, used "params" from class)
        t0 - time of zeros epoch (necessary if not given in model or epoch not calculated)
        P - period (necessary if not given in model or epoch not calculated)
        '''

        if params is None: params=self.params
        
        #get linear ephemeris
        if 't0' in params: t0=params['t0']
        elif len(self.epoch)==len(self.t): t0=self._t0P[0]
        elif t0 is None: raise TypeError('t0 is not given!')
        
        if 'P' in params: P=params['P']
        elif len(self.epoch)==len(self.t): P=self._t0P[1]
        elif P is None: raise TypeError('P is not given!')
        
        old_epoch=self.epoch
        if not len(self.epoch)==len(self.t): self.Epoch(t0,P)
        
        #same interval of epoch like in plot
        if len(self.epoch)<1000: dE=50*(self.epoch[-1]-self.epoch[0])/1000.
        else: dE=0.05*(self.epoch[-1]-self.epoch[0])
        
        if E_min is None: E_min=min(self.epoch)-dE
        if E_max is None: E_max=max(self.epoch)+dE
            
        self.epoch=np.linspace(E_min,E_max,n)
        t=t0+P*self.epoch
        
        if self.model=='Apsidal':            
            typeA=np.append(np.zeros(t.shape),np.ones(t.shape))
            t=np.append(t,t)
            self.epoch=np.append(self.epoch,self.epoch)
            i=np.argsort(np.append(np.arange(0,len(t),2),np.arange(1,len(t),2)))
            t=t[i]
            typeA=typeA[i]
            self.epoch=self.epoch[i]
            model=self.Model(t,params,min_type=typeA)            
            
            f=open(name,'w')
            np.savetxt(f,np.column_stack((t+model,self.epoch,model,typeA)), fmt=["%14.7f",'%10.3f',"%+12.10f","%1d"]
                       ,delimiter='    ',header='Obs. Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')+'    model O-C'.ljust(13,' ')+'    type')
            f.close()
        else: 
            model=self.Model(t,params)

            f=open(name,'w')
            np.savetxt(f,np.column_stack((t+model,self.epoch,model)),fmt=["%14.7f",'%10.3f',"%+12.10f"]
                       ,delimiter='    ',header='Obs. Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    model O-C')
            f.close()

        self.epoch=old_epoch


    def SaveRes(self,name,params=None,t0=None,P=None,weight=None):
        '''save residue to file
        name - name of output file
        params - parameters of model (if not given, used "params" from class)
        t0 - time of zeros epoch (necessary if not given in model or epoch not calculated)
        P - period (necessary if not given in model or epoch not calculated)
        weight - weights of input data points
        
        warning: weights have to be in same order as input date!
        '''
        

        if params is None: params=self.params
        
        #get linear ephemeris
        if 't0' in params: t0=params['t0']
        elif len(self.epoch)==len(self.t): t0=self._t0P[0]
        elif t0 is None: raise TypeError('t0 is not given!')
        
        if 'P' in params: P=params['P']
        elif len(self.epoch)==len(self.t): P=self._t0P[1]
        elif P is None: raise TypeError('P is not given!')

        old_epoch=self.epoch        
        if not len(self.epoch)==len(self.t): self.Epoch(self.t,t0,P)

        model=self.Model(self.t,params)

        self.res=self.oc-model
        f=open(name,'w')
        if self._set_err:
            if self._corr_err: err=self._old_err
            else: err=self.err
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.res,err)),
                       fmt=["%14.7f",'%10.3f',"%+12.10f","%.10f"],delimiter="    ",
                       header='Obs. Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    '+'new O-C'.ljust(10,' ')+'    Error')
        elif weight is not None:
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.res,np.array(weight)[self._order])),
                       fmt=["%14.7f",'%10.3f',"%+12.10f","%.10f"],delimiter="    ",
                       header='Obs. Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    '+'new O-C'.ljust(12,' ')+'    Weight')  
        else:
            np.savetxt(f,np.column_stack((self.t,self.epoch,self.res)),
                       fmt=["%14.7f",'%10.3f',"%+12.10f"],delimiter="    ",
                       header='Obs. Time'.ljust(14,' ')+'    '+'Epoch'.ljust(10,' ')
                       +'    new O-C')
        f.close()
        self.epoch=old_epoch



class OCFitLoad(OCFit):
    '''loading saved data, model... from OCFit class''' 
    def __init__(self,path):
        '''loading data, model, parameters... from file'''
        self._order=[]
        self.t=[]    #times
        self.oc=[]  #O-Cs
        self.err=[]   #errors
        self._set_err=False
        
        self.limits={}          #limits of parameters for fitting
        self.steps={}           #steps (width of normal distibution) of parameters for fitting
        self.params={}          #values of parameters, fixed values have to be set here
        self.params_err={}      #errors of fitted parameters
        self.paramsMore={}      #values of parameters calculated from model params
        self.paramsMore_err={}  #errors of calculated parameters
        self.fit_params=[]      #list of fitted parameters
        self._calc_err=False    #errors were calculated
        self._corr_err=False    #errors were corrected
        self._old_err=[]        #given errors 
        self.model='LiTE3'      #used model of O-C
        self._t0P=[]            #linear ephemeris of binary
        self.epoch=[]           #epoch of binary
        self.res=[]             #residua = new O-C
        self._min_type=[]        #type of minima (primary=0 / secondary=1)
        self.availableModels=['LiTE3','LiTE34','LiTE3Quad','LiTE34Quad',\
                              'AgolInPlanet','AgolInPlanetLin','AgolExPlanet',\
                              'AgolExPlanetLin','Apsidal']   #list of available models        
        self.Load(path)
