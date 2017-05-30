import os
import sys
import datetime
import subprocess
import time

print 'Starting'
server = str(sys.argv[1])
filter = str(sys.argv[2])
delay = str(sys.argv[3])

for i in range(0,100):
    filename = "/tmp/echo_" + delay + "_" + str(i) + ".log"
    # subprocess.Popen(["python", "/home/tarun/flexfcpf/code/echoclient.py", str(server), str(filter), filename, "&"])
    subprocess.Popen(["python", "/home/crowd/flexfcpf/code/echoclient.py", str(server), str(filter), filename, "&"])
    # os.system("python /home/crowd/flexfcpf/code/echoclient.py " + str(server) + " " + str(filter) + " /tmp/echo_" + str(i) + ".log &")
time.sleep(60)
