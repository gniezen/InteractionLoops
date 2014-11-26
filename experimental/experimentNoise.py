import matplotlib.pyplot as mp
import random
import numpy as np
from scipy import signal

n = []
y = []
tm=100

# provide them to firwin
h=signal.firwin(6, 0.1)


alpha = 0.1

for i in range(0,tm):
    n.append(0.1*random.gauss( 0, 10 ))
    
    #y = signal.wiener(n,mysize=55)
    y=signal.lfilter( h, 1.0, n)
    
t = range(0,tm)
mp.plot(t,n,'r')
mp.plot(t,y,'b')
mp.show()
