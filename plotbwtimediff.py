from __future__ import division
import sys
import math
# from pprint import pprint
import pylab as P
import numpy as np
from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties
from collections import defaultdict

bwobj = ['<0', '0>=to<=0.1', '0.1>to<=1', '1>to<=5', '5>to<=10', '>10']
# tobj = ['<-0.5Sec', '-0.5Sec>=to<-0.2Sec', '-0.2Sec>=to<-0.1Sec', '-0.1Sec>=to<=0.1Sec', '0.1Sec>to<=0.2Sec', '0.2Sec>to<=0.5Sec', '>0.5Sec']
tobj = ['<-0.2', '-0.2>=to<-0.1', '-0.1>=to<=0.1', '>0.1']

bwresults = {}
bwresults['mesh16gen']=[1979, 24818, 356, 48, 10, 10, 27221]
bwresults['mesh36gen']=[734, 30106, 398, 41, 5, 5, 31289]
bwresults['ring36gen']=[501, 30398, 358, 42, 7, 12, 31318]
bwresults['mesh16comp']=[1232, 7552, 883, 211, 41, 228, 10147]
bwresults['mesh36comp']=[631, 7905, 566, 73, 11, 20, 9206]
bwresults['ring36comp']=[475, 7959, 572, 56, 12, 9, 9083]

tresults = {}
tresults['mesh16gen']=[0, 2246, 24975, 0, 27221]
tresults['mesh36gen']=[0, 2570, 28719, 0, 31289]
tresults['ring36gen']=[0, 2538, 28780, 0, 31318]
tresults['mesh16comp']=[0, 1, 10146, 0, 10147]
tresults['mesh36comp']=[0, 0, 9206, 0, 9206]
tresults['ring36comp']=[0, 0, 9083, 0, 9083]

markers = ['^', '*', 'o', 'v']
font = FontProperties(size=12)
font_smaller = FontProperties(size=10)

plotlabels = []
plotlines = []

y_label = "% of DFGs"
F = P.figure()
AX1 = F.add_subplot(111)
AX1.set_ylabel(y_label, fontproperties=font)
AX1.set_xlabel("Data rate difference in Kbit/Sec", fontproperties=font)

ind = np.arange(len(bwobj))
width = 0.15
AX1.set_xticks(ind+0.40)
AX1.set_xticklabels(bwobj)
# for label in (AX1.get_xticklabels()):
#     label.set_fontsize(20)

mesh16gen = []
mesh36gen = []
ring36gen = []
mesh16comp = []
mesh36comp = []
ring36comp =[]

for i in range(0,len(bwobj)):
    mesh16gen.append(bwresults['mesh16gen'][i]*100/bwresults['mesh16gen'][len(bwobj)])
    mesh36gen.append(bwresults['mesh36gen'][i]*100/bwresults['mesh36gen'][len(bwobj)])
    ring36gen.append(bwresults['ring36gen'][i]*100/bwresults['ring36gen'][len(bwobj)])
    mesh16comp.append(bwresults['mesh16comp'][i]*100/bwresults['mesh16comp'][len(bwobj)])
    mesh36comp.append(bwresults['mesh36comp'][i]*100/bwresults['mesh36comp'][len(bwobj)])
    ring36comp.append(bwresults['ring36comp'][i]*100/bwresults['ring36comp'][len(bwobj)])

title_font = {'fontname':'Arial', 'size':'20', 'color':'black', 'weight':'normal', 'verticalalignment':'bottom'}

pl = AX1.bar(ind + 0*width, mesh16gen, width, color='blue')
plotlines.append(pl)
plotlabels.append("mesh16gen")
# F.text(0.7, 0.60, "mesh16gen", bbox=dict(facecolor='blue'))

pl = AX1.bar(ind + 1*width, mesh36gen, width, color='cyan')
plotlines.append(pl)
plotlabels.append("mesh36gen")
# F.text(0.7, 0.65, "mesh36gen", bbox=dict(facecolor='cyan'))

pl = AX1.bar(ind + 2*width, ring36gen, width, color='red')
plotlines.append(pl)
plotlabels.append("ring36gen")
# F.text(0.7, 0.70, "ring36gen", bbox=dict(facecolor='red'))

pl = AX1.bar(ind + 3*width, mesh16comp, width, color='magenta')
plotlines.append(pl)
plotlabels.append("mesh16comp")
# F.text(0.7, 0.75, "mesh16comp", bbox=dict(facecolor='magenta'))

pl = AX1.bar(ind + 4*width, mesh36comp, width, color='green')
plotlines.append(pl)
plotlabels.append("mesh36comp")
# F.text(0.7, 0.80, "mesh36comp", bbox=dict(facecolor='green'))

pl = AX1.bar(ind + 5*width, ring36comp, width, color='yellow')
plotlines.append(pl)
plotlabels.append("ring36comp")
# F.text(0.7, 0.85, "ring36comp", bbox=dict(facecolor='yellow'))

F.legend(plotlines, plotlabels, loc=(0.71,0.69), shadow=False, fancybox=True, prop=font_smaller, ncol=1)
AX1.set_ylim(ymin=0)
# AX1.set_yscale('log')
for tick in AX1.xaxis.get_major_ticks():
    tick.label1.set_fontsize(12)
for tick in AX1.yaxis.get_major_ticks():
    tick.label1.set_fontsize(12)

plotlabels = []
plotlines = []

y_label = "% of DFGs"
F = P.figure()
AX1 = F.add_subplot(111)
AX1.set_ylabel(y_label, fontproperties=font)
AX1.set_xlabel("Duration difference in Seconds", fontproperties=font)

ind = np.arange(len(tobj))
width = 0.15
AX1.set_xticks(ind+0.50)
AX1.set_xticklabels(tobj)

mesh16gen = []
mesh36gen = []
ring36gen = []
mesh16comp = []
mesh36comp = []
ring36comp =[]

for i in range(0,len(tobj)):
    mesh16gen.append(tresults['mesh16gen'][i]*100/tresults['mesh16gen'][len(tobj)])
    mesh36gen.append(tresults['mesh36gen'][i]*100/tresults['mesh36gen'][len(tobj)])
    ring36gen.append(tresults['ring36gen'][i]*100/tresults['ring36gen'][len(tobj)])
    mesh16comp.append(tresults['mesh16comp'][i]*100/tresults['mesh16comp'][len(tobj)])
    mesh36comp.append(tresults['mesh36comp'][i]*100/tresults['mesh36comp'][len(tobj)])
    ring36comp.append(tresults['ring36comp'][i]*100/tresults['ring36comp'][len(tobj)])

pl = AX1.bar(ind + 0*width, mesh16gen, width, color='blue')
plotlines.append(pl)
plotlabels.append("mesh16gen")
# F.text(0.2, 0.60, "mesh16gen", bbox=dict(facecolor='blue'))

pl = AX1.bar(ind + 1*width, mesh36gen, width, color='cyan')
plotlines.append(pl)
plotlabels.append("mesh36gen")
# F.text(0.2, 0.65, "mesh36gen", bbox=dict(facecolor='cyan'))

pl = AX1.bar(ind + 2*width, ring36gen, width, color='red')
plotlines.append(pl)
plotlabels.append("ring36gen")
# F.text(0.2, 0.70, "ring36gen", bbox=dict(facecolor='red'))

pl = AX1.bar(ind + 3*width, mesh16comp, width, color='magenta')
plotlines.append(pl)
plotlabels.append("mesh16comp")
# F.text(0.2, 0.75, "mesh16comp", bbox=dict(facecolor='magenta'))

pl = AX1.bar(ind + 4*width, mesh36comp, width, color='green')
plotlines.append(pl)
plotlabels.append("mesh36comp")
# F.text(0.2, 0.80, "mesh36comp", bbox=dict(facecolor='green'))

pl = AX1.bar(ind + 5*width, ring36comp, width, color='yellow')
plotlines.append(pl)
plotlabels.append("ring36comp")
# F.text(0.2, 0.85, "ring36comp", bbox=dict(facecolor='yellow'))

F.legend(plotlines, plotlabels, loc=(0.14,0.69), shadow=False, fancybox=True, prop=font_smaller, ncol=1)

AX1.set_ylim(ymin=0)
# AX1.set_yscale('log')
for tick in AX1.xaxis.get_major_ticks():
    tick.label1.set_fontsize(12)
for tick in AX1.yaxis.get_major_ticks():
    tick.label1.set_fontsize(12)


P.show()
P.savefig('aaa' + '.pdf', bbox_inches='tight')

