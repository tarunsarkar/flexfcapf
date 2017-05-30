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
            # filename = "16mesh40gen.txt"
            # filename = "16mesh05comp.txt"
            # filename = "36mesh02comp.txt"
            # filename = "36mesh20gen.txt"
            filename = "36ring02comp.txt"
            # filename = "36ring20gen.txt"
            filepath = self.LogDir + "/" + filename
            self.FileList.append(filepath)
            timepat = "Time: *"
            systimepat = "System Time Passed: *"
            flowsatpat = "Flows satisfied: *"
            for file in self.FileList:
                print file
                tfile = os.path.basename(file)
                self.AllTraffic[tfile] = []

                flow = {'time': 0,
                        'systime': 0,
                        'folwsat': 0,
                        'outofflow': 0,
                        }
                bFound = False

                with open(file, "r") as ifile:
                    for line in ifile:
                        if re.match(timepat, line):
                            # Split connection line
                            token = re.split(" ", line)
                            flow['time'] = token[1]
                        elif re.match(systimepat, line):
                            # Split status line
                            token = re.split(" ", line)
                            flow['systime'] = token[3]
                        elif re.match(flowsatpat, line):
                            token = re.split(" ", line)
                            flow['folwsat'] = token[2]
                            flow['outofflow'] = token[5]
                            bFound = True
                        else:
                            pass
                            # print "I am others:" + line
                        if bFound == True:
                            self.AllTraffic[tfile].append(flow)
                            flow = {'time': 0,
                                    'systime': 0,
                                    'folwsat': 0,
                                    'outofflow': 0,
                                    }
                            bFound = False
                    ifile.close()
            simtime = []
            difftime = []
            min = 0
            max = 0
            for entry in self.AllTraffic[filename]:
                simtime.append(float(entry['time']))
                dt = float(entry['time']) - float(entry['systime'])
                difftime.append(dt)
                if dt > max:
                    max = dt
                if dt < min:
                    min = dt
            plt.plot(simtime, difftime, marker='o', color='b')
            figtxt = "Min = " + str(min)
            plt.figtext(0.15, 0.91, figtxt, bbox=dict(facecolor='cyan'))
            figtxt = "Max = " + str(max)
            plt.figtext(0.67, 0.91, figtxt, bbox=dict(facecolor='magenta'))

            plt.ylabel('Time difference in Sec')
            plt.xlabel('Emulation time in Sec')
            plt.show()

        except:
            traceback.print_exc(file=sys.stdout)
            #traceback.print_stack()
            return False

    def printflowstat(self):

        # simtime = [float(i['time']) for i in self.AllTraffic['16mesh05comp.txt']]
        # difftime = [float(i['time'])-float(i['systime']) for i in self.AllTraffic['16mesh05comp.txt']]
        # plt.plot(simtime, difftime, marker='o', color='m')

        # simtime = [float(i['time']) for i in self.AllTraffic['36mesh20gen.txt']]
        # systime = [float(i['systime']) for i in self.AllTraffic['36mesh20gen.txt']]
        # difftime = [float(i['time'])-float(i['systime']) for i in self.AllTraffic['36mesh20gen.txt']]
        # folwsat = [float(i['folwsat']) for i in self.AllTraffic['36mesh20gen.txt']]
        # outofflow = [float(i['outofflow']) for i in self.AllTraffic['36mesh20gen.txt']]
        # plt.plot(simtime, difftime, marker='o', color='c')

        # simtime = [float(i['time']) for i in self.AllTraffic['36ring20gen.txt']]
        # difftime = [float(i['time'])-float(i['systime']) for i in self.AllTraffic['36ring20gen.txt']]
        # plt.plot(simtime, difftime, marker='o', color='r')

        # simtime = [float(i['time']) for i in self.AllTraffic['36mesh02comp.txt']]
        # difftime = [float(i['time'])-float(i['systime']) for i in self.AllTraffic['36mesh02comp.txt']]
        # plt.plot(simtime, difftime, marker='o', color='g')

        simtime = [float(i['time']) for i in self.AllTraffic['36ring02comp.txt']]
        difftime = [float(i['time'])-float(i['systime']) for i in self.AllTraffic['36ring02comp.txt']]
        plt.plot(simtime, difftime, marker='o', color='y')

        plt.ylabel('Difference Time in Sec')
        plt.xlabel('Emulation Time in Sec')
        plt.title('Emulation Time Vs System Time difference')
        plt.show()

if '__main__' == __name__:
    try:
        logDir = str(sys.argv[1])
    except:
        logDir = "/tmp"
    tf = TrafficDistribution(logDir)
    tf.readclientlogfile()
    # tf.printflowstat()
