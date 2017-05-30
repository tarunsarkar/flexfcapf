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
        self.AllPlotFive = []
        self.AllPlotTen = []
        self.AllPlotFifty = []

    def readclientlogfile(self):
        totalClientFile = 0
        totalFlowConnected = 0
        totalFlowStatistics = 0
        # read input file
        try:
            for file in os.listdir(self.LogDir):
                if fnmatch.fnmatch(file, 'echo*.log'):
                    filepath = self.LogDir + "/" + file
                    self.FileList.append(filepath)
                    totalClientFile += 1
            statpat = "All Delta:*"
            filepatfive = "echo_5_*"
            filepatten = "echo_10_*"
            filepatfifty = "echo_50_*"
            globalid = 0
            for file in self.FileList:
                tfile = os.path.basename(file)
                filedict = {'filename': tfile, 'alldelta': []}
                tfile = os.path.basename(file)
                with open(file, "r") as ifile:
                    for line in ifile:
                        if re.match(statpat, line):
                            # Split connection line
                            line = line[11:-2]
                            token = re.split(",", line)
                            filedict['alldelta']=token
                            if re.match(filepatfifty, tfile):
                                self.AllPlotFifty.append(filedict)
                            elif re.match(filepatten, tfile):
                                self.AllPlotTen.append(filedict)
                            elif re.match(filepatfive, tfile):
                                self.AllPlotFive.append(filedict)
                            else:
                                pass
                        else:
                            pass
                            # print "I am others:" + line
            alldelay = []
            totdeltafive = 0.0
            for f in self.AllPlotFive:
                for i in f['alldelta']:
                    delta = float(i) / 1000
                    alldelay.append(delta)
                    totdeltafive += delta
                plt.plot(alldelay, 'ro')
            print "Average of 5 : " + str(totdeltafive/len(alldelay))
            figtxt = "Average = " + str(totdeltafive/len(alldelay))
            plt.figtext(0.5, 0.45, figtxt, bbox=dict(facecolor='red'))
            alldelay = []
            totdeltaten = 0.0
            for f in self.AllPlotTen:
                for i in f['alldelta']:
                    delta = float(i) / 1000
                    alldelay.append(delta)
                    totdeltaten += delta
                plt.plot(alldelay, 'yo')
            print "Average of 10 : " + str(totdeltaten/len(alldelay))
            figtxt = "Average = " + str(totdeltaten/len(alldelay))
            plt.figtext(0.5, 0.50, figtxt, bbox=dict(facecolor='yellow'))
            alldelay = []
            totdeltafifty = 0.0
            for f in self.AllPlotFifty:
                for i in f['alldelta']:
                    delta = float(i) / 1000
                    alldelay.append(delta)
                    totdeltafifty += delta
                plt.plot(alldelay, 'go')
            print "Average of 50 : " + str(totdeltafifty/len(alldelay))
            figtxt = "Average = " + str(totdeltafifty/len(alldelay))
            plt.figtext(0.5, 0.55, figtxt, bbox=dict(facecolor='green'))

            # plt.title("Processing Delay Distribution")
            plt.ylabel("Delay in Miliseconds")
            plt.xlabel("Number of Packets")
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
