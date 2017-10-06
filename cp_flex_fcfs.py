from __future__ import division
import networkx as nx
import sys, math, random, time, copy
from crowd_network import *
import pdb
# pdb.set_trace()

from mininet.node import OVSSwitch
from mininet.node import RemoteController
from mininet.link import TCLink
from mininet.node import CPULimitedHost
from mininet.topo import Topo
from MaxiNet.Frontend import maxinet
from MaxiNet.tools import Tools
from mininet.net import Mininet

import functools
import subprocess, shlex
import requests
import json
from ryu.lib import dpid as dpid_lib
import traceback
import datetime
import re


# g_iperf_path = "/home/crowd/flexfcpf/iperf2-code/src/iperf"
g_iperf_path = "/home/tarun/flexfcpf/iperf2-code/src/iperf"
# g_conf_script_path = "/home/crowd/flexfcpf/code/configure_delay.sh"
g_conf_script_path= "/home/tarun/flexfcpf/code/configure_delay.sh"
# g_echoserver_path = "python /home/crowd/flexfcpf/code/echoserver.py"
g_echoserver_path = "python /home/tarun/flexfcpf/code/echoserver.py"

class CPFlex:
    def __init__(self, filename=None, flowOption="MostDemanding", scenario=None, modify_controllers=False, contrProb=None, cn=None, inputversion="flex", evalscen="generic", emulator=None):
        if emulator is None:
            print("Error: Emulator missing!")
            exit(1)
        if filename is not None:
            if scenario is None:
                read_weights_from_file = True
            else:
                read_weights_from_file = False

            self.cn = CrowdNetwork()
            valid_network = self.cn.generate_from_file(filename, read_weights_from_file, scenario, modify_controllers, contrProb, inputversion, evalscen)
            if valid_network:
                self.state = "NOT SOLVED"
            else:
                self.state = "INVALID NETWORK"
                print "Error: Invalid network!"
                exit(1)
        else:
            if cn is None:
                print "Error: Nothing to create CPFlex network from!"
                exit(1)
            else:
                self.cn = cn
                self.state = "NOT SOLVED"

        self.getFlowOption = flowOption
        self.iterations = 0
        self.Controlled = []
        self.CRCs = []
        self.CLCs = []
        self.Satisfied = []
        self.uncontrolledCLCs = []
        self.banlist = []
        self.use_banlist = False
        self.CLCloadlimit = 0.5
        self.remCLCswithlowload = False
        self.flexOperation = False
        if len(self.cn.C) > 1:
            self.VCRatio = len(self.cn.V) / (len(self.cn.C) - 1)
        else:
            self.VCRatio = len(self.cn.V)
        self.Switches = {}
        self.Hosts = {}
        self.Links = None
        self.RoutingPaths = []
        self.TestbedNetwork = None
        self.ParentProcess = []
        self.TotalSatisfied = []
        self.TotalUnsatisfied = []
        self.TotalFlowStopped = []
        self.emulator = emulator
        self.CurrentRoutingPaths = []
        self.hObjs = []
        self.JsonEntries = []
        self.CLCBucketIdList = []

    def scratchCopy(self):
        cntmp = self.cn.copy()
        cntmp.cleanup()

        return CPFlex(filename=None, cn=cntmp)

    def cpgreedy(self):
        if self.state == "INVALID NETWORK":
            print "Error: Invalid network!"
            exit(1)

        self.banlist = []
        self.iterations += 1
        self.newCLCcontrols = 0  # for simulation stats
        self.newFlowSats = 0

        if self.iterations > 1:
            if self.remCLCswithlowload == True:
                tmp = list(self.CLCs)
                for c in tmp:
                    if self.CLCload(c) < self.CLCloadlimit:
                        self.remCLC(c)
            while len(self.uncontrolledCLCs) > 0:
                v = self.uncontrolledCLCs[0]
                tmp = self.findCRC(v)
                if tmp == False:
                    self.remCLC(v)
                self.uncontrolledCLCs.remove(v)
            self.updateVCRatio()
            self.browseCurrentCLCs()

        if len(self.Controlled) < len(self.cn.V):
            self.state = "NOT SOLVED"

        self.globalOption = "neighbors"
        while len(self.Controlled) < len(self.cn.V):
            self.findCLC(self.globalOption)
            if len(self.CLCs) == len(self.cn.C):
                break

        if len(self.Controlled) == len(self.cn.V):
            self.state = "Solved"

        if len(self.CLCs) < len(self.cn.C):
            self.globalOption = "flows"
            while len(self.Satisfied) < len(self.cn.F):
                tmpsat = len(self.Satisfied)
                self.findCLC(self.globalOption)
                if self.use_banlist == True:
                    if len(self.CLCs) + len(self.banlist) == len(self.cn.C):
                        break
                    if tmpsat == len(self.Satisfied):
                        self.banlist.append(self.CLCs[-1])
                        self.newCLCcontrols -= len(self.cn.G.node[self.CLCs[-1]]['CLCcontrol'])
                        self.remCLC(self.CLCs[-1])
                else:
                    if len(self.CLCs) == len(self.cn.C) or tmpsat == len(self.Satisfied):
                        if tmpsat == len(self.Satisfied):
                            self.newCLCcontrols -= len(self.cn.G.node[self.CLCs[-1]]['CLCcontrol'])
                            self.remCLC(self.CLCs[-1])
                        break

        self.cleanupCLCcontrols(self.cn.V)

    def findCLC(self, option):
        # tstart = time.time()
        candidates = self.getCLCcandidates(option)
        # tend = time.time()
        # print "Candidate-Runtime: " + str(tend-tstart)
        for v in candidates:
            tmp = self.findCRC(v)
            if tmp == True:
                self.addNewCLC(v)
                break

    def getCLCcandidates(self, option=None):

        candidates = list(set(self.cn.C) - set(self.CLCs) - set(self.banlist))
        # avoid CRCs to be used as CLCs as long as possible
        if len(set(candidates) - set(self.CRCs)) > 0:
            candidates = [c for c in candidates if not c in self.CRCs]
        remaining_nodes = set(self.cn.V) - set(self.Controlled)
        remaining_flows = set(self.cn.F) - set(self.Satisfied)

        if option == "neighbors":
            ctmp = [(k, len((set([k]) | set(self.cn.G.neighbors(k))) - set(self.Controlled))) for k in candidates]
            ctmp.sort(key=lambda x: x[1], reverse=True)
            bestvalue = ctmp[0][1]
            if bestvalue > 0:
                candidates = [x[0] for x in ctmp]
            else:
                self.globalOption = "isolated_nodes"
                candidates = self.getCLCcandidates("isolated_nodes")
        elif option == "isolated_nodes":
            paths = []
            for i in remaining_nodes:
                for j in candidates:
                    paths.append(nx.shortest_path(self.cn.G, source=j, target=i))
            paths.sort(key=len)
            candidates = []
            for p in paths:
                if not p[0] in candidates:
                    candidates.append(p[0])
        elif option == "flows":
            ctmp = [(k, len(set(self.cn.Wf[k]) - set(self.Satisfied))) for k in candidates]
            ctmp.sort(key=lambda x: x[1], reverse=True)
            bestvalue = ctmp[0][1]
            if bestvalue > 0:
                candidates = [x[0] for x in ctmp]
            else:
                self.globalOption = "isolated_flows"
                candidates = self.getCLCcandidates("isolated_flows")
        elif option == "flows_nn":  # CAUTION: very slow for many flows in the network! Currently not used.
            ctmp = [(k, len(set(self.cn.Wf[k]) - set(self.Satisfied)) + sum(len(set(self.cn.Wf[j]) - set(self.Satisfied)) for j in self.cn.G.neighbors(k))) for k in candidates]
            ctmp.sort(key=lambda x: x[1], reverse=True)
            bestvalue = ctmp[0][1]
            if bestvalue > 0:
                candidates = [x[0] for x in ctmp]
            else:
                self.globalOption = "isolated_flows"
                candidates = self.getCLCcandidates("isolated_flows")
        elif option == "isolated_flows":
            paths = []
            for f in remaining_flows:
                for i in self.cn.Wb[f]:
                    for j in candidates:
                        paths.append(nx.shortest_path(self.cn.G, source=j, target=i))
            paths.sort(key=len)
            candidates = []
            for p in paths:
                if not p[0] in candidates:
                    candidates.append(p[0])
        elif option == "isolated_flows2":  # just a test, currently not used.
            nodes_with_flows = [(k, len(set(self.cn.Wf[k]) - set(self.Satisfied))) for k in self.cn.V]
            nodes_with_flows.sort(key=lambda x: x[1], reverse=True)
            node_with_most_flows = nodes_with_flows[0][0]
            paths = []
            for j in candidates:
                paths.append(nx.shortest_path(self.cn.G, source=j, target=node_with_most_flows))
            paths.sort(key=len)
            candidates = [p[0] for p in paths]
        elif option == "neighbors_and_flows":  # currently not used.
            ctmp = [(k, len(set([k]) | set(self.cn.G.neighbors(k)) - set(self.Controlled)) + len(set(self.cn.Wf[k]) - set(self.Satisfied))) for k in candidates]
            ctmp.sort(key=lambda x: x[1], reverse=True)
            candidates = [x[0] for x in ctmp]

        return candidates

    def addNewCLC(self, v):
        paths = []
        pf = set([])
        nc = 0
        nnc = 0
        fs = 0

        tmp = self.checkCLC([v])
        if tmp == True:
            nc += 1
            if v not in self.Controlled:
                nnc += 1
            self.addCLCcontrol([v])
            pf = self.updatePotentialFlows(pf, v, [v])
        else:
            self.cn.C.remove(v)

        for i in self.cn.V:
            if i <> v and (i not in self.Controlled or len(set(self.cn.Wf[i]) - set(self.Satisfied)) > 0):
                paths.append((nx.shortest_path(self.cn.G, source=v, target=i), i in self.Controlled, len(set(self.cn.Wf[i]) - set(self.Satisfied))))
        if len(self.Controlled) < len(self.cn.V):
            paths.sort(key=lambda x: x[1])
            paths.sort(key=lambda x: len(x[0]))
            notyetsolved = True
        else:
            paths.sort(key=lambda x: len(x[0]))
            paths.sort(key=lambda x: x[2], reverse=True)
            notyetsolved = False

        while (len(paths) > 0 or len(pf) > 0) and (len(self.Controlled) < len(self.cn.V) or len(self.Satisfied) < len(self.cn.F)):
            # print "Controlled: "  + str(len(self.Controlled)) + " / " + str(len(self.cn.V)) + "   Satisfied: " + str(len(self.Satisfied)) + " / " + str(len(self.cn.F))
            # print "Current CLC: " + str(v) + "   NNC: " + str(nnc) + "   VCRatio: " + str(self.VCRatio)
            # time.sleep(0.1)
            if notyetsolved and len(self.Controlled) == len(self.cn.V):
                paths.sort(key=lambda x: len(x[0]))
                paths.sort(key=lambda x: x[2], reverse=True)
                notyetsolved = False
            if (len(pf) > 0 and (nnc >= self.VCRatio or len(self.Controlled) == len(self.cn.V))) or len(paths) == 0:
                f = self.getFlow(pf, self.getFlowOption)
                tmp = self.checkFlowSat(v, f)
                # print "CLC: " + str(v) + " Flow: " + str(f) + " Result: " + str(tmp)
                if tmp == True:
                    self.addFlowSat(v, f)
                    fs += 1
                pf.remove(f)
            else:
                if len(paths) == 0:
                    break
                p = list(paths[0][0])
                del paths[0]
                tmp = self.checkCLC(p)
                # print "CLC: " + str(v) + " Node: " + str(p[-1]) + " Result: " + str(tmp)
                if tmp == True:
                    nc += 1
                    if p[-1] not in self.Controlled:
                        nnc += 1
                    self.addCLCcontrol(p)
                    pf = self.updatePotentialFlows(pf, v, [p[-1]])
                elif tmp > 2:
                    break

    def updateVCRatio(self):
        self.VCRatio = (len(self.cn.V) - len(self.Controlled)) / len(self.cn.C)

    def updatePotentialFlows(self, pf, v, nn):
        cpf = set([])
        for w in nn:
            cpf = cpf | set(self.cn.Wf[w])
        for f in cpf:
            if self.cn.fdata[f]['isSat'] == False and set(self.cn.Wb[f]) <= set(self.cn.G.node[v]['CLCcontrol']):
                pf.add(f)

        return pf

    def getFlow(self, pf, option):
        tmp = list(pf)
        if len(tmp) == 0:
            return None
        else:
            if option == "MostDemanding":
                tmp.sort(key=lambda f: self.cn.fdata[f]['p_flow'], reverse=True)
            elif option == "LeastDemanding":
                tmp.sort(key=lambda f: self.cn.fdata[f]['p_flow'])
            return tmp[0]

    def findCRC(self, v):
        # check already active CRCs first
        paths = []
        for i in self.CRCs:
            paths.append(nx.shortest_path(self.cn.G, source=i, target=v))
        paths.sort(key=len)
        for p in paths:
            if self.checkCRC(p) == True:
                self.addCRCcontrol(p)
                return True

        # need to add a new CRC, at first try to avoid active CLCs and CLC candidate
        return self.findNewCRC(v)

    def findNewCRC(self, v):
        paths = []
        for i in list(set(self.cn.C) - (set(self.CRCs) | set(self.CLCs) | set([v]))):
            paths.append(nx.shortest_path(self.cn.G, source=i, target=v))
        if len(self.CRCs) == 0:  # first CRC should be placed centrally
            paths.sort(key=lambda p: sum(len(nx.shortest_path(self.cn.G, source=p[0], target=c)) for c in self.cn.C))
        else:
            paths.sort(key=lambda p: len(p))
        for p in paths:
            if self.checkCRC(p) == True:
                self.addCRCcontrol(p)
                return True
        # last option: try CLC candidate, then already active CLCs
        if self.checkCRC([v]) == True:
            self.addCRCcontrol([v])
            return True
        paths = []
        for i in self.CLCs:
            paths.append(nx.shortest_path(self.cn.G, source=i, target=v))
        paths.sort(key=len)
        for p in paths:
            if self.checkCRC(p) == True:
                self.addCRCcontrol(p)
                return True

        return False

    def addCRCcontrol(self, path):
        v = path[0]
        w = path[-1]
        for i in range(0, len(path) - 1):
            self.cn.G.edge[path[i]][path[i + 1]]['b_rem'] -= self.cn.b_CRC
        self.cn.G.node[v]['p_rem'] -= self.cn.p_CRC / (
        self.cn.l_CRC - sum(2 * self.cn.G.edge[path[i]][path[i + 1]]['l_cap'] for i in range(0, len(path) - 1)))
        self.cn.G.node[v]['ProcCRC'][w] = self.cn.p_CRC / (
        self.cn.l_CRC - sum(2 * self.cn.G.edge[path[i]][path[i + 1]]['l_cap'] for i in range(0, len(path) - 1)))
        self.cn.G.node[v]['CRCcontrol'].append(w)
        self.cn.G.node[v]['CRCpaths'][w] = path
        self.cn.G.node[v]['isCRC'] = True
        self.cn.G.node[w]['CRC'] = v
        self.cn.G.node[w]['pathtoCRC'] = path
        if v not in self.CRCs:
            self.CRCs.append(v)

    def addCLCcontrol(self, path):
        self.newCLCcontrols += 1
        v = path[0]
        w = path[-1]
        for i in range(0, len(path) - 1):
            self.cn.G.edge[path[i]][path[i + 1]]['b_rem'] -= self.cn.b_CLC
        self.cn.G.node[v]['p_rem'] -= self.cn.p_CLC / (
        self.cn.l_CLC - sum(2 * self.cn.G.edge[path[i]][path[i + 1]]['l_cap'] for i in range(0, len(path) - 1)))
        self.cn.G.node[v]['ProcCLC'][w] = self.cn.p_CLC / (
        self.cn.l_CLC - sum(2 * self.cn.G.edge[path[i]][path[i + 1]]['l_cap'] for i in range(0, len(path) - 1)))
        self.cn.G.node[v]['CLCcontrol'].append(w)
        self.cn.G.node[v]['CLCpaths'][w] = path
        self.cn.G.node[v]['isCLC'] = True
        self.cn.G.node[w]['CLCs'].append(v)
        self.cn.G.node[w]['pathtoCLC'][v] = path
        if v not in self.CLCs:
            self.CLCs.append(v)
        if w not in self.Controlled:
            self.Controlled.append(w)

    def addFlowSat(self, v, f):
        self.newFlowSats += 1
        self.cn.fdata[f]['isSat'] = True
        self.cn.fdata[f]['CLC'] = v
        flowpaths = [self.cn.G.node[v]['CLCpaths'][k] for k in self.cn.Wb[f]]
        for path in flowpaths:
            for i in range(0, len(path) - 1):
                self.cn.G.edge[path[i]][path[i + 1]]['b_rem'] -= self.cn.fdata[f]['b_flow']
        maxpathlatency = max([sum(2 * self.cn.G.edge[path[i]][path[i + 1]]['l_cap'] for i in range(0, len(path) - 1)) for path in flowpaths])
        self.cn.G.node[v]['p_rem'] -= self.cn.fdata[f]['p_flow'] / (self.cn.fdata[f]['l_flow'] - 1e-4 - maxpathlatency)
        self.cn.G.node[v]['ProcFlow'][f] = self.cn.fdata[f]['p_flow'] / (self.cn.fdata[f]['l_flow'] - maxpathlatency)
        self.cn.G.node[v]['Satisfies'].append(f)
        self.Satisfied.append(f)

    # checks if a certain CRC control can be established
    def checkCRC(self, path):
        v = path[0]
        for i in range(0, len(path) - 1):
            if self.cn.G.edge[path[i]][path[i + 1]]['b_rem'] < self.cn.b_CRC:
                return False
        if sum(2 * self.cn.G.edge[path[i]][path[i + 1]]['l_cap'] for i in range(0, len(path) - 1)) + self.cn.p_CRC / self.cn.G.node[v]['p_rem'] > self.cn.l_CRC:
            return False

        return True

    # checks if a certain CLC control can be established
    def checkCLC(self, path):
        v = path[0]
        for i in range(0, len(path) - 1):
            if self.cn.G.edge[path[i]][path[i + 1]]['b_rem'] < self.cn.b_CLC:  # + 2*self.cn.b_CRC
                return 2
        if sum(2 * self.cn.G.edge[path[i]][path[i + 1]]['l_cap'] for i in range(0, len(path) - 1)) + self.cn.p_CLC / self.cn.G.node[v]['p_rem'] > self.cn.l_CLC:
            return 4

        return True

    # checks if a flow f can be satisfied by a controller v
    def checkFlowSat(self, v, f):
        if self.cn.fdata[f]['isSat'] == True:
            return False
        if not set(self.cn.Wb[f]) <= set(self.cn.G.node[v]['CLCcontrol']):
            return False
        flowedgecount = {}
        for k in self.cn.Wb[f]:
            path = self.cn.G.node[v]['CLCpaths'][k]
            for i in range(0, len(path) - 1):
                if not (path[i], path[i + 1]) in flowedgecount:
                    flowedgecount[(path[i], path[i + 1])] = 1
                else:
                    flowedgecount[(path[i], path[i + 1])] += 1
            if sum(2 * self.cn.G.edge[path[i]][path[i + 1]]['l_cap'] for i in range(0, len(path) - 1)) + self.cn.fdata[f]['p_flow'] / self.cn.G.node[v]['p_rem'] > self.cn.fdata[f]['l_flow'] - 1e-4:
                return False
        for e in flowedgecount:
            if self.cn.G.edge[e[0]][e[1]]['b_rem'] < flowedgecount[(e[0], e[1])] * self.cn.fdata[f]['b_flow']:  # + (2*self.cn.b_CRC + 5*self.cn.b_CLC)
                return False

        return True

    def remCRC(self, v):
        self.cn.G.node[v]['isCRC'] = False
        tmp = list(self.cn.G.node[v]['CRCcontrol'])
        for w in tmp:
            self.remCRCcontrol(v, w)
        self.CRCs.remove(v)

    def remCRCcontrol(self, v, w):
        path = self.cn.G.node[v]['CRCpaths'][w]
        for i in range(0, len(path) - 1):
            self.cn.G.edge[path[i]][path[i + 1]]['b_rem'] += self.cn.b_CRC
        self.cn.G.node[v]['p_rem'] += self.cn.G.node[v]['ProcCRC'][w]
        del self.cn.G.node[v]['ProcCRC'][w]
        self.cn.G.node[v]['CRCcontrol'].remove(w)
        del self.cn.G.node[v]['CRCpaths'][w]
        self.cn.G.node[w]['CRC'] = None
        self.cn.G.node[w]['pathtoCRC'] = None
        if self.cn.G.node[w]['isCLC'] == True:
            self.uncontrolledCLCs.append(w)
            self.state = "NOT SOLVED"
        if len(self.cn.G.node[v]['CRCcontrol']) == 0:
            self.remCRC(v)

    def remCLC(self, v):
        tmp = list(self.cn.G.node[v]['Satisfies'])
        for f in tmp:
            self.remFlowSat(f)
        tmp = list(self.cn.G.node[v]['CLCcontrol'])
        for w in tmp:
            self.remCLCcontrol(v, w)
        self.cn.G.node[v]['isCLC'] = False
        if self.cn.G.node[v]['CRC'] is not None:
            self.remCRCcontrol(self.cn.G.node[v]['CRC'], v)
        self.CLCs.remove(v)

    def remCLCcontrol(self, v, w):
        path = self.cn.G.node[v]['CLCpaths'][w]
        for i in range(0, len(path) - 1):
            self.cn.G.edge[path[i]][path[i + 1]]['b_rem'] += self.cn.b_CLC
        self.cn.G.node[v]['p_rem'] += self.cn.G.node[v]['ProcCLC'][w]
        del self.cn.G.node[v]['ProcCLC'][w]
        self.cn.G.node[v]['CLCcontrol'].remove(w)
        del self.cn.G.node[v]['CLCpaths'][w]
        self.cn.G.node[w]['CLCs'].remove(v)
        del self.cn.G.node[w]['pathtoCLC'][v]
        if len(self.cn.G.node[w]['CLCs']) == 0:
            self.Controlled.remove(w)
            self.state = "NOT SOLVED"

    def remFlowSat(self, f, stopiperf=True):
        v = self.cn.fdata[f]['CLC']
        for k in self.cn.Wb[f]:
            path = self.cn.G.node[v]['CLCpaths'][k]
            for i in range(0, len(path) - 1):
                self.cn.G.edge[path[i]][path[i + 1]]['b_rem'] += self.cn.fdata[f]['b_flow']
        self.cn.G.node[v]['p_rem'] += self.cn.G.node[v]['ProcFlow'][f]
        del self.cn.G.node[v]['ProcFlow'][f]
        self.cn.G.node[v]['Satisfies'].remove(f)
        if stopiperf == True:
            self.stopTrafficGenerationForSingleFlow(fid=f)
        self.cn.fdata[f]['isSat'] = False
        self.cn.fdata[f]['CLC'] = None
        self.cn.fdata[f]['isGen'] = False
        self.Satisfied.remove(f)

    def addFlow(self, stime=0, dur=None, amount=1):
        for i in range(1, amount + 1):
            self.cn.addFlow(stime=stime, dur=dur)
        if self.flexOperation and len(self.CLCs) > 0:
            if amount == 1:
                self.browseCurrentCLCsforSingleFlow(self.cn.F[-1])
            else:
                self.browseCurrentCLCs()

    def remFlow(self, f, stopiperf=True):
        # self.cn.fdata[-f] = copy.deepcopy(self.cn.fdata[f]) # uncomment ONLY for debbuging!
        if self.cn.fdata[f]['isSat'] == True:
            self.remFlowSat(f, stopiperf)
        tmplist = list(self.cn.Wb[f])
        self.cn.remFlow(f)
        if self.flexOperation:
            self.cleanupCLCcontrols(tmplist)

    def clearFlows(self):
        tmp = list(self.cn.F)
        for f in tmp:
            self.remFlow(f)

    def browseCurrentCLCs(self):
        paths = []
        pf = {}
        nnc = {}
        for v in self.CLCs:
            if self.CLCload(v) < 0.99:
                pf[v] = self.updatePotentialFlows(set([]), v, self.cn.G.node[v]['CLCcontrol'])
                nnc[v] = 0
                for i in list(set(self.cn.V) - set(self.cn.G.node[v]['CLCcontrol'])):
                    if i not in self.Controlled or len(set(self.cn.Wf[i]) - set(self.Satisfied)) > 0:
                        paths.append((nx.shortest_path(self.cn.G, source=v, target=i), i in self.Controlled, len(set(self.cn.Wf[i]) - set(self.Satisfied))))

        if len(self.Controlled) < len(self.cn.V):
            paths.sort(key=lambda x: x[1])
            paths.sort(key=lambda x: len(x[0]))
            notyetsolved = True
        else:
            paths.sort(key=lambda x: len(x[0]))
            paths.sort(key=lambda x: x[2], reverse=True)
            notyetsolved = False

        while (len(paths) > 0 or sum(len(pf[v]) for v in pf) > 0) and (len(self.Controlled) < len(self.cn.V) or len(self.Satisfied) < len(self.cn.F)):
            if notyetsolved and len(self.Controlled) == len(self.cn.V):
                paths.sort(key=lambda x: len(x[0]))
                paths.sort(key=lambda x: x[2], reverse=True)
                notyetsolved = False

            if sum(len(pf[v]) for v in pf) > 0 and (len(paths) == 0 or len(self.Controlled) == len(self.cn.V)):
                currv = [v for v in pf if len(pf[v]) > 0][0]
            else:
                currv = paths[0][0][0]

            if self.CLCload(currv) > 0.99:
                pf[currv] = set([])
                paths = [p for p in paths if p[0][0] <> currv]
            elif len(pf[currv]) > 0 and (len(paths) == 0 or nnc[currv] >= self.VCRatio or len(self.Controlled) == len(self.cn.V)):
                f = self.getFlow(pf[currv], self.getFlowOption)
                tmp = self.checkFlowSat(currv, f)
                if tmp == True:
                    self.addFlowSat(currv, f)
                    for w in pf:
                        if f in pf[w]:
                            pf[w].remove(f)
                else:
                    pf[currv].remove(f)
            else:
                p = list(paths[0][0])
                del paths[0]
                tmp = self.checkCLC(p)
                if tmp == True:
                    if p[-1] not in self.Controlled:
                        nnc[currv] += 1
                    self.addCLCcontrol(p)
                    pf[currv] = self.updatePotentialFlows(pf[currv], currv, [p[-1]])
                elif tmp > 2:
                    paths = [p for p in paths if p[0][0] <> currv]
                    pf[currv] = set([])

    def CLCload(self, c):
        if not c in self.CLCs:
            return 0

        return 1.0 - self.cn.G.node[c]['p_rem'] / self.cn.G.node[c]['p_node']

    def CLCoutput(self, c):
        out = "Data for CLC " + str(c) + ":\n"
        out += "Load: " + str(self.CLCload(c)) + "\n"
        out += "p_rem: " + str(self.cn.G.node[c]['p_rem']) + ", Nodes controlled: " + str(len(self.cn.G.node[c]['CLCcontrol'])) + ", Flows satisfied: " + str(len(self.cn.G.node[c]['Satisfies'])) + "\n"
        if len(self.cn.G.node[c]['Satisfies']) > 0:
            out += "Biggest flow satisfied: " + str(max(self.cn.fdata[f]['p_flow'] for f in self.cn.G.node[c]['Satisfies'])) + "\n"

        return out

    def getAverageCLCload(self):
        return sum(self.CLCload(c) for c in self.CLCs) / len(self.CLCs)

    def getCLCwithLeastLoad(self):
        tmp = list(self.CLCs)
        tmp.sort(key=lambda c: self.CLCload(c))
        return tmp[0]

    def getAverageCLCpathlength(self):
        return sum(len(self.cn.G.node[c]['CLCpaths'][v]) for c in self.CLCs for v in self.cn.G.node[c]['CLCcontrol']) / sum(len(self.cn.G.node[c]['CLCcontrol']) for c in self.CLCs)

    def getAverageCRCpathlength(self):
        return sum(len(self.cn.G.node[c]['CRCpaths'][v]) for c in self.CRCs for v in self.cn.G.node[c]['CRCcontrol']) / sum(len(self.cn.G.node[c]['CRCcontrol']) for c in self.CRCs)

    def CLCcontrolRatio(self):
        return sum(len(self.cn.G.node[c]['CLCcontrol']) for c in self.CLCs) / len(self.cn.V)

    def cleanupCLCcontrols(self, nodelist):
        counter = 0
        vtmp = list(nodelist)
        random.shuffle(vtmp)
        for v in vtmp:
            ctmp = list(self.cn.G.node[v]['CLCs'])
            random.shuffle(ctmp)
            for c in ctmp:
                if c <> v and len(self.cn.G.node[v]['CLCs']) > 1 and len(set(self.cn.G.node[c]['Satisfies']) & set(self.cn.Wf[v])) == 0:
                    self.remCLCcontrol(c, v)
                    counter += 1
                    # print "CLC controls removed: " + str(counter)

    def browseCurrentCLCsforSingleFlow(self, f):
        CLCstmp = list([c for c in self.CLCs if set(self.cn.Wb[f]) <= set(self.cn.G.node[c]['CLCcontrol'])])
        for c in CLCstmp:
            tmp = self.checkFlowSat(c, f)
            if tmp == True:
                self.addFlowSat(c, f)
                return 1

        CLCstmp = list([c for c in self.CLCs if not set(self.cn.Wb[f]) <= set(self.cn.G.node[c]['CLCcontrol'])])
        CLCstmp.sort(key=lambda c: sum(len(nx.shortest_path(self.cn.G, source=c, target=i)) for i in self.cn.Wb[f]))
        CLCstmp.sort(key=lambda c: len(set(self.cn.Wb[f]) - set(self.cn.G.node[c]['CLCcontrol'])))
        for c in CLCstmp:
            paths = (nx.shortest_path(self.cn.G, source=c, target=i) for i in self.cn.Wb[f] if not i in self.cn.G.node[c]['CLCcontrol'])
            for p in paths:
                tmp = self.checkCLC(p)
                if tmp == True:
                    self.addCLCcontrol(p)
                else:
                    break
            if tmp == True:
                tmp = self.checkFlowSat(c, f)
                if tmp == True:
                    self.addFlowSat(c, f)
                else:
                    for p in paths:
                        self.remCLCcontrol(c, p[-1])

    def setupEmulationNetwork(self):
        topo = Topo(link=TCLink, host=CPULimitedHost)
        # linkopts = dict(bw=1000, delay='0ms', loss=0, use_htb=True)
        linkopts = dict()  # delay='0ms', use_hfsc=True
        # clcpower = 0.7/len(self.cn.C) #TODO
        # cpupower = 0.1/(len(self.cn.V) - len(self.cn.C))
        # Add switches and associated hosts
        s = 1
        for n in self.cn.G.node:
            hName = 'h' + str(n)
            hIp = Tools.makeIP(n + 1)
            hMac = Tools.makeMAC(n + 1)
            # if n in self.cn.C:
            #	 cpupower = clcpower
            # hObj = topo.addHost(name=hName, ip=hIp, mac=hMac, cpu=cpupower)
            hObj = topo.addHost(name=hName, ip=hIp, mac=hMac)
            self.Hosts[hName] = {'obj': hObj, 'ip': hIp, 'mac': hMac}
            sName = 's' + str(n)
            sDpid = Tools.makeDPID(n + 1)
            sListenPort = (13000 + s - 1)
            switchopts = dict(listenPort=sListenPort)
            sObj = topo.addSwitch(name=sName, dpid=sDpid, **switchopts)
            self.Switches[sName] = {'obj': sObj, 'dpid': sDpid, 'listenport': sListenPort}
            s += 1
            topo.addLink(hObj, sObj, **linkopts)

        for key, value in self.cn.G.edges():
            sName1 = 's' + str(key)
            sName2 = 's' + str(value)
            sObj1 = self.Switches[sName1]['obj']
            sObj2 = self.Switches[sName2]['obj']
            topo.addLink(sObj1, sObj2, **linkopts)

        if self.emulator == "Mininet":
            # Mininet
            switch = functools.partial(OVSSwitch, protocols='OpenFlow13')
            net = Mininet(topo=topo, switch=switch, controller=RemoteController, host=CPULimitedHost, link=TCLink)
            net.start()
            # Save the Mininet object for future reference
            self.TestbedNetwork = net
        elif self.emulator == "MaxiNet":
            # MaxiNet
            cluster = maxinet.Cluster()
            exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
            exp.setup()
            # Save the Experiment object for future reference
            for switch in exp.switches:
                exp.get_worker(switch).run_cmd('ovs-vsctl -- set Bridge %s ' % switch.name + 'protocols=OpenFlow10,OpenFlow12,OpenFlow13')
            self.TestbedNetwork = exp
        else:
            print("Error: Emulator missing!")
            exit(1)

        # Start iperf server in potential CLC host
        for n in self.cn.G.node:
            if n in self.cn.C:
                hName = 'h' + str(n)
                hObj = self.TestbedNetwork.get(hName) if self.emulator == "Mininet" else self.TestbedNetwork.get_node(hName)
                hObj.cmd("socat -T 5 UDP-LISTEN:5001,fork,reuseaddr EXEC:\'/bin/cat\' &")
                # hObj.cmd("ncat -e /bin/cat -k -u -m 1000 -l 5001 &")
                # hObj.cmd("iperf -u -f 'b' -s > /tmp/iperf_server_" + hName + ".log &")

        # for n in self.cn.G.node:
        #     if n in self.cn.C:
        #         hName = 'h' + str(n)
        #         hObj = self.TestbedNetwork.get(hName) if self.emulator == "Mininet" else self.TestbedNetwork.get_node(hName)
        #         hObj.cmd("ps -eaf|grep \"socat -T 5 UDP-LISTEN:5001,fork,reuseaddr EXEC:/bin/cat\"|grep -v \"grep socat\"|awk \'{print $2}\'|tr \'\\n\' \',\' > /tmp/socatpid.txt")
        #         f = open("/tmp/socatpid.txt", "r")
        #         line = f.readline()
        #         linetoken = re.split(",", line)
        #         for onelinetocken in linetoken:
        #             if len(onelinetocken) > 1 and onelinetocken not in self.ParentProcess:
        #                 self.ParentProcess.append(onelinetocken)
        #         f.close()
        # print self.ParentProcess

    def populateNetworkLinks(self):
        urlpath = "http://127.0.0.1:8080/fcapfnetworkcontroller/topology/links"
        resp = requests.get(urlpath)
        self.Links = resp.json()
    # print self.Links

    def checkRoutingPath(self, src, dst, path):
        key = (src, dst, path)
        self.CurrentRoutingPaths.append(key)
        foundPath = key in self.RoutingPaths
        if foundPath == False:
            self.RoutingPaths.append(key)
        return foundPath

    def modifyRoutingTable(self):
        for n in self.cn.G.node:
            node = self.cn.G.node[n]
            pathToCLC = node['pathtoCLC']
            # print pathToCLC
            for clc, path in pathToCLC.items():
                # print path
                src = clc
                dst = n
                foundPath = self.checkRoutingPath(src, dst, path)
                if foundPath == False:
                    self.addRoutingPath(src, dst, path)

        self.requestAddRoutingEntries()
        # print "Earlier Routing Entries"
        # self.RoutingEntries.sort()
        # print self.RoutingEntries
        self.clearObsoleteRoutingPaths()
        # print "After clean Routing Entries"
        # self.RoutingEntries.sort()
        # print self.RoutingEntries
        # print "Current Routing Entries"
        # self.CurrentEntries.sort()
        # print self.CurrentEntries
        # Do not delete forwarding entries from switch, because there might be some flow still running,
        # we will set the timeout for the entries, so that the entries will be removed automatically
        # for being idle for sometime, see the function we commented the call for forward entry deletion.
        self.requestDeleteRoutingEntries()

    def addRoutingPath(self, src, dst, path):
        links = self.Links
        nw_src = Tools.makeIP(src + 1)
        nw_dst = Tools.makeIP(dst + 1)
        if len(path) > 1:
            i = 0
            while i < len(path) - 1:
                n1 = path[i]
                n2 = path[i + 1]
                if n1 == src and n2 == dst:
                    # Assuming host is always connected to the port 1 of the switch
                    inport = 1
                    node1 = 's' + str(n1)
                    node2 = 's' + str(n2)
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    action = port1
                    switch = node1
                    # Add route entry for outward traffic
                    self.addRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst, action=action)
                    # Add route entry for inward traffic
                    self.addRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src, action=inport)
                    # Assuming host is always connected to the port 1 of the switch
                    action = 1
                    inport = port2
                    switch = node2
                    # Add route entry for outward traffic
                    self.addRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst, action=action)
                    # Add route entry for inward traffic
                    self.addRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src, action=inport)
                elif n1 == src and n2 != dst:
                    # Assuming host is always connected to the port 1 of the switch
                    inport = 1
                    node1 = 's' + str(n1)
                    node2 = 's' + str(n2)
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    action = port1
                    switch = node1
                    # Add route entry for outward traffic
                    self.addRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst, action=action)
                    # Add route entry for inward traffic
                    self.addRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src, action=inport)
                    inport = port2
                    switch = node2
                    node1 = 's' + str(n2)
                    node2 = 's' + str(path[i + 2])
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    action = port1
                    # Add route entry for outward traffic
                    self.addRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst, action=action)
                    # Add route entry for inward traffic
                    self.addRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src, action=inport)
                elif n1 != src and n2 != dst:
                    node1 = 's' + str(n1)
                    node2 = 's' + str(n2)
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    inport = port2
                    switch = node2
                    node1 = 's' + str(n2)
                    node2 = 's' + str(path[i + 2])
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    action = port1
                    # Add route entry for outward traffic
                    self.addRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst, action=action)
                    # Add route entry for inward traffic
                    self.addRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src, action=inport)
                elif n1 != src and n2 == dst:
                    # Assuming host is always connected to the port 1 of the switch
                    action = 1
                    node1 = 's' + str(n1)
                    node2 = 's' + str(n2)
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    inport = port2
                    switch = node2
                    # Add route entry for outward traffic
                    self.addRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst, action=action)
                    # Add route entry for inward traffic
                    self.addRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src, action=inport)
                else:
                    pass  # do nothing

                i += 1

    def addRoutingEntry(self, switch, inport, nwsrc, nwdst, action):
        dpid = "0000" + self.Switches[switch]['dpid']
        # Add route entry for ARP
        entry = {
            "dpid": dpid,
            "payload": {
                "inport": int(inport),
                "action": int(action),
                "dltype": "arp",
                "ipsrc": nwsrc,
                "ipdest": nwdst
            }
        }
        self.JsonEntries.append(entry)
        # Add route entry for TCP
        payload = {"inport": int(inport),
                   "action": int(action),
                   "dltype": "ip",
                   "ipsrc": nwsrc,
                   "ipdest": nwdst}
        entry = {
            "dpid": dpid,
            "payload": {
                "inport": int(inport),
                "action": int(action),
                "dltype": "ip",
                "ipsrc": nwsrc,
                "ipdest": nwdst
            }
        }
        self.JsonEntries.append(entry)

    def requestAddRoutingEntries(self):
        try:
            url = "http://127.0.0.1:8080/fcapfnetworkcontroller/flowtable/addflows"
            data = json.dumps(self.JsonEntries)
            resp = requests.put(url, data=data)
            if resp.status_code != 200:
                print "Something is wrong adding Routing entries, check controller log!!"
        except:
            print "Controller is not available!!"
        del self.JsonEntries
        self.JsonEntries = []

    def clearObsoleteRoutingPaths(self):
        entries = copy.deepcopy(self.RoutingPaths)
        for entry in entries:
            (src, dst, path) = entry
            if entry not in self.CurrentRoutingPaths:
                self.deleteRoutingPath(src, dst, path)
                self.RoutingPaths.remove(entry)
        del entries
        del self.CurrentRoutingPaths
        self.CurrentRoutingPaths = []

    def deleteRoutingPath(self, src, dst, path):
        links = self.Links
        nw_src = Tools.makeIP(src + 1)
        nw_dst = Tools.makeIP(dst + 1)
        if len(path) > 1:
            i = 0
            while i < len(path) - 1:
                n1 = path[i]
                n2 = path[i + 1]
                if n1 == src and n2 == dst:
                    # Assuming host is always connected to the port 1 of the switch
                    inport = 1
                    node1 = 's' + str(n1)
                    node2 = 's' + str(n2)
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    action = port1
                    switch = node1
                    # Delete route entry for outward traffic
                    self.deleteRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst)
                    # Delete route entry for inward traffic
                    self.deleteRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src)
                    # Assuming host is always connected to the port 1 of the switch
                    action = 1
                    inport = port2
                    switch = node2
                    # Delete route entry for outward traffic
                    self.deleteRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst)
                    # Delete route entry for inward traffic
                    self.deleteRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src)
                elif n1 == src and n2 != dst:
                    # Assuming host is always connected to the port 1 of the switch
                    inport = 1
                    node1 = 's' + str(n1)
                    node2 = 's' + str(n2)
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    action = port1
                    switch = node1
                    # Delete route entry for outward traffic
                    self.deleteRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst)
                    # Delete route entry for inward traffic
                    self.deleteRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src)
                    inport = port2
                    switch = node2
                    node1 = 's' + str(n2)
                    node2 = 's' + str(path[i + 2])
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    action = port1
                    # Delete route entry for outward traffic
                    self.deleteRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst)
                    # Delete route entry for inward traffic
                    self.deleteRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src)
                elif n1 != src and n2 != dst:
                    node1 = 's' + str(n1)
                    node2 = 's' + str(n2)
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    inport = port2
                    switch = node2
                    node1 = 's' + str(n2)
                    node2 = 's' + str(path[i + 2])
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    action = port1
                    # Delete route entry for outward traffic
                    self.deleteRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst)
                    # Delete route entry for inward traffic
                    self.deleteRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src)
                elif n1 != src and n2 == dst:
                    # Assuming host is always connected to the port 1 of the switch
                    action = 1
                    node1 = 's' + str(n1)
                    node2 = 's' + str(n2)
                    port1, port2 = self.getLinkPort(links, node1, node2)
                    inport = port2
                    switch = node2
                    # Delete route entry for outward traffic
                    self.deleteRoutingEntry(switch=switch, inport=inport, nwsrc=nw_src, nwdst=nw_dst)
                    # Delete route entry for inward traffic
                    self.deleteRoutingEntry(switch=switch, inport=action, nwsrc=nw_dst, nwdst=nw_src)
                else:
                    pass  # do nothing

                i += 1

    def deleteRoutingEntry(self, switch, inport, nwsrc, nwdst):
        dpid = "0000" + self.Switches[switch]['dpid']
        # Delete route entry for ARP
        entry = {
            "dpid": dpid,
            "payload": {
                "inport": int(inport),
                "dltype": "arp",
                "ipsrc": nwsrc,
                "ipdest": nwdst
            }
        }
        self.JsonEntries.append(entry)
        # Delete route entry for IP
        entry = {
            "dpid": dpid,
            "payload": {
                "inport": int(inport),
                "dltype": "ip",
                "ipsrc": nwsrc,
                "ipdest": nwdst
            }
        }
        self.JsonEntries.append(entry)

    def requestDeleteRoutingEntries(self):
        try:
            url = "http://127.0.0.1:8080/fcapfnetworkcontroller/flowtable/delflows"
            data = json.dumps(self.JsonEntries)
            resp = requests.put(url, data=data)
            if resp.status_code != 200:
                print "Something is wrong deleting Routing entries, check controller log!!"
        except:
            print "Controller is not available!!"
        del self.JsonEntries
        self.JsonEntries = []

    def checkBucketInCLC(self, clc, bucketId):
        key = (clc, bucketId)
        found = key in self.CLCBucketIdList
        if found == False:
            self.CLCBucketIdList.append(key)
        return found

    def generateTrafficFlow(self):
        iperfcount = 0
        for fid in self.cn.fdata:
            flow = self.cn.fdata[fid]
            if flow['isSat'] == True and flow['isGen'] == False:
                self.getHostForFlow(fid)
                dur = flow['duration']
                # Total bandwidth is for both upload and download traffic therefore one way traffic bandwidth should be half
                bw = flow['b_flow'] / 2
                delay = self.cn.fdata[fid]['p_flow'] / self.cn.G.node[flow['CLC']]['ProcFlow'][fid] * 1000
                bucket_id = int(round(delay * 10))
                hName = "h" + str(flow['CLC'])
                clcObj = self.TestbedNetwork.get(hName) if self.emulator == "Mininet" else self.TestbedNetwork.get_node(hName)
                clcIP = Tools.makeIP(flow['CLC'] + 1)
                for hObj in self.hObjs:
                    (n, obj) = hObj
                    id = bucket_id + n * 1000
                    bucket_id = bucket_id + n * 65536
                    hexFid = "0x%0.8x" % bucket_id
                    if False == self.checkBucketInCLC(flow['CLC'], bucket_id):
                        clcObj.cmd(g_conf_script_path + " add " + hName + "-eth0 1 " + str(id) + " " + str(delay) + " " + hexFid)
                    obj.cmd(g_iperf_path + " -u -c " + clcIP + " -f b -b " + str(bw) + " -t " + str(dur) + " -k " + str(bucket_id) + " > /tmp/iperf_client_" + str(fid) + "_" + str(bw) + "_" + str(dur) + "_" + str(obj.name) + "_to_" + str(hName) + ".log &")
                self.cn.fdata[fid]['genstime'] = time.time()
                self.cn.fdata[fid]['isGen'] = True
                iperfcount += 1
                self.TotalSatisfied.append(fid)
                if fid in self.TotalUnsatisfied:
                    self.TotalUnsatisfied.remove(fid)
            elif flow['isSat'] == False:
                self.TotalUnsatisfied.append(fid)
                print "Flow not satisfied : " + str(flow)
            else:
                pass # do nothing

        # print "New iperf client started:" + str(iperfcount)

    def generateTrafficForSingleFlow(self, fid):
        flow = self.cn.fdata[fid]
        if flow['isSat'] == True and flow['isGen'] == False:
            self.getHostForFlow(fid)
            dur = flow['duration']
            # Total bandwidth is for both upload and download traffic therefore one way traffic bandwidth should be half
            bw = flow['b_flow'] / 2
            delay = self.cn.fdata[fid]['p_flow'] / self.cn.G.node[flow['CLC']]['ProcFlow'][fid] * 1000
            bucket_id = int(round(delay * 10))
            hName = "h" + str(flow['CLC'])
            clcObj = self.TestbedNetwork.get(hName) if self.emulator == "Mininet" else self.TestbedNetwork.get_node(hName)
            clcIP = Tools.makeIP(flow['CLC'] + 1)
            for hObj in self.hObjs:
                (n,obj)=hObj
                id = bucket_id + n * 1000
                bucket_id = bucket_id + n * 65536
                hexFid = "0x%0.8x" % bucket_id
                if False == self.checkBucketInCLC(flow['CLC'], bucket_id):
                    clcObj.cmd(g_conf_script_path + " add " + hName + "-eth0 1 " + str(id) + " " + str(delay) + " " + hexFid)
                obj.cmd(g_iperf_path + " -u -c " + clcIP + " -f b -b " + str(bw) + " -t " + str(dur) + " -k " + str(bucket_id) + " > /tmp/iperf_client_" + str(fid) + "_" + str(bw) + "_" + str(dur) + "_" + str(obj.name) + "_to_" + str(hName) + ".log &")
            self.cn.fdata[fid]['genstime'] = time.time()
            self.cn.fdata[fid]['isGen'] = True
            self.TotalSatisfied.append(fid)
            if fid in self.TotalUnsatisfied:
                self.TotalUnsatisfied.remove(fid)
        elif flow['isSat'] == False:
            self.TotalUnsatisfied.append(fid)
            print "Flow not satisfied : " + str(flow)
        else:
            pass  # do nothing

    def stopTrafficGenerationForSingleFlow(self, fid):
        flow = self.cn.fdata[fid]
        currTime = time.time()
        # giving 0.01 sec extra time assuming the processing time of to start the ipref
        if (flow['duration'] > currTime - flow['genstime'] + 0.01) and flow['isSat'] == True and flow['isGen'] == True:
            # print "Why I am here duration " + str(flow['duration']) + " currTime " + str(currTime) + " genstime " + str(flow['genstime']) + " difference " + str(currTime - flow['genstime'])
            self.getHostForFlow(fid)
            clcIP = Tools.makeIP(flow['CLC'] + 1)
            dur = flow['duration']
            # Total bandwidth is for both upload and download traffic therefore one way traffic bandwidth should be half
            bw = flow['b_flow'] / 2
            searchStr = "iperf -u -c " + clcIP + " -f b -b " + str(bw) + " -t " + str(dur)
            for hObj in self.hObjs:
                (n,obj)=hObj
                obj.cmd("ps -eaf|grep \"" + searchStr + "\"|awk \'{print \"kill -9 \" $2}\'|sh")
            self.cn.fdata[fid]['duration'] = flow['duration'] - (currTime - flow['genstime'])
            self.cn.fdata[fid]['isGen'] = False
            self.TotalFlowStopped.append(fid)
            if fid in self.TotalSatisfied:
                self.TotalSatisfied.remove(fid)
                # print "stopped flow for " + str(fid) + " and search string is " + searchStr

    def getLinkPort(self, links, node1, node2):
        """Return ports of Links between node1 and node2"""
        port1 = port2 = None
        dpid1 = "0000" + self.Switches[node1]['dpid']
        dpid2 = "0000" + self.Switches[node2]['dpid']
        for link in links:
            if (dpid1, dpid2) == (link['src']['dpid'], link['dst']['dpid']):
                # print link
                port1 = int(link['src']['port_no'], 16)
                port2 = int(link['dst']['port_no'], 16)
                break
            elif (dpid1, dpid2) == (link['dst']['dpid'], link['src']['dpid']):
                # print link
                port1 = int(link['dst']['port_no'], 16)
                port2 = int(link['src']['port_no'], 16)
                break
            else:
                pass # do nothing
        return port1, port2

    def getHostForFlow(self, flow):
        del self.hObjs
        self.hObjs = []
        for n in self.cn.Wb[flow]:
            hName = 'h' + str(n)
            if self.emulator == "Mininet":
                # Mininet
                self.hObjs.append((n,self.TestbedNetwork.getNodeByName(hName)))
            elif self.emulator == "MaxiNet":
                # MaxiNet
                self.hObjs.append((n,self.TestbedNetwork.get_node(hName)))
            else:
                print("Error: Emulator missing!")
                exit(1)
        # return hObjs


