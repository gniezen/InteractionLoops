import random
import math
import matplotlib.pyplot as mp

xplot = []
yplot =[]

class System:
    def __init__(self):
        self.x = 0
        self.m = 1

    def work( self, u, t):
        self.x += u * self.m
        if( (t % 9 == 0) and (self.x <= 100)):
            self.m = self.x

        if(u == 0):
            self.m = 10
        
        return self.x

class Controller:
    def __init__( self, kp):
        self.kp = kp

    def work( self, e, t ):
        return self.kp * math.copysign(1,e)                        

# ============================================================    

def closed_loop( c, p, tm=5000 ):
    def setpoint( t ):
        return 814
    
    y = 0 
    for t in range( tm ):
        r = setpoint(t)
        e = r - y

        u = c.work(e,t)
        y = p.work(u,t)

        print t, r, e, u, y
        xplot.append(t)
        yplot.append(y)

# ============================================================

c = Controller( 1 )
p = System()

closed_loop( c, p, 30 )
mp.plot(xplot,yplot)
mp.show()
