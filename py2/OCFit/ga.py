#class for Genetic Algorithms
#version 0.1.1
#update: 12.3.2017
# (c) Pavol Gajdos, 2018

import numpy as np
import random

class TPopul:
    '''class for Genetic Algorithms'''
    def __init__(self,size,params,mut,steps,limits,SP):
        self.size=size  #size of population
        self.n=len(params)    #count of free parameters
        self.params=params   #free parameters
        self.n_mut=int(round(mut*size))   #count of mutations
        self.steps=steps    #variation of Gauss distribution for changing of params
        self.limits=limits   #limits of parameters
        self.edge=[]        #edges for roulette wheel

        #creating of population
        self.p=[]
        self.o=[]
        for i in range(size):
            temp={}
            for p in params:
                temp[p]=(limits[p][1]-limits[p][0])*np.random.rand()+limits[p][0]
            self.p.append(temp)
            self.o.append(dict(temp))

        #create sectors for roulette wheel (selective pressure) for crossing generations
        #given by Razali, N. M., Geraghty, J., 2011, Lect. Notes in Eng. Comp. Sci., 2191, 1134
        self.sectors=[]
        for i in range(self.size,0,-1): self.sectors.append(2-SP+2*(SP-1)*(i-1)/float(size-1))


    def Roulette(self,objfun):
        '''creating roulette wheel for crossing generations'''
        rank=np.argsort(objfun)
        self.edge=np.zeros(self.size)
        self.edge[rank]=self.sectors
        for i in range(1,self.size): self.edge[i]+=self.edge[i-1]
        self.edge=np.array(self.edge)/self.edge[-1]

    def Rand(self):
        '''select individual from population according to slot in roulette wheel'''
        temp=np.random.rand()
        i=np.where(temp<self.edge)[0][0]
        return i

    def Cross(self,p1,p2):
        '''crossing of generations'''
        cxb=random.sample(self.params,random.randint(1,self.n))

        #copy p->o
        o1=dict(p1)
        o2=dict(p2)

        if random.randint(0,2)==2:
            return [p1,p2]

        #crossing
        for p in cxb:
            o1[p]=p2[p]
            o2[p]=p1[p]
        return [o1,o2]


    def Mutation(self,i):
        '''mutations'''
        for p in self.params:
            #change from Gauss normal distribution
            dx=np.random.normal(scale=self.steps[p])
            self.p[i][p]+=dx
            #if new value is outside searching interval
            if (self.p[i][p]>self.limits[p][1]) or (self.p[i][p]<self.limits[p][0]):
                self.p[i][p]=self.o[i][p]

    def Next(self,objfun):
        '''creating new generation'''
        #create roulette
        self.Roulette(objfun)
        #new population
        i=0
        while i<self.size-1:
            o=self.Cross(self.p[self.Rand()],self.p[self.Rand()])
            self.o[i]=dict(o[0])
            self.o[i+1]=dict(o[1])
            i+=2

        #reversing population
        for i in range(self.size): self.p[i]=dict(self.o[i])

        #applying mutation
        for mut in range(self.n_mut): self.Mutation(random.randint(0,self.size-1))
