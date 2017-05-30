#!/usr/bin/env python

import sys
import os
import fnmatch
import re
import traceback
import random
import math

import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt


obj = ["#Satisfied","#CRCs","#CLCs","#CLCDiff","#nodeDiff","#flowDiff","CRCpathlength","CLCpathlength","CLCload","controlRatio","runtime", "netmodtime"]

class TrafficDistribution:
    def __init__(self, logDir):
        self.LogDir = logDir
        self.FileList = []
        self.AllTraffic = {}

    def readclientlogfile(self):
        totalClientFile = 0
        totalFlowConnected = 0
        totalFlowStatistics = 0
        # read input file
        try:
            filename = "sim_results_pfo_fcfs_Test_36_mesh_gen.dat"
            filepath = self.LogDir + "/" + filename
            self.FileList.append(filepath)
            filename = "emu_results_pfo_fcfs_Test_36_mesh_gen.dat"
            filepath = self.LogDir + "/" + filename
            self.FileList.append(filepath)
            timepat = "Time: *"
            systimepat = "System Time Passed: *"
            flowsatpat = "Flows satisfied: *"
            for file in self.FileList:
                tfile = os.path.basename(file)
                self.AllTraffic[tfile] = []

                fin = open(file, "r")
                tmp = fin.readline()

                while True:
                    tmp = fin.readline().split(" ")
                    entry = {}
                    try:
                        # entry["counter"] += 1
                        entry["time"] = float(tmp[0])
                        entry["flows"] = int(tmp[1])
                        for i in range(0, 6):
                            entry[obj[i]] = int(tmp[i + 2])
                        for i in range(6, len(obj)):
                            entry[obj[i]] = float(tmp[i + 2])
                        self.AllTraffic[tfile].append(entry)
                    except:
                        traceback.print_exc(file=sys.stdout)
                        break
            emutime = []
            simtime = []
            emuclcused = []
            simclcused = []
            filename = "sim_results_pfo_fcfs_Test_36_mesh_gen.dat"
            for entry in self.AllTraffic[filename]:
                simtime.append(entry['time'])
                simclcused.append(entry['#CLCs'])

            filename = "emu_results_pfo_fcfs_Test_36_mesh_gen.dat"
            for entry in self.AllTraffic[filename]:
                emutime.append(entry['time'])
                emuclcused.append(entry['#CLCs'])

            plt.plot(simtime, simclcused, 'bv')
            # figtxt = "Simulation"
            # plt.figtext(0.2, 0.80, figtxt, bbox=dict(facecolor='cyan'))
            plt.ylabel('Number of LCA used')
            plt.xlabel('Simulation time in Sec')
            plt.show()

            plt.plot(emutime, emuclcused, 'rv')
            # figtxt = "Emulation"
            # plt.figtext(0.2, 0.85, figtxt, bbox=dict(facecolor='red'))
            plt.ylabel('Number of LCA used')
            plt.xlabel('Emulation time in Sec')
            plt.show()


        except:
            traceback.print_exc(file=sys.stdout)
            #traceback.print_stack()
            return False

if '__main__' == __name__:
    try:
        logDir = str(sys.argv[1])
    except:
        logDir = "/tmp"
    tf = TrafficDistribution(logDir)
    tf.readclientlogfile()
