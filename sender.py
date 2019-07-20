import threading
import time
import socket
import sys
from packet import packet

# functino for getting current time in miliseconds
getMiliTime = lambda: int(round(time.time() * 1000))

seqNumLock = threading.Lock();
noMoreAckLock = threading.Lock();
lastAckSeqNum = -1
lastAckChanged = False
noMoreAck = False

# function for ack receiver thread
def genACKReceiver(portNumber):
  # print("Listening for ACKs on Port: %d" % portNumber)

  # Create new UDP socket and bind to a randomly assigned avaliable port
  global lastAckSeqNum
  global lastAckChanged
  global noMoreAck

  # create ack receiver port based on supplied port number
  rSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  rSocket.bind(('', portNumber))

  # start listening for ack packets
  while True:
    noMoreAckLock.acquire()
    # check if main thread ended
    if noMoreAck:
      noMoreAckLock.release()
      return
    noMoreAckLock.release()
    try:
      ackMessage = rSocket.recv(1024)
    except:
      # Error case, the connection is lost or the message is invalid
      sys.exit(3)
    ackPackage = packet.parse_udp_data(ackMessage)

    # process all ack packet
    if (ackPackage.type == 0):
      # print("New ack: %d" % ackPackage.seq_num)
      # print("Last ack: %d" % lastAckSeqNum)

      # write the received ack packet to log file
      with open('ack.log', 'a+') as file:
        file.write("%d\n" % ackPackage.seq_num)
        file.close()

      # only update last received ack packet sequence number
      # when a new different ack is received
      seqNumLock.acquire()
      ackDiff = ackPackage.seq_num - lastAckSeqNum
      if ackDiff > 0:
        lastAckSeqNum = ackPackage.seq_num
        lastAckChanged = True
      elif ackDiff >= -31 and ackDiff <= -23:
        lastAckSeqNum = ackPackage.seq_num
        lastAckChanged = True
      seqNumLock.release()
      

# Function for sending packets
def sendPackages(pkgList, addr, port, recvPort):
  global lastAckSeqNum
  global lastAckChanged
  global noMoreAck

  # create sender socket
  sSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sSocket.bind(('', 0))

  baseSeqNum = 0
  baseIdxNum = 0
  currentPkgIdx = 0

  # create new thread for ack receiver, pass in function and receiver port
  receiver = threading.Thread(target=genACKReceiver, args = (recvPort,))
  receiver.daemon = True
  receiver.start()

  firstRun = True
  pause = False

  # start looping through all packets
  while baseIdxNum < len(pkgList):

    # check if new ack is received, 
    # update timer and new base sequence number accordingly
    seqNumLock.acquire()
    if lastAckChanged:
      lastAckChanged = False
      newBase = lastAckSeqNum + 1
      diff = newBase - baseSeqNum
      if diff < 0:
        diff += 32
      if newBase > 31:
        newBase -= 32
      baseIdxNum += diff
      baseSeqNum = newBase
      packageTimerStart = getMiliTime()
    seqNumLock.release()

    # initialize timer for first run
    if firstRun:
      packageTimerStart = getMiliTime()
      firstRun = False

    # check if the timer is expired,
    # update timer if timeout happens,
    # reset current sending packet to the base
    if (getMiliTime() - packageTimerStart) > 100:
      # print('timeout')

      currentPkgIdx = baseIdxNum
      packageTimerStart = getMiliTime()
      pause = False

    # send packets to the specified port
    if not pause:
      sSocket.sendto(pkgList[currentPkgIdx].get_udp_data(), (addr, port))

      # write all sent packet to the log file
      with open('seqnum.log', 'a+') as file:
        file.write("%d\n" % pkgList[currentPkgIdx].seq_num)
        file.close()

    # check if packet window limit is reached or all packets are sent,
    # wait for window update if window limit is reached
    currentPkgIdx += 1
    if currentPkgIdx < baseIdxNum + 10 and currentPkgIdx < len(pkgList):
      pause = False
    else:
      pause = True
  
  # all packets are sent and all acks are received
  # inform ack receiver thread to exit, send eot packet
  noMoreAckLock.acquire()
  noMoreAck = True
  noMoreAckLock.release()
  eotPkg = packet.create_eot(len(pkgList) - 1)
  sSocket.sendto(eotPkg.get_udp_data(), (addr, port))
  receiver.join()
  return

# main function
def main(commandlineArgs):
  # check if correct number of arguments is supplied
  if not len(commandlineArgs) == 5:
    print('Error: the number of parameter supplied is incorrect')
    sys.exit(2)

  hostAddr = commandlineArgs[1]
  hostPort = int(commandlineArgs[2])
  ackPort = int(commandlineArgs[3])
  fileName = commandlineArgs[4]

  # open and prepare files
  fileToBeSent = open(fileName, 'r')
  seqNumLog = open('seqnum.log', 'w+')
  ackLog = open('ack.log', 'w+')

  # clear the content of log files before writing
  seqNumLog.write('')
  ackLog.write('')
  seqNumLog.close()
  ackLog.close()

  # read to-be-sent file content to a variable
  if fileToBeSent.mode == 'r':
    fileContent = fileToBeSent.read()
  else:
    print('Error: cannot open file to be sent')
    sys.exit(3)

  # calculate the number of packets needed to send the file
  numOfPkgs = len(fileContent) // 500
  if len(fileContent) % 500 > 0:
    numOfPkgs += 1

  pkgList = []

  # create a list of packets to be sent
  for i in range(0, numOfPkgs):
    if i == numOfPkgs - 1:
      start = i * 500
      end = len(fileContent)
    else:
      offset = i * 500
      start = 0 + offset
      end = 500 + offset
    newPkg = packet.create_packet(i, fileContent[start:end])
    pkgList.append(newPkg)

  # send the packets using the sending function
  sendPackages(pkgList, hostAddr, hostPort, ackPort)
  sys.exit(0)

# wrapper main function
if __name__ == "__main__":
  main(sys.argv)