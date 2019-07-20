import time
import socket
import sys
from packet import packet

# main function
def main(commandlineArgs):
  # check if correct number of arguments is supplied
  if not len(commandlineArgs) == 5:
    print('Error: the number of parameter supplied is incorrect')
    sys.exit(2)
  
  hostAddr = commandlineArgs[1]
  hostPort = int(commandlineArgs[2])
  recvPort = int(commandlineArgs[3])
  fileName = commandlineArgs[4]

  # open log file and to-be-saved file
  file = open(fileName, 'w+')
  arrivalLog = open('arrival.log', 'w+')

  # create packet receiving packet
  rSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  rSocket.bind(('', recvPort))

  expectedSeqNum = 0

  firstRun = True

  # print('Listenning on port: %d' % recvPort)

  count = 0

  # start listening for packets
  while True:
    try:
      udpData = rSocket.recv(1024)
    except:
      print('Error: package error')
      sys.exit(2)
    # print('new packet')

    # process received packet
    dataPackage = packet.parse_udp_data(udpData)

    # the received packet is data
    if dataPackage.type == 1:
      # print('New packet: %d' % dataPackage.seq_num)
      # print('Expected: %d' % expectedSeqNum)

      # write newly received packet sequence number to log file
      arrivalLog.write('%d\n' % dataPackage.seq_num)

      # if the packet received has the expected sequence number
      # update expected sequence number and write data to file
      if dataPackage.seq_num == expectedSeqNum:
        file.write(dataPackage.data)
        expectedSeqNum += 1
        expectedSeqNum = expectedSeqNum % packet.SEQ_NUM_MODULO
        ackPkg = packet.create_ack(dataPackage.seq_num)
        firstRun = False
      else:
        # packet sequence number is not expected
        # resend ack packet with last received sequence number
        lastAckSeqNum = expectedSeqNum - 1
        if (lastAckSeqNum < 0):
          lastAckSeqNum = 31
        ackPkg = packet.create_ack(lastAckSeqNum)

      # if it's first run and packet sequence number is not correct
      # don't send any ack packet
      if not firstRun:
        rSocket.sendto(ackPkg.get_udp_data(), (hostAddr, hostPort))
      count += 1

    elif dataPackage.type == 2:
      # packet type is eot, send a eot packet then exit
      rSocket.sendto(packet.create_eot(expectedSeqNum - 1).get_udp_data(), (hostAddr, hostPort))
      sys.exit(0)

# wrapper main function
if __name__ == "__main__":
  main(sys.argv)