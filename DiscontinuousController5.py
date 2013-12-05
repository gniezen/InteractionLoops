import random
import math
import feedback as fb
import matplotlib.pyplot as mp
from scipy import signal
import numpy as np

xplot = []
yplot =[]
uplot =[]
class System (fb.Component):
    def __init__(self):
        self.xi = 0
        self.m = 0.1 # internal multiplier (slope)
        self.t = 0 # internal time counter, needed for adjusting slope

    def work( self, u):
        self.xi += u * self.m
        if( (self.t % 9 == 0) and (abs(self.xi) <= 100)):
            self.m = u * self.m # m(t) -> x(t)

        if(u == 0):
            self.m = 0.1

        self.t += 1
        
        return self.xi



class Controller(fb.Component):
    def __init__( self, kp,k1,k2,xref, noise=True):
        self.prev = xref
        self.kp = kp
        self.k1 = k1
        self.k2 = k2
        self.kc = 1
        self.u=0
        self.noise = noise
        self.sigma = 5
        self.z = 1
        self.p = 0
        self.square = False # boolean toggle for square wave

    def work( self, e):
        

        e += self._noise()  # Introduce noise, if any 
        
        print "Perceived error: " + str(e)   
        yplot.append(e)    

        self.d = ( e - self.prev )/fb.DT
        #return self.kp * math.copysign(1,e)  

        if (e > 100):
            if (self.u-self.z > 0):
                self.z = 0
                self.p = self.u
        
            if (self.z <= 0):
                self.z = 1

            self.u = self.z * (self.kp * ((self.k1 * math.copysign(1,e))-(self.k2*math.copysign(1,self.d)))) 
        else: # e(t) <= 100
            self.square = not self.square
            print self.square

            if(self.square):
                self.u = self.kc * math.copysign(1,e)        
            else:
                self.u = 0
    
        self.prev = e

        uplot.append(self.u)
                      
        return self.u

    def _noise( self ):
        if self.noise == False: return 0
        
        return fb.DT*random.gauss( 0, self.sigma )
        

# ============================================================    

#def closed_loop( c, p, tm=5000):
#    def setpoint( t ):
#        return 810
#    
#    y = 0 
#    for t in range( tm ):
#        r = setpoint(t)
#        
#        e = r - y

#        u = c.work(e,t)
#        y = p.work(u,t)

#        print t, r, e, u, y
#        xplot.append(t)
#        yplot.append(y)
#        ytarget.append(setpoint(t))

# ============================================================

def setpoint(t):
    return 810

fb.DT = 0.1
tm = 50 
c = Controller( 1, 5.5, 4.5, 810,noise=False )
p = System()

fb.closed_loop(setpoint, c, p, tm)
mp.plot(yplot,'r')
mp.step(uplot,'b')
mp.show()

