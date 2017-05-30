from __future__ import division
import sys
import math
import random
from cp_flex_fcfs import *
import time
from mininet.cli import CLI

# initialize
try:
    emulator = str(sys.argv[1])
except:
    emulator = "Mininet"

print "Info: Emulator " + emulator + " is used."

try:
    filename = str(sys.argv[2])
except:
    filename = 'Test_9_mesh.dat'

print "Info: The test will use topology specified in " + filename

cpf = CPFlex(filename, emulator=emulator)
# Create the network topology reading the input file
    # Create switch and the associated host and the link between them
    # Create edges i.e. connection between switches
# Start the network
#For testing how many ncat running
# cpf.clearFlows()

cpf.setupEmulationNetwork()
time.sleep(20)
# cpf.cn.output()
cpf.populateNetworkLinks()

tstart = time.time()
cpf.cpgreedy()
tend = time.time()

cpf.modifyRoutingTable()
cpf.generateTrafficFlow()

cpf.cn.output()

for n in cpf.cn.G.node:
    node = cpf.cn.G.node[n]
    pathToCLC = node['pathtoCLC']
    print n
    print pathToCLC
    # for clc, path in pathToCLC.items():
    #     src = clc
    #     dst = n
    #     hName = "h" + str(src)
    #     nw_dst = "10.0.0." + str(dst + 1)
    #     print cpf.TestbedNetwork.get_node(hName).cmd("ping -c 2 " + nw_dst)
    #     hName = "h" + str(dst)
    #     nw_src = "10.0.0." + str(src + 1)
    #     print cpf.TestbedNetwork.get_node(hName).cmd("ping -c 2 " + nw_src)

print cpf.ParentProcess
if emulator == "Mininet":
    # Mininet
    # cpf.TestbedNetwork.startTerms()
    CLI(cpf.TestbedNetwork)
elif emulator == "MaxiNet":
    # MaxiNet
    cpf.TestbedNetwork.CLI(locals(), globals())
else:
    print("Error: Emulator missing!")
    exit(1)
cpf.TestbedNetwork.stop()

print "State: " + cpf.state
if cpf.state == "NOT SOLVED":
    print "Remaining nodes: " + str([i for i in cpf.cn.V if not i in cpf.Controlled])
print "CRCs: " + str(len(cpf.CRCs))
print str(cpf.CRCs)
print "CLCs: " + str(len(cpf.CLCs)) + " (out of " + str(len(cpf.cn.C)) + " available)"
print str(cpf.CLCs)
print "Flows satisfied: " + str(len(cpf.Satisfied)) + " out of " + str(len(cpf.cn.F))
print "Runtime: " + str(tend - tstart) + " seconds"

