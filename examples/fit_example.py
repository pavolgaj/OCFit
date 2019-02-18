from OCFit import OCFit, FitLinear
import numpy as np

#generating data
E = np.arange(0, 100, 1)  #epochs
#simulation of observed times, LiTE with amplitude 72 min. and period 1125 d
P = 15
t0 = 1540
t = P*E + t0 + 0.05*np.sin(2*np.pi/(5*P)*E) + np.random.normal(scale = 0.01, size = E.shape)
err = 0.01*np.ones(E.shape)  #errors of 'observed' times

#usage of FitLinear for calculation of O-C
#initialization using estiamtion (original values) of linear ephemeris
#for long time range of observation, the value of period has to be close
#to the right value, otherwise the primary and secondary minims could be mixed
lin = FitLinear(t, t0, P, err = err)
oc = lin.oc  #O-C calculated from original ephemeris

#WARNING! FitLinear sorts input data. "oc" is sorted now! Combination of
#sorted and unsorted data ("t", "err") leads to bad O-C diagram.
#Next to lines sort all data.
t = t[lin._order]
err = err[lin._order]

#initialization of class OCFit and O-C calculated using FitLinear
fit=OCFit(t,oc,err = err)
fit.Epoch(t0,P)  #calculating epochs

#setting the model and parameters for fitting
fit.model='LiTE3'
fit.fit_params=['a_sin_i3', 'e3', 'w3', 't03', 'P3']
fit.limits={'a_sin_i3': [5, 10], 'e3': [0, 1], 'w3': [0, 2*np.pi],
            't03': [1540, 3000], 'P3': [900, 1300]}
fit.steps={'a_sin_i3': 1e-2, 'e3': 1e-2, 'w3': 1e-2, 't03': 10, 'P3': 10}

#fitting using GA without displaying fitting progress
fit.FitGA(100,100,visible=False)
#sumarry of results after GA
fit.Summary()

#fitting using MCMC without displaying fitting progress
fit.FitMCMC(1e3,visible=False)
#sumarry of results after MC
fit.Summary() 

#plotting figure
#figure with original O-C with fit without transformation of x axis
#together with residue and 2nd axis in epochs
fit.Plot(trans = False,with_res=True,double_ax=True)

