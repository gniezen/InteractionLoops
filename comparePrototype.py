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
import numpy as np
import decimal


## Set up logging
#%(asctime)s 
logging.basicConfig(filename='compare.log',format='%(message)s', level=logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

SWITCH_SENSITIVITY = 0.1
NOISE_SIGMA = 10

tstart = datetime.now() # Used to calculcate time to run simulation
speed = [] # Used to calculcate average time to finish for iterations

# Set up graphs
with ppl.pretty:
    fig = mp.figure(figsize=(8,6))
    ax = fig.add_subplot(111)

if len(sys.argv) > 1:
    ref = float(sys.argv[1])
else:
    ref = 56.7 


class Device (fb.Component):
    def __init__(self):
        self.xi = 0
        self.prev = None
        self.ws = None
    
    def work( self, u):
        
        if(self.ws == None): 
            self.ws,self.prev = ps.connect(u) # connect to pvsio-web server       
        else:
            self.prev = ps.getDisplay(self.ws,u,self.prev) # Get displayed value from pvsio-web

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
        self.square = False # boolean toggle for square wave
        self.delay = delay
        self.usignal = []
        self.eplot = []
        self.xplot = []
        self.yplot =[]
        self.reference =[xref]
        self.h=signal.firwin(9, 0.1) # simple low-pass filter, FIR design using window method, 9 taps and 0.1 as cutoff
                                     # taps = Length of the filter (number of coefficients, i.e. the filter order + 1).
        self.noise = []
        self.crossings = 0
        self.last_sign = 1
        self.ended = False

        d = decimal.Decimal(str(xref))
        places = abs(d.as_tuple().exponent)
        if(places > 1):
            logging.debug("Setpoint has two decimal places")
            self.sigma = NOISE_SIGMA/10.0 # use smaller noise signal
           


    def work( self, e):
        
        # stop if target reached
        if(len(self.usignal)>0):
            if(e == 0 and self.usignal[-1] == 0):
                self.eplot.append(0);
                if self.ended == False:
                    logging.debug("Reached target value")
                    speed.append((len(self.usignal)-1)/4.0)
                    logging.debug("Speed: " + str(speed[-1]))
                    self.ended = True;
                return 0;

        logging.debug("Actual error: " + str(e))
        e += self._noise()  # Introduce noise, if any 
        
        logging.debug("Perceived error: " + str(e))   
        self.eplot.append(e)    

        self.d = ( e - self.prev )/fb.DT # First derivative
        self.d2 = (e - 2*self.prev + self.prev2)/((fb.DT)**2) # Second derivative

        logging.debug("First derivative: " +str (self.d))
        logging.debug("Second derivative: " + str(self.d2))

        # Count number of crossings
        if len(self.yplot) > 2:
            if( ((self.yplot[-2] > self.reference[-1]) and (self.yplot[-1] < self.reference[-1]))
                or ((self.yplot[-2] < self.reference[-1]) and (self.yplot[-1] > self.reference[-1])) ):
                    self.crossings +=1

        
        ## Begin - hybrid automation

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
                if((self.crossings > 2) and (abs(e) < 1.0)): #if overshot three times or more and the error is small, only use small chevron
                    self.u = self.kp * (self.k1 - self.k2) * math.copysign(1,e)
                else:                    
                    # This is the default behaviour
                    self.u =  (self.kp * ((self.k1 * math.copysign(1,e))-(self.k2 * math.copysign(1,self.d))))       
            else:
                self.u = 0
        
        ## End - hybrid automation
        
        # Record output signal
        self.usignal.append(self.u)
        
        # Introduce variable delay, but not for stepping behaviour
        if( (self.delay > 0) and (abs(self.prev) > self.switch)):
            varDelay = random.randint(1,self.delay)

            if varDelay > 0:
                if len(self.usignal) < varDelay:
                    self.u = 0
                else:
                    ##Delay
                    logging.debug("self.usignal[-%d] = %.2f ",varDelay, self.usignal[-varDelay])
                    self.u = self.usignal[-varDelay] #delay u(t) by x timesteps
                    
                    
        # If output signal has changed signs, first set to zero to simulate finger switching between buttons
        if ((self.u != 0) and (len(self.usignal) > 0)):
             self.sign = self.u / abs(self.u)

             if self.sign == -self.last_sign:
                 self.last_sign = self.sign
                 self.u = 0
                 self.usignal[-1]=self.u #replace previous recording of output signal
        
        
        #Record previous error to calculate derivatives
        self.prev2 = self.prev
        self.prev = e
        

        logging.debug("self.u = %.2f", self.u)
        return self.u


    def _noise(self):
        if self.hasNoise == False: 
            return 0

        self.noise.append(fb.DT*random.gauss( 0, self.sigma ))
        y=signal.lfilter( self.h, 1.0, self.noise)
        logging.debug("Random: %.2f", y[-1])
        return y[-1]


def setpoint(t):
    return ref

fb.DT = 0.1
tm = 160 

for i in range(0,33):
    
    c = Controller( 1, 5.5, 4.5, setpoint(0),hasNoise=True, delay=2)

    p = Device()

    fb.closed_loop(setpoint, c, p, tm)
    logging.debug("Crossings: " +str(c.crossings))

    newxplot = [x / 4.0 for x in c.xplot] # Each time step is 250ms
    
    ppl.plot(ax,newxplot,c.reference,'b')
    ppl.plot(ax,newxplot, c.yplot)

logging.debug("Time to run: " + str(datetime.now() - tstart))

speed = np.array(speed)
logging.debug("Mean: " + str(np.mean(speed)))
logging.debug("Standard deviation: " + str(np.std(speed)))
logging.info(str(setpoint(0))+","+str(np.mean(speed))+","+str(np.std(speed)))

mp.xlabel("Time (s)")
mp.ylabel("Displayed value")
mp.text(0.5,setpoint(0)+0.1,"Setpoint")         
fig = mp.gcf() # get current figure
fig.set_size_inches(11.69, 8.27)
#mp.show()
fig.savefig("compare/compareResults"+str(setpoint(0))+".pdf",format="pdf",papertype='a4',dpi=100)
mp.close()


