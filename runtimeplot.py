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
            # filename = "emu_results_pfo_fcfs_Test_16_mesh_comp.dat"
            # filename = "emu_results_pfo_fcfs_Test_16_mesh_gen.dat"
            # filename = "emu_results_pfo_fcfs_Test_36_mesh_comp.dat"
            # filename = "emu_results_pfo_fcfs_Test_36_mesh_gen.dat"
            # filename = "emu_results_pfo_fcfs_Test_36_ring_comp.dat"
            filename = "emu_results_pfo_fcfs_Test_36_ring_gen.dat"
            filepath = self.LogDir + "/" + filename
            self.FileList.append(filepath)
            timepat = "Time: *"
            systimepat = "System Time Passed: *"
            flowsatpat = "Flows satisfied: *"
            for file in self.FileList:
                print file
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
            algodifftime = []
            emudifftime = []
            totalgodifftime = 0
            totemudifftime = 0
            for entry in self.AllTraffic[filename]:
                emutime.append(entry['time'])
                algodifftime.append(entry['runtime'] * 1000)
                totalgodifftime = totalgodifftime + entry['runtime'] * 1000
                emudifftime.append(entry['netmodtime'] * 1000)
                totemudifftime = totemudifftime + entry['netmodtime'] * 1000
            plt.plot(emutime, algodifftime, marker='o', color='c')
            plt.plot(emutime, emudifftime, marker='o', color='r')
            figtxt = "Average = " + str(totalgodifftime/len(algodifftime))
            plt.figtext(0.15, 0.91, figtxt, bbox=dict(facecolor='cyan'))
            figtxt = "Average = " + str(totemudifftime/len(emudifftime))
            plt.figtext(0.6, 0.91, figtxt, bbox=dict(facecolor='red'))

            plt.ylabel('Runtime in ms')
            plt.xlabel('Emulation time in Sec')
            # plt.title('Emulation Time Vs Runtime')
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
