import random
import math
import feedback as fb
import matplotlib.pyplot as mp

xplot = []
yplot =[]

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
        self.u=0
        self.noise = noise
        self.sigma = 50

    def work( self, e):

        e += self._noise()  # Introduce noise, if any 
        
        print "Perceived error: " + str(e)   
        yplot.append(e)    

        self.d = ( e - self.prev )/fb.DT
        #return self.kp * math.copysign(1,e)  

        self.u = (self.kp * ((self.k1 * math.copysign(1,e))-(self.k2*math.copysign(1,self.d)))) 
        self.prev = e
                      
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
c = Controller( 1, 5.5, 4.5, 810,noise=True )
p = System()

fb.closed_loop(setpoint, c, p, tm)
mp.plot(yplot,'r')
mp.show()

