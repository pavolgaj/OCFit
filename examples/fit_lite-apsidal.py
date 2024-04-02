import OCFit

name='lite-apsidal.json'        #name of file with loaded data, saved in GUI using "Save Class" button
ocf=OCFit.OCFitLoad(name)       #loading class from file

#set model and parameters
ocf.model='LiTE3ApsidalQuad'    #model LiTE3Apsidal or LiTE3ApsidalQuad 
ocf.fit_params=['a_sin_i3', 'e3','w3', 't03', 'P3',    #for LiTE3
                't0', 'P', 'w0', 'dw', 'e','Q']        #for Apsidal, "Q" for Quad
ocf.limits={'a_sin_i3': [5, 15], 'e3': [0, 1], 'w3': [0, 6.28],'t03': [1540, 4500], 'P3': [2000, 3000],      #for LiTE3
            't0':[1539.5,1540.5],'P':[14.9,15.1], 'w0':[0,6.28], 'dw':[0,1], 'e':[0,0.5],'Q':[1e-8,1e-4]}    #for Apsidal, "Q" for Quad
ocf.steps={'a_sin_i3': 1e-2, 'e3': 1e-2, 'w3': 1e-2, 't03': 10, 'P3': 10,     #for LiTE3
           't0': 1e-2, 'P':1e-3, 'w0':1e-2, 'dw':1e-4, 'e':1e-3,'Q':1e-8}     #for Apsidal, "Q" for Quad

ocf.Save(name)  #save class to file, can be loaded in GUI and used for fitting & plotting. BUT! NOT possible to change model and model params!!!

#or run fitting here...

#ocf.FitGA(generation=100,size=100)
#ocf.FitMCMC(n_iter=1e3,burn=0,binn=1)
#ocf.Plot()
#ocf.Summary()
#ocf.Save(name)  #save class to file
