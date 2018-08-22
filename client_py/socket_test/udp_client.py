import socket
import sys

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#server_address = ('113.195.xxx.xxx', 57856)
#server_address = ('192.168.1.126', 8888)
#server_address = ('xxx.xxx.245.148',9999)
#server_address = ('118.212.208.19', 50380)


server_address = (sys.argv[1],int(sys.argv[2]))


message = b'i am udp client'

try:

    # Send data
    print('sending {!r}'.format(message))
    sock.bind(("0.0.0.0",8080))
    sent = sock.sendto(message, server_address)

    # Receive response
    print('waiting to receive')
    data, server = sock.recvfrom(4096)
    print('received {!r}'.format(data))

finally:
    print('closing socket')
    sock.close()
