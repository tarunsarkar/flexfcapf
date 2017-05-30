import socket
import sys
import codecs
import datetime

AllDiffTime = []
server = str(sys.argv[1])
filter = str(sys.argv[2])
filename = str(sys.argv[3])

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (server, 5001)
data = codecs.decode(filter, "hex_codec")
# # Send data
# print >>sys.stderr, 'sending "%s"' % data
# print "Before sending:"
# bst = datetime.datetime.now()
# sent = sock.sendto(data, server_address)
# print "After sending:"
# ast = datetime.datetime.now()
#
# # Receive response
# print >>sys.stderr, 'waiting to receive'
# print "Before receiving:"
# brt = datetime.datetime.now()
# data, server = sock.recvfrom(4096)
# print "After receiving:"
# art = datetime.datetime.now()
# print >>sys.stderr, 'received "%s"' % data
# print art-brt
print 'start sending packet'
for i in range(0,1000):
    sent = sock.sendto(data, server_address)
    brt = datetime.datetime.now()
    data, server = sock.recvfrom(2048)
    art = datetime.datetime.now()
    delta = art-brt
    AllDiffTime.append(delta.microseconds)

totdelta = 0
for delta in AllDiffTime:
    totdelta += delta
avgdelta = totdelta / len(AllDiffTime)
f = open(filename, 'w')
f.write("All Delta:" + str(AllDiffTime) + "\nAverage Delta:" + str(avgdelta) + "\n")
f.close()
print 'closing socket'
#sock.shutdown(socket.SHUT_RDWR)
sock.close()

