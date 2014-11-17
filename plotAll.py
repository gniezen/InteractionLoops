import matplotlib
import matplotlib.pyplot as plt
import numpy as np

numbers = [1.01,
1.03,
11.1,
12.5,
1.38,
2.05,
2.08,
21.7,
24.9,
2.5,
40.8,
43.7,
4.5,
45.8,
5.05,
5.5,
56.7,
5.9,
62.5,
6.7]

x = [str(i) for i in numbers]

pop1mean = [9.059333333,
10.67236364,
15.61734615,
17.5487,
12.81172727,
14.00351515,
14.90254545,
20.74972727,
19.55693939,
14.34684848,
17.28763636,
19.72033333,
13.07706061,
19.8810303,
16.8240303,
15.83972727,
19.68215152,
16.36039394,
21.0790303,
18.15163636]

pop1std = [3.149369794,
5.968346885,
5.519978107,
6.441923941,
4.097239169,
3.78530364,
4.73980132,
9.361751896,
6.773668904,
4.827362534,
5.97054147,
4.862836195,
4.369869799,
6.553998957,
8.570198178,
5.50045027,
5.872718333,
5.045087613,
9.523248626,
7.679642482]

pop2mean = []
pop2std = []
text_file = open("compare.log","r")
lines = text_file.readlines()
for i in lines:
    vals = i.split(',')
    print vals
    pop2mean.append(float(vals[1]))
    pop2std.append(float(vals[2]))

#pop2mean = [23.8333333333,
#18.875,
#18.6893939394,
#19.4393939394,
#24.1875,
#22.625,
#20.0,
#18.8787878788,
#17.046875,
#14.21875,
#19.0303030303,
#19.3560606061,
#13.6583333333,
#21.553030303,
#31.975,
#16.296875,
#20.7575757576,
#16.6818181818,
#22.7045454545,
#16.8671875]

#pop2std = [10.5323575497,
#8.625,
#5.46130683628,
#4.85471900344,
#7.2551167289,
#8.375,
#4.87767020889,
#4.63277242577,
#5.25685471403,
#6.97561321229,
#4.18771542899,
#4.75618827481,
#4.66301196176,
#5.50060519252,
#5.40537926514,
#6.18795373968,
#4.95069816338,
#7.36938608296,
#3.11913361214,
#6.14250825924]

N = 20

ind = np.arange(N)  # the x locations for the groups
width = 0.35       # the width of the bars

font = {'size'   : 22}
matplotlib.rc('font', **font)

fig, ax = plt.subplots()
rects1 = ax.bar(ind, pop1mean, width, color='#3498db', yerr=pop1std)
rects2 = ax.bar(ind+width, pop2mean, width, color='#d35400', yerr=pop2std)

# add some text for labels, title and axes ticks
ax.set_ylabel('Mean time to finish (s)')
ax.set_xlabel('Number used in trials')
#ax.set_title('Comparing simulation to lab study over 33 trials for 20 different numbers')
ax.set_xticks(ind+width)
ax.set_xticklabels(x)

ax.xaxis.set_ticks_position('bottom')
ax.yaxis.set_ticks_position('left')
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)

ax.legend( (rects1[0], rects2[0]), ('Lab study', 'Simulation') )

def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                ha='center', va='bottom')

#autolabel(rects1)
#autolabel(rects2)

plt.show()


