#!/bin/bash

ps -eaf|grep MaxiNetFrontend|awk '{print "sudo kill -9 " $2}'|sh
sudo ps -eaf|grep fcapf_ryu_controller|awk '{print "kill -9 " $2}'|sh
sudo mn -c
screen -d -m -S MaxiNetFrontend MaxiNetFrontendServer
#screen -d -m -S fcpf_ryu_controller /home/maxinet/ryu/bin/ryu-manager --observe-links /home/maxinet/flexfcapf/fcapf_ryu_controller.py


