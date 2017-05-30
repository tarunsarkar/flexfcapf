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
        self.AllTraffic = []

    def readclientlogfile(self):
        totalClientFile = 0
        totalFlowConnected = 0
        totalFlowStatistics = 0
        # read input file
        try:
            for file in os.listdir(self.LogDir):
                # if fnmatch.fnmatch(file, 'iperf_server_h*.log'):
                if fnmatch.fnmatch(file, 'iperf_client_*.log'):
                    filepath = self.LogDir + "/" + file
                    self.FileList.append(filepath)
                    totalClientFile += 1

            connpat = "\[[0-9 ]+\] local .*connected with.*"
            statpat = "\[[0-9 ]+\].*sec.*Bytes.*bits.*sec.*"
            # statpat = "\[[0-9 ]+\] .*Bytes.*bits.*sec.*\(.*\).*"
            warnpat = "\[[0-9 ]+\] .*datagrams received out-of-order.*"
            globalid = 0
            for file in self.FileList:
                filedict = {'filename': file, 'flow': []}
                allflow = []
                tfile = os.path.basename(file)
#                tfile = tfile.replace('.', '_')
                ftoken = re.split("_", tfile)
                desttok = re.split("\.", ftoken[7])
                flow = {'filename': file,
                        'flowid': ftoken[2],
                        'flowbw': ftoken[3],
                        'flowrt': ftoken[4],
                        'flowsrc': ftoken[5],
                        'flowdst': desttok[0],
                        'gensrc': "",
                        'gendst': "",
                        'genrt': "",
                        'gentransamt': "",
                        'genbw': ""
                        }

                with open(file, "r") as ifile:
                    for line in ifile:
                        if re.match(connpat, line):
                            # Split connection line
                            line = line.replace('[',' ')
                            line = line.replace(']',' ')
                            token = re.split(" *", line)
                            flow['gensrc'] = token[3]
                            flow['gendst'] = token[8]
                            totalFlowConnected += 1
                        elif re.match(statpat, line):
                            # Split status line
                            line = line.replace('[',' ')
                            line = line.replace(']',' ')
                            line = line.replace('(',' ')
                            line = line.replace(')',' ')
                            line = line.replace('%',' ')
                            line = line.replace('/',' ')
                            line = line.replace('- ','-')
                            token = re.split(" *", line)
                            totalFlowStatistics += 1
                            timetok = re.split("-", token[2])
                            flow['genrt'] = timetok[1]
                            flow['gentransamt'] = token[4]
                            flow['genbw'] = token[6]
                            bStatForund = True
                        elif re.match(warnpat, line):
                            pass
                            # print "I am warning:" + line
                        else:
                            pass
                            # print "I am others:" + line
                self.AllTraffic.append(flow)
            print "Total Client File: " + str(totalClientFile)
            print "Total Flow Connected: " + str(totalFlowConnected)
            print "Total Flow Statistics: " + str(totalFlowStatistics)

        except:
            traceback.print_exc(file=sys.stdout)
            #traceback.print_stack()
            return False

    def printflowstat(self):
        bwAllDiff = []
        bwLessThanZero = [] # Bandwdth difference less < 0Kbit
        bwZeroToHundredB = [] # Bandwdth difference >= 0Kbit to <= 0.1Kbit
        bwHundredBToOne = [] # Bandwdth difference > 0.1Kbit to <= 1Kbit
        bwOneToFive = [] # Bandwdth difference > 1Kbit to <= 5Kbit
        bwFiveToTen = [] # Bandwdth difference > 5Kbit to <= 10Kbit
        bwMoreThanTen = [] # Bandwdth difference more than 10Kbit

        tAllDiff = []
        tLessThanMinusPointFive = [] # Time difference < -0.5Sec
        tMinusPointFiveToMinusPointTwo = [] # Time difference >= -0.5Sec < -0.2Sec
        tMinusPointTwoToMinusPointOne = [] # Time difference >= -0.2Sec < -0.1Sec
        tMinusPointOneToPointOne = [] # Time difference >= -0.1Sec to <= 0.1Sec
        tPointOneToPointTwo = [] # Time difference > 0.1Sec to <= 0.2Sec
        tPointTwoToPointFive = [] # Time difference > 0.2Sec to <= 0.5Sec
        tMoreThanPointFive = [] # Time difference more than 0.5Sec
        for flow in self.AllTraffic:
            # Bandwidth difference segregation
            try:
                bwdiff = float(flow['flowbw']) - float(flow['genbw'])
            except ValueError:
                # print "Bandwidth conversion failed:" + str(flow)
                continue
            bwAllDiff.append(bwdiff)
            if bwdiff < 0:
                bwLessThanZero.append(bwdiff)
            elif bwdiff >= 0 and bwdiff <= 100:
                bwZeroToHundredB.append(bwdiff)
            elif bwdiff > 100 and bwdiff <= 1000:
                bwHundredBToOne.append(bwdiff)
            elif bwdiff > 1000 and bwdiff <= 5000:
                bwOneToFive.append(bwdiff)
            elif bwdiff > 5000 and bwdiff <= 10000:
                bwFiveToTen.append(bwdiff)
            else:
                bwMoreThanTen.append(bwdiff)

            # Time difference segregation
            try:
                timediff = float(flow['flowrt']) - float(flow['genrt'])
            except ValueError:
                # print "Time conversion failed:" + str(flow)
                continue
            tAllDiff.append(timediff)
            if timediff < -0.5:
                tLessThanMinusPointFive.append(timediff)
            elif timediff >= -0.5 and timediff < -0.2:
                tMinusPointFiveToMinusPointTwo.append(bwdiff)
            elif timediff >= -0.2 and timediff < -0.1:
                tMinusPointTwoToMinusPointOne.append(bwdiff)
            elif timediff >= -0.1 and timediff <= 0.1:
                tMinusPointOneToPointOne.append(bwdiff)
            elif timediff > 0.1 and bwdiff <= 0.2:
                tPointOneToPointTwo.append(bwdiff)
            elif timediff > 0.2 and bwdiff <= 0.5:
                tPointTwoToPointFive.append(bwdiff)
            else:
                tMoreThanPointFive.append(bwdiff)

        # print "All Bandwidth Count:" + str(len(bwAllDiff))
        # plt.plot(bwAllDiff, 'ro')
        # plt.title("All Flow")
        # plt.ylabel("Bandwidth Difference")
        # plt.xlabel("Flow Ids")
        # plt.show()

        bwObjects = ('<0Kb', '0Kb>=to<=0.1Kb', '0.1Kb>to<=1Kb', '1Kb>to<=5Kb', '5Kb>to<=10Kb', '>10Kb')
        y_pos = np.arange(len(bwObjects))
        bwNumber = [len(bwLessThanZero), len(bwZeroToHundredB), len(bwHundredBToOne), len(bwOneToFive), len(bwFiveToTen), len(bwMoreThanTen), len(bwAllDiff)]
        print bwObjects
        print "Bandwidth Difference Count:" + str(bwNumber)
        print bwObjects
        bwPercent = [(len(bwLessThanZero)*100)/len(bwAllDiff), (len(bwZeroToHundredB)*100)/len(bwAllDiff), (len(bwHundredBToOne)*100)/len(bwAllDiff), (len(bwOneToFive)*100)/len(bwAllDiff), (len(bwFiveToTen)*100)/len(bwAllDiff), (len(bwMoreThanTen)*100)/len(bwAllDiff)]
        print "Bandwidth Difference Percent:" + str(bwPercent)

        # plt.bar(y_pos, bwPercent, align='center', alpha=0.5)
        # plt.xticks(y_pos, bwObjects)
        # plt.ylabel('Bandwidth Difference')
        # plt.title('Bandwidth Expected Vs Achived')
        # plt.show()

        # print "All Time Count:" + str(len(tAllDiff))
        # plt.plot(tAllDiff, 'ro')
        # plt.title("All Flow")
        # plt.ylabel("Time Difference")
        # plt.xlabel("Flow Ids")
        # plt.show()

        tObjects = ('<-0.5Sec', '-0.5Sec>=to<-0.2Sec', '-0.2Sec>=to<-0.1Sec', '-0.1Sec>=to<=0.1Sec', '0.1Sec>to<=0.2Sec', '0.2Sec>to<=0.5Sec', '>0.5Sec')
        y_pos = np.arange(len(tObjects))
        tNumber = [len(tLessThanMinusPointFive), len(tMinusPointFiveToMinusPointTwo), len(tMinusPointTwoToMinusPointOne), len(tMinusPointOneToPointOne), len(tPointOneToPointTwo), len(tPointTwoToPointFive), len(tMoreThanPointFive), len(tAllDiff)]
        print tObjects
        print "Time Difference Count:" + str(tNumber)
        tPercent = [(len(tLessThanMinusPointFive)*100)/len(tAllDiff), (len(tMinusPointFiveToMinusPointTwo)*100)/len(tAllDiff), (len(tMinusPointTwoToMinusPointOne)*100)/len(tAllDiff), (len(tMinusPointOneToPointOne)*100)/len(tAllDiff), (len(tPointOneToPointTwo)*100)/len(tAllDiff), (len(tPointTwoToPointFive)*100)/len(tAllDiff), (len(tMoreThanPointFive)*100)/len(tAllDiff)]
        print tObjects
        print "Time Difference Percent:" + str(tPercent)

        # plt.bar(y_pos, tPercent, align='center', alpha=0.5)
        # plt.xticks(y_pos, tObjects)
        # plt.ylabel('Time Difference')
        # plt.title('Time Expected Vs Achived')
        # plt.show()

        dtAllDiff = []
        dtAllDuration = 0.0
        dtLessThanZero = [] # Bandwdth difference less < 0Kbit
        dtZeroToHundredB = [] # Bandwdth difference >= 0Kbit to <= 0.1Kbit
        dtHundredBToOne = [] # Bandwdth difference > 0.1Kbit to <= 1Kbit
        dtOneToFive = [] # Bandwdth difference > 1Kbit to <= 5Kbit
        dtFiveToTen = [] # Bandwdth difference > 5Kbit to <= 10Kbit
        dtMoreThanTen = [] # Bandwdth difference more than 10Kbit
        for flow in self.AllTraffic:
            # Bandwidth difference segregation
            try:
                dtdiff = (float(flow['flowbw']) * float(flow['flowrt'])) - (float(flow['genbw']) * float(flow['genrt']))
                dtAllDuration += float(flow['flowrt'])
            except ValueError:
                # print "Bandwidth conversion failed:" + str(flow)
                continue
            dtAllDiff.append(dtdiff)
            if dtdiff < 0:
                dtLessThanZero.append(dtdiff)
            elif dtdiff >= 0 and dtdiff <= 5000:
                dtZeroToHundredB.append(dtdiff)
            elif dtdiff > 5000 and dtdiff <= 50000:
                dtHundredBToOne.append(dtdiff)
            elif dtdiff > 50000 and dtdiff <= 250000:
                dtOneToFive.append(dtdiff)
            elif dtdiff > 250000 and dtdiff <= 500000:
                dtFiveToTen.append(dtdiff)
            else:
                dtMoreThanTen.append(dtdiff)

        print "All data transfer Count:" + str(len(dtAllDiff))
        print "Average Duration:" + str(dtAllDuration/len(dtAllDiff))
        plt.plot(dtAllDiff, 'ro')
        plt.title("All Flow")
        plt.ylabel("Data transfer Difference")
        plt.xlabel("Flow Ids")
        plt.show()

        dtObjects = ('<0Kb', '0Kb>=to<=05Kb', '5Kb>to<=50Kb', '50Kb>to<=250Kb', '250Kb>to<=500Kb', '>500Kb')
        y_pos = np.arange(len(dtObjects))
        dtNumber = [len(dtLessThanZero), len(dtZeroToHundredB), len(dtHundredBToOne), len(dtOneToFive), len(dtFiveToTen), len(dtMoreThanTen), len(dtAllDiff)]
        print dtObjects
        print "Data transfer Difference Count:" + str(dtNumber)
        print dtObjects
        dtPercent = [(len(dtLessThanZero)*100)/len(dtAllDiff), (len(dtZeroToHundredB)*100)/len(dtAllDiff), (len(dtHundredBToOne)*100)/len(dtAllDiff), (len(dtOneToFive)*100)/len(dtAllDiff), (len(dtFiveToTen)*100)/len(dtAllDiff), (len(dtMoreThanTen)*100)/len(dtAllDiff)]
        print "Data transfer Difference Percent:" + str(dtPercent)
        plt.bar(y_pos, dtPercent, align='center', alpha=0.5)
        plt.xticks(y_pos, dtObjects)
        plt.ylabel('Data transfer Difference')
        plt.title('Data transfer Expected Vs Achived')
        plt.show()


if '__main__' == __name__:
    try:
        logDir = str(sys.argv[1])
    except:
        logDir = "/tmp"
    tf = TrafficDistribution(logDir)
    tf.readclientlogfile()
    tf.printflowstat()
