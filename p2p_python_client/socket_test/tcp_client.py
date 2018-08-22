import socket,time
import sys

try:

    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
except Exception as e:

    print(e)
    sys.exit()
s.connect(('192.168.0.101',3478))

while True:
    st = 'input command: '
    if not st:break
    s.send(st.encode('utf-8'))
    
    echo_back = s.recv(1024)
    print(echo_back.decode('utf-8'))

    sys.exit(

    )
 
s.close()