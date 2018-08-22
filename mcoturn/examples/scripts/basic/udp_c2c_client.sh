#!/bin/sh
#
# This is an example of a script to run a "unsecure" TURN UDP client,
# in client-to-client fashion (when client talks to another client
# through their corresponding allocated relayed endpoints).
# Options:
# 1) -t is absent, it means that UDP networking is used.
# 5) -n 1000 means 1000 messages per single emulated client. Messages
# are sent with interval of 20 milliseconds, to emulate an RTP stream.
# 6) -m 10 means that 10 clients are emulated.
# 7) -y means "client to client" communication pattern. 
# the client calculates the peer address
# (which is the allocated relayed endpoint of the next client in array of clients).
# 8) -l 170 means that the payload size of the packets is 170 bytes 
# like average audio RTP packet).  
# 9) -s option is absent - it means that the client will be using 
# the "channel" mechanism for data.
# 10) 127.0.0.1 (the last parameter) is the TURN Server IP address.
# 11) -z 5 means that we want 5 ms interval between the packets (per each session).
#

# -v -n 1 -m 1 -y -l 170 -z 15 $@ 113.195.xxx.xxx -p 3488 -A 25001 -H 25002


if [ -d examples ] ; then
       cd examples
fi

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib/

PATH=examples/bin/:../bin/:bin/:${PATH} /home/dl/workspace/xxxxrtc/mcoturn/bin/turnutils_uclient \
 -v -n 1 -m 1 -y -l 170 -z 15 $@ 192.168.1.191 -p 3478 -A 25001 -H 25002

