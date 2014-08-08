import os, sys
import random
import math
import feedback as fb
import matplotlib.pyplot as mp
import pvsioSocket as ps
import prettyplotlib as ppl
from datetime import datetime
import logging
from scipy import signal

logging.basicConfig(level=logging.DEBUG)

SWITCH_SENSITIVITY = 0.1
NOISE_SIGMA = 10

tstart = datetime.now()

with ppl.pretty:
    fig = mp.figure()
    ax = fig.add_subplot(111) 

class Device (fb.Component):
    def __init__(self):
        self.xi = 0
        self.prev = None
        self.ws = None
    
    def work( self, u):
        
        if(self.ws == None): # not connected to server yet
            self.ws,self.prev = ps.connect(u)         
        else:
            self.prev = ps.getDisplay(self.ws,u,self.prev)

        self.xi = self.prev['left_display']
        
        return self.xi



class Controller(fb.Component):
    def __init__( self, kp,k1,k2,xref, hasNoise=True,delay=0):
        self.prev = xref
        self.kp = kp
        self.k1 = k1
        self.k2 = k2
        self.u=0
        self.hasNoise = hasNoise
        self.sigma = NOISE_SIGMA
        self.z = 1
        self.p = 0
        self.square = False # boolean toggle for square wave
        self.delay = delay
        self.usignal = []
        self.eplot = []
        self.xplot = []
        self.yplot =[]
        self.reference =[xref]
        self.h=signal.firwin(6, 0.1) # simple low-pass filter, FIR design using window method, 15 taps and 0.1 as cutoff
        self.noise = []

    def work( self, e):

        e += self._noise()  # Introduce noise, if any 
        
        logging.debug("Perceived error: " + str(e))   
        self.eplot.append(e)    

        self.d = ( e - self.prev )/fb.DT
        
        ## Begin - hybrid automation

        if self.reference[-1] > 100: # for large setpoints, use larger constant value for switch signal
            self.switch = 100
        else:
            self.switch = (SWITCH_SENSITIVITY*self.reference[-1]) # for small setpoints, switch signal changes proportionately 
        logging.debug("Switch signal: %.2f", self.switch)

        if (abs(e) > self.switch):
            self.u = self.kp * ((self.k1 * math.copysign(1,e))-(self.k2*math.copysign(1,self.d)))
        else: # |e(t)| <= switch signal
            self.square = not self.square # square wave

            if(self.square):
                self.u =  (self.kp * ((self.k1 * math.copysign(1,e))-(self.k2*math.copysign(1,self.d))))       
            else:
                self.u = 0
        
        ## End - hybrid automation
    
        self.prev = e
        logging.debug("self.u = %.2f", self.u)
        self.usignal.append(self.u)
        
        ##Delay
        logging.debug("self.usignal[-1] = %.2f ", self.usignal[-1])
        if self.delay > 0:
            if len(self.usignal) < self.delay:
                self.u = 0
            else:
                self.u = self.usignal[-self.delay] #delay u(t) by x timesteps


        return self.u

    def _noise(self):
        if self.hasNoise == False: return 0
        if(random.random()*100 < 80):
            return 0;
        self.noise.append(fb.DT*random.gauss( 0, self.sigma ))
        y=signal.lfilter( self.h, 1.0, self.noise)
        logging.debug("Random: %.2f", y[-1])
        return y[-1]

        

def setpoint(t):
    #return 2.05
    return 56.7

fb.DT = 0.1
tm = 100 

for i in range(0,33):
    
    c = Controller( 1, 5.5, 4.5, setpoint(0),hasNoise=True, delay=2 )

    p = Device()

    fb.closed_loop(setpoint, c, p, tm)


    ppl.plot(ax,c.xplot,c.reference,'b')
    ppl.plot(ax,c.xplot, c.yplot)

print datetime.now() - tstart

#mp.text(0.7,0.9,"Overshoot = "+str(overshoot),transform = ax.transAxes) 
#mp.title("Reference = "+ str(ref)+ " (" + str(i) + " trials)")           
fig.set_size_inches(11.69, 8.27)
mp.show()
fig.savefig("compareResults"+str(setpoint(0))+".pdf",format="pdf",papertype='a4',dpi=100)
mp.close()

