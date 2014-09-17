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

logging.basicConfig(filename='compare.log',format='%(asctime)s %(message)s', level=logging.DEBUG, filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

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
        self.prev2 = xref
        self.yprev = 1
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
        #self.signchanged = 0
        self.crossings = 0

    def work( self, e):
        
        # stop if target reached
        if(len(self.usignal)>0):
            if(e == 0 and self.usignal[-1] == 0):
                self.eplot.append(0);
                logging.debug("ENDED")
                return 0;

        logging.debug("Actual error: " + str(e))
        e += self._noise()  # Introduce noise, if any 
        
        logging.debug("Perceived error: " + str(e))   
        self.eplot.append(e)    

        self.d = ( e - self.prev )/fb.DT # First derivative
        self.d2 = (e - 2*self.prev + self.prev2)/((fb.DT)**2) # Second derivative

        logging.debug("First derivative: " +str (self.d))
        logging.debug("Second derivative: " + str(self.d2))

        if len(self.yplot) > 2:
            if( ((self.yplot[-2] > self.reference[-1]) and (self.yplot[-1] < self.reference[-1]))
                or ((self.yplot[-2] < self.reference[-1]) and (self.yplot[-1] > self.reference[-1])) ):
                    self.crossings +=1

        
        ## Begin - hybrid automation
        
        # Count number of crossings

        #if(self.crossings > 2):
        #    self.switch = 1000
        #    self.delay = 0
        

        if self.reference[-1] > 100: # for large setpoints, use larger constant value for switch signal
            self.switch = 100
        else:
            self.switch = (SWITCH_SENSITIVITY*self.reference[-1]) # for small setpoints, switch signal changes proportionately 
        logging.debug("Switch signal: %.2f", self.switch)

        if (abs(e) > self.switch):
            self.u = self.kp * ((self.k1 * math.copysign(1, e))-(self.k2 * math.copysign(1,self.d)))
        else: # |e(t)| <= switch signal
            self.square = not self.square # square wave

            if(self.square):

#                if(abs(self.signchanged)>0):
#                    logging.debug("USE SIGNCHANGED")
#                    self.u = self.signchanged
#                else:
#                    #when stepping, if the error changed signs, use a small step
#                    if((math.copysign(1,self.prev)+math.copysign(1,e)) == 0):
#                        self.signchanged=abs(self.k1-self.k2)*math.copysign(1,e)
#                        logging.debug("ERROR CHANGED SIGNS, SO U(T): " + str(self.signchanged))
#                    else:

                if((self.crossings > 2) and (e < 0.1)):
                    self.u = self.kp * (self.k1 - self.k2) * math.copysign(1,e)
                else:                    
                    # This is the default behaviour
                    self.u =  (self.kp * ((self.k1 * math.copysign(1,e))-(self.k2 * math.copysign(1,self.d))))       
            else:
                self.u = 0
        
        ## End - hybrid automation
    
        self.prev2 = self.prev
        self.prev = e
        logging.debug("self.u = %.2f", self.u)
        self.usignal.append(self.u)
        

        if(self.delay > 0):
            varDelay = random.randint(1,self.delay)

            if varDelay > 0:
                if len(self.usignal) < varDelay:
                    self.u = 0
                else:
                    ##Delay
                    logging.debug("self.usignal[-%d] = %.2f ",varDelay, self.usignal[-varDelay])
                    self.u = self.usignal[-varDelay] #delay u(t) by x timesteps

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
    
    c = Controller( 1, 5.5, 4.5, setpoint(0),hasNoise=True, delay=2)

    p = Device()

    fb.closed_loop(setpoint, c, p, tm)
    logging.debug("Crossings: " +str(c.crossings))


    ppl.plot(ax,c.xplot,c.reference,'b')
    ppl.plot(ax,c.xplot, c.yplot)

print datetime.now() - tstart

#mp.text(0.7,0.9,"Overshoot = "+str(overshoot),transform = ax.transAxes) 
#mp.title("Reference = "+ str(ref)+ " (" + str(i) + " trials)")           
fig.set_size_inches(11.69, 8.27)
mp.show()
fig.savefig("compareResults"+str(setpoint(0))+".pdf",format="pdf",papertype='a4',dpi=100)
mp.close()


