from __future__ import division
import sys
import math
#from pprint import pprint
import pylab as P
from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties
from collections import defaultdict

def loadlevel(i): # time i is provided in seconds
	#i = (i/3600) % 24 # switch from seconds to day time
	i = i % 24
	if i <= 3:
		return 0.9*(-1/27*pow(i,2)+1)
	elif i <= 6:
		return 0.9*(1/27*pow(i-6,2)+1/3)
	elif i <= 15:
		return 0.9*(1/243*pow(i-6,2)+1/3)
	else:
		return 0.9*(-1/243*pow(i-24,2)+1)

font = FontProperties(size=28)
font_smaller = FontProperties(size=18)
F = P.figure()
AX1 = F.add_subplot(111)
AX1.set_xticks([6.0*i for i in range(0,5)])
x = [i/3600 for i in range(0,86401)]
pl = AX1.plot(x, [loadlevel(i) for i in x], lw=1)
AX1.set_xlim(0,24)
AX1.set_ylim(0,1.0)
AX1.set_xlabel("day time (hours)", fontproperties=font)
AX1.set_ylabel("load level", fontproperties=font)
for tick in AX1.xaxis.get_major_ticks():
	tick.label1.set_fontsize(24)
for tick in AX1.yaxis.get_major_ticks():
	tick.label1.set_fontsize(24)
P.savefig("loadlevel.pdf", bbox_inches='tight')
P.show()