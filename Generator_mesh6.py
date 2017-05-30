from __future__ import division
from time import *
from math import exp,sqrt,pow
from ChModel import *
import sys, random, os

class Basestation:
	pass
class Link:
	pass
class Flow:
	pass

# initialize

try: 
	dim1 = int(sys.argv[1])
except:
	print("Error: dimension missing!")
	exit(1)
	
try: 
	dim2 = int(sys.argv[2])
except:
	dim2 = dim1
	
no_bs = dim1 * dim2

try:
	no_flows = int(sys.argv[3])
except:
	no_flows = no_bs
	
try: 
	instance = str(sys.argv[4])
except:
	instance = str(time())

try:
	if not os.path.exists(os.path.dirname(instance)):
		os.makedirs(os.path.dirname(instance))
except:
	pass
	
dist = 1000.0
sdev = 0.125
contrProb = 0.6
r_con = 1.5
SingleConnectionFlowProcessing = True

while True:
	no_links = 0
	BSs = []
	Links = []
	Flows = []
	W = [[0 for x in xrange(no_bs)] for x in xrange(no_flows)]

	# generate nodes

	for i in range(0, dim1):
		for j in range(0, dim2):
			
			bs = Basestation()
			bs.name = i * dim2 + j
			bs.index = i * dim2 + j
			
			c = random.random()
			if c < contrProb:
				bs.isContr = 1
			else:
				bs.isContr = 0			
				
			bs.b_max = 1.0e9 # earlier 5.0e9
			bs.p_own = 4.0e10 # earlier 2.0e11
			bs.x = i * dist + random.gauss(0,dist*sdev)
			bs.y = j * dist + random.gauss(0,dist*sdev)
			
			bs.isConnected = 0
			
			BSs.append(bs)
			
	# generate edges
			
	for k in range(0, no_bs):
		for l in range(k, no_bs):                                                                                                                                                                                                       
		
			s = sqrt(pow(BSs[k].x - BSs[l].x, 2) + pow(BSs[k].y - BSs[l].y, 2))
			
			if k != l and s < r_con * dist:
				l1 = Link()
				l2 = Link()
				l1.start = k
				l1.end = l
				l2.start = l
				l2.end = k
				l1.b_cap = 0.5e9 # earlier 2.5e9 Set the bandwidth of link for MaxiNet (500Mbits)
				l2.b_cap = 0.5e9  # earlier 2.5e9 Set the bandwidth of link for MaxiNet (500Mbits)
				l1.l_cap = s * 1.45 / 299792458.0
				l2.l_cap = s * 1.45 / 299792458.0
				Links.append(l1)
				Links.append(l2)
				no_links = no_links + 2
				BSs[k].isConnected = 1
				BSs[l].isConnected = 1
				
	if sum(bs.isConnected for bs in BSs) == no_bs:
		break
	else:
		print "Warning: Graph not connected!"
			
# generate flows

ftypes = []
ftypedata = {}
fin = open("flowtypes.csv", "r")
tmp = fin.readline()
while True:
	try:
		tmp = fin.readline().split(";")
		if len(tmp[0]) == 0:
			break
		ftypes.append(tmp[0])
		ftypedata[tmp[0]] = {}
		ftypedata[tmp[0]]['prob'] = float(tmp[1])
		ftypedata[tmp[0]]['bflowlbound'] = float(tmp[2])
		ftypedata[tmp[0]]['bflowubound'] = float(tmp[3])
		ftypedata[tmp[0]]['lflow'] = float(tmp[4])
	except:
		break

if sum(ftypedata[type]['prob'] for type in ftypes) < 0.999 or sum(ftypedata[type]['prob'] for type in ftypes) > 1.001:
	print("ERROR: flow probabilities don't sum up to 1.0!")
	exit(1)

for i in range(0, no_flows):

	f = Flow()
	f.name = i
	f.index = i
	sinr_insufficient = True
	
	while (sinr_insufficient):
		f.x = random.uniform(-dist, dim1 * dist)
		f.y = random.uniform(-dist, dim2 * dist)
		f.connections = 0
		
		rspw = []
		for bs in BSs:
			s = sqrt(pow(bs.x - f.x, 2) + pow(bs.y - f.y, 2))
			rspw.append([bs,received_signal_power_watts(s),s])
			
		rspw.sort(key=lambda rspw: rspw[1], reverse=True)
		
		wattsum = rspw[0][1]
		f.connections += 1
		while (sinr(rspw, f.connections, no_bs) < -7.5 and f.connections < min(3, no_bs)):
			f.connections += 1
		
		if (sinr(rspw, f.connections, no_bs) >= -7.5):
			sinr_insufficient = False
			
	for j in range(0, f.connections):
		W[i][rspw[j][0].index] = 1
		
	c = random.random()
	pcheck = 0.0
	
	for type in ftypes:
		f.type = type
		pcheck += ftypedata[type]['prob']
		if pcheck > c:
			break
	
	d = random.random()
	f.b_flow = d * (ftypedata[f.type]['bflowubound'] - ftypedata[f.type]['bflowlbound']) + ftypedata[f.type]['bflowlbound']
	f.l_flow = ftypedata[f.type]['lflow']
	Flows.append(f)

# generate output
	
fout = open(instance, "w")	
fout.write("set V := ")
for bs in BSs:
	fout.write(str(bs.name) + " ")
fout.write(";\n")

fout.write("set C := ")
for bs in BSs:
	if bs.isContr == 1:
		fout.write(str(bs.name) + " ")
fout.write(";\n")

fout.write("set F := ")
for f in Flows:
	if SingleConnectionFlowProcessing or f.connections > 1:
		fout.write(str(f.name) + " ")
fout.write(";\n")

fout.write("set E := ")
for l in Links:
	fout.write("(" + str(l.start) + "," + str(l.end) + ") ")
fout.write(";\n\n")

fout.write("param : b_max p_own bx by :=\n")
for bs in BSs:
	if bs.isContr == 1:
		fout.write(str(bs.name) + " " + str(bs.b_max) + " " + str(bs.p_own) + " " + str(bs.x) + " " + str(bs.y) + "\n")
	else: 
		fout.write(str(bs.name) + " 0 0 " + str(bs.x) + " " + str(bs.y) + "\n")
fout.write(";\n")

fout.write("param : b_cap l_cap :=\n")
for l in Links:
	fout.write(str(l.start) + " " + str(l.end) + " " + str(l.b_cap) + " " + str(l.l_cap) + "\n")
fout.write(";\n")

if no_flows > 0:
	if SingleConnectionFlowProcessing or sum(f.connections for f in Flows) > no_flows:
		fout.write("param : b_flow l_flow fx fy :=\n")
		for f in Flows:
			if SingleConnectionFlowProcessing or f.connections > 1:
				fout.write(str(f.name) + " " + str(f.b_flow) + " " + str(f.l_flow) + " " + str(f.x) + " " + str(f.y) + "\n")
		fout.write(";\n")

fout.write("param : b_CLC := 1e5 ;\n")
fout.write("param : b_CRC := 1e5 ;\n")
fout.write("param : l_CLC := 1e-3 ;\n")
fout.write("param : l_CRC := 1e-2 ;\n")
fout.write("param : p_CLC := 1e6 ;\n")
fout.write("param : p_CRC := 1e6 ;\n")
fout.write("\n")
fout.write("param : bigM := 100000 ;\n")
fout.write("\n")
fout.write("param : m_CRC := 1 ;\n")
fout.write("param : m_CLC := 1 ;\n")
m_W = 3 * no_bs
fout.write("param : m_W := " + str(m_W) + " ;\n")
fout.write("param : m_b := 0 ;\n")
fout.write("param : dist := " + str(dist) + " ;\n")
fout.write("param : dim1 := " + str(dim1) + " ;\n")
fout.write("param : dim2 := " + str(dim2) + " ;\n")

if no_flows > 0:
	if SingleConnectionFlowProcessing or sum(f.connections for f in Flows) > no_flows:
		fout.write("\n")
		fout.write("param : W :=\n")
		for f in Flows:
			if SingleConnectionFlowProcessing or f.connections > 1:
				for bs in BSs:
					fout.write(str(f.name) + " " + str(bs.name) + " " + str(W[f.index][bs.index]) + "\n")
		fout.write(";\n")
		
fout.close()

print "Generated: " + instance