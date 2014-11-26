import random
import math
import feedback as fb
import matplotlib.pyplot as mp
import pvsioSocket as ps

#ps.debug = False
SWITCH_SENSITIVITY = 0.1
NOISE_SIGMA = 10

#class System (fb.Component):
#    def __init__(self):
#        self.xi = 0
#        self.m = 0.1 # internal multiplier (slope)
#        self.t = 0 # internal time counter, needed for adjusting slope

#    def work( self, u):
#        self.xi += u * self.m
#        if( (self.t % 9 == 0) and self.m < 10): 
#            self.m = abs(u) * self.m # m(t) -> x(t), slope should not be negative

#            #count number of digits in x
##            intx = int(self.xi)
##            if intx > 0:
##                digits = int(math.log10(intx))+1
##            elif intx == 0:
##                digits = 1
##            else:
##                digits = int(math.log10(-intx))+1 
##            
##            self.m = math.pow(10,digits-1)/10

#        if(u == 0):
#            self.m = 0.1
#        
#        print "m=",self.m
#        self.t += 1
#        
#        return self.xi


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
    def __init__( self, kp,k1,k2,xref, noise=True,delay=0):
        self.prev = xref
        self.kp = kp
        self.k1 = k1
        self.k2 = k2
 #       self.kc = 1
        self.u=0
        self.noise = noise
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

        #self.random.seed(42) # make sure each Controller object uses same random stream to compare

    def work( self, e):
        
        e += self._noise()  # Introduce noise, if any 
        
        print "Perceived error: " + str(e)   
        self.eplot.append(e)    

        self.d = ( e - self.prev )/fb.DT
        #return self.kp * math.copysign(1,e)  

        ## Begin - hybrid automation

        if self.reference[-1] > 100: # for large setpoints, use larger constant value for switch signal
            self.switch = 100
        else:
            self.switch = (SWITCH_SENSITIVITY*self.reference[-1]) # for small setpoints, switch signal changes proportionately 

        print "Switch signal: ", self.switch

        if (abs(e) > self.switch):
#            if (abs(self.u-self.p) > 0):
#                print "Z=0"
#                self.z = 0
#                self.p = self.u
        
#            if (self.z <= 0):
#                print "Z=1"
#                self.z = 1

#            self.u = self.z * (self.kp * ((self.k1 * math.copysign(1,e))-(self.k2*math.copysign(1,self.d))))
            self.u = self.kp * ((self.k1 * math.copysign(1,e))-(self.k2*math.copysign(1,self.d)))
        else: # |e(t)| <= switch signal
            self.square = not self.square # square wave
            print self.square

            if(self.square):
                self.u =  (self.kp * ((self.k1 * math.copysign(1,e))-(self.k2*math.copysign(1,self.d))))       
            else:
                self.u = 0
        
        ## End - hybrid automation
    
        self.prev = e

        print "self.u = ", self.u
        self.usignal.append(self.u)
        
        ##Delay
        print "self.usignal[-1] = ", self.usignal[-1]              
        if self.delay > 0:
            if len(self.usignal) < self.delay:
                return 0
            else:
                return self.usignal[-self.delay] #delay u(t) by x timesteps
        else:
            return self.u

    def _noise(self):
        if self.noise == False: return 0
        n = fb.DT*random.gauss( 0, self.sigma )
        print "Random:", n
        return n

        

def setpoint(t):
    #return 2.05
    return 56.7

fb.DT = 0.1
tm = 100 
c = Controller( 1, 5.5, 4.5, setpoint(0),noise=True,delay=3 )
c2 = Controller( 1, 5.5, 4.5, setpoint(0),noise=False )

#p = System()
#p2= System()
p = Device()
p2 = Device()

fb.closed_loop(setpoint, c, p, tm)
fb.closed_loop(setpoint, c2, p2, tm)


mp.plot(c.yplot,'r')
mp.plot(c.reference,'b')
mp.plot(c2.yplot,'c')
mp.plot(c2.reference,'m')
mp.show()

mp.plot(c.eplot,'r')
mp.step(c.usignal,'b')
mp.plot(c2.eplot,'c')
mp.step(c2.usignal,'m')
mp.show()

