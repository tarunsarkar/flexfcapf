from __future__ import division
import sys, math, random, time, pdb
from math import exp, sqrt, pow
from cp_flex_fcfs import *
import datetime
import thread
from mininet.cli import CLI

import os
# We want to traffic pattern of whole 24 hours in 2 hours so here assuming a hours has only 300 sec
def loadlevel(i,scaling=1):  # time i is provided in seconds, scaling if necessary, default is 1
    i = 24 * (i / 3600) % 24  # switch from seconds to day time
    if i <= 3:
        return 0.9 * (-1 / 27 * pow(i, 2) + 1) * scaling
    elif i <= 6:
        return 0.9 * (1 / 27 * pow(i - 6, 2) + 1 / 3) * scaling
    elif i <= 15:
        return 0.9 * (1 / 243 * pow(i - 6, 2) + 1 / 3) * scaling
    else:
        return 0.9 * (-1 / 243 * pow(i - 24, 2) + 1) * scaling


def output(cpf, trun=None):
    print "State: " + cpf.state
    if cpf.state == "NOT SOLVED":
        print "Remaining nodes: " + str([i for i in cpf.cn.V if not i in cpf.Controlled])
    print "CRCs: " + str(len(cpf.CRCs))
    print str(cpf.CRCs)
    print "LCAs: " + str(len(cpf.CLCs)) + " (out of " + str(len(cpf.cn.C)) + " available)"
    print str(cpf.CLCs)
    print "Flows satisfied: " + str(len(cpf.Satisfied)) + " out of " + str(len(cpf.cn.F))
    if trun is not None:
        print "Runtime: " + str(trun) + " seconds"


def slimoutput(cpf, trun=None):
    if cpf.state == "NOT SOLVED":
        print "State: " + cpf.state + ", Remaining nodes: " + str(
            len([i for i in cpf.cn.V if not i in cpf.Controlled])) + " out of " + str(len(cpf.cn.V))
    else:
        print "State: " + cpf.state
    print "CRCs: " + str(len(cpf.CRCs)) + ", CLCs: " + str(len(cpf.CLCs)) + " (out of " + str(
        len(cpf.cn.C)) + " available), Control ratio: " + str(cpf.CLCcontrolRatio()) \
          + ", Average load: " + str(cpf.getAverageCLCload())
    print "Latest CRCs: " + str(cpf.CRCs) + " and , CLCs: " + str(cpf.CLCs)
    print "Flows satisfied: " + str(len(cpf.Satisfied)) + " out of " + str(len(cpf.cn.F))
    if trun is not None:
        print "Runtime: " + str(trun) + " seconds"


def simstep(cpf, calctime, realtime):
    tmpCLCs = list(cpf.CLCs)
    tstart = time.time()
    cpf.cpgreedy()
    tend = time.time()
    trun = tend - tstart
    nodeDiff = cpf.newCLCcontrols
    flowDiff = cpf.newFlowSats

    CLCDiff = len(set(cpf.CLCs) - set(tmpCLCs))

    # print "Start Adding routing entry:" + str(time.time())
    cpf.modifyRoutingTable()
    # print "End Adding routing entry:" + str(time.time())
    # print "Start the iperf client:" + str(time.time())
    iperfcount = cpf.generateTrafficFlow()
    # print "End the iperf client:" + str(time.time())
    tnetmodend = time.time()
    tnetrun = tnetmodend - tend

    if display_output:
        print "Time: " + str(calctime)
        print "System Time Passed: " + str(realtime)
        slimoutput(cpf, trun)
        print "\n"

    if graph_output:
        cpf.cn.output()

    global graph_output_once
    if graph_output_once:
        graph_output_once = False
        cpf.cn.output(results_path + '/graph_fcfs_' + filename[:-4] + '.pdf')
        if only_graph_output:
            exit(1)

    if results_output and t >= 0:
        foutmain = open(results_filename, "a")
        foutmain.write(str(calctime) + " " + str(len(cpf.cn.F)) + " " + str(len(cpf.Satisfied)) + " " + str(len(cpf.CRCs)) + " " + str(len(cpf.CLCs)) + " " + str(CLCDiff) + " " + str(nodeDiff) + " " + str(flowDiff) \
                       + " " + str(cpf.getAverageCRCpathlength()) + " " + str(cpf.getAverageCLCpathlength()) + " " + str(cpf.getAverageCLCload()) + " " + str(cpf.CLCcontrolRatio()) + " " + str(trun) + " " + str(tnetrun) + " " + str(iperfcount)\
            #            + " " + str(len(cpf2.Satisfied)) + " " + str(len(cpf2.CRCs)) + " " + str(
            # len(cpf2.CLCs)) + " " + str(CLCDiff2) + " " + str(nodeDiff2) + " " + str(flowDiff2) \
            #            + " " + str(cpf2.getAverageCRCpathlength()) + " " + str(
            # cpf2.getAverageCLCpathlength()) + " " + str(cpf2.getAverageCLCload()) + " " + str(
            # cpf2.CLCcontrolRatio()) + " " + str(trun2)
                       + " \n")
        foutmain.close()

# initialize
try:
    emulator = str(sys.argv[1])
except:
    emulator = "Mininet"

print "Info: Emulator " + emulator + " is used."

try:
    sim_duration = int(sys.argv[2])
except:
    sim_duration = 600

print "Info: The test will run for " + str(sim_duration) + " seconds"

try:
    filename = str(sys.argv[3])
except:
    filename = 'Test_9_mesh.dat'


print "Info: The test will use topology specified in " + filename

time.sleep(10)


# sim_duration = 7200
stdll = 0.9
lltimeframe = 10.0
# filename = 'Test_9_mesh.dat'
results_path = 'Simulation_Results'
results_filename = results_path + '/emu_results_pfo_fcfs_' + str(stdll) + '_' + str(lltimeframe) + '_' + filename
display_output = True
graph_output = False
results_output = True
graph_output_once = False
only_graph_output = False

# cpf = CPFlex(filename, emulator=emulator)
cpf = CPFlex(filename, emulator=emulator, evalscen="CoMP")
cpf.flexOperation = True
cpf.clearFlows()
no_nodes = len(cpf.cn.V)

cpf.setupEmulationNetwork()
time.sleep(20)
cpf.populateNetworkLinks()
time.sleep(10)

if results_output:
    foutmain = open(results_filename, "a")
    foutmain.write(
        "time #flows #Satisfied #CRCs #CLCs #CLCDiff #nodeDiff #flowDiff CRCpathlength CLCpathlength CLCload controlRatio runtime netmodtime #flowGen" \
        # + "#SatisfiedScratch #CRCsScratch #CLCsScratch #CLCDiffScratch #nodeDiffScratch #flowDiffScratch CRCpathlengthScratch CLCpathlengthScratch CLCloadScratch controlRatioScratch runtimeScratch" \
        + "\n")
    foutmain.close()

t = 0.0 #-3600.0
tlast = t
perform_simstep = False
CLCloadlimit = stdll
lastdisp = 0.0 #-3600.0
calctime = 0.0 #-3600.0
fremhelp = {}
blacklist = []
llalarm = False
# ll_scale = 0.20
ll_scale = 0.02
lambdamax = max([loadlevel(i, ll_scale) for i in range(0, 25)]) * no_nodes

rejectedFlows = 0
remcount = 0
addcount = 0
lastsleeptime = 0
starttime = time.time()
lastcontr = 0
stt = datetime.datetime.now()

while t < sim_duration:
    t1 = datetime.datetime.now()
    nextvar = random.expovariate(lambdamax)
    t += nextvar
    c = random.random()
    if c < loadlevel(t, ll_scale) * no_nodes / lambdamax:
        d = random.expovariate(0.02)

        bltmp = list(blacklist)
        for f in bltmp:
            if f in cpf.cn.fdata:
                if cpf.cn.fdata[f]['isSat']:
                    blacklist.remove(f)
                else:
                    tt1 = time.time()
                    iflowend = cpf.cn.fdata[f]['stime'] + cpf.cn.fdata[f]['duration']
                    fremindex = math.ceil(iflowend + t - tlast)
                    if tt1 < iflowend + t - tlast:
                    # if math.ceil(iflowend) in fremhelp and math.ceil(iflowend) < math.ceil(iflowend + t - tlast) and f in fremhelp[math.ceil(iflowend)]:
                        fremhelp[math.ceil(iflowend)].remove(f)
                        if not fremindex in fremhelp:
                            fremhelp[fremindex] = []
                        cpf.cn.fdata[f]['fremindex'] = fremindex
                        fremhelp[fremindex].append(f)
                    cpf.cn.fdata[f]['stime'] = t

        for i in range(int(math.ceil(tlast)), int(math.ceil(t))):
            if i in fremhelp:
                tmp = list(fremhelp[i])
                for f in tmp:
                    tt1 = time.time()
                    iperfend = cpf.cn.fdata[f]['genstime'] + cpf.cn.fdata[f]['duration']
                    #print "First for :1:" + "i:" + str(i) + " genstime:" + str(cpf.cn.fdata[f]['genstime']) + " duration:" + str(cpf.cn.fdata[f]['duration'])
                    fremindex = math.ceil(iperfend - starttime)
                    if cpf.cn.fdata[f]['isGen'] == True and tt1 < iperfend and t < iperfend - starttime:
                        if not fremindex in fremhelp:
                            fremhelp[fremindex] = []
                        cpf.cn.fdata[f]['fremindex'] = fremindex
                        fremhelp[fremindex].append(f)
                    elif cpf.cn.fdata[f]['isGen'] == False:
                        print "First elif :1:" + "isSat:" + str(cpf.cn.fdata[f]['isSat']) + " isGen:" + str(cpf.cn.fdata[f]['isGen']) + " tt1:" + str(tt1) + " t:" + str(t) + " iperfend:" + str(iperfend)
                        cpf.remFlow(f, stopiperf=False)
                        remcount += 1
                    else:
                        cpf.remFlow(f, stopiperf=False)
                        remcount += 1
                del fremhelp[i]
        if math.ceil(t) in fremhelp:
            tmp = list(fremhelp[math.ceil(t)])
            for f in tmp:
                # if cpf.cn.fdata[f]['stime'] + cpf.cn.fdata[f]['duration'] < t:
                tt1 = time.time()
                iperfend = cpf.cn.fdata[f]['genstime'] + cpf.cn.fdata[f]['duration']
                fremindex = math.ceil(iperfend - starttime)
                if cpf.cn.fdata[f]['isGen'] == True and tt1 < iperfend and t < iperfend - starttime:
                    if fremindex > math.ceil(t):
                        if not fremindex in fremhelp:
                            fremhelp[fremindex] = []
                        cpf.cn.fdata[f]['fremindex'] = fremindex
                        fremhelp[fremindex].append(f)
                        fremhelp[math.ceil(t)].remove(f)
                elif cpf.cn.fdata[f]['isGen'] == False:
                    print "Second elif :2:" + " isSat:" + str(cpf.cn.fdata[f]['isSat']) + " isGen:" + str(cpf.cn.fdata[f]['isGen']) + " tt1:" + str(tt1) + " t:" + str(t) + " iperfend:" + str(iperfend)
                    cpf.remFlow(f, stopiperf=False)
                    remcount += 1
                    fremhelp[math.ceil(t)].remove(f)
                else:
                    cpf.remFlow(f, stopiperf=False)
                    remcount += 1
                    fremhelp[math.ceil(t)].remove(f)
        if t + d >= -10:
        # tt1-starttime used to be t before
            tt1 = time.time()
            cpf.addFlow(stime=tt1-starttime, dur=d)
            if cpf.cn.fdata[cpf.cn.F[-1]]['isSat'] == True:
                cpf.generateTrafficForSingleFlow(cpf.cn.F[-1])
            else:
                cpf.TotalUnsatisfied.append(cpf.cn.F[-1])
                print "Flow not satisfied : " + str(cpf.cn.fdata[cpf.cn.F[-1]])
            fremindex = math.ceil(tt1 - starttime + d)
            if not fremindex in fremhelp:
                fremhelp[fremindex] = []
            cpf.cn.fdata[cpf.cn.F[-1]]['fremindex'] = fremindex
            fremhelp[fremindex].append(cpf.cn.F[-1])
            addcount += 1

        tlast = t

        if cpf.state <> "Solved":  # for reality purpose in case of a CLC or CRC failure, should currently not happen
            perform_simstep = True
            reason = 1

        if ((len(cpf.cn.F) > len(cpf.Satisfied) + len(blacklist)) or (len(blacklist) > 0 and t-calctime > 60)) \
                and len(cpf.cn.C) > len(cpf.CLCs):
            perform_simstep = True
            reason = 2  # Incoming data flows

        if len(cpf.CLCs) > 1:  # Code for identifying low load situation
            if cpf.getAverageCLCload() < CLCloadlimit:
                if llalarm == False:
                    tll = t
                    llalarm = True
                if llalarm and t - tll > lltimeframe:
                    llalarm = False
                    tmplenCLCs = len(cpf.CLCs)
                    loadtmp = cpf.getAverageCLCload() * tmplenCLCs
                    while len(cpf.CLCs) > math.ceil(loadtmp):
                        cpf.remCLC(cpf.getCLCwithLeastLoad())
                    if len(cpf.CLCs) < tmplenCLCs:
                        perform_simstep = True
                        reason = 3  # Low load situation
                    else:
                        CLCloadlimit -= 0.05
            else:
                llalarm = False

        if perform_simstep and t >= -10:
            print "Reason: " + str(reason) + ", t = " + str(t)
            calctime = t
            lastdisp = t
            realtime = time.time() - starttime
            # simstep(cpf, calctime, realtime)
            if t >= 0:
                simstep(cpf, calctime, realtime)
            else:
                cpf.cpgreedy()
                print "Using " + str(len(cpf.CLCs)) + " CLCs out of " + str(len(cpf.cn.C))
                print "Adding routing entry:" + str(time.time())
                cpf.modifyRoutingTable()
                print "Start of iperf client for the satisfied flow:" + str(time.time())
                cpf.generateTrafficFlow()
                print "End of iperf client for the satisfied flow:" + str(time.time())
            if reason == 2 and len(cpf.cn.F) > len(cpf.Satisfied): # Add non-satisfied flow to blacklisted
                btmp = list(set(cpf.cn.F) - set(cpf.Satisfied))
                for f in btmp:
                    if not f in blacklist:
                        blacklist.append(f)
                    else:
                        fremindex = cpf.cn.fdata[f]['fremindex']
                        fremhelp[fremindex].remove(f)
                        cpf.remFlow(f, stopiperf=False)
                        remcount += 1
                        rejectedFlows += 1
            if reason == 3 and len(cpf.CLCs) >= tmplenCLCs:
                CLCloadlimit -= 0.05
            else:
                CLCloadlimit = stdll
            perform_simstep = False

        if t - lastdisp > 60:
            print "Time: " + str(t)
            print "System Time Passed: " + str(time.time()-starttime)
            print "Flows satisfied: " + str(len(cpf.cn.F)) + " out of " + str(len(cpf.Satisfied))
            print "Next flow removed at: " + str(min([cpf.cn.fdata[f]['genstime'] - starttime \
                                                     + cpf.cn.fdata[f]['duration'] for f in cpf.cn.F]))
            print "Average CLC load: " + str(cpf.getAverageCLCload())
            print "addcount:" + str(addcount) + " and remcount:" + str(remcount)
            print "\n"
            lastdisp = t
    if t >= -10:
        t2 = datetime.datetime.now()
        # Sleep/Deduct the duration moved ahead minus the processing time
        delta = t2 - t1
        deltafloat = delta.seconds + delta.microseconds / 1000000
        startdelta = t2 - stt
        startdeltafloat = startdelta.seconds + startdelta.microseconds / 1000000
        sleeptime = min(nextvar-deltafloat, t-startdeltafloat)
        if sleeptime > 0.0009 and t > startdeltafloat:
            time.sleep(sleeptime)

print "At the end"
print "starttime:" + str(starttime)
print "difftime:" + str(time.time() - starttime)
print "t:" + str(t)

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

print "At the end addcount:" + str(addcount) + " and remcount:" + str(remcount) + " and rejectedFlows:" + str(rejectedFlows)
cpf.TotalSatisfied = set(cpf.TotalSatisfied)
cpf.TotalUnsatisfied = set(cpf.TotalUnsatisfied)
print "At the end TotalSatisfied:" + str(len(cpf.TotalSatisfied)) + " and TotalUnsatisfied:" + str(len(cpf.TotalUnsatisfied)) + " and TotalFlowStopped:" + str(len(cpf.TotalFlowStopped))
cpf.TestbedNetwork.stop()
print "At the end starttime:" + str(starttime) + " and endtime:" + str(time.time())
