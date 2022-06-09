#!/usr/bin/python3

#main file for GUI for OCFit class
#update: 2022...
# (c) Pavol Gajdos, 2018-2022

import tkinter as tk
import tkinter.ttk
import tkinter.filedialog,tkinter.messagebox

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as mpl

import numpy as np

import subprocess

import os,sys

import OCFit

tPQ=[]


def load():
    #loading data from file

    global data

    def openFile():
        #create OpenFile dialog
        global path

        path=tkinter.filedialog.askopenfilename(parent=tLoad,filetypes=[('Data files','*.dat *.txt'),('All files','*.*')],title='Open file')
        path=path.replace('\\','/')
        tFName.config(text=path[path.rfind('/')+1:])

        if len(path)>0:
            if os.path.isfile(path):
                #test if file exists -> if yes, make buttons available
                bProc.config(state=tk.NORMAL)
                bPrev.config(state=tk.NORMAL)

    def preview():
        #open file with data in default software
        if sys.platform=='linux' or sys.platform=='linux2':
            subprocess.call(['xdg-open',path])
        else:
            os.startfile(path)


    def procFile():
        #load and analyse data file
        global data

        f=open(path,'r')
        lines=f.readlines()
        f.close()

        delimiter=delimVar.get().strip()

        #set header
        header=headVar.get()
        if len(header)==0: header=0
        else: header=int(header)

        #set used columns and their meaning
        cols={}
        if obsVarCh.get()==1 and len(obsVar.get())>0: cols['tO']=int(obsVar.get())
        if calcVarCh.get()==1 and len(calcVar.get())>0: cols['tC']=int(calcVar.get())
        if epVarCh.get()==1 and len(epVar.get())>0: cols['E']=int(epVar.get())
        if ocVarCh.get()==1 and len(ocVar.get())>0: cols['oc']=int(ocVar.get())
        if errVarCh.get()==1 and len(errVar.get())>0: cols['err']=int(errVar.get())
        if wVarCh.get()==1 and len(wVar.get())>0: cols['w']=int(wVar.get())
        if metVarCh.get()==1 and len(metVar.get())>0 and errVarCh.get()==0 and wVarCh.get()==0:
            cols['met']=int(metVar.get())

        data={}
        method=[]
        for c in cols: data[c]=[]

        #reading data
        for l in lines[header:]:
            #remove blank lines or comments
            if len(l.strip())==0: continue
            if l[0]=='#': continue

            if len(delimiter)==0: tmp=[x.strip() for x in l.split()]
            else: tmp=[x.strip() for x in l.split(delimiter)]

            for c in cols:
                #add data to columns
                if c=='met':
                    #observing methods
                    if not tmp[cols[c]].strip() in method: method.append(tmp[cols[c]].strip())
                    data[c].append(tmp[cols[c]].strip())
                else: data[c].append(float(tmp[cols[c]]))

        if 'met' in cols:
            #transform observing methods to errors / weights
            metFile=path[:path.rfind('.')]+'-methods.txt'
            metDic={}

            def gen():
                #create text file with used methods
                f=open(metFile,'w')
                f.write('# Write errors / weights for each used method to next column!\n')
                for m in method: f.write(m+'     \n')
                f.close()

                #open this file in default text editor
                if sys.platform=='linux' or sys.platform=='linux2':
                    subprocess.call(['xdg-open',metFile])
                else:
                    os.startfile(metFile)

            def loadM():
                #load file with errors / weights of methods
                tmp=metFile.replace('\\','/')
                #loading from generated file or open another file (e.g. created before)
                result=tkinter.messagebox.askquestion('Load file','Use file "'+tmp[tmp.rfind('/')+1:]+'"?',parent=tMet,icon='question')
                if result=='yes': name=metFile
                else: name=tkinter.filedialog.askopenfilename(parent=tMet,filetypes=[('Text files','*.lst *.txt'),('All files','*.*')],title='Open file')

                if len(name)==0: return

                f=open(name,'r')
                for l in f:
                    if not l[0]=='#' and len(l.strip())>0:
                        tmp=l.split()
                        metDic[tmp[0].strip()]=float(tmp[1])
                f.close()
                Button1.config(state=tk.NORMAL)

            def setM():
                #transform observing methods to errors / weights
                if valType.get()==0: c='err'
                else: c='w'
                data[c]=[]
                for i in range(len(data['met'])): data[c].append(metDic[data['met'][i]])

                tMet.destroy()
                tLoad.destroy()
                bPlot0.config(state=tk.NORMAL)
                bSave0.config(state=tk.NORMAL)
                bInit.config(state=tk.NORMAL)
                bLin.config(state=tk.NORMAL)
                bQuad.config(state=tk.NORMAL)

            #create window
            tMet=tk.Toplevel(tLoad)
            #default scale of window - NOT change this values if you want to change size
            tmwidth=258
            tmheight=150
            if fixed:
                tMet.geometry(str(tmwidth)+'x'+str(tmheight))   #modif. this line to change size - e.g. master.geometry('400x500')
            else:
                #set relatively to screen size
                tMet.geometry('{}x{}'.format(int(tmwidth/mwidth*screenwidth), int(tmheight/mheight*screenheight)))
            tMet.title('Methods')

            valType=tk.IntVar(tMet,value=0)   #variable for radiobuttons errors / weights

            #button - generate file
            bGen=tk.Button(tMet)
            bGen.place(relx=0.08,rely=0.09,relheight=b1height/tmheight,relwidth=b5width/tmwidth)
            bGen.configure(command=gen)
            bGen.configure(text='Generate file')

            #button - load file
            bLoadM=tk.Button(tMet)
            bLoadM.place(relx=0.54,rely=0.09,relheight=b1height/tmheight,relwidth=b5width/tmwidth)
            bLoadM.configure(command=loadM)
            bLoadM.configure(text='Load file')

            #radiobutton - given values are errors
            Radiobutton1=tk.Radiobutton(tMet)
            Radiobutton1.place(relx=0.16,rely=0.56,relheight=rheight/tmheight,relwidth=rwidth/tmwidth)
            Radiobutton1.configure(justify=tk.LEFT)
            Radiobutton1.configure(text='errors')
            Radiobutton1.configure(variable=valType)
            Radiobutton1.configure(value=0)
            Radiobutton1.configure(font=('None',9))

            #radiobutton - given values are weights
            Radiobutton2=tk.Radiobutton(tMet)
            Radiobutton2.place(relx=0.5,rely=0.56,relheight=rheight/tmheight,relwidth=rwidth/tmwidth)
            Radiobutton2.configure(justify=tk.LEFT)
            Radiobutton2.configure(text='weights')
            Radiobutton2.configure(variable=valType)
            Radiobutton2.configure(value=1)
            Radiobutton2.configure(font=('None',9))

            #label
            Label1=tk.Label(tMet)
            Label1.place(relx=0.08,rely=0.39,relheight=lheight/tmheight,relwidth=0.9)
            Label1.configure(text='Given values for methods are:')
            Label1.configure(anchor=tk.W)
            Label1.configure(font=('None',9))

            #button - process file and set errors / weights for all methods
            Button1=tk.Button(tMet)
            Button1.place(relx=0.35,rely=0.73,relheight=b1height/tmheight,relwidth=b6width/tmwidth)
            Button1.configure(command=setM)
            Button1.configure(text='OK')
            Button1.config(state=tk.DISABLED)

        else:
            #close window and make some buttons on main window available
            tLoad.destroy()
            bPlot0.config(state=tk.NORMAL)
            bSave0.config(state=tk.NORMAL)
            bInit.config(state=tk.NORMAL)
            bLin.config(state=tk.NORMAL)
            bQuad.config(state=tk.NORMAL)


    #create window
    tLoad=tk.Toplevel(master)
    #default scale of window - NOT change this values if you want to change size
    twidth=297
    theight=406
    if fixed:
        tLoad.geometry(str(twidth)+'x'+str(theight))   #modif. this line to change size - e.g. master.geometry('400x500')
    else:
        #set relatively to screen size
        tLoad.geometry('{}x{}'.format(int(twidth/mwidth*screenwidth), int(theight/mheight*screenheight)))
    tLoad.title('Load Data')

    #variables for delimiter and header
    delimVar=tk.StringVar(tLoad)
    headVar=tk.StringVar(tLoad,value='0')

    #variables for number of column with values
    obsVar=tk.StringVar(tLoad,value='0')
    calcVar=tk.StringVar(tLoad)
    epVar=tk.StringVar(tLoad)
    ocVar=tk.StringVar(tLoad)
    errVar=tk.StringVar(tLoad,value='1')
    wVar=tk.StringVar(tLoad)
    metVar=tk.StringVar(tLoad)

    #variables for using the types of data (if is available in file)
    obsVarCh=tk.IntVar(tLoad,value=1)
    calcVarCh=tk.IntVar(tLoad)
    epVarCh=tk.IntVar(tLoad)
    ocVarCh=tk.IntVar(tLoad)
    errVarCh=tk.IntVar(tLoad,value=1)
    wVarCh=tk.IntVar(tLoad)
    metVarCh=tk.IntVar(tLoad)

    #button load file
    bOpen=tk.Button(tLoad)
    bOpen.place(relx=0.2,rely=0.02,relheight=b1height/theight,relwidth=b6width/twidth)
    bOpen.configure(command=openFile)
    bOpen.configure(text='Open file')

    #button show file
    bPrev=tk.Button(tLoad)
    bPrev.place(relx=0.57,rely=0.02,relheight=b1height/theight,relwidth=b6width/twidth)
    bPrev.configure(command=preview)
    bPrev.configure(state=tk.DISABLED)
    bPrev.configure(text='Preview')

    #label with name of file
    tFName=tk.Label(tLoad)
    tFName.place(relx=0.07,rely=0.11,relheight=l2height/theight,relwidth=0.9)
    tFName.configure(text='')
    tFName.configure(width=256)

    #frame with delimiter and header
    Frame1=tk.Frame(tLoad)
    f1height=65
    f1width=265
    Frame1.place(relx=0.07,rely=0.17,relheight=f1height/theight,relwidth=f1width/twidth)
    Frame1.configure(relief=tk.GROOVE)
    Frame1.configure(borderwidth='2')
    Frame1.configure(relief=tk.GROOVE)
    Frame1.configure(width=265)

    #label
    Label3=tk.Label(Frame1)
    Label3.place(relx=0.02,rely=0.15,relheight=l2height/f1height,relwidth=0.27)
    Label3.configure(anchor=tk.W)
    Label3.configure(text='Delimiter')
    Label3.configure(width=86)
    Label3.configure(font=('None',9))

    #label
    Label4=tk.Label(Frame1)
    Label4.place(relx=0.02,rely=0.54,relheight=l2height/f1height,relwidth=0.27)
    Label4.configure(anchor=tk.W)
    Label4.configure(text='Header')
    Label4.configure(width=66)
    Label4.configure(font=('None',9))

    #input - delimiter
    delim=tk.Entry(Frame1)
    delim.place(relx=0.3,rely=0.08,relheight=iheight/f1height,relwidth=0.64)
    delim.configure(textvariable=delimVar)
    delim.configure(width=170)

    #input - header
    header=tk.Entry(Frame1)
    header.place(relx=0.3,rely=0.46,relheight=iheight/f1height,relwidth=0.64)
    header.configure(textvariable=headVar)

    #frame with columns
    Frame2=tk.Frame(tLoad)
    f2height=223
    f2width=265
    Frame2.place(relx=0.07,rely=0.34,relheight=f2height/theight,relwidth=f2width/twidth)
    Frame2.configure(relief=tk.GROOVE)
    Frame2.configure(borderwidth='2')
    Frame2.configure(relief=tk.GROOVE)
    Frame2.configure(width=265)

    #labels
    Label2=tk.Label(Frame2)
    Label2.place(relx=0.02,rely=0.04,relheight=l2height/f2height,relwidth=0.95)
    Label2.configure(text='Columns')
    Label2.configure(width=246)
    Label2.configure(font=('None',9))

    Label5=tk.Label(Frame2)
    Label5.place(relx=0.02,rely=0.16,relheight=l2height/f2height,relwidth=0.27)
    Label5.configure(anchor=tk.W)
    Label5.configure(text='Obs. time')
    Label5.configure(width=66)
    Label5.configure(font=('None',9))

    Label6=tk.Label(Frame2)
    Label6.place(relx=0.02,rely=0.26,relheight=l2height/f2height,relwidth=0.27)
    Label6.configure(anchor=tk.W)
    Label6.configure(text='Calc.time')
    Label6.configure(font=('None',9))

    Label7=tk.Label(Frame2)
    Label7.place(relx=0.02,rely=0.36,relheight=l2height/f2height,relwidth=0.27)
    Label7.configure(anchor=tk.W)
    Label7.configure(text='Epoch')
    Label7.configure(font=('None',9))

    Label8=tk.Label(Frame2)
    Label8.place(relx=0.02,rely=0.46,relheight=l2height/f2height,relwidth=0.27)
    Label8.configure(anchor=tk.W)
    Label8.configure(text='O-C')
    Label8.configure(font=('None',9))

    Label9=tk.Label(Frame2)
    Label9.place(relx=0.02,rely=0.56,relheight=l2height/f2height,relwidth=0.27)
    Label9.configure(anchor=tk.W)
    Label9.configure(text='Error')
    Label9.configure(font=('None',9))

    Label10=tk.Label(Frame2)
    Label10.place(relx=0.02,rely=0.66,relheight=l2height/f2height,relwidth=0.27)
    Label10.configure(anchor=tk.W)
    Label10.configure(text='Weight')
    Label10.configure(font=('None',9))

    Label11=tk.Label(Frame2)
    Label11.place(relx=0.02,rely=0.76,relheight=l2height/f2height,relwidth=0.27)
    Label11.configure(anchor=tk.W)
    Label11.configure(text='Method')
    Label11.configure(font=('None',9))

    #input - column observed times
    obs=tk.Entry(Frame2)
    obs.place(relx=0.3,rely=0.13,relheight=iheight/f2height,relwidth=0.57)
    obs.configure(textvariable=obsVar)

    #input - column calculated times
    calc=tk.Entry(Frame2)
    calc.place(relx=0.3,rely=0.23,relheight=iheight/f2height,relwidth=0.57)
    calc.configure(textvariable=calcVar)

    #input - column epochs
    ep=tk.Entry(Frame2)
    ep.place(relx=0.3,rely=0.33,relheight=iheight/f2height,relwidth=0.57)
    ep.configure(textvariable=epVar)

    #input - column O-Cs
    oc=tk.Entry(Frame2)
    oc.place(relx=0.3,rely=0.43,relheight=iheight/f2height,relwidth=0.57)
    oc.configure(textvariable=ocVar)

    #input - column errors
    err=tk.Entry(Frame2)
    err.place(relx=0.3,rely=0.53,relheight=iheight/f2height,relwidth=0.57)
    err.configure(textvariable=errVar)

    #input - column weights
    w=tk.Entry(Frame2)
    w.place(relx=0.3,rely=0.63,relheight=iheight/f2height,relwidth=0.57)
    w.configure(textvariable=wVar)

    #input - column methods
    met=tk.Entry(Frame2)
    met.place(relx=0.3,rely=0.73,relheight=iheight/f2height,relwidth=0.57)
    met.configure(textvariable=metVar)

    #check - column observed times available
    obsCh=tk.Checkbutton(Frame2)
    obsCh.place(relx=0.87,rely=0.14,relheight=0.09,relwidth=0.09)
    obsCh.configure(justify=tk.LEFT)
    obsCh.configure(variable=obsVarCh)

    #check - column calculated times available
    calcCh=tk.Checkbutton(Frame2)
    calcCh.place(relx=0.87,rely=0.24,relheight=0.09,relwidth=0.09)
    calcCh.configure(justify=tk.LEFT)
    calcCh.configure(variable=calcVarCh)

    #check - column epochs available
    epCh=tk.Checkbutton(Frame2)
    epCh.place(relx=0.87,rely=0.34,relheight=0.09,relwidth=0.09)
    epCh.configure(justify=tk.LEFT)
    epCh.configure(variable=epVarCh)

    #check - column O-Cs available
    ocCh=tk.Checkbutton(Frame2)
    ocCh.place(relx=0.87,rely=0.44,relheight=0.09,relwidth=0.09)
    ocCh.configure(justify=tk.LEFT)
    ocCh.configure(variable=ocVarCh)

    #check - column errors available
    errCh=tk.Checkbutton(Frame2)
    errCh.place(relx=0.87,rely=0.54,relheight=0.09,relwidth=0.09)
    errCh.configure(justify=tk.LEFT)
    errCh.configure(variable=errVarCh)

    #check - column weights available
    wCh=tk.Checkbutton(Frame2)
    wCh.place(relx=0.87,rely=0.64,relheight=0.09,relwidth=0.09)
    wCh.configure(justify=tk.LEFT)
    wCh.configure(variable=wVarCh)

    #check - column methods available
    metCh=tk.Checkbutton(Frame2)
    metCh.place(relx=0.87,rely=0.74,relheight=0.09,relwidth=0.09)
    metCh.configure(justify=tk.LEFT)
    metCh.configure(variable=metVarCh)

    #button process file
    bProc=tk.Button(tLoad)
    bProc.place(relx=0.35,rely=0.92,relheight=b1height/theight,relwidth=b3width/twidth)
    bProc.configure(command=procFile)
    bProc.configure(state=tk.DISABLED)
    bProc.configure(text='Process file')


def deltaE():
    #calculate phase/difference in epoch for secondary minima
    tkinter.messagebox.showerror('Calculate delta Epoch','Not implemented, yet!')
    return

def system():
    #set some general parameters of studied systems
    tkinter.messagebox.showerror('System Params','Not implemented, yet!')
    return

def plot0():
    #plot O-Cs calculated according to initial ephemeris
    global data,weight

    if len(t0Var.get())*len(pVar.get())==0:
        tkinter.messagebox.showerror('Fit Linear','Set linear ephemeris (T0, P)!')
        return

    t0=float(t0Var.get())
    P=float(pVar.get())

    if not 'tO' in data:
        if not 'tC' in data:
            if not 'E' in data: data['E']=range(len(data['oc']))
            data['tC']=[t0+P*data['E'][i] for i in range(len(data['oc']))]
        data['tO']=[data['tC'][i]+data['oc'][i] for i in range(len(data['oc']))]


    #setting errors
    if not 'err' in data and 'w' in data:
        weight=True
        err=[1./x for x in data['w']]
    elif 'err' in data:
        weight=False
        err=data['err']
    else:
        weight=True
        err=[1 for x in range(len(data['tO']))]

    oc=OCFit.FitLinear(data['tO'],t0,P,err=err)
    if weight: oc._set_err=False

    if data['tO'][0]<2e6: trans=False
    else: trans=True

    if not 'err' in data and 'w' in data: oc.Plot(trans=trans,weight=data['w'],min_type=True)
    else: oc.Plot(trans=trans,min_type=True)

def save0():
    #save O-Cs calculated according to initial ephemeris
    global data,weight

    if len(t0Var.get())*len(pVar.get())==0:
        tkinter.messagebox.showerror('Fit Linear','Set linear ephemeris (T0, P)!')
        return

    t0=float(t0Var.get())
    P=float(pVar.get())

    if not 'tO' in data:
        if not 'tC' in data:
            if not 'E' in data: data['E']=range(len(data['oc']))
            data['tC']=[t0+P*data['E'][i] for i in range(len(data['oc']))]
        data['tO']=[data['tC'][i]+data['oc'][i] for i in range(len(data['oc']))]

    #setting errors
    if not 'err' in data and 'w' in data:
        weight=True
        err=[1./x for x in data['w']]
    elif 'err' in data:
        weight=False
        err=data['err']
    else:
        weight=True
        err=[1 for x in range(len(data['tO']))]

    oc=OCFit.FitLinear(data['tO'],t0,P,err=err)
    if weight: oc._set_err=False

    for x in data: data[x]=np.array(data[x])[oc._order]   #save sorted values

    f=tkinter.filedialog.asksaveasfilename(parent=master,title='Save O-C to file',filetypes=[('Data files','*.dat *.txt'),('All files','*.*')],defaultextension='.dat')
    if len(f)==0: return

    if not 'err' in data and 'w' in data: oc.SaveOC(f,weight=data['w'])
    else: oc.SaveOC(f)

def fitParams0():
    #define params of fitting (used method, its params etc.) for linear/quadratic fitting
    tkinter.messagebox.showerror('Fit Params','Not implemented, yet!')
    return

def lin():
    #fitting O-Cs with a linear function
    global data,simple,weight,tPQ

    if len(t0Var.get())*len(pVar.get())==0:
        tkinter.messagebox.showerror('Fit Linear','Set linear ephemeris (T0, P)!')
        return

    if not 'tO' in data: data['tO']=[data['tC'][i]+data['oc'][i] for i in range(len(data['oc']))]

    t0=float(t0Var.get())
    P=float(pVar.get())

    #setting errors
    if not 'err' in data and 'w' in data:
        weight=True
        err=[1./x for x in data['w']]
    elif 'err' in data:
        weight=False
        err=data['err']
    else:
        weight=True
        err=[1 for x in range(len(data['tO']))]


    simple=OCFit.FitLinear(data['tO'],t0,P,err=err)
    if weight: simple._set_err=False

    simple.FitLinear()

    #save results
    for x in data: data[x]=np.array(data[x])[simple._order]   #save sorted values
    data['oc']=simple.new_oc
    data['tC']=simple.tC
    tPQ=[simple.t0,simple.P,0]

    #make some buttons available
    bPlotS.config(state=tk.NORMAL)
    bPlotRS.config(state=tk.NORMAL)
    bSumS.config(state=tk.NORMAL)
    bSaveRS.config(state=tk.NORMAL)
    bUpd.config(state=tk.NORMAL)

def quad():
    #fitting O-Cs with a quadratic function
    global data,simple,weight,tPQ

    if len(t0Var.get())*len(pVar.get())==0:
        tkinter.messagebox.showerror('Fit Linear','Set linear ephemeris (T0, P)!')
        return

    if not 'tO' in data: data['tO']=[data['tC'][i]+data['oc'][i] for i in range(len(data['oc']))]

    t0=float(t0Var.get())
    P=float(pVar.get())

    #setting errors
    if not 'err' in data and 'w' in data:
        weight=True
        err=[1./x for x in data['w']]
    elif 'err' in data:
        weight=False
        err=data['err']
    else:
        weight=True
        err=[1 for x in range(len(data['tO']))]

    simple=OCFit.FitQuad(data['tO'],t0,P,err=err)
    if weight: simple._set_err=False

    simple.FitQuad()

    #save results
    for x in data: data[x]=np.array(data[x])[simple._order]   #save sorted values
    data['oc']=simple.new_oc
    data['tC']=simple.tC
    tPQ=[simple.t0,simple.P,simple.Q]

    #make some buttons available
    bPlotS.config(state=tk.NORMAL)
    bPlotRS.config(state=tk.NORMAL)
    bSumS.config(state=tk.NORMAL)
    bSaveRS.config(state=tk.NORMAL)
    bUpd.config(state=tk.NORMAL)

def plotS():
    #plot O-Cs together with linear / quadratic fit
    if data['tO'][0]<2e6: trans=False
    else: trans=True

    if not 'err' in data and 'w' in data: simple.Plot(trans=trans,weight=data['w'],min_type=True)
    else: simple.Plot(trans=trans,min_type=True)


def plotRS():
    #plot residual O-Cs after linear / quadratic fit
    if data['tO'][0]<2e6: trans=False
    else: trans=True

    if not 'err' in data and 'w' in data: simple.PlotRes(trans=trans,weight=data['w'],min_type=True)
    else: simple.PlotRes(trans=trans,min_type=True)

class IORedirector(object):
    '''A general class for redirecting I/O to this Text widget.'''
    def __init__(self,text_area):
        self.text_area=text_area

class StdoutRedirector(IORedirector):
    '''A class for redirecting stdout to this Text widget.'''
    def write(self,str):
        self.text_area.insert(tk.END,str)


def sumS():
    #summary for linear / quadratic fit

    #create new window
    sumW=tk.Toplevel(master)
    #default scale of window - NOT change this values if you want to change size
    twidth=750
    theight=450
    if fixed:
        sumW.geometry(str(twidth)+'x'+str(theight))   #modif. this line to change size - e.g. master.geometry('400x500')
    else:
        #set relatively to screen size
        sumW.geometry('{}x{}'.format(int(twidth/mwidth*screenwidth), int(theight/mheight*screenheight)))
    sumW.title('Summary')

    #text field
    text=tk.Text(sumW)
    text.place(relx=0.02,rely=0.02,relheight=0.96,relwidth=0.96)

    old=sys.stdout
    #redirect output to text field
    sys.stdout=StdoutRedirector(text)
    simple.Summary()

    sys.stdout=old


def saveRS():
    #save residual O-Cs to file
    f=tkinter.filedialog.asksaveasfilename(parent=master,title='Save new O-C to file',filetypes=[('Data files','*.dat *.txt'),('All files','*.*')],defaultextension='.dat')
    if len(f)==0: return
    if not 'err' in data and 'w' in data: simple.SaveRes(f,weight=data['w'])
    else: simple.SaveRes(f)

def saveAll0():
    #run all saving functions
    tkinter.messagebox.showerror('Save All','Not implemented, yet!')
    return

def update():
    #update linear ephemeris
    t0Var.set(tPQ[0])
    pVar.set(tPQ[1])

def initC():
    #main class (OCFit) initialization
    global ocf,weight

    if len(t0Var.get())*len(pVar.get())==0:
        tkinter.messagebox.showerror('O-C Fit','Set linear ephemeris (T0, P)!')
        return

    t0=float(t0Var.get())
    P=float(pVar.get())

    #calculationg O-Cs
    if not 'oc' in data:
        lin=OCFit.FitLinear(data['tO'],t0,P)
        for x in data: data[x]=np.array(data[x])[lin._order]   #save sorted values
        data['oc']=lin.oc

    if not 'tO' in data:
        if not 'tC' in data:
            if not 'E' in data: data['E']=range(len(data['oc']))
            data['tC']=[t0+P*data['E'][i] for i in range(len(data['oc']))]
        data['tO']=[data['tC'][i]+data['oc'][i] for i in range(len(data['oc']))]

    #setting errors
    weight=False
    if not 'err' in data and 'w' in data:
        weight=True
        err=[1./x for x in data['w']]
    elif not 'err' in data and not 'w' in data:
        weight=True
        err=[1 for x in range(len(data['tO']))]
    else: err=data['err']

    ocf=OCFit.OCFit(data['tO'],data['oc'],err)

    ocf.Epoch(float(t0Var.get()),float(pVar.get()))   #calculate epochs

    if weight: ocf._set_err=False

    #make some buttons (un)available
    bSaveC.config(state=tk.NORMAL)
    bRunBG.config(state=tk.DISABLED)
    bFitGA.config(state=tk.DISABLED)
    bFitMC.config(state=tk.DISABLED)
    bFitParams.config(state=tk.DISABLED)
    bParams.config(state=tk.NORMAL)
    bPlot.config(state=tk.DISABLED)
    bPlotR.config(state=tk.DISABLED)
    bSaveM.config(state=tk.DISABLED)
    bSaveR.config(state=tk.DISABLED)
    bSum.config(state=tk.DISABLED)
    bSaveAll.config(state=tk.DISABLED)

def saveC(f=None):
    #save class to file
    if f is None:
        f=tkinter.filedialog.asksaveasfilename(parent=master,title='Save class to file',filetypes=[('OCFit files','*.ocf'),('All files','*.*')],defaultextension='.ocf')
    if len(f)==0: return
    ocf.Save(f)
    return f


def loadC():
    #load class from file
    global ocf
    f=tkinter.filedialog.askopenfilename(parent=master,title='Load class from file',filetypes=[('OCFit files','*.ocf'),('All files','*.*')])
    if len(f)==0: return
    ocf=OCFit.OCFitLoad(f)

    #make some buttons available
    bSaveC.config(state=tk.NORMAL)
    bFitParams.config(state=tk.NORMAL)
    bParams.config(state=tk.NORMAL)
    bPlot.config(state=tk.NORMAL)
    bPlotR.config(state=tk.NORMAL)
    bSaveM.config(state=tk.NORMAL)
    bSaveR.config(state=tk.NORMAL)
    bSum.config(state=tk.NORMAL)
    bSaveAll.config(state=tk.NORMAL)

def fitGA():
    #fitting using genetic algorithms
    for p in ocf.fit_params:
        if not p in ocf.limits:
            tkinter.messagebox.showerror('Fit GA','Set limits of parameter "'+p+'"!')
            return
        if not p in ocf.steps:
            tkinter.messagebox.showerror('Fit GA','Set step of parameter "'+p+'"!')
            return

    if save==1:
        f=tkinter.filedialog.asksaveasfilename(parent=master,title='Save GA fitting to file',filetypes=[('Temp files','*.tmp'),('All files','*.*')],defaultextension='.tmp')
        if len(f)==0: return
        ocf.FitGA(ga['gen'],ga['size'],db=f)
    else: ocf.FitGA(ga['gen'],ga['size'])

    #make some buttons available
    bPlot.config(state=tk.NORMAL)
    bPlotR.config(state=tk.NORMAL)
    bSaveM.config(state=tk.NORMAL)
    bSaveR.config(state=tk.NORMAL)
    bSum.config(state=tk.NORMAL)
    bSaveAll.config(state=tk.NORMAL)

def fitDE():
    #fitting using scipy differentional evolution
    tkinter.messagebox.showerror('Fit DE','Not implemented, yet!')
    return

def fitMC():
    #fitting using Monte Carlo method
    for p in ocf.fit_params:
        if not p in ocf.params:
            tkinter.messagebox.showerror('Fit MCMC','Set value of parameter "'+p+'"!')
            return
        if not p in ocf.limits:
            tkinter.messagebox.showerror('Fit MCMC','Set limits of parameter "'+p+'"!')
            return
        if not p in ocf.steps:
            tkinter.messagebox.showerror('Fit MCMC','Set step of parameter "'+p+'"!')
            return

    if not ocf._set_err: ocf.AddWeight(1./ocf.err) #adding weights

    if save==1:
        f=tkinter.filedialog.asksaveasfilename(parent=master,title='Save MCMC fitting to file',filetypes=[('Temp files','*.tmp'),('All files','*.*')],defaultextension='.tmp')
        if len(f)==0: return
        ocf.FitMCMC(mc['n'],mc['burn'],mc['binn'],db=f)
    else: ocf.FitMCMC(mc['n'],mc['burn'],mc['binn'])

    #make some buttons available
    bPlot.config(state=tk.NORMAL)
    bPlotR.config(state=tk.NORMAL)
    bSaveM.config(state=tk.NORMAL)
    bSaveR.config(state=tk.NORMAL)
    bSum.config(state=tk.NORMAL)
    bSaveAll.config(state=tk.NORMAL)

def infoMC():
    #posterior info about MC/GA/DE fitting
    tkinter.messagebox.showerror('Info MCMC/GA/DE','Not implemented, yet!')
    return

def corrErr():
    #correction of errors level - sometimes useful before MCMC
    tkinter.messagebox.showerror('Correct Errors','Not implemented, yet!')
    return

def fitParams():
    #setting parameters of GA and MC fitting
    global ga,mc,save

    def ok():
        #save values
        global ga,mc,save

        save=saveChVar.get()

        ga['gen']=int(genVar.get())
        ga['size']=int(sizeVar.get())

        mc['n']=float(nVar.get())
        mc['burn']=float(burnVar.get())
        mc['binn']=float(binnVar.get())

        tFitPar.destroy()

        #make some buttons available
        bRunBG.config(state=tk.NORMAL)
        bFitGA.config(state=tk.NORMAL)
        bFitMC.config(state=tk.NORMAL)


    #create new window
    tFitPar=tk.Toplevel(master)
    #default scale of window - NOT change this values if you want to change size
    twidth=288
    theight=316
    if fixed:
        tFitPar.geometry(str(twidth)+'x'+str(theight))   #modif. this line to change size - e.g. master.geometry('400x500')
    else:
        #set relatively to screen size
        tFitPar.geometry('{}x{}'.format(int(twidth/mwidth*screenwidth), int(theight/mheight*screenheight)))
    tFitPar.title('Parameters of Fitting')

    #variables
    saveChVar=tk.IntVar(tFitPar)
    genVar=tk.StringVar(tFitPar,value='100')
    sizeVar=tk.StringVar(tFitPar,value='100')
    nVar=tk.StringVar(tFitPar,value='1000')
    burnVar=tk.StringVar(tFitPar,value='0')
    binnVar=tk.StringVar(tFitPar,value='1')

    #button process file
    bOK=tk.Button(tFitPar)
    bOK.place(relx=0.35,rely=0.88,relheight=b1height/theight,relwidth=b3width/twidth)
    bOK.configure(command=ok)
    bOK.configure(text='OK')

    #label
    Label1=tk.Label(tFitPar)
    Label1.place(relx=0.07,rely=0.79,relheight=l2height/theight,relwidth=0.4)
    Label1.configure(text='Save fitting to file')
    Label1.configure(anchor=tk.W)
    Label1.configure(font=('None',9))

    #check - save fitting sample to file
    saveCh=tk.Checkbutton(tFitPar)
    saveCh.place(relx=0.5,rely=0.78,relheight=0.06,relwidth=0.09)
    saveCh.configure(justify=tk.LEFT)
    saveCh.configure(variable=saveChVar)

    #frame for GA
    Labelframe1=tk.LabelFrame(tFitPar)
    f1height=95
    f1width=250
    Labelframe1.place(relx=0.07,rely=0.03,relheight=f1height/theight,relwidth=f1width/twidth)
    Labelframe1.configure(relief=tk.GROOVE)
    Labelframe1.configure(text='FitGA')
    Labelframe1.configure(width=250)

    #labels
    Label2=tk.Label(Labelframe1)
    Label2.place(relx=0.08,rely=0.26,relheight=l2height/f1height,relwidth=0.3)
    Label2.configure(text='generation')
    Label2.configure(anchor=tk.W)
    Label2.configure(font=('None',9))

    Label3=tk.Label(Labelframe1)
    Label3.place(relx=0.08,rely=0.61,relheight=l2height/f1height,relwidth=0.3)
    Label3.configure(text='size')
    Label3.configure(anchor=tk.W)
    Label3.configure(font=('None',9))

    #input - number of generations
    gen=tk.Entry(Labelframe1)
    gen.place(relx=0.4,rely=0.17,relheight=iheight/f1height,relwidth=0.56)
    gen.configure(textvariable=genVar)

    #input - size of generation
    size=tk.Entry(Labelframe1)
    size.place(relx=0.4,rely=0.53,relheight=iheight/f1height,relwidth=0.56)
    size.configure(textvariable=sizeVar)

    #frame for MC
    Labelframe2=tk.LabelFrame(tFitPar)
    f2height=127
    f2width=250
    Labelframe2.place(relx=0.07,rely=0.35,relheight=f2height/theight,relwidth=f2width/twidth)
    Labelframe2.configure(relief=tk.GROOVE)
    Labelframe2.configure(text='FitMCMC')
    Labelframe2.configure(width=250)

    #labels
    Label4=tk.Label(Labelframe2)
    Label4.place(relx=0.08,rely=0.16,relheight=l2height/f2height,relwidth=0.3)
    Label4.configure(text='n_iter')
    Label4.configure(anchor=tk.W)
    Label4.configure(font=('None',9))

    Label5=tk.Label(Labelframe2)
    Label5.place(relx=0.08,rely=0.43,relheight=l2height/f2height,relwidth=0.3)
    Label5.configure(text='burn')
    Label5.configure(anchor=tk.W)
    Label5.configure(font=('None',9))

    Label6=tk.Label(Labelframe2)
    Label6.place(relx=0.08,rely=0.69,relheight=l2height/f2height,relwidth=0.3)
    Label6.configure(text='binn')
    Label6.configure(anchor=tk.W)
    Label6.configure(font=('None',9))

    #input - number of MC steps
    n=tk.Entry(Labelframe2)
    n.place(relx=0.4,rely=0.1,relheight=iheight/f2height,relwidth=0.56)
    n.configure(textvariable=nVar)

    #input - number of removed steps
    burn=tk.Entry(Labelframe2)
    burn.place(relx=0.4,rely=0.36,relheight=iheight/f2height,relwidth=0.56)
    burn.configure(textvariable=burnVar)

    #input - binning size
    binn=tk.Entry(Labelframe2)
    binn.place(relx=0.4,rely=0.63,relheight=iheight/f2height,relwidth=0.56)
    binn.configure(textvariable=binnVar)


def params():
    #setting model parameters
    def ok():
        #save parameters of model
        result=tkinter.messagebox.askquestion('Saving parameters','It is necessary to set values of all fixed parameters and limits\
         and steps of all fitted parameters. Do you want to continue?',icon='warning',parent=tParams)
        if result=='no': return

        #save model
        model=modelVar.get()
        ocf.model=model

        #clear vars with model params
        ocf.fit_params=[]
        ocf.params={}
        ocf.steps={}
        ocf.limits={}

        if 'LiTE' in model:
            #models with LiTE (LiTE3, LiTE34, LiTE3Quad, LiTE34Quad)

            #checking if params will be fitted
            if a3Fit.get()==1: ocf.fit_params.append('a_sin_i3')
            if e3Fit.get()==1: ocf.fit_params.append('e3')
            if w3Fit.get()==1: ocf.fit_params.append('w3')
            if t3Fit.get()==1: ocf.fit_params.append('t03')
            if P3Fit.get()==1: ocf.fit_params.append('P3')

            #get values of params
            if len(a3Val.get())>0: ocf.params['a_sin_i3']=float(a3Val.get())
            if len(e3Val.get())>0: ocf.params['e3']=float(e3Val.get())
            if len(w3Val.get())>0: ocf.params['w3']=float(w3Val.get())
            if len(t3Val.get())>0: ocf.params['t03']=float(t3Val.get())
            if len(P3Val.get())>0: ocf.params['P3']=float(P3Val.get())

            #get params steps
            if len(a3Step.get())>0: ocf.steps['a_sin_i3']=float(a3Step.get())
            if len(e3Step.get())>0: ocf.steps['e3']=float(e3Step.get())
            if len(w3Step.get())>0: ocf.steps['w3']=float(w3Step.get())
            if len(t3Step.get())>0: ocf.steps['t03']=float(t3Step.get())
            if len(P3Step.get())>0: ocf.steps['P3']=float(P3Step.get())

            #get limits for params
            if len(a3Min.get())*len(a3Max.get())>0: ocf.limits['a_sin_i3']=[float(a3Min.get()),float(a3Max.get())]
            if len(e3Min.get())*len(e3Max.get())>0: ocf.limits['e3']=[float(e3Min.get()),float(e3Max.get())]
            if len(w3Min.get())*len(w3Max.get())>0: ocf.limits['w3']=[float(w3Min.get()),float(w3Max.get())]
            if len(t3Min.get())*len(t3Max.get())>0: ocf.limits['t03']=[float(t3Min.get()),float(t3Max.get())]
            if len(P3Min.get())*len(P3Max.get())>0: ocf.limits['P3']=[float(P3Min.get()),float(P3Max.get())]

            if 'Quad' in model:
                #LiTE3Quad and LiTE34Quad models

                #checking if params will be fitted
                if t0Fit.get()==1: ocf.fit_params.append('t0')
                if PFit.get()==1: ocf.fit_params.append('P')
                if QFit.get()==1: ocf.fit_params.append('Q')

                #get values of params
                if len(t0Val.get())>0: ocf.params['t0']=float(t0Val.get())
                if len(PVal.get())>0: ocf.params['P']=float(PVal.get())
                if len(QVal.get())>0: ocf.params['Q']=float(QVal.get())

                #get params steps
                if len(t0Step.get())>0: ocf.steps['t0']=float(t0Step.get())
                if len(PStep.get())>0: ocf.steps['P']=float(PStep.get())
                if len(QStep.get())>0: ocf.steps['Q']=float(QStep.get())

                #get limits for params
                if len(t0Min.get())*len(t0Max.get())>0: ocf.limits['t0']=[float(t0Min.get()),float(t0Max.get())]
                if len(PMin.get())*len(PMax.get())>0: ocf.limits['P']=[float(PMin.get()),float(PMax.get())]
                if len(QMin.get())*len(QMax.get())>0: ocf.limits['Q']=[float(QMin.get()),float(QMax.get())]

            if '4' in model:
                #LiTE34 and LiTE34Quad models

                #checking if params will be fitted
                if a4Fit.get()==1: ocf.fit_params.append('a_sin_i4')
                if e4Fit.get()==1: ocf.fit_params.append('e4')
                if w4Fit.get()==1: ocf.fit_params.append('w4')
                if t4Fit.get()==1: ocf.fit_params.append('t04')
                if P4Fit.get()==1: ocf.fit_params.append('P4')

                #get values of params
                if len(a4Val.get())>0: ocf.params['a_sin_i4']=float(a4Val.get())
                if len(e4Val.get())>0: ocf.params['e4']=float(e4Val.get())
                if len(w4Val.get())>0: ocf.params['w4']=float(w4Val.get())
                if len(t4Val.get())>0: ocf.params['t04']=float(t4Val.get())
                if len(P4Val.get())>0: ocf.params['P4']=float(P4Val.get())

                #get params steps
                if len(a4Step.get())>0: ocf.steps['a_sin_i4']=float(a4Step.get())
                if len(e4Step.get())>0: ocf.steps['e4']=float(e4Step.get())
                if len(w4Step.get())>0: ocf.steps['w4']=float(w4Step.get())
                if len(t4Step.get())>0: ocf.steps['t04']=float(t4Step.get())
                if len(P4Step.get())>0: ocf.steps['P4']=float(P4Step.get())

                #get limits for params
                if len(a4Min.get())*len(a4Max.get())>0: ocf.limits['a_sin_i4']=[float(a4Min.get()),float(a4Max.get())]
                if len(e4Min.get())*len(e4Max.get())>0: ocf.limits['e4']=[float(e4Min.get()),float(e4Max.get())]
                if len(w4Min.get())*len(w4Max.get())>0: ocf.limits['w4']=[float(w4Min.get()),float(w4Max.get())]
                if len(t4Min.get())*len(t4Max.get())>0: ocf.limits['t04']=[float(t4Min.get()),float(t4Max.get())]
                if len(P4Min.get())*len(P4Max.get())>0: ocf.limits['P4']=[float(P4Min.get()),float(P4Max.get())]

        if 'AgolIn' in model:
            #models based on Agol et al. (2005, their eq. (12)) - AgolInPlanet, AgolInPlanetLin

            #checking if params will be fitted
            if PFit.get()==1: ocf.fit_params.append('P')
            if aFit.get()==1: ocf.fit_params.append('a')
            if wFit.get()==1: ocf.fit_params.append('w')
            if eFit.get()==1: ocf.fit_params.append('e')
            if mu3Fit.get()==1: ocf.fit_params.append('mu3')
            if r3Fit.get()==1: ocf.fit_params.append('r3')
            if w3Fit.get()==1: ocf.fit_params.append('w3')
            if t3Fit.get()==1: ocf.fit_params.append('t03')
            if P3Fit.get()==1: ocf.fit_params.append('P3')

            #get values of params
            if len(PVal.get())>0: ocf.params['P']=float(PVal.get())
            if len(aVal.get())>0: ocf.params['a']=float(aVal.get())
            if len(wVal.get())>0: ocf.params['w']=float(wVal.get())
            if len(eVal.get())>0: ocf.params['e']=float(eVal.get())
            if len(mu3Val.get())>0: ocf.params['mu3']=float(mu3Val.get())
            if len(r3Val.get())>0: ocf.params['r3']=float(r3Val.get())
            if len(w3Val.get())>0: ocf.params['w3']=float(w3Val.get())
            if len(t3Val.get())>0: ocf.params['t03']=float(t3Val.get())
            if len(P3Val.get())>0: ocf.params['P3']=float(P3Val.get())

            #get params steps
            if len(PStep.get())>0: ocf.steps['P']=float(PStep.get())
            if len(aStep.get())>0: ocf.steps['a']=float(aStep.get())
            if len(wStep.get())>0: ocf.steps['w']=float(wStep.get())
            if len(eStep.get())>0: ocf.steps['e']=float(eStep.get())
            if len(mu3Step.get())>0: ocf.steps['mu3']=float(mu3Step.get())
            if len(r3Step.get())>0: ocf.steps['r3']=float(r3Step.get())
            if len(w3Step.get())>0: ocf.steps['w3']=float(w3Step.get())
            if len(t3Step.get())>0: ocf.steps['t03']=float(t3Step.get())
            if len(P3Step.get())>0: ocf.steps['P3']=float(P3Step.get())

            #get limits for params
            if len(PMin.get())*len(PMax.get())>0: ocf.limits['P']=[float(PMin.get()),float(PMax.get())]
            if len(aMin.get())*len(aMax.get())>0: ocf.limits['a']=[float(aMin.get()),float(aMax.get())]
            if len(wMin.get())*len(wMax.get())>0: ocf.limits['w']=[float(wMin.get()),float(wMax.get())]
            if len(eMin.get())*len(eMax.get())>0: ocf.limits['e']=[float(eMin.get()),float(eMax.get())]
            if len(mu3Min.get())*len(mu3Max.get())>0: ocf.limits['mu3']=[float(mu3Min.get()),float(mu3Max.get())]
            if len(r3Min.get())*len(r3Max.get())>0: ocf.limits['r3']=[float(r3Min.get()),float(r3Max.get())]
            if len(w3Min.get())*len(w3Max.get())>0: ocf.limits['w3']=[float(w3Min.get()),float(w3Max.get())]
            if len(t3Min.get())*len(t3Max.get())>0: ocf.limits['t03']=[float(t3Min.get()),float(t3Max.get())]
            if len(P3Min.get())*len(P3Max.get())>0: ocf.limits['P3']=[float(P3Min.get()),float(P3Max.get())]

            if 'Lin' in model:
                #model AgolInPlanetLin
                if t0Fit.get()==1: ocf.fit_params.append('t0')
                if len(t0Val.get())>0: ocf.params['t0']=float(t0Val.get())
                if len(t0Step.get())>0: ocf.steps['t0']=float(t0Step.get())
                if len(t0Min.get())*len(t0Max.get())>0: ocf.limits['t0']=[float(t0Min.get()),float(t0Max.get())]


        if 'AgolEx' in model:
            #models based on Agol et al. (2005, their eq. (25)) - AgolExPlanet, AgolExPlanetLin

            #checking if params will be fitted
            if PFit.get()==1: ocf.fit_params.append('P')
            if mu3Fit.get()==1: ocf.fit_params.append('mu3')
            if e3Fit.get()==1: ocf.fit_params.append('e3')
            if t3Fit.get()==1: ocf.fit_params.append('t03')
            if P3Fit.get()==1: ocf.fit_params.append('P3')

            #get values of params
            if len(PVal.get())>0: ocf.params['P']=float(PVal.get())
            if len(mu3Val.get())>0: ocf.params['mu3']=float(mu3Val.get())
            if len(e3Val.get())>0: ocf.params['e3']=float(e3Val.get())
            if len(t3Val.get())>0: ocf.params['t03']=float(t3Val.get())
            if len(P3Val.get())>0: ocf.params['P3']=float(P3Val.get())

            #get params steps
            if len(PStep.get())>0: ocf.steps['P']=float(PStep.get())
            if len(mu3Step.get())>0: ocf.steps['mu3']=float(mu3Step.get())
            if len(e3Step.get())>0: ocf.steps['e3']=float(e3Step.get())
            if len(t3Step.get())>0: ocf.steps['t03']=float(t3Step.get())
            if len(P3Step.get())>0: ocf.steps['P3']=float(P3Step.get())

            #get limits for params
            if len(PMin.get())*len(PMax.get())>0: ocf.limits['P']=[float(PMin.get()),float(PMax.get())]
            if len(mu3Min.get())*len(mu3Max.get())>0: ocf.limits['mu3']=[float(mu3Min.get()),float(mu3Max.get())]
            if len(e3Min.get())*len(e3Max.get())>0: ocf.limits['e3']=[float(e3Min.get()),float(e3Max.get())]
            if len(t3Min.get())*len(t3Max.get())>0: ocf.limits['t03']=[float(t3Min.get()),float(t3Max.get())]
            if len(P3Min.get())*len(P3Max.get())>0: ocf.limits['P3']=[float(P3Min.get()),float(P3Max.get())]

            if 'Lin' in model:
                #model AgolExPlanetLin
                if t0Fit.get()==1: ocf.fit_params.append('t0')
                if len(t0Val.get())>0: ocf.params['t0']=float(t0Val.get())
                if len(t0Step.get())>0: ocf.steps['t0']=float(t0Step.get())
                if len(t0Min.get())*len(t0Max.get())>0: ocf.limits['t0']=[float(t0Min.get()),float(t0Max.get())]

        elif 'Apsid' in model:
            #model of apsidal motion (Apsidal)

            #checking if params will be fitted
            if t0Fit.get()==1: ocf.fit_params.append('t0')
            if PFit.get()==1: ocf.fit_params.append('P')
            if w0Fit.get()==1: ocf.fit_params.append('w0')
            if dwFit.get()==1: ocf.fit_params.append('dw')
            if eFit.get()==1: ocf.fit_params.append('e')

            #get values of params
            if len(t0Val.get())>0: ocf.params['t0']=float(t0Val.get())
            if len(PVal.get())>0: ocf.params['P']=float(PVal.get())
            if len(w0Val.get())>0: ocf.params['w0']=float(w0Val.get())
            if len(dwVal.get())>0: ocf.params['dw']=float(dwVal.get())
            if len(eVal.get())>0: ocf.params['e']=float(eVal.get())

            #get params steps
            if len(t0Step.get())>0: ocf.steps['t0']=float(t0Step.get())
            if len(PStep.get())>0: ocf.steps['P']=float(PStep.get())
            if len(w0Step.get())>0: ocf.steps['w0']=float(w0Step.get())
            if len(dwStep.get())>0: ocf.steps['dw']=float(dwStep.get())
            if len(eStep.get())>0: ocf.steps['e']=float(eStep.get())

            #get limits for params
            if len(t0Min.get())*len(t0Max.get())>0: ocf.limits['t0']=[float(t0Min.get()),float(t0Max.get())]
            if len(PMin.get())*len(PMax.get())>0: ocf.limits['P']=[float(PMin.get()),float(PMax.get())]
            if len(w0Min.get())*len(w0Max.get())>0: ocf.limits['w0']=[float(w0Min.get()),float(w0Max.get())]
            if len(dwMin.get())*len(dwMax.get())>0: ocf.limits['dw']=[float(dwMin.get()),float(dwMax.get())]
            if len(eMin.get())*len(eMax.get())>0: ocf.limits['e']=[float(eMin.get()),float(eMax.get())]

        #close window
        tParams.destroy()
        bFitParams.config(state=tk.NORMAL)

    def change(event=None):
        #changing selected model
        model=modelVar.get()

        #make inputbox (un)available according to selected model
        if 'LiTE' in model:
            #models with LiTE (LiTE3, LiTE34, LiTE3Quad, LiTE34Quad)
            tNTB.select(0)
            if 'Quad' in model:
                #models LiTE3Quad, LiTE34Quad
                for i in range(5):
                    t0[i].config(state=tk.NORMAL)
                    P[i].config(state=tk.NORMAL)
                    Q[i].config(state=tk.NORMAL)
            else:
                #models LiTE3, LiTE34
                for i in range(5):
                    t0[i].config(state=tk.DISABLED)
                    P[i].config(state=tk.DISABLED)
                    Q[i].config(state=tk.DISABLED)
            if '4' in model:
                #models LiTE34, LiTE34Quad
                for i in range(5):
                    a4[i].config(state=tk.NORMAL)
                    e4[i].config(state=tk.NORMAL)
                    w4[i].config(state=tk.NORMAL)
                    t4[i].config(state=tk.NORMAL)
                    P4[i].config(state=tk.NORMAL)
            else:
                #models LiTE3, LiTE3Quad
                for i in range(5):
                    a4[i].config(state=tk.DISABLED)
                    e4[i].config(state=tk.DISABLED)
                    w4[i].config(state=tk.DISABLED)
                    t4[i].config(state=tk.DISABLED)
                    P4[i].config(state=tk.DISABLED)
        elif 'AgolIn' in model:
            #models based on Agol et al. (2005, their eq. (12)) - AgolInPlanet, AgolInPlanetLin
            tNTB.select(1)
            if 'Lin' in model:
                for i in range(5):
                    t0I[i].config(state=tk.NORMAL)
            else:
                for i in range(5):
                    t0I[i].config(state=tk.DISABLED)
        elif 'AgolEx' in model:
            #models based on Agol et al. (2005, their eq. (25)) - AgolExPlanet, AgolExPlanetLin
            tNTB.select(2)
            if 'Lin' in model:
                for i in range(5):
                    t0E[i].config(state=tk.NORMAL)
            else:
                for i in range(5):
                    t0E[i].config(state=tk.DISABLED)
        elif 'Apsid' in model:
            #model of apsidal motion (Apsidal)
            tNTB.select(3)


    def init_vars():
        #initialization of model parameters values from class
        modelVar.set(ocf.model)   #set model
        change()

        #linear ephemeris
        if len(t0Var.get())>0: t0Val.set(t0Var.get())
        if len(pVar.get())>0: PVal.set(pVar.get())

        #setting selectbox for fitted params
        if 't0' in ocf.fit_params: t0Fit.set(1)
        if 'P' in ocf.fit_params: PFit.set(1)
        if 'Q' in ocf.fit_params: QFit.set(1)

        if 'a_sin_i3' in ocf.fit_params: a3Fit.set(1)
        if 'e3' in ocf.fit_params: e3Fit.set(1)
        if 'w3' in ocf.fit_params: w3Fit.set(1)
        if 't03' in ocf.fit_params: t3Fit.set(1)
        if 'P3' in ocf.fit_params: P3Fit.set(1)

        if 'a_sin_i4' in ocf.fit_params: a4Fit.set(1)
        if 'e4' in ocf.fit_params: e4Fit.set(1)
        if 'w4' in ocf.fit_params: w4Fit.set(1)
        if 't04' in ocf.fit_params: t4Fit.set(1)
        if 'P4' in ocf.fit_params: P4Fit.set(1)

        if 'a' in ocf.fit_params: aFit.set(1)
        if 'w' in ocf.fit_params: wFit.set(1)
        if 'e' in ocf.fit_params: eFit.set(1)
        if 'mu3' in ocf.fit_params: mu3Fit.set(1)
        if 'r3' in ocf.fit_params: r3Fit.set(1)

        if 'w0' in ocf.fit_params: w0Fit.set(1)
        if 'dw' in ocf.fit_params: dwFit.set(1)

        #setting valus of params
        if 't0' in ocf.params: t0Val.set(str(ocf.params['t0']))
        if 'P' in ocf.params: PVal.set(str(ocf.params['P']))
        if 'Q' in ocf.params: QVal.set(str(ocf.params['Q']))

        if 'a_sin_i3' in ocf.params: a3Val.set(str(ocf.params['a_sin_i3']))
        if 'e3' in ocf.params: e3Val.set(str(ocf.params['e3']))
        if 'w3' in ocf.params: w3Val.set(str(ocf.params['w3']))
        if 't03' in ocf.params: t3Val.set(str(ocf.params['t03']))
        if 'P3' in ocf.params: P3Val.set(str(ocf.params['P3']))

        if 'a_sin_i4' in ocf.params: a4Val.set(str(ocf.params['a_sin_i4']))
        if 'e4' in ocf.params: e4Val.set(str(ocf.params['e4']))
        if 'w4' in ocf.params: w4Val.set(str(ocf.params['w4']))
        if 't04' in ocf.params: t4Val.set(str(ocf.params['t04']))
        if 'P4' in ocf.params: P4Val.set(str(ocf.params['P4']))

        if 'a' in ocf.params: aVal.set(str(ocf.params['a']))
        if 'w' in ocf.params: wVal.set(str(ocf.params['w']))
        if 'e' in ocf.params: eVal.set(str(ocf.params['e']))
        if 'mu3' in ocf.params: mu3Val.set(str(ocf.params['mu3']))
        if 'r3' in ocf.params: r3Val.set(str(ocf.params['r3']))

        if 'w0' in ocf.params: w0Val.set(str(ocf.params['w0']))
        if 'dw' in ocf.params: dwVal.set(str(ocf.params['dw']))

        #setting steps for params
        if 't0' in ocf.steps: t0Step.set(str(ocf.steps['t0']))
        if 'P' in ocf.steps: PStep.set(str(ocf.steps['P']))
        if 'Q' in ocf.steps: QStep.set(str(ocf.steps['Q']))

        if 'a_sin_i3' in ocf.steps: a3Step.set(str(ocf.steps['a_sin_i3']))
        if 'e3' in ocf.steps: e3Step.set(str(ocf.steps['e3']))
        if 'w3' in ocf.steps: w3Step.set(str(ocf.steps['w3']))
        if 't03' in ocf.steps: t3Step.set(str(ocf.steps['t03']))
        if 'P3' in ocf.steps: P3Step.set(str(ocf.steps['P3']))

        if 'a_sin_i4' in ocf.steps: a4Step.set(str(ocf.steps['a_sin_i4']))
        if 'e4' in ocf.steps: e4Step.set(str(ocf.steps['e4']))
        if 'w4' in ocf.steps: w4Step.set(str(ocf.steps['w4']))
        if 't04' in ocf.steps: t4Step.set(str(ocf.steps['t04']))
        if 'P4' in ocf.steps: P4Step.set(str(ocf.steps['P4']))

        if 'a' in ocf.steps: aStep.set(str(ocf.steps['a']))
        if 'w' in ocf.steps: wStep.set(str(ocf.steps['w']))
        if 'e' in ocf.steps: eStep.set(str(ocf.steps['e']))
        if 'mu3' in ocf.steps: mu3Step.set(str(ocf.steps['mu3']))
        if 'r3' in ocf.steps: r3Step.set(str(ocf.steps['r3']))

        if 'w0' in ocf.steps: w0Step.set(str(ocf.steps['w0']))
        if 'dw' in ocf.steps: dwStep.set(str(ocf.steps['dw']))

        #setting lower bound of params
        if 't0' in ocf.limits: t0Min.set(str(ocf.limits['t0'][0]))
        if 'P' in ocf.limits: PMin.set(str(ocf.limits['P'][0]))
        if 'Q' in ocf.limits: QMin.set(str(ocf.limits['Q'][0]))

        if 'a_sin_i3' in ocf.limits: a3Min.set(str(ocf.limits['a_sin_i3'][0]))
        if 'e3' in ocf.limits: e3Min.set(str(ocf.limits['e3'][0]))
        if 'w3' in ocf.limits: w3Min.set(str(ocf.limits['w3'][0]))
        if 't03' in ocf.limits: t3Min.set(str(ocf.limits['t03'][0]))
        if 'P3' in ocf.limits: P3Min.set(str(ocf.limits['P3'][0]))

        if 'a_sin_i4' in ocf.limits: a4Min.set(str(ocf.limits['a_sin_i4'][0]))
        if 'e4' in ocf.limits: e4Min.set(str(ocf.limits['e4'][0]))
        if 'w4' in ocf.limits: w4Min.set(str(ocf.limits['w4'][0]))
        if 't04' in ocf.limits: t4Min.set(str(ocf.limits['t04'][0]))
        if 'P4' in ocf.limits: P4Min.set(str(ocf.limits['P4'][0]))

        if 'a' in ocf.limits: aMin.set(str(ocf.limits['a'][0]))
        if 'w' in ocf.limits: wMin.set(str(ocf.limits['w'][0]))
        if 'e' in ocf.limits: eMin.set(str(ocf.limits['e'][0]))
        if 'mu3' in ocf.limits: mu3Min.set(str(ocf.limits['mu3'][0]))
        if 'r3' in ocf.limits: r3Min.set(str(ocf.limits['r3'][0]))

        if 'w0' in ocf.limits: w0Min.set(str(ocf.limits['w0'][0]))
        if 'dw' in ocf.limits: dwMin.set(str(ocf.limits['dw'][0]))

        #setting upper bound of params
        if 't0' in ocf.limits: t0Max.set(str(ocf.limits['t0'][1]))
        if 'P' in ocf.limits: PMax.set(str(ocf.limits['P'][1]))
        if 'Q' in ocf.limits: QMax.set(str(ocf.limits['Q'][1]))

        if 'a_sin_i3' in ocf.limits: a3Max.set(str(ocf.limits['a_sin_i3'][1]))
        if 'e3' in ocf.limits: e3Max.set(str(ocf.limits['e3'][1]))
        if 'w3' in ocf.limits: w3Max.set(str(ocf.limits['w3'][1]))
        if 't03' in ocf.limits: t3Max.set(str(ocf.limits['t03'][1]))
        if 'P3' in ocf.limits: P3Max.set(str(ocf.limits['P3'][1]))

        if 'a_sin_i4' in ocf.limits: a4Max.set(str(ocf.limits['a_sin_i4'][1]))
        if 'e4' in ocf.limits: e4Max.set(str(ocf.limits['e4'][1]))
        if 'w4' in ocf.limits: w4Max.set(str(ocf.limits['w4'][1]))
        if 't04' in ocf.limits: t4Max.set(str(ocf.limits['t04'][1]))
        if 'P4' in ocf.limits: P4Max.set(str(ocf.limits['P4'][1]))

        if 'a' in ocf.limits: aMax.set(str(ocf.limits['a'][1]))
        if 'w' in ocf.limits: wMax.set(str(ocf.limits['w'][1]))
        if 'e' in ocf.limits: eMax.set(str(ocf.limits['e'][1]))
        if 'mu3' in ocf.limits: mu3Max.set(str(ocf.limits['mu3'][1]))
        if 'r3' in ocf.limits: r3Max.set(str(ocf.limits['r3'][1]))

        if 'w0' in ocf.limits: w0Max.set(str(ocf.limits['w0'][1]))
        if 'dw' in ocf.limits: dwMax.set(str(ocf.limits['dw'][1]))

    #create new window
    tParams=tk.Toplevel(master)
    #default scale of window - NOT change this values if you want to change size
    twidth=595
    theight=500
    if fixed:
        tParams.geometry(str(twidth)+'x'+str(theight))   #modif. this line to change size - e.g. master.geometry('400x500')
    else:
        #set relatively to screen size
        tParams.geometry('{}x{}'.format(int(twidth/mwidth*screenwidth), int(theight/mheight*screenheight)))
    tParams.title('Model Parameters')

    #model
    modelVar=tk.StringVar(tParams)

    #vars for t0
    t0Val=tk.StringVar(tParams)
    t0Min=tk.StringVar(tParams)
    t0Max=tk.StringVar(tParams)
    t0Step=tk.StringVar(tParams,value='0.001')
    t0Fit=tk.IntVar(tParams)

    #vars for P
    PVal=tk.StringVar(tParams)
    PMin=tk.StringVar(tParams)
    PMax=tk.StringVar(tParams)
    PStep=tk.StringVar(tParams,value='0.0001')
    PFit=tk.IntVar(tParams)

    #vars for Q
    QVal=tk.StringVar(tParams)
    QMin=tk.StringVar(tParams,value='-1e-11')
    QMax=tk.StringVar(tParams,value='1e-11')
    QStep=tk.StringVar(tParams,value='1e-13')
    QFit=tk.IntVar(tParams)

    #vars for other params values
    #LiTE models
    a3Val=tk.StringVar(tParams)
    e3Val=tk.StringVar(tParams)
    w3Val=tk.StringVar(tParams)
    t3Val=tk.StringVar(tParams)
    P3Val=tk.StringVar(tParams)
    a4Val=tk.StringVar(tParams)
    e4Val=tk.StringVar(tParams)
    w4Val=tk.StringVar(tParams)
    t4Val=tk.StringVar(tParams)
    P4Val=tk.StringVar(tParams)

    #+apsidal motion
    w0Val=tk.StringVar(tParams)
    dwVal=tk.StringVar(tParams)
    eVal=tk.StringVar(tParams)

    #+Agol models
    aVal=tk.StringVar(tParams)
    wVal=tk.StringVar(tParams)
    mu3Val=tk.StringVar(tParams)
    r3Val=tk.StringVar(tParams)

    #vars for steps of other params
    #LiTE models
    a3Step=tk.StringVar(tParams,value='0.01')
    e3Step=tk.StringVar(tParams,value='0.01')
    w3Step=tk.StringVar(tParams,value='0.01')
    t3Step=tk.StringVar(tParams,value='10')
    P3Step=tk.StringVar(tParams,value='10')
    a4Step=tk.StringVar(tParams,value='0.01')
    e4Step=tk.StringVar(tParams,value='0.01')
    w4Step=tk.StringVar(tParams,value='0.01')
    t4Step=tk.StringVar(tParams,value='10')
    P4Step=tk.StringVar(tParams,value='10')

    #+apsidal motion
    w0Step=tk.StringVar(tParams,value='0.01')
    dwStep=tk.StringVar(tParams,value='1e-5')
    eStep=tk.StringVar(tParams,value='0.01')

    #+Agol models
    aStep=tk.StringVar(tParams,value='0.01')
    wStep=tk.StringVar(tParams,value='0.01')
    mu3Step=tk.StringVar(tParams)
    r3Step=tk.StringVar(tParams,value='0.01')

    #vars for lower bound of other params
    #LiTE models
    a3Min=tk.StringVar(tParams)
    e3Min=tk.StringVar(tParams,value='0')
    w3Min=tk.StringVar(tParams,value='0')
    t3Min=tk.StringVar(tParams)
    P3Min=tk.StringVar(tParams)
    a4Min=tk.StringVar(tParams)
    e4Min=tk.StringVar(tParams,value='0')
    w4Min=tk.StringVar(tParams,value='0')
    t4Min=tk.StringVar(tParams)
    P4Min=tk.StringVar(tParams)

    #+apsidal motion
    w0Min=tk.StringVar(tParams,value='0')
    dwMin=tk.StringVar(tParams)
    eMin=tk.StringVar(tParams,value='0')

    #+Agol models
    aMin=tk.StringVar(tParams)
    wMin=tk.StringVar(tParams,value='0')
    mu3Min=tk.StringVar(tParams)
    r3Min=tk.StringVar(tParams)

    #vars for upper bound of other params
    #LiTE models
    a3Max=tk.StringVar(tParams)
    e3Max=tk.StringVar(tParams,value='1')
    w3Max=tk.StringVar(tParams,value='6.28')
    t3Max=tk.StringVar(tParams)
    P3Max=tk.StringVar(tParams)
    a4Max=tk.StringVar(tParams)
    e4Max=tk.StringVar(tParams,value='1')
    w4Max=tk.StringVar(tParams,value='6.28')
    t4Max=tk.StringVar(tParams)
    P4Max=tk.StringVar(tParams)

    #+apsidal motion
    w0Max=tk.StringVar(tParams,value='6.28')
    dwMax=tk.StringVar(tParams)
    eMax=tk.StringVar(tParams,value='1')

    #+Agol models
    aMax=tk.StringVar(tParams)
    wMax=tk.StringVar(tParams,value='6.28')
    mu3Max=tk.StringVar(tParams)
    r3Max=tk.StringVar(tParams)

    #vars for selectbox of fitted params
    #LiTE models
    a3Fit=tk.IntVar(tParams)
    e3Fit=tk.IntVar(tParams)
    w3Fit=tk.IntVar(tParams)
    t3Fit=tk.IntVar(tParams)
    P3Fit=tk.IntVar(tParams)
    a4Fit=tk.IntVar(tParams)
    e4Fit=tk.IntVar(tParams)
    w4Fit=tk.IntVar(tParams)
    t4Fit=tk.IntVar(tParams)
    P4Fit=tk.IntVar(tParams)

    #+apsidal motion
    w0Fit=tk.IntVar(tParams)
    dwFit=tk.IntVar(tParams)
    eFit=tk.IntVar(tParams)

    #+Agol models
    aFit=tk.IntVar(tParams)
    wFit=tk.IntVar(tParams)
    mu3Fit=tk.IntVar(tParams)
    r3Fit=tk.IntVar(tParams)

    #combobox with all available models
    model=tkinter.ttk.Combobox(tParams)
    model.place(relx=0.15,rely=0.02,relheight=0.04,relwidth=0.4)
    model.configure(textvariable=modelVar)
    model.configure(state='readonly')
    model['values']=('LiTE3','LiTE34','LiTE3Quad','LiTE34Quad','AgolInPlanet','AgolInPlanetLin','AgolExPlanet','AgolExPlanetLin','Apsidal')
    model.current(0)
    model.bind('<<ComboboxSelected>>',change)

    #label
    Label1=tk.Label(tParams)
    Label1.place(relx=0.05,rely=0.02,relheight=l2height/theight,relwidth=40/twidth)
    Label1.configure(text='Model')
    Label1.configure(anchor=tk.W)
    Label1.configure(font=('None',9))

    #create notebook with objects for params of all models
    style=tkinter.ttk.Style(tParams)
    style.layout('TNotebook.Tab',[])

    tNTB=tkinter.ttk.Notebook(tParams)
    nheight=430
    nwidth=571
    tNTB.place(relx=0.02,rely=0.07,relheight=nheight/theight,relwidth=nwidth/twidth)

    ##########################################################################################
    #           LiTE                                                                         #
    ##########################################################################################

    fLiTE=tk.Frame(tNTB)
    tNTB.add(fLiTE)

    #labels
    Label15=tk.Label(fLiTE)
    Label15.place(relx=0.02,rely=0.03,relheight=l2height/nheight,relwidth=0.12)
    Label15.configure(text='param.')
    Label15.configure(anchor=tk.W)
    Label15.configure(font=('None',9))

    Label16=tk.Label(fLiTE)
    Label16.place(relx=0.15,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label16.configure(text='value')
    Label16.configure(anchor=tk.W)
    Label16.configure(font=('None',9))

    Label17=tk.Label(fLiTE)
    Label17.place(relx=0.35,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label17.configure(text='min.')
    Label17.configure(anchor=tk.W)
    Label17.configure(font=('None',9))

    Label18=tk.Label(fLiTE)
    Label18.place(relx=0.55,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label18.configure(text='max.')
    Label18.configure(anchor=tk.W)
    Label18.configure(font=('None',9))

    Label19=tk.Label(fLiTE)
    Label19.place(relx=0.75,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label19.configure(text='step')
    Label19.configure(anchor=tk.W)
    Label19.configure(font=('None',9))

    Label20=tk.Label(fLiTE)
    Label20.place(relx=0.95,rely=0.03,relheight=l2height/nheight,relwidth=0.04)
    Label20.configure(text='fit')
    Label20.configure(font=('None',9))

    Label2=tk.Label(fLiTE)
    Label2.place(relx=0.02,rely=0.10,relheight=l2height/nheight,relwidth=0.12)
    Label2.configure(text='t0')
    Label2.configure(anchor=tk.W)
    Label2.configure(font=('None',9))

    Label3=tk.Label(fLiTE)
    Label3.place(relx=0.02,rely=0.17,relheight=l2height/nheight,relwidth=0.12)
    Label3.configure(text='P')
    Label3.configure(anchor=tk.W)
    Label3.configure(font=('None',9))

    Label14=tk.Label(fLiTE)
    Label14.place(relx=0.02,rely=0.24,relheight=l2height/nheight,relwidth=0.12)
    Label14.configure(text='Q')
    Label14.configure(anchor=tk.W)
    Label14.configure(font=('None',9))

    Label4=tk.Label(fLiTE)
    Label4.place(relx=0.02,rely=0.31,relheight=l2height/nheight,relwidth=0.12)
    Label4.configure(text='a_sin_i3')
    Label4.configure(anchor=tk.W)
    Label4.configure(font=('None',9))

    Label5=tk.Label(fLiTE)
    Label5.place(relx=0.02,rely=0.38,relheight=l2height/nheight,relwidth=0.12)
    Label5.configure(text='e3')
    Label5.configure(anchor=tk.W)
    Label5.configure(font=('None',9))

    Label6=tk.Label(fLiTE)
    Label6.place(relx=0.02,rely=0.45,relheight=l2height/nheight,relwidth=0.12)
    Label6.configure(text='w3')
    Label6.configure(anchor=tk.W)
    Label6.configure(font=('None',9))

    Label7=tk.Label(fLiTE)
    Label7.place(relx=0.02,rely=0.52,relheight=l2height/nheight,relwidth=0.12)
    Label7.configure(text='t03')
    Label7.configure(anchor=tk.W)
    Label7.configure(font=('None',9))

    Label8=tk.Label(fLiTE)
    Label8.place(relx=0.02,rely=0.59,relheight=l2height/nheight,relwidth=0.12)
    Label8.configure(text='P3')
    Label8.configure(anchor=tk.W)
    Label8.configure(font=('None',9))

    Label9=tk.Label(fLiTE)
    Label9.place(relx=0.02,rely=0.66,relheight=l2height/nheight,relwidth=0.12)
    Label9.configure(text='a_sin_i4')
    Label9.configure(anchor=tk.W)
    Label9.configure(font=('None',9))

    Label10=tk.Label(fLiTE)
    Label10.place(relx=0.02,rely=0.73,relheight=l2height/nheight,relwidth=0.12)
    Label10.configure(text='e4')
    Label10.configure(anchor=tk.W)
    Label10.configure(font=('None',9))

    Label11=tk.Label(fLiTE)
    Label11.place(relx=0.02,rely=0.80,relheight=l2height/nheight,relwidth=0.12)
    Label11.configure(text='w4')
    Label11.configure(anchor=tk.W)
    Label11.configure(font=('None',9))

    Label12=tk.Label(fLiTE)
    Label12.place(relx=0.02,rely=0.87,relheight=l2height/nheight,relwidth=0.12)
    Label12.configure(text='t04')
    Label12.configure(anchor=tk.W)
    Label12.configure(font=('None',9))

    Label13=tk.Label(fLiTE)
    Label13.place(relx=0.02,rely=0.94,relheight=l2height/nheight,relwidth=0.12)
    Label13.configure(text='P4')
    Label13.configure(anchor=tk.W)
    Label13.configure(font=('None',9))

    #input objects for param t0
    t0=[tk.Entry(fLiTE)]
    t0[-1].place(relx=0.15,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0[-1].configure(textvariable=t0Val)

    t0.append(tk.Entry(fLiTE))
    t0[-1].place(relx=0.35,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0[-1].configure(textvariable=t0Min)

    t0.append(tk.Entry(fLiTE))
    t0[-1].place(relx=0.55,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0[-1].configure(textvariable=t0Max)

    t0.append(tk.Entry(fLiTE))
    t0[-1].place(relx=0.75,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0[-1].configure(textvariable=t0Step)

    t0.append(tk.Checkbutton(fLiTE))
    t0[-1].place(relx=0.95,rely=0.09,relheight=0.06,relwidth=0.04)
    t0[-1].configure(justify=tk.LEFT)
    t0[-1].configure(variable=t0Fit)

    #input objects for param P
    P=[tk.Entry(fLiTE)]
    P[-1].place(relx=0.15,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    P[-1].configure(textvariable=PVal)

    P.append(tk.Entry(fLiTE))
    P[-1].place(relx=0.35,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    P[-1].configure(textvariable=PMin)

    P.append(tk.Entry(fLiTE))
    P[-1].place(relx=0.55,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    P[-1].configure(textvariable=PMax)

    P.append(tk.Entry(fLiTE))
    P[-1].place(relx=0.75,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    P[-1].configure(textvariable=PStep)

    P.append(tk.Checkbutton(fLiTE))
    P[-1].place(relx=0.95,rely=0.16,relheight=0.06,relwidth=0.04)
    P[-1].configure(justify=tk.LEFT)
    P[-1].configure(variable=PFit)

    #input objects for param Q
    Q=[tk.Entry(fLiTE)]
    Q[-1].place(relx=0.15,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    Q[-1].configure(textvariable=QVal)

    Q.append(tk.Entry(fLiTE))
    Q[-1].place(relx=0.35,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    Q[-1].configure(textvariable=QMin)

    Q.append(tk.Entry(fLiTE))
    Q[-1].place(relx=0.55,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    Q[-1].configure(textvariable=QMax)

    Q.append(tk.Entry(fLiTE))
    Q[-1].place(relx=0.75,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    Q[-1].configure(textvariable=QStep)

    Q.append(tk.Checkbutton(fLiTE))
    Q[-1].place(relx=0.95,rely=0.23,relheight=0.06,relwidth=0.04)
    Q[-1].configure(justify=tk.LEFT)
    Q[-1].configure(variable=QFit)

    #input objects for param a_sin_i3
    a3=[tk.Entry(fLiTE)]
    a3[-1].place(relx=0.15,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    a3[-1].configure(textvariable=a3Val)

    a3.append(tk.Entry(fLiTE))
    a3[-1].place(relx=0.35,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    a3[-1].configure(textvariable=a3Min)

    a3.append(tk.Entry(fLiTE))
    a3[-1].place(relx=0.55,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    a3[-1].configure(textvariable=a3Max)

    a3.append(tk.Entry(fLiTE))
    a3[-1].place(relx=0.75,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    a3[-1].configure(textvariable=a3Step)

    a3.append(tk.Checkbutton(fLiTE))
    a3[-1].place(relx=0.95,rely=0.30,relheight=0.06,relwidth=0.04)
    a3[-1].configure(justify=tk.LEFT)
    a3[-1].configure(variable=a3Fit)

    #input objects for param e3
    e3=[tk.Entry(fLiTE)]
    e3[-1].place(relx=0.15,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    e3[-1].configure(textvariable=e3Val)

    e3.append(tk.Entry(fLiTE))
    e3[-1].place(relx=0.35,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    e3[-1].configure(textvariable=e3Min)

    e3.append(tk.Entry(fLiTE))
    e3[-1].place(relx=0.55,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    e3[-1].configure(textvariable=e3Max)

    e3.append(tk.Entry(fLiTE))
    e3[-1].place(relx=0.75,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    e3[-1].configure(textvariable=e3Step)

    e3.append(tk.Checkbutton(fLiTE))
    e3[-1].place(relx=0.95,rely=0.37,relheight=0.06,relwidth=0.04)
    e3[-1].configure(justify=tk.LEFT)
    e3[-1].configure(variable=e3Fit)

    #input objects for param w3
    w3=[tk.Entry(fLiTE)]
    w3[-1].place(relx=0.15,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    w3[-1].configure(textvariable=w3Val)

    w3.append(tk.Entry(fLiTE))
    w3[-1].place(relx=0.35,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    w3[-1].configure(textvariable=w3Min)

    w3.append(tk.Entry(fLiTE))
    w3[-1].place(relx=0.55,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    w3[-1].configure(textvariable=w3Max)

    w3.append(tk.Entry(fLiTE))
    w3[-1].place(relx=0.75,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    w3[-1].configure(textvariable=w3Step)

    w3.append(tk.Checkbutton(fLiTE))
    w3[-1].place(relx=0.95,rely=0.44,relheight=0.06,relwidth=0.04)
    w3[-1].configure(justify=tk.LEFT)
    w3[-1].configure(variable=w3Fit)

    #input objects for param t03
    t3=[tk.Entry(fLiTE)]
    t3[-1].place(relx=0.15,rely=0.51,relheight=iheight/nheight,relwidth=0.19)
    t3[-1].configure(textvariable=t3Val)

    t3.append(tk.Entry(fLiTE))
    t3[-1].place(relx=0.35,rely=0.51,relheight=iheight/nheight,relwidth=0.19)
    t3[-1].configure(textvariable=t3Min)

    t3.append(tk.Entry(fLiTE))
    t3[-1].place(relx=0.55,rely=0.51,relheight=iheight/nheight,relwidth=0.19)
    t3[-1].configure(textvariable=t3Max)

    t3.append(tk.Entry(fLiTE))
    t3[-1].place(relx=0.75,rely=0.51,relheight=iheight/nheight,relwidth=0.19)
    t3[-1].configure(textvariable=t3Step)

    t3.append(tk.Checkbutton(fLiTE))
    t3[-1].place(relx=0.95,rely=0.51,relheight=0.06,relwidth=0.04)
    t3[-1].configure(justify=tk.LEFT)
    t3[-1].configure(variable=t3Fit)

    #input objects for param P
    P3=[tk.Entry(fLiTE)]
    P3[-1].place(relx=0.15,rely=0.58,relheight=iheight/nheight,relwidth=0.19)
    P3[-1].configure(textvariable=P3Val)

    P3.append(tk.Entry(fLiTE))
    P3[-1].place(relx=0.35,rely=0.58,relheight=iheight/nheight,relwidth=0.19)
    P3[-1].configure(textvariable=P3Min)

    P3.append(tk.Entry(fLiTE))
    P3[-1].place(relx=0.55,rely=0.58,relheight=iheight/nheight,relwidth=0.19)
    P3[-1].configure(textvariable=P3Max)

    P3.append(tk.Entry(fLiTE))
    P3[-1].place(relx=0.75,rely=0.58,relheight=iheight/nheight,relwidth=0.19)
    P3[-1].configure(textvariable=P3Step)

    P3.append(tk.Checkbutton(fLiTE))
    P3[-1].place(relx=0.95,rely=0.58,relheight=0.06,relwidth=0.04)
    P3[-1].configure(justify=tk.LEFT)
    P3[-1].configure(variable=P3Fit)

    #input objects for param a_sin_i4
    a4=[tk.Entry(fLiTE)]
    a4[-1].place(relx=0.15,rely=0.65,relheight=iheight/nheight,relwidth=0.19)
    a4[-1].configure(textvariable=a4Val)

    a4.append(tk.Entry(fLiTE))
    a4[-1].place(relx=0.35,rely=0.65,relheight=iheight/nheight,relwidth=0.19)
    a4[-1].configure(textvariable=a4Min)

    a4.append(tk.Entry(fLiTE))
    a4[-1].place(relx=0.55,rely=0.65,relheight=iheight/nheight,relwidth=0.19)
    a4[-1].configure(textvariable=a4Max)

    a4.append(tk.Entry(fLiTE))
    a4[-1].place(relx=0.75,rely=0.65,relheight=iheight/nheight,relwidth=0.19)
    a4[-1].configure(textvariable=a4Step)

    a4.append(tk.Checkbutton(fLiTE))
    a4[-1].place(relx=0.95,rely=0.65,relheight=0.06,relwidth=0.04)
    a4[-1].configure(justify=tk.LEFT)
    a4[-1].configure(variable=a4Fit)

    #input objects for param e4
    e4=[tk.Entry(fLiTE)]
    e4[-1].place(relx=0.15,rely=0.72,relheight=iheight/nheight,relwidth=0.19)
    e4[-1].configure(textvariable=e4Val)

    e4.append(tk.Entry(fLiTE))
    e4[-1].place(relx=0.35,rely=0.72,relheight=iheight/nheight,relwidth=0.19)
    e4[-1].configure(textvariable=e4Min)

    e4.append(tk.Entry(fLiTE))
    e4[-1].place(relx=0.55,rely=0.72,relheight=iheight/nheight,relwidth=0.19)
    e4[-1].configure(textvariable=e4Max)

    e4.append(tk.Entry(fLiTE))
    e4[-1].place(relx=0.75,rely=0.72,relheight=iheight/nheight,relwidth=0.19)
    e4[-1].configure(textvariable=e4Step)

    e4.append(tk.Checkbutton(fLiTE))
    e4[-1].place(relx=0.95,rely=0.72,relheight=0.06,relwidth=0.04)
    e4[-1].configure(justify=tk.LEFT)
    e4[-1].configure(variable=e4Fit)

    #input objects for param w4
    w4=[tk.Entry(fLiTE)]
    w4[-1].place(relx=0.15,rely=0.79,relheight=iheight/nheight,relwidth=0.19)
    w4[-1].configure(textvariable=w4Val)

    w4.append(tk.Entry(fLiTE))
    w4[-1].place(relx=0.35,rely=0.79,relheight=iheight/nheight,relwidth=0.19)
    w4[-1].configure(textvariable=w4Min)

    w4.append(tk.Entry(fLiTE))
    w4[-1].place(relx=0.55,rely=0.79,relheight=iheight/nheight,relwidth=0.19)
    w4[-1].configure(textvariable=w4Max)

    w4.append(tk.Entry(fLiTE))
    w4[-1].place(relx=0.75,rely=0.79,relheight=iheight/nheight,relwidth=0.19)
    w4[-1].configure(textvariable=w4Step)

    w4.append(tk.Checkbutton(fLiTE))
    w4[-1].place(relx=0.95,rely=0.79,relheight=0.06,relwidth=0.04)
    w4[-1].configure(justify=tk.LEFT)
    w4[-1].configure(variable=w4Fit)

    #input objects for param t04
    t4=[tk.Entry(fLiTE)]
    t4[-1].place(relx=0.15,rely=0.86,relheight=iheight/nheight,relwidth=0.19)
    t4[-1].configure(textvariable=t4Val)

    t4.append(tk.Entry(fLiTE))
    t4[-1].place(relx=0.35,rely=0.86,relheight=iheight/nheight,relwidth=0.19)
    t4[-1].configure(textvariable=t4Min)

    t4.append(tk.Entry(fLiTE))
    t4[-1].place(relx=0.55,rely=0.86,relheight=iheight/nheight,relwidth=0.19)
    t4[-1].configure(textvariable=t4Max)

    t4.append(tk.Entry(fLiTE))
    t4[-1].place(relx=0.75,rely=0.86,relheight=iheight/nheight,relwidth=0.19)
    t4[-1].configure(textvariable=t4Step)

    t4.append(tk.Checkbutton(fLiTE))
    t4[-1].place(relx=0.95,rely=0.86,relheight=0.06,relwidth=0.04)
    t4[-1].configure(justify=tk.LEFT)
    t4[-1].configure(variable=t4Fit)

    #input objects for param P4
    P4=[tk.Entry(fLiTE)]
    P4[-1].place(relx=0.15,rely=0.93,relheight=iheight/nheight,relwidth=0.19)
    P4[-1].configure(textvariable=P4Val)

    P4.append(tk.Entry(fLiTE))
    P4[-1].place(relx=0.35,rely=0.93,relheight=iheight/nheight,relwidth=0.19)
    P4[-1].configure(textvariable=P4Min)

    P4.append(tk.Entry(fLiTE))
    P4[-1].place(relx=0.55,rely=0.93,relheight=iheight/nheight,relwidth=0.19)
    P4[-1].configure(textvariable=P4Max)

    P4.append(tk.Entry(fLiTE))
    P4[-1].place(relx=0.75,rely=0.93,relheight=iheight/nheight,relwidth=0.19)
    P4[-1].configure(textvariable=P4Step)

    P4.append(tk.Checkbutton(fLiTE))
    P4[-1].place(relx=0.95,rely=0.93,relheight=0.06,relwidth=0.04)
    P4[-1].configure(justify=tk.LEFT)
    P4[-1].configure(variable=P4Fit)

    ##########################################################################################
    #           AgolInPlanet                                                                 #
    ##########################################################################################

    fIn=tk.Frame(tNTB)
    tNTB.add(fIn)

    #labels
    Label15=tk.Label(fIn)
    Label15.place(relx=0.02,rely=0.03,relheight=l2height/nheight,relwidth=0.12)
    Label15.configure(text='param.')
    Label15.configure(font=('None',9))
    Label15.configure(anchor=tk.W)

    Label16=tk.Label(fIn)
    Label16.place(relx=0.15,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label16.configure(text='value')
    Label16.configure(font=('None',9))
    Label16.configure(anchor=tk.W)

    Label17=tk.Label(fIn)
    Label17.place(relx=0.35,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label17.configure(text='min.')
    Label17.configure(font=('None',9))
    Label17.configure(anchor=tk.W)

    Label18=tk.Label(fIn)
    Label18.place(relx=0.55,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label18.configure(text='max.')
    Label18.configure(font=('None',9))
    Label18.configure(anchor=tk.W)

    Label19=tk.Label(fIn)
    Label19.place(relx=0.75,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label19.configure(text='step')
    Label19.configure(font=('None',9))
    Label19.configure(anchor=tk.W)

    Label20=tk.Label(fIn)
    Label20.place(relx=0.95,rely=0.03,relheight=l2height/nheight,relwidth=0.04)
    Label20.configure(text='fit')
    Label20.configure(font=('None',9))

    Label2=tk.Label(fIn)
    Label2.place(relx=0.02,rely=0.10,relheight=l2height/nheight,relwidth=0.12)
    Label2.configure(text='t0')
    Label2.configure(anchor=tk.W)
    Label2.configure(font=('None',9))

    Label3=tk.Label(fIn)
    Label3.place(relx=0.02,rely=0.17,relheight=l2height/nheight,relwidth=0.12)
    Label3.configure(text='P')
    Label3.configure(anchor=tk.W)
    Label3.configure(font=('None',9))

    Label14=tk.Label(fIn)
    Label14.place(relx=0.02,rely=0.24,relheight=l2height/nheight,relwidth=0.12)
    Label14.configure(text='a')
    Label14.configure(anchor=tk.W)
    Label14.configure(font=('None',9))

    Label4=tk.Label(fIn)
    Label4.place(relx=0.02,rely=0.31,relheight=l2height/nheight,relwidth=0.12)
    Label4.configure(text='w')
    Label4.configure(anchor=tk.W)
    Label4.configure(font=('None',9))

    Label5=tk.Label(fIn)
    Label5.place(relx=0.02,rely=0.38,relheight=l2height/nheight,relwidth=0.12)
    Label5.configure(text='e')
    Label5.configure(anchor=tk.W)
    Label5.configure(font=('None',9))

    Label6=tk.Label(fIn)
    Label6.place(relx=0.02,rely=0.45,relheight=l2height/nheight,relwidth=0.12)
    Label6.configure(text='mu3')
    Label6.configure(anchor=tk.W)
    Label6.configure(font=('None',9))

    Label7=tk.Label(fIn)
    Label7.place(relx=0.02,rely=0.52,relheight=l2height/nheight,relwidth=0.12)
    Label7.configure(text='r3')
    Label7.configure(anchor=tk.W)
    Label7.configure(font=('None',9))

    Label8=tk.Label(fIn)
    Label8.place(relx=0.02,rely=0.59,relheight=l2height/nheight,relwidth=0.12)
    Label8.configure(text='w3')
    Label8.configure(anchor=tk.W)
    Label8.configure(font=('None',9))

    Label9=tk.Label(fIn)
    Label9.place(relx=0.02,rely=0.66,relheight=l2height/nheight,relwidth=0.12)
    Label9.configure(text='t03')
    Label9.configure(anchor=tk.W)
    Label9.configure(font=('None',9))

    Label10=tk.Label(fIn)
    Label10.place(relx=0.02,rely=0.73,relheight=l2height/nheight,relwidth=0.12)
    Label10.configure(text='P3')
    Label10.configure(anchor=tk.W)
    Label10.configure(font=('None',9))

    #input objects for param t0
    t0I=[tk.Entry(fIn)]
    t0I[-1].place(relx=0.15,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0I[-1].configure(textvariable=t0Val)

    t0I.append(tk.Entry(fIn))
    t0I[-1].place(relx=0.35,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0I[-1].configure(textvariable=t0Min)

    t0I.append(tk.Entry(fIn))
    t0I[-1].place(relx=0.55,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0I[-1].configure(textvariable=t0Max)

    t0I.append(tk.Entry(fIn))
    t0I[-1].place(relx=0.75,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0I[-1].configure(textvariable=t0Step)

    t0I.append(tk.Checkbutton(fIn))
    t0I[-1].place(relx=0.95,rely=0.09,relheight=0.06,relwidth=0.04)
    t0I[-1].configure(justify=tk.LEFT)
    t0I[-1].configure(variable=t0Fit)

    #input objects for param P
    PI=[tk.Entry(fIn)]
    PI[-1].place(relx=0.15,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PI[-1].configure(textvariable=PVal)

    PI.append(tk.Entry(fIn))
    PI[-1].place(relx=0.35,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PI[-1].configure(textvariable=PMin)

    PI.append(tk.Entry(fIn))
    PI[-1].place(relx=0.55,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PI[-1].configure(textvariable=PMax)

    PI.append(tk.Entry(fIn))
    PI[-1].place(relx=0.75,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PI[-1].configure(textvariable=PStep)

    PI.append(tk.Checkbutton(fIn))
    PI[-1].place(relx=0.95,rely=0.16,relheight=0.06,relwidth=0.04)
    PI[-1].configure(justify=tk.LEFT)
    PI[-1].configure(variable=PFit)

    #input objects for param a
    aI=[tk.Entry(fIn)]
    aI[-1].place(relx=0.15,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    aI[-1].configure(textvariable=aVal)

    aI.append(tk.Entry(fIn))
    aI[-1].place(relx=0.35,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    aI[-1].configure(textvariable=aMin)

    aI.append(tk.Entry(fIn))
    aI[-1].place(relx=0.55,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    aI[-1].configure(textvariable=aMax)

    aI.append(tk.Entry(fIn))
    aI[-1].place(relx=0.75,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    aI[-1].configure(textvariable=aStep)

    aI.append(tk.Checkbutton(fIn))
    aI[-1].place(relx=0.95,rely=0.23,relheight=0.06,relwidth=0.04)
    aI[-1].configure(justify=tk.LEFT)
    aI[-1].configure(variable=aFit)

    #input objects for param w
    wI=[tk.Entry(fIn)]
    wI[-1].place(relx=0.15,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    wI[-1].configure(textvariable=wVal)

    wI.append(tk.Entry(fIn))
    wI[-1].place(relx=0.35,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    wI[-1].configure(textvariable=wMin)

    wI.append(tk.Entry(fIn))
    wI[-1].place(relx=0.55,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    wI[-1].configure(textvariable=wMax)

    wI.append(tk.Entry(fIn))
    wI[-1].place(relx=0.75,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    wI[-1].configure(textvariable=wStep)

    wI.append(tk.Checkbutton(fIn))
    wI[-1].place(relx=0.95,rely=0.30,relheight=0.06,relwidth=0.04)
    wI[-1].configure(justify=tk.LEFT)
    wI[-1].configure(variable=wFit)

    #input objects for param e
    eI=[tk.Entry(fIn)]
    eI[-1].place(relx=0.15,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    eI[-1].configure(textvariable=eVal)

    eI.append(tk.Entry(fIn))
    eI[-1].place(relx=0.35,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    eI[-1].configure(textvariable=eMin)

    eI.append(tk.Entry(fIn))
    eI[-1].place(relx=0.55,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    eI[-1].configure(textvariable=eMax)

    eI.append(tk.Entry(fIn))
    eI[-1].place(relx=0.75,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    eI[-1].configure(textvariable=eStep)

    eI.append(tk.Checkbutton(fIn))
    eI[-1].place(relx=0.95,rely=0.37,relheight=0.06,relwidth=0.04)
    eI[-1].configure(justify=tk.LEFT)
    eI[-1].configure(variable=eFit)

    #input objects for param mu3
    mu3I=[tk.Entry(fIn)]
    mu3I[-1].place(relx=0.15,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    mu3I[-1].configure(textvariable=mu3Val)

    mu3I.append(tk.Entry(fIn))
    mu3I[-1].place(relx=0.35,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    mu3I[-1].configure(textvariable=mu3Min)

    mu3I.append(tk.Entry(fIn))
    mu3I[-1].place(relx=0.55,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    mu3I[-1].configure(textvariable=mu3Max)

    mu3I.append(tk.Entry(fIn))
    mu3I[-1].place(relx=0.75,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    mu3I[-1].configure(textvariable=mu3Step)

    mu3I.append(tk.Checkbutton(fIn))
    mu3I[-1].place(relx=0.95,rely=0.44,relheight=0.06,relwidth=0.04)
    mu3I[-1].configure(justify=tk.LEFT)
    mu3I[-1].configure(variable=mu3Fit)

    #input objects for param r3
    r3I=[tk.Entry(fIn)]
    r3I[-1].place(relx=0.15,rely=0.51,relheight=iheight/nheight,relwidth=0.19)
    r3I[-1].configure(textvariable=r3Val)

    r3I.append(tk.Entry(fIn))
    r3I[-1].place(relx=0.35,rely=0.51,relheight=iheight/nheight,relwidth=0.19)
    r3I[-1].configure(textvariable=r3Min)

    r3I.append(tk.Entry(fIn))
    r3I[-1].place(relx=0.55,rely=0.51,relheight=iheight/nheight,relwidth=0.19)
    r3I[-1].configure(textvariable=r3Max)

    r3I.append(tk.Entry(fIn))
    r3I[-1].place(relx=0.75,rely=0.51,relheight=iheight/nheight,relwidth=0.19)
    r3I[-1].configure(textvariable=r3Step)

    r3I.append(tk.Checkbutton(fIn))
    r3I[-1].place(relx=0.95,rely=0.51,relheight=0.06,relwidth=0.04)
    r3I[-1].configure(justify=tk.LEFT)
    r3I[-1].configure(variable=r3Fit)

    #input objects for param w3
    w3I=[tk.Entry(fIn)]
    w3I[-1].place(relx=0.15,rely=0.58,relheight=iheight/nheight,relwidth=0.19)
    w3I[-1].configure(textvariable=w3Val)

    w3I.append(tk.Entry(fIn))
    w3I[-1].place(relx=0.35,rely=0.58,relheight=iheight/nheight,relwidth=0.19)
    w3I[-1].configure(textvariable=w3Min)

    w3I.append(tk.Entry(fIn))
    w3I[-1].place(relx=0.55,rely=0.58,relheight=iheight/nheight,relwidth=0.19)
    w3I[-1].configure(textvariable=w3Max)

    w3I.append(tk.Entry(fIn))
    w3I[-1].place(relx=0.75,rely=0.58,relheight=iheight/nheight,relwidth=0.19)
    w3I[-1].configure(textvariable=w3Step)

    w3I.append(tk.Checkbutton(fIn))
    w3I[-1].place(relx=0.95,rely=0.58,relheight=0.06,relwidth=0.04)
    w3I[-1].configure(justify=tk.LEFT)
    w3I[-1].configure(variable=w3Fit)

    #input objects for param t03
    t3I=[tk.Entry(fIn)]
    t3I[-1].place(relx=0.15,rely=0.65,relheight=iheight/nheight,relwidth=0.19)
    t3I[-1].configure(textvariable=t3Val)

    t3I.append(tk.Entry(fIn))
    t3I[-1].place(relx=0.35,rely=0.65,relheight=iheight/nheight,relwidth=0.19)
    t3I[-1].configure(textvariable=t3Min)

    t3I.append(tk.Entry(fIn))
    t3I[-1].place(relx=0.55,rely=0.65,relheight=iheight/nheight,relwidth=0.19)
    t3I[-1].configure(textvariable=t3Max)

    t3I.append(tk.Entry(fIn))
    t3I[-1].place(relx=0.75,rely=0.65,relheight=iheight/nheight,relwidth=0.19)
    t3I[-1].configure(textvariable=t3Step)

    t3I.append(tk.Checkbutton(fIn))
    t3I[-1].place(relx=0.95,rely=0.65,relheight=0.06,relwidth=0.04)
    t3I[-1].configure(justify=tk.LEFT)
    t3I[-1].configure(variable=t3Fit)

    #input objects for param P3
    P3I=[tk.Entry(fIn)]
    P3I[-1].place(relx=0.15,rely=0.72,relheight=iheight/nheight,relwidth=0.19)
    P3I[-1].configure(textvariable=P3Val)

    P3I.append(tk.Entry(fIn))
    P3I[-1].place(relx=0.35,rely=0.72,relheight=iheight/nheight,relwidth=0.19)
    P3I[-1].configure(textvariable=P3Min)

    P3I.append(tk.Entry(fIn))
    P3I[-1].place(relx=0.55,rely=0.72,relheight=iheight/nheight,relwidth=0.19)
    P3I[-1].configure(textvariable=P3Max)

    P3I.append(tk.Entry(fIn))
    P3I[-1].place(relx=0.75,rely=0.72,relheight=iheight/nheight,relwidth=0.19)
    P3I[-1].configure(textvariable=P3Step)

    P3I.append(tk.Checkbutton(fIn))
    P3I[-1].place(relx=0.95,rely=0.72,relheight=0.06,relwidth=0.04)
    P3I[-1].configure(justify=tk.LEFT)
    P3I[-1].configure(variable=P3Fit)

    ##########################################################################################
    #           AgolExPlanet                                                                 #
    ##########################################################################################

    fEx=tk.Frame(tNTB)
    tNTB.add(fEx)

    #labels
    Label15=tk.Label(fEx)
    Label15.place(relx=0.02,rely=0.03,relheight=l2height/nheight,relwidth=0.12)
    Label15.configure(text='param.')
    Label15.configure(font=('None',9))
    Label15.configure(anchor=tk.W)

    Label16=tk.Label(fEx)
    Label16.place(relx=0.15,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label16.configure(text='value')
    Label16.configure(font=('None',9))
    Label16.configure(anchor=tk.W)

    Label17=tk.Label(fEx)
    Label17.place(relx=0.35,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label17.configure(text='min.')
    Label17.configure(font=('None',9))
    Label17.configure(anchor=tk.W)

    Label18=tk.Label(fEx)
    Label18.place(relx=0.55,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label18.configure(text='max.')
    Label18.configure(font=('None',9))
    Label18.configure(anchor=tk.W)

    Label19=tk.Label(fEx)
    Label19.place(relx=0.75,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label19.configure(text='step')
    Label19.configure(font=('None',9))
    Label19.configure(anchor=tk.W)

    Label20=tk.Label(fEx)
    Label20.place(relx=0.95,rely=0.03,relheight=l2height/nheight,relwidth=0.04)
    Label20.configure(text='fit')
    Label20.configure(font=('None',9))

    Label2=tk.Label(fEx)
    Label2.place(relx=0.02,rely=0.10,relheight=l2height/nheight,relwidth=0.12)
    Label2.configure(text='t0')
    Label2.configure(anchor=tk.W)

    Label3=tk.Label(fEx)
    Label3.place(relx=0.02,rely=0.17,relheight=l2height/nheight,relwidth=0.12)
    Label3.configure(text='P')
    Label3.configure(anchor=tk.W)
    Label3.configure(font=('None',9))

    Label14=tk.Label(fEx)
    Label14.place(relx=0.02,rely=0.24,relheight=l2height/nheight,relwidth=0.12)
    Label14.configure(text='mu3')
    Label14.configure(anchor=tk.W)
    Label14.configure(font=('None',9))

    Label4=tk.Label(fEx)
    Label4.place(relx=0.02,rely=0.31,relheight=l2height/nheight,relwidth=0.12)
    Label4.configure(text='e3')
    Label4.configure(anchor=tk.W)
    Label4.configure(font=('None',9))

    Label5=tk.Label(fEx)
    Label5.place(relx=0.02,rely=0.38,relheight=l2height/nheight,relwidth=0.12)
    Label5.configure(text='t03')
    Label5.configure(anchor=tk.W)
    Label5.configure(font=('None',9))

    Label6=tk.Label(fEx)
    Label6.place(relx=0.02,rely=0.45,relheight=l2height/nheight,relwidth=0.12)
    Label6.configure(text='P3')
    Label6.configure(anchor=tk.W)
    Label6.configure(font=('None',9))

    #input objects for param t0
    t0E=[tk.Entry(fEx)]
    t0E[-1].place(relx=0.15,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0E[-1].configure(textvariable=t0Val)

    t0E.append(tk.Entry(fEx))
    t0E[-1].place(relx=0.35,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0E[-1].configure(textvariable=t0Min)

    t0E.append(tk.Entry(fEx))
    t0E[-1].place(relx=0.55,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0E[-1].configure(textvariable=t0Max)

    t0E.append(tk.Entry(fEx))
    t0E[-1].place(relx=0.75,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0E[-1].configure(textvariable=t0Step)

    t0E.append(tk.Checkbutton(fEx))
    t0E[-1].place(relx=0.95,rely=0.09,relheight=0.06,relwidth=0.04)
    t0E[-1].configure(justify=tk.LEFT)
    t0E[-1].configure(variable=t0Fit)

    #input objects for param P
    PE=[tk.Entry(fEx)]
    PE[-1].place(relx=0.15,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PE[-1].configure(textvariable=PVal)

    PE.append(tk.Entry(fEx))
    PE[-1].place(relx=0.35,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PE[-1].configure(textvariable=PMin)

    PE.append(tk.Entry(fEx))
    PE[-1].place(relx=0.55,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PE[-1].configure(textvariable=PMax)

    PE.append(tk.Entry(fEx))
    PE[-1].place(relx=0.75,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PE[-1].configure(textvariable=PStep)

    PE.append(tk.Checkbutton(fEx))
    PE[-1].place(relx=0.95,rely=0.16,relheight=0.06,relwidth=0.04)
    PE[-1].configure(justify=tk.LEFT)
    PE[-1].configure(variable=PFit)

    #input objects for param mu3
    mu3E=[tk.Entry(fEx)]
    mu3E[-1].place(relx=0.15,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    mu3E[-1].configure(textvariable=mu3Val)

    mu3E.append(tk.Entry(fEx))
    mu3E[-1].place(relx=0.35,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    mu3E[-1].configure(textvariable=mu3Min)

    mu3E.append(tk.Entry(fEx))
    mu3E[-1].place(relx=0.55,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    mu3E[-1].configure(textvariable=mu3Max)

    mu3E.append(tk.Entry(fEx))
    mu3E[-1].place(relx=0.75,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    mu3E[-1].configure(textvariable=mu3Step)

    mu3E.append(tk.Checkbutton(fEx))
    mu3E[-1].place(relx=0.95,rely=0.23,relheight=0.06,relwidth=0.04)
    mu3E[-1].configure(justify=tk.LEFT)
    mu3E[-1].configure(variable=mu3Fit)

    #input objects for param e3
    e3E=[tk.Entry(fEx)]
    e3E[-1].place(relx=0.15,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    e3E[-1].configure(textvariable=e3Val)

    e3E.append(tk.Entry(fEx))
    e3E[-1].place(relx=0.35,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    e3E[-1].configure(textvariable=e3Min)

    e3E.append(tk.Entry(fEx))
    e3E[-1].place(relx=0.55,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    e3E[-1].configure(textvariable=e3Max)

    e3E.append(tk.Entry(fEx))
    e3E[-1].place(relx=0.75,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    e3E[-1].configure(textvariable=e3Step)

    e3E.append(tk.Checkbutton(fEx))
    e3E[-1].place(relx=0.95,rely=0.30,relheight=0.06,relwidth=0.04)
    e3E[-1].configure(justify=tk.LEFT)
    e3E[-1].configure(variable=e3Fit)

    #input objects for param t03
    t3E=[tk.Entry(fEx)]
    t3E[-1].place(relx=0.15,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    t3E[-1].configure(textvariable=t3Val)

    t3E.append(tk.Entry(fEx))
    t3E[-1].place(relx=0.35,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    t3E[-1].configure(textvariable=t3Min)

    t3E.append(tk.Entry(fEx))
    t3E[-1].place(relx=0.55,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    t3E[-1].configure(textvariable=t3Max)

    t3E.append(tk.Entry(fEx))
    t3E[-1].place(relx=0.75,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    t3E[-1].configure(textvariable=t3Step)

    t3E.append(tk.Checkbutton(fEx))
    t3E[-1].place(relx=0.95,rely=0.37,relheight=0.06,relwidth=0.04)
    t3E[-1].configure(justify=tk.LEFT)
    t3E[-1].configure(variable=t3Fit)

    #input objects for param P3
    P3E=[tk.Entry(fEx)]
    P3E[-1].place(relx=0.15,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    P3E[-1].configure(textvariable=P3Val)

    P3E.append(tk.Entry(fEx))
    P3E[-1].place(relx=0.35,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    P3E[-1].configure(textvariable=P3Min)

    P3E.append(tk.Entry(fEx))
    P3E[-1].place(relx=0.55,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    P3E[-1].configure(textvariable=P3Max)

    P3E.append(tk.Entry(fEx))
    P3E[-1].place(relx=0.75,rely=0.44,relheight=iheight/nheight,relwidth=0.19)
    P3E[-1].configure(textvariable=P3Step)

    P3E.append(tk.Checkbutton(fEx))
    P3E[-1].place(relx=0.95,rely=0.44,relheight=0.06,relwidth=0.04)
    P3E[-1].configure(justify=tk.LEFT)
    P3E[-1].configure(variable=P3Fit)

    ##########################################################################################
    #           Apsidal                                                                      #
    ##########################################################################################

    fAps=tk.Frame(tNTB)
    tNTB.add(fAps)

    #labels
    Label15=tk.Label(fAps)
    Label15.place(relx=0.02,rely=0.03,relheight=l2height/nheight,relwidth=0.12)
    Label15.configure(text='param.')
    Label15.configure(font=('None',9))
    Label15.configure(anchor=tk.W)

    Label16=tk.Label(fAps)
    Label16.place(relx=0.15,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label16.configure(text='value')
    Label16.configure(font=('None',9))
    Label16.configure(anchor=tk.W)

    Label17=tk.Label(fAps)
    Label17.place(relx=0.35,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label17.configure(text='min.')
    Label17.configure(font=('None',9))
    Label17.configure(anchor=tk.W)

    Label18=tk.Label(fAps)
    Label18.place(relx=0.55,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label18.configure(text='max.')
    Label18.configure(font=('None',9))
    Label18.configure(anchor=tk.W)

    Label19=tk.Label(fAps)
    Label19.place(relx=0.75,rely=0.03,relheight=l2height/nheight,relwidth=0.19)
    Label19.configure(text='step')
    Label19.configure(font=('None',9))
    Label19.configure(anchor=tk.W)

    Label20=tk.Label(fAps)
    Label20.place(relx=0.95,rely=0.03,relheight=l2height/nheight,relwidth=0.04)
    Label20.configure(text='fit')
    Label20.configure(font=('None',9))

    Label2=tk.Label(fAps)
    Label2.place(relx=0.02,rely=0.10,relheight=l2height/nheight,relwidth=0.12)
    Label2.configure(text='t0')
    Label2.configure(font=('None',9))
    Label2.configure(anchor=tk.W)

    Label3=tk.Label(fAps)
    Label3.place(relx=0.02,rely=0.17,relheight=l2height/nheight,relwidth=0.12)
    Label3.configure(text='P')
    Label3.configure(font=('None',9))
    Label3.configure(anchor=tk.W)

    Label14=tk.Label(fAps)
    Label14.place(relx=0.02,rely=0.24,relheight=l2height/nheight,relwidth=0.12)
    Label14.configure(text='w0')
    Label14.configure(font=('None',9))
    Label14.configure(anchor=tk.W)

    Label4=tk.Label(fAps)
    Label4.place(relx=0.02,rely=0.31,relheight=l2height/nheight,relwidth=0.12)
    Label4.configure(text='dw')
    Label4.configure(font=('None',9))
    Label4.configure(anchor=tk.W)

    Label5=tk.Label(fAps)
    Label5.place(relx=0.02,rely=0.38,relheight=l2height/nheight,relwidth=0.12)
    Label5.configure(text='e')
    Label5.configure(font=('None',9))
    Label5.configure(anchor=tk.W)

    #input objects for param t0
    t0A=[tk.Entry(fAps)]
    t0A[-1].place(relx=0.15,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0A[-1].configure(textvariable=t0Val)

    t0A.append(tk.Entry(fAps))
    t0A[-1].place(relx=0.35,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0A[-1].configure(textvariable=t0Min)

    t0A.append(tk.Entry(fAps))
    t0A[-1].place(relx=0.55,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0A[-1].configure(textvariable=t0Max)

    t0A.append(tk.Entry(fAps))
    t0A[-1].place(relx=0.75,rely=0.09,relheight=iheight/nheight,relwidth=0.19)
    t0A[-1].configure(textvariable=t0Step)

    t0A.append(tk.Checkbutton(fAps))
    t0A[-1].place(relx=0.95,rely=0.09,relheight=0.06,relwidth=0.04)
    t0A[-1].configure(justify=tk.LEFT)
    t0A[-1].configure(variable=t0Fit)

    #input objects for param P
    PA=[tk.Entry(fAps)]
    PA[-1].place(relx=0.15,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PA[-1].configure(textvariable=PVal)

    PA.append(tk.Entry(fAps))
    PA[-1].place(relx=0.35,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PA[-1].configure(textvariable=PMin)

    PA.append(tk.Entry(fAps))
    PA[-1].place(relx=0.55,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    PA[-1].configure(textvariable=PMax)

    P.append(tk.Entry(fAps))
    P[-1].place(relx=0.75,rely=0.16,relheight=iheight/nheight,relwidth=0.19)
    P[-1].configure(textvariable=PStep)

    PA.append(tk.Checkbutton(fAps))
    PA[-1].place(relx=0.95,rely=0.16,relheight=0.06,relwidth=0.04)
    PA[-1].configure(justify=tk.LEFT)
    PA[-1].configure(variable=PFit)

    #input objects for param w0
    w0A=[tk.Entry(fAps)]
    w0A[-1].place(relx=0.15,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    w0A[-1].configure(textvariable=w0Val)

    w0A.append(tk.Entry(fAps))
    w0A[-1].place(relx=0.35,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    w0A[-1].configure(textvariable=w0Min)

    w0A.append(tk.Entry(fAps))
    w0A[-1].place(relx=0.55,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    w0A[-1].configure(textvariable=w0Max)

    w0A.append(tk.Entry(fAps))
    w0A[-1].place(relx=0.75,rely=0.23,relheight=iheight/nheight,relwidth=0.19)
    w0A[-1].configure(textvariable=w0Step)

    w0A.append(tk.Checkbutton(fAps))
    w0A[-1].place(relx=0.95,rely=0.23,relheight=0.06,relwidth=0.04)
    w0A[-1].configure(justify=tk.LEFT)
    w0A[-1].configure(variable=w0Fit)

    #input objects for param dw
    dwA=[tk.Entry(fAps)]
    dwA[-1].place(relx=0.15,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    dwA[-1].configure(textvariable=dwVal)

    dwA.append(tk.Entry(fAps))
    dwA[-1].place(relx=0.35,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    dwA[-1].configure(textvariable=dwMin)

    dwA.append(tk.Entry(fAps))
    dwA[-1].place(relx=0.55,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    dwA[-1].configure(textvariable=dwMax)

    dwA.append(tk.Entry(fAps))
    dwA[-1].place(relx=0.75,rely=0.30,relheight=iheight/nheight,relwidth=0.19)
    dwA[-1].configure(textvariable=dwStep)

    dwA.append(tk.Checkbutton(fAps))
    dwA[-1].place(relx=0.95,rely=0.30,relheight=0.06,relwidth=0.04)
    dwA[-1].configure(justify=tk.LEFT)
    dwA[-1].configure(variable=dwFit)

    #input objects for param e
    eA=[tk.Entry(fAps)]
    eA[-1].place(relx=0.15,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    eA[-1].configure(textvariable=eVal)

    eA.append(tk.Entry(fAps))
    eA[-1].place(relx=0.35,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    eA[-1].configure(textvariable=eMin)

    eA.append(tk.Entry(fAps))
    eA[-1].place(relx=0.55,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    eA[-1].configure(textvariable=eMax)

    eA.append(tk.Entry(fAps))
    eA[-1].place(relx=0.75,rely=0.37,relheight=iheight/nheight,relwidth=0.19)
    eA[-1].configure(textvariable=eStep)

    eA.append(tk.Checkbutton(fAps))
    eA[-1].place(relx=0.95,rely=0.37,relheight=0.06,relwidth=0.04)
    eA[-1].configure(justify=tk.LEFT)
    eA[-1].configure(variable=eFit)


    #button - save params
    bOk=tk.Button(tParams)
    bOk.place(relx=0.39,rely=0.94,relheight=b1height/theight,relwidth=b4width/twidth)
    bOk.configure(command=ok)
    bOk.configure(text='OK')

    init_vars()


def plot(f=None):
    #plot O-Cs together with model
    if ocf.t[0]<2e6: trans=False
    else: trans=True

    if f is not None:
        #solving problem with closing GUI when "f" is given
        try: mpl.switch_backend('Agg')
        except: pass #old version of matplotlib

    try:
        if not ocf._set_err:
            w=1./ocf.err
            if min(w)==max(w): ocf.Plot(name=f,trans=trans,weight=w,min_type=True)
            else: ocf.Plot(name=f,trans=trans,weight=w,trans_weight=True,min_type=True)
        else: ocf.Plot(name=f,trans=trans,min_type=True)
    except:
        mpl.close()
        tkinter.messagebox.showerror('Plot O-C','Fit the model!')

    if f is not None:
        #solving problem with closing GUI when "f" is given -> change to default backend
        try: mpl.switch_backend('TkAgg')
        except: pass #old version of matplotlib

def plotR(f=None):
    #plot residual O-Cs
    if ocf.t[0]<2e6: trans=False
    else: trans=True

    if f is not None:
        #solving problem with closing GUI when "f" is given
        try: mpl.switch_backend('Agg')
        except: pass #old version of matplotlib

    try:
        if not ocf._set_err:
            w=1./ocf.err
            if min(w)==max(w): ocf.PlotRes(name=f,trans=trans,weight=w,min_type=True)
            else: ocf.PlotRes(name=f,trans=trans,weight=w,trans_weight=True,min_type=True)
        else: ocf.PlotRes(name=f,trans=trans,min_type=True)
    except:
        mpl.close()
        tkinter.messagebox.showerror('Plot new O-C','Fit the model!')

    if f is not None:
        #solving problem with closing GUI when "f" is given -> change to default backend
        try: mpl.switch_backend('TkAgg')
        except: pass #old version of matplotlib

def runBG():
    #run fitting on background
    for p in ocf.fit_params:
        if not p in ocf.limits:
            tkinter.messagebox.showerror('Fit on background','Set limits of parameter "'+p+'"!')
            return
        if not p in ocf.steps:
            tkinter.messagebox.showerror('Fit on background','Set step of parameter "'+p+'"!')
            return

    f=saveC() #save class to file

    cmd='nohup python3 -u ocfit-bg.py '+f+' '+str(ga['gen'])+' '+str(ga['size'])+' '+str(mc['n'])+' '+str(mc['burn'])+' '+\
            str(mc['binn'])+' '+str(save)+' > '+f[:f.rfind('.')]+'.log'  #generate command for fitting

    #create fitting script
    if 'win' in sys.platform:
        fsh=open(f[:f.rfind('.')]+'.bat','w')
        fsh.write('REM Please,check the paths to OCFit file and python file "ocfit-bg.py"!\n')
        fsh.write('START /B python'+cmd[13:]+'\n')
        fsh.close()
    fsh=open(f[:f.rfind('.')]+'.sh','w')
    fsh.write('# Please,check the paths to OCFit file and python file "ocfit-bg.py"!\n')
    fsh.write(cmd+' &\n')
    fsh.close()

    #start fitting?
    result=tkinter.messagebox.askquestion('Run on background','Start fitting on background?',icon='question')
    if result=='yes':
        if 'win' in sys.platform: cmd='START /B python'+cmd[13:]
        else: cmd+=' &'
        subprocess.Popen(cmd,shell=True)

def saveM(f=None):
    #save model O-Cs
    if f is None:
        f=tkinter.filedialog.asksaveasfilename(parent=master,title='Save model O-C to file',filetypes=[('Data files','*.dat *.txt'),('All files','*.*')],defaultextension='.dat')
    if len(f)==0: return

    try: ocf.SaveModel(f)
    except: tkinter.messagebox.showerror('Save model','Fit the model!')

def saveR(f=None):
    #save residual O-Cs
    if f is None:
        f=tkinter.filedialog.asksaveasfilename(parent=master,title='Save new O-C to file',filetypes=[('Data files','*.dat *.txt'),('All files','*.*')],defaultextension='.dat')
    if len(f)==0: return

    try:
        if not 'err' in data and 'w' in data: ocf.SaveRes(f,weight=data['w'])
        else: ocf.SaveRes(f)
    except: tkinter.messagebox.showerror('Save new O-C','Fit the model!')

def saveAll():
    #run all saving functions
    f=tkinter.filedialog.asksaveasfilename(parent=master,title='Save all to file',filetypes=[('All files','*.*')])
    if len(f)==0: return

    if '.' in f[-5:]: f=f[:f.rfind('.')]

    saveM(f+'_model.dat')
    saveR(f+'_res.dat')
    saveC(f+'.ocf')
    summary(f+'_summary.txt')
    plot(f)
    plotR(f+'_res')

def summary(f=None):
    #show summary for fitting

    if f is not None:
        try: ocf.Summary(f)
        except: tkinter.messagebox.showerror('Summary','Fit the model!')
        return


    #create new window
    sumW=tk.Toplevel(master)
    #default scale of window - NOT change this values if you want to change size
    twidth=750
    theight=650
    if fixed:
        sumW.geometry(str(twidth)+'x'+str(theight))   #modif. this line to change size - e.g. master.geometry('400x500')
    else:
        #set relatively to screen size
        sumW.geometry('{}x{}'.format(int(twidth/mwidth*screenwidth), int(theight/mheight*screenheight)))
    sumW.title('Summary')

    #text field
    text=tk.Text(sumW)
    text.place(relx=0.02,rely=0.02,relheight=0.96,relwidth=0.96)

    old=sys.stdout
    #redirect output to text field
    sys.stdout=StdoutRedirector(text)

    try: ocf.Summary()
    except:
        sumW.destroy()
        tkinter.messagebox.showerror('Summary','Fit the model!')

    sys.stdout=old

data={}
ga={}
mc={}
save=0

#main window
master=tk.Tk()
#default scale of window - NOT change this values if you want to change size
mwidth=350
mheight=560

fixed=True   #fixed size to default

if fixed:
    master.geometry(str(mwidth)+'x'+str(mheight))   #modif. this line to change size - e.g. master.geometry('400x500')
else:
    #set relatively to screen size
    height = master.winfo_screenheight()
    width = master.winfo_screenwidth()
    screenheight = int(0.6*height)
    screenwidth = int(0.25*width)
    master.geometry('{}x{}'.format(screenwidth, screenheight))
master.title('OCFit GUI')

#set size of buttons, labels etc.
b1height=26   #button
b2height=31
iheight=25    #input/entry
lheight=23    #label
l2height=18
rheight=27      #radiobutton

b1width=90
b2width=117
b3width=95
b4width=140
b5width=100
b6width=80
rwidth=75

style=tkinter.ttk.Style()

style.layout('TNotebook.Tab',[])

#variable for T0 and P
t0Var=tk.StringVar(master)
pVar=tk.StringVar(master)
dEVar=tk.StringVar(master)
dEVar.set('0.5')

#button - load data from file
bLoad=tk.Button(master)
bLoad.place(relx=0.5-b1width/mwidth/2,rely=5/mheight,relheight=b1height/mheight,relwidth=b1width/mwidth)
bLoad.configure(command=load)
bLoad.configure(text='Load Data')

#frame for linear ephemeris
Frame1=tk.Frame(master)
f1height=95
f1width=316
Frame1.place(relx=0.06,rely=40/mheight,relheight=f1height/mheight,relwidth=f1width/mwidth)
Frame1.configure(relief=tk.GROOVE)
Frame1.configure(borderwidth='2')
Frame1.configure(relief=tk.GROOVE)
Frame1.configure(width=295)

#labels
Label1=tk.Label(Frame1)
Label1.place(relx=0.07,rely=15/f1height,relheight=lheight/f1height,relwidth=0.15)
Label1.configure(anchor=tk.W)
Label1.configure(text='T0')
Label1.configure(font=('None',9))

#input - T0
Entry1=tk.Entry(Frame1)
Entry1.place(relx=0.24,rely=15/f1height,relheight=iheight/f1height,relwidth=0.73)
Entry1.configure(textvariable=t0Var)

Label2=tk.Label(Frame1)
Label2.place(relx=0.07,rely=(15+24)/f1height,relheight=lheight/f1height,relwidth=0.15)
Label2.configure(anchor=tk.W)
Label2.configure(justify=tk.LEFT)
Label2.configure(text='P')
Label2.configure(font=('None',9))

#input - P
Entry2=tk.Entry(Frame1)
Entry2.place(relx=0.24,rely=(15+24)/f1height,relheight=iheight/f1height,relwidth=0.73)
Entry2.configure(textvariable=pVar)

Label3=tk.Label(Frame1)
Label3.place(relx=0.07,rely=(15+2*24)/f1height,relheight=lheight/f1height,relwidth=0.15)
Label3.configure(anchor=tk.W)
Label3.configure(justify=tk.LEFT)
Label3.configure(text='dE')
Label3.configure(font=('None',9))

#input - dE
Entry3=tk.Entry(Frame1)
Entry3.place(relx=0.24,rely=(15+2*24)/f1height,relheight=iheight/f1height,relwidth=0.35)
Entry3.configure(textvariable=dEVar)

bdE=tk.Button(Frame1)
bdE.place(relx=0.6,rely=(15+2*24)/f1height,relheight=iheight/f1height,relwidth=0.37)
bdE.configure(command=deltaE)
bdE.configure(text='Calculate')

#button - Plot O-C
bPlot0=tk.Button(master)
bPlot0.place(relx=0.06,rely=140/mheight,relheight=b1height/mheight,relwidth=b5width/mwidth)
bPlot0.configure(command=plot0)
bPlot0.configure(state=tk.DISABLED)
bPlot0.configure(text='Plot O-C')


#button - Save O-C
bSave0=tk.Button(master)
bSave0.place(relx=0.365,rely=140/mheight,relheight=b1height/mheight,relwidth=b5width/mwidth)
bSave0.configure(command=save0)
bSave0.configure(state=tk.DISABLED)
bSave0.configure(text='Save O-C')

#button - System Params
bSyst=tk.Button(master)
bSyst.place(relx=0.67,rely=140/mheight,relheight=b1height/mheight,relwidth=b5width/mwidth)
bSyst.configure(command=system)
bSyst.configure(text='Sys.Params.')

#frame for linear / quadratic fitting
Frame2=tk.Frame(master)
f2height=113
f2width=316
Frame2.place(relx=0.06,rely=177/mheight,relheight=f2height/mheight,relwidth=f2width/mwidth)
Frame2.configure(relief=tk.GROOVE)
Frame2.configure(borderwidth='2')
Frame2.configure(relief=tk.GROOVE)
Frame2.configure(width=295)

#button - fit params
bFit0=tk.Button(Frame2)
bFit0.place(relx=0.02,rely=9/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bFit0.configure(command=fitParams0)
bFit0.configure(state=tk.DISABLED)
bFit0.configure(text='FitParams')

#button - fit linear
bLin=tk.Button(Frame2)
bLin.place(relx=0.35,rely=9/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bLin.configure(command=lin)
bLin.configure(state=tk.DISABLED)
bLin.configure(text='FitLinear')

#button - fit quadratic
bQuad=tk.Button(Frame2)
bQuad.place(relx=0.68,rely=9/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bQuad.configure(command=quad)
bQuad.configure(state=tk.DISABLED)
bQuad.configure(text='FitQuad')

#button - plot O-C
bPlotS=tk.Button(Frame2)
bPlotS.place(relx=0.02,rely=(9+34)/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bPlotS.configure(command=plotS)
bPlotS.configure(state=tk.DISABLED)
bPlotS.configure(text='Plot O-C')

#button - plot residual O-C
bPlotRS=tk.Button(Frame2)
bPlotRS.place(relx=0.35,rely=(9+34)/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bPlotRS.configure(command=plotRS)
bPlotRS.configure(state=tk.DISABLED)
bPlotRS.configure(text='Plot O-C res.')

#button - summary
bSumS=tk.Button(Frame2)
bSumS.place(relx=0.68,rely=(9+34)/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bSumS.configure(command=sumS)
bSumS.configure(state=tk.DISABLED)
bSumS.configure(text='Summary')

#button - save residual O-C
bSaveRS=tk.Button(Frame2)
bSaveRS.place(relx=0.02,rely=(9+2*34)/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bSaveRS.configure(command=saveRS)
bSaveRS.configure(state=tk.DISABLED)
bSaveRS.configure(text='Save O-C res.')

#button - save all
bSaveAll0=tk.Button(Frame2)
bSaveAll0.place(relx=0.35,rely=(9+2*34)/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bSaveAll0.configure(command=saveAll0)
bSaveAll0.configure(state=tk.DISABLED)
bSaveAll0.configure(text='Save all')

#button - save residual O-C
bUpd=tk.Button(Frame2)
bUpd.place(relx=0.68,rely=(9+2*34)/f2height,relheight=b2height/f2height,relwidth=b3width/f2width)
bUpd.configure(command=update)
bUpd.configure(state=tk.DISABLED)
bUpd.configure(text='UpdateEph')

#frame for O-C fitting
Frame3=tk.Frame(master)
f3height=220
f3width=316
Frame3.place(relx=0.06,rely=300/mheight,relheight=f3height/mheight,relwidth=f3width/mwidth)
Frame3.configure(relief=tk.GROOVE)
Frame3.configure(borderwidth='2')
Frame3.configure(relief=tk.GROOVE)
Frame3.configure(width=295)

#button - class initialization
bInit=tk.Button(Frame3)
bInit.place(relx=0.02,rely=9/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bInit.configure(command=initC)
bInit.configure(state=tk.DISABLED)
bInit.configure(text='Init class')

#button - load class from file
bLoadC=tk.Button(Frame3)
bLoadC.place(relx=0.35,rely=9/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bLoadC.configure(command=loadC)
bLoadC.configure(text='Load Class')

#button - set model parameters
bParams=tk.Button(Frame3)
bParams.place(relx=0.68,rely=9/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bParams.configure(command=params)
bParams.configure(state=tk.DISABLED)
bParams.configure(text='Set Params')

#button - set parameters of GA and MC fitting
bFitParams=tk.Button(Frame3)
bFitParams.place(relx=0.02,rely=(9+35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bFitParams.configure(command=fitParams)
bFitParams.configure(state=tk.DISABLED)
bFitParams.configure(text='Fit. Params')

#button - GA fitting
bFitGA=tk.Button(Frame3)
bFitGA.place(relx=0.35,rely=(9+35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bFitGA.configure(command=fitGA)
bFitGA.configure(state=tk.DISABLED)
bFitGA.configure(text='Fit GA')

#button - MC fitting
bFitDE=tk.Button(Frame3)
bFitDE.place(relx=0.68,rely=(9+35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bFitDE.configure(command=fitDE)
bFitDE.configure(state=tk.DISABLED)
bFitDE.configure(text='Fit DE')

#button - MC fitting
bCorr=tk.Button(Frame3)
bCorr.place(relx=0.02,rely=(9+2*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bCorr.configure(command=corrErr)
bCorr.configure(state=tk.DISABLED)
bCorr.configure(text='Corr. Err.')

#button - MC fitting
bFitMC=tk.Button(Frame3)
bFitMC.place(relx=0.35,rely=(9+2*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bFitMC.configure(command=fitMC)
bFitMC.configure(state=tk.DISABLED)
bFitMC.configure(text='Fit MCMC')

#button - info about MC/GA fitting
bInfoMC=tk.Button(Frame3)
bInfoMC.place(relx=0.68,rely=(9+2*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bInfoMC.configure(command=infoMC)
bInfoMC.configure(text='Info MC/GA')

#button - plot O-C with model
bPlot=tk.Button(Frame3)
bPlot.place(relx=0.02,rely=(9+3*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bPlot.configure(command=plot)
bPlot.configure(state=tk.DISABLED)
bPlot.configure(text='Plot O-C')

#button - plot residual O-C
bPlotR=tk.Button(Frame3)
bPlotR.place(relx=0.35,rely=(9+3*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bPlotR.configure(command=plotR)
bPlotR.configure(state=tk.DISABLED)
bPlotR.configure(text='Plot O-C res.')

#button - summary of fitting
bSum=tk.Button(Frame3)
bSum.place(relx=0.68,rely=(9+3*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bSum.configure(command=summary)
bSum.configure(state=tk.DISABLED)
bSum.configure(text='Summary')

#button - save model O-C
bSaveM=tk.Button(Frame3)
bSaveM.place(relx=0.02,rely=(9+4*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bSaveM.configure(command=saveM)
bSaveM.configure(state=tk.DISABLED)
bSaveM.configure(text='Save model')

#button - save residual O-C
bSaveR=tk.Button(Frame3)
bSaveR.place(relx=0.35,rely=(9+4*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bSaveR.configure(command=saveR)
bSaveR.configure(state=tk.DISABLED)
bSaveR.configure(text='Save O-C res.')

#button - save class to file
bSaveC=tk.Button(Frame3)
bSaveC.place(relx=0.68,rely=(9+4*35)/f3height,relheight=b1height/f3height,relwidth=b3width/f3width)
bSaveC.configure(command=saveC)
bSaveC.configure(state=tk.DISABLED)
bSaveC.configure(text='Save class')

#button - fitting on background
bRunBG=tk.Button(Frame3)
bRunBG.place(relx=0.02,rely=(9+5*35)/f3height,relheight=b1height/f3height,relwidth=b4width/f3width)
bRunBG.configure(command=runBG)
bRunBG.configure(state=tk.DISABLED)
bRunBG.configure(text='Fit on Background')

#buttom - save all
bSaveAll=tk.Button(Frame3)
bSaveAll.place(relx=0.53,rely=(9+5*35)/f3height,relheight=b1height/f3height,relwidth=b4width/f3width)
bSaveAll.configure(command=saveAll)
bSaveAll.configure(state=tk.DISABLED)
bSaveAll.configure(text='Save All')

#label
Label3=tk.Label(master)
Label3.place(relx=0.09,rely=1-24/mheight,relheight=l2height/mheight,relwidth=0.9)
Label3.configure(text='(c) Pavol Gajdos, 2018 - 2022')
Label3.configure(font=('None',9))

tk.mainloop()
