from OCFit import FitQuad, FitLinear
import numpy as np

#generate data
E = np.arange(0, 100, 1)  #epochs
#simulation of observed times
t = 1e-5*E**2+15*E + 1540.4 + np.random.normal(scale = 0.01, size = E.shape)
err = 0.01*np.ones(E.shape)  #errors of 'observed' times

#usage of FitLinear to first estimation of linear ephemeris
#initialization using estiamtion (original values) of linear ephemeris
#for long time range of observation, the value of period has to be close
#to the right value, otherwise the primary and secondary minims could be mixed
lin = FitLinear(t, 1540, 15.01, err = err)
oc = lin.oc  #O-C calculated from original ephemeris
lin.FitLinear()  #linear fit
lin.FitRobust()  #fitting using robust regression

lin.Summary() #summary of parameters

err = lin.CorrectErr() #re-normalization of errors
oc = lin.FitRobust()  #fitting using robust regression

lin.Summary() #summary of parameters

#plotting figures
#plot of original values of O-C with fit, without transformation of x axis
lin.Plot(trans = False)
#plot of residual O-C, without transformation of x axis
lin.PlotRes(trans = False)

#usage of class FitQuad
#as estimation of linear ephemeris the resault from FitLinear are used
#new values of O-C are only fitted
quad = FitQuad(t, lin.t0, lin.P, oc = oc, err = err)
oc = quad.oc  #O-C calculated from original ephemeris
quad.FitQuad()  #quadratic fit
quad.FitRobust()  #fitting using robust regression

quad.Summary() #summary of parameters

#plotting figures
#plot of original values of O-C with fit, without transformation of x axis
quad.Plot(trans = False)
#plot of residual O-C, without transformation of x axis
quad.PlotRes(trans = False)
