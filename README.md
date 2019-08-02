### How to run the scripts (with network Emulator already running):
* Starting the sender: 
  
  `./sender.sh <host address of the network emu lator> <UDP port number used by the emulator to receive data from the sender> <UDP port number used by the sender to receive ACKs from the emulator> <name of the file to be transferred>`
  
  Example:
  ```bash
  $ ./sender.sh 129.97.167.27 9001 9002 "send.txt"
  ```
* Starting the receiver: 
    
    `./receiver.sh <hostname for the network emulator> <UDP port number used by the link emulator to receive ACKs from the receiver> <UDP port number used by the receiver to receive data from the emulator> emulator> <name of the file into which the received data is written>`

  Example:
  ```bash
  $ ./receiver.sh 129.97.167.27 9004 9003 "receive.txt"
  ```
  
### Python version: 
```
Python 3.6.7 (default, Oct 22 2018, 11:32:17) 
[GCC 8.2.0] on linux
```