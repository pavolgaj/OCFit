#!/usr/bin/python3

#script for fitting on background using OCFit
#input params: name_of_file number_of_generations size_of_gen number_of_MC_steps number_of_removed_steps binning_size save_fitting_sample
#update: 10.12.2021
# (c) Pavol Gajdos, 2021

import sys
import OCFit

name=sys.argv[1].strip()    #name of input file with saved class
path=name[:name.rfind('.')]

genGA=int(sys.argv[2])  #number of generations
sizeGA=int(sys.argv[3]) #size of generation

nMC=float(sys.argv[4])  #number of MC steps
burnMC=float(sys.argv[5])       #number of removed steps
binnMC=float(sys.argv[6])       #binning size

saveFit=bool(int(sys.argv[7]))   #save fitting sample to file; values = 0 / 1

ocf=OCFit.OCFitLoad(name)       #loading class from file

if genGA*sizeGA>0:
    #fitting with GA
    if saveFit: ocf.FitGA(genGA,sizeGA,db=path+'-ga.tmp')
    else: ocf.FitGA(genGA,sizeGA)

if nMC>0:
    #fitting with MCMC
    if not ocf._set_err: ocf.AddWeight(1./ocf.err)
    if saveFit: ocf.FitMCMC(nMC,burnMC,binnMC,db=path+'-mcmc.tmp')
    else: ocf.FitMCMC(nMC,burnMC,binnMC)

ocf.Save(name)  #save class to file
