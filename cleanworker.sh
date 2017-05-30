#!/bin/bash

ps -eaf|grep mininet|awk '{print "sudo kill -9 " $2}'|sh
ps -eaf|grep MaxiNetWorker|awk '{print "sudo kill -9 " $2}'|sh
sudo mn -c
sudo screen -d -m -S MaxiNetWorker MaxiNetWorker


