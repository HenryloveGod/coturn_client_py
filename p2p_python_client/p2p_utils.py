
import struct
import socket
import ipaddress
import sys
import logging
import os, signal

MESSAGE_MAX_LENGTH = 10240
STUN_HEADER_LENGTH = (20)

FAMILY_IPV4 = 0x0001

logging.basicConfig(
    stream = sys.stdout,
    level=logging.DEBUG,
    format=' %(filename)s[%(funcName)s][line:%(lineno)d] %(message)s',
    datefmt='%Y-%M-%D'
    )


def timeout_handle(num,b):
    logging.error("TIME OUT ")

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip



MY_LOCAL_IP = get_host_ip()



'''
    int类型转化为unsigned char array
@num    int位数
@value  int值
'''

def int_to_unsiged_array(value,num=1):
    pack_type = {
        1:">B",
        2:">H",
        4:">L",
        8:">Q"
    }
    if not num in pack_type:
        return None

    if not isinstance(value,int):
        print("error !!!!!!!!!!!!!!!!!")
        print(value)
        

    return struct.pack(pack_type[num], value)    


def bytes_to_int(data_bytes):
    r = 0
    for i in data_bytes:
        r = r * 256 + i

    return r



'''
    拼接一个int到msg_buf，int位数由bit_num决定
@msg_buf
@sttp       msg_buf起始位置
@endp       msg_buf结束位置
@src        要拼接的int
@bit_num    int的位数
'''
def set_int_to_msg_buf(msg_buf,sttp,src,bit_num):
    src_array = int_to_unsiged_array(src,bit_num)
    for i in range(0,bit_num,1):
        msg_buf[sttp+i]=src_array[i]
    return msg_buf

'''
 拼接buf到msg_buf中，
@msg_buf    
@sttp       msg_buf起始位置
@src        要拼接的内容
@bit_num    要拼接内容的长度 
'''

def set_buf_to_msg_buf(msg_buf,sttp,src,bit_num):

    for i in range(bit_num):
        msg_buf[sttp+i]=src[i]
    return msg_buf

'''
    拼装addr={ip_str,port_int}成8字节
    FAMILI 2  PORT 2
    ADDR 4
'''
def covert_addr_to_buf_array(addr):
    buf = bytearray(8)
    buf = set_int_to_msg_buf(buf,0,FAMILY_IPV4,2)
    buf = set_int_to_msg_buf(buf,2,addr[1],2)
    ip_int = int(ipaddress.IPv4Address(addr[0]))
    buf = set_int_to_msg_buf(buf,4,ip_int,4)
    return buf

#   ip转化为4字节的int
def iptoint(ip):
    return int(socket.inet_aton(ip).encode('hex'),32)

#   ip整数转化为ip string
def inttoip(ip):
    return socket.inet_ntoa(hex(ip)[2:].decode('hex'))



'''
    获取一个socket连接
@addr (ip,port) 要连接的server
    return (local_addr,s) local_addr 为本地的(ip,port),s 为socket连接
'''
def get_new_socket(allocation_times = 0 ,port=12345,connect_server_addr = None,timeout = 0):
    
    port = port +allocation_times
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #s.setblocking(0)
    s.bind((MY_LOCAL_IP,port))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if timeout >0:
        s.settimeout(timeout)
    if connect_server_addr:
        s.connect(connect_server_addr)
    local_addr = (MY_LOCAL_IP,s.getsockname()[1])
    #logging.debug("GET NEW SOCKET listening [%s:%d]" % (s.getsockname()[0],s.getsockname()[1]))
    return local_addr,s


'''
    获取一个socket连接
@addr (ip,port) 要连接的server
    return (local_addr,s) local_addr 为本地的(ip,port),s 为socket连接
'''
def get_new_connect_socket(addr,port=8888):

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(addr)
    local_addr = (s.getsockname()[0],s.getsockname()[1])
    logging.debug("GET NEW SOCKET connecting [%s:%d] with local[%s:%d]" % (addr[0],addr[1],local_addr[0],local_addr[1]))
    return local_addr,s