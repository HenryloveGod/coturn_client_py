import select
import socket
from p2p_definition import *
from p2pmsg_recv import allocation_recv_handle,dismessage
import json
from time import sleep

import threading

from p2p_allocation import *
from threading import Timer

from raw_socket import *

import time

lock=threading.Lock()

is_padding_continue = True




# 尝试与peer_addr 建立连接

def test_connect_peer_loop(allocation_times,guess_peer_addr,my_user,timeout=10,my_defend_addr = None,new_socket = None,padding_hole_range = 100):

    # if allocation_times == 5:
    #     print("=============== user raw data !!!!!!!!!!")
    #     if my_defend_addr ==None:
    #         a_addr = ('113.195.207.216', 3488)
    #     else:
    #         a_addr = my_defend_addr
    #     new_socket = raw_udp_send(" TESETTTTTTTTTTTTT111111111111111", guess_peer_addr, src_addr=a_addr)
    # else: 
    #     a_addr,new_socket = get_new_socket(allocation_times=allocation_times,connect_server_addr= guess_peer_addr,timeout= timeout )

    if new_socket == None:
        logging.error("new_socket please input ")
        sys.exit(-1)
  
    

    times = 0
    try_times = 0
    while True:
        try:

            try_times=0
            new_socket.settimeout(timeout)
            new_peer_addr = (guess_peer_addr[0],guess_peer_addr[1] + try_times)
            msg_to_send = "user[%d:%d] send [hello] times[%d] " % (my_user[0],my_user[1],times)
            logging.debug("TRY TO CNNECT [%s:%d] send [%s]" % (new_peer_addr[0],new_peer_addr[1],msg_to_send))
            new_socket.sendto(bytes(msg_to_send,encoding="utf-8"),new_peer_addr)
            data,addr = new_socket.recvfrom(MESSAGE_MAX_LENGTH)
            logging.debug("RECIEVED FROM [%s:%d] data[%s]" % (addr[0],addr[1],data.hex()))
            print("[%s]" % data.decode("utf-8") )
            times = times + 1
            print("GOT TEST OK !!!!!!!!!!!! CONTINUE ..........")
            continue
        except Exception as e:
            print(e)
            print("Error while connecting to peer[{}]".format(guess_peer_addr))
            try_times = try_times+1
            if try_times >100:
                try_times = -10
            continue

#上线

def step_allocate(max_allocation_times,coturn_server,my_user,ask_user ,
                    onwaiting= 0,allocation_times_stt = 0):

    allocation_gain = None
    allocation_times = allocation_times_stt
    allocation_gain = None

    my_mapped_addr=[]
    stun_server_cnn = None
    print(allocation_times,max_allocation_times)
    if allocation_times > max_allocation_times:
        logging.error("刚走 第一步就 allocation_times < max_allocation_times ,错误退出.....")
        sys.exit()


    while(allocation_times < max_allocation_times):
        logging.debug("ALLOCATION NO.[%d]" % allocation_times)
        #初始化
        #第一步  allocation
        stun_server_cnn = stun_allocation_class(coturn_server,onwaiting=onwaiting,max_allocation_times=10,my_user = my_user,ask_user=ask_user)

        allocation_gain = stun_server_cnn.allocation_start(allocation_times)
        if STUN_ATTRIBUTE_XOR_MAPPED_ADDRESS in allocation_gain:
            g = allocation_gain[STUN_ATTRIBUTE_XOR_MAPPED_ADDRESS][0]
            port =  g["port"]
            ip =    g["ip"]
            addr =(ip,port)
            logging.info("MY MAPPED ADDR [%s:%d]"%(addr))

            if addr not in my_mapped_addr:
                my_mapped_addr.append(addr)
        

        allocation_times = allocation_times + 1

    if stun_server_cnn == None:
        logging.error("stun_server_cnn is None EXITING ....")
        sys.exit(-1)

    return allocation_gain,my_mapped_addr,stun_server_cnn,allocation_times



# 请求用户信息
def step_ask_user(stun_server_cnn):
    ask_gain = stun_server_cnn.method_eotu_ask_user_start()
    
    if STUN_ATTRIBUTE_RES_USER_INFO_RELAYED_ADDR not  in ask_gain:
        logging.error("no STUN_ATTRIBUTE_RES_USER_INFO_RELAYED_ADDR EXITING...")
        sys.exit(-1)
    
    if STUN_ATTRIBUTE_RES_USER_INFO_MAPEED_ADDR not in ask_gain:
        logging.error("no STUN_ATTRIBUTE_RES_USER_INFO_MAPEED_ADDR EXITING...")
        sys.exit(-1) 

    return ask_gain


def refresh_thread(stun_server_cnn,freq,wait_recv = 1):    
    stun_server_cnn.method_refresh_start()
    t = Timer(freq, refresh_thread, (stun_server_cnn,freq,wait_recv))
    t.start()

# 心跳刷新
def step_refresh(stun_server_cnn,timeout = 10,use_thread = 0,freq = 60,wait_recv = 1):

    #refresh_gain = stun_server_cnn.method_refresh_start()
    if use_thread == 1:
        logging.debug("####################CREATE NEW THREAD FRESHING LOOP ...")
        t = threading.Thread(target =  refresh_thread, args = (stun_server_cnn,freq,wait_recv,))
        t.setName("threadport_fresh")
        t.start() 
    else:
        logging.debug("##############################STARTING TO REFRESH ONCE ...")

        stun_server_cnn.method_refresh_start()
  



#创建许可
def step_create_permission(stun_server_cnn,peer_addr):
        #第四步 create permission
    logging.debug("##############################STARTING TO CREATE PERMISSION  peer_addr[%s:%d]..." % peer_addr)
    stun_server_cnn.method_create_permission_start(peer_addr)


#发送中转数据
def step_method_send(stun_server_cnn,send_data,ask_user,server = None,is_wait = 1):
    times = 0
    while True:
        sleep(1)
        send_data_times = "%s times[%d]" % (send_data,times)
        method_gain =  stun_server_cnn.method_send_start(bytes(send_data_times,encoding="utf-8"),ask_user,server = server,is_wait = is_wait)
        try:
            print(json.dumps(method_gain,indent=2))
        except Exception as e:
            print(method_gain)
        times = times+1

'''
中转测试

'''

def start_test_turn_by_method_send(ask_user,my_user,coturn_server,max_allocation_times = 0):

    allocation_gain,my_mapped_addr,stun_server_cnn,allocation_times = step_allocate(1 ,
                    coturn_server ,my_user,ask_user ,onwaiting= 0)
    logging.info("==== MY MAPPED ADDR")
    logging.info(json.dumps(my_mapped_addr,indent=2))

    # ask_gain = step_ask_user(stun_server_cnn)
    # logging.info("======================= ASK USER MAPPED ADDR")
    # logging.info(json.dumps(ask_gain[STUN_ATTRIBUTE_RES_USER_INFO_MAPEED_ADDR],indent=2))
    
    # one_gain = ask_gain[STUN_ATTRIBUTE_RES_USER_INFO_RELAYED_ADDR][0]
    # peer_addr = (one_gain["ip"],one_gain["port"])
    # step_refresh(stun_server_cnn)
    # step_create_permission(stun_server_cnn,peer_addr)

    # send_data = "user[%d] send [hello]" % (my_user[0])   
    # logging.debug("##############################STARTING TO CONNECT USER peer_addr[{}] send_data[{}]".format(peer_addr,send_data))
    # sleep(2)
    
    send_data = "user[%d] channel[%d] send [hello]" % (my_user[0],my_user[1]) 
    step_method_send(stun_server_cnn,send_data,ask_user,coturn_server,1)




'''
    根据ask_gain 得到 p2p通信的 addr 
'''

def guess_peer_ip_port(ask_gain,allocation_gain=None,padding_type_port_add_num=0):

    port_rsv = []
    peer_ip=None
    peer_new_port = 0

    #判断是否同一个局域网，就获取对方的 real_addr
    if allocation_gain !=None:
        if STUN_ATTRIBUTE_XOR_MAPPED_ADDRESS in allocation_gain:
            my_mapped_ip = allocation_gain[STUN_ATTRIBUTE_XOR_MAPPED_ADDRESS][0]["ip"]
            if my_mapped_ip == peer_ip:
                if STUN_ATTRIBUTE_RES_USER_INFO_REAL_ADDR in ask_gain:
                    peer_ip = ask_gain[STUN_ATTRIBUTE_RES_USER_INFO_REAL_ADDR][0]["ip"]
                    for p in ask_gain[STUN_ATTRIBUTE_RES_USER_INFO_REAL_ADDR]:
                        port_rsv.append(p["port"])
                    
                    peer_new_port = max(port_rsv)+padding_type_port_add_num
                    return (peer_ip,peer_new_port)


    for p in ask_gain[STUN_ATTRIBUTE_RES_USER_INFO_MAPEED_ADDR]:
        port_rsv.append(p["port"])
        peer_ip = p["ip"]

    peer_new_port = max(port_rsv) + padding_type_port_add_num
    return (peer_ip,peer_new_port)


'''
    根据2个服务器的ask_gain 得到 p2p通信的 addr 
'''


def cook_ask_gains(ask_gain1):
    port_list = []
    ip_list = []
    response_strings = ""
    for p in ask_gain1[STUN_ATTRIBUTE_RES_USER_INFO_MAPEED_ADDR]:
        
        if p["ip"] not in ip_list:
            ip_list.append(p["ip"])

        port_list.append(p["port"])

        if p["ip"] not in response_strings:
            response_strings = "%s\n%s\n" %(response_strings,p["ip"])
        response_strings = "%s;%d" %(response_strings,p["port"])
    
    return response_strings,ip_list,port_list




def guess_peer_ip_port_by_one(ask_gain1,coturn_server1,padding_type_port_add_num):

    response_strings1,ip_list1,port_list1 = cook_ask_gains(ask_gain1)

    if len(ip_list1) == 1:
        ip = ip_list1[0]
        max_port = max(port_list1)+padding_type_port_add_num
        print("\n====================================================\n")
        print("对方 MAPPED IP:%s" % ip)
        print("对方 port[%s]" % ";".join( map(str,port_list1)))

        if padding_type_port_add_num >0:
            print("端口号  = max  + %d" % padding_type_port_add_num)
        print("可能地址： [%s:%d]" %(ip,max_port))
        print("\n====================================================\n")

        return (ip,max_port)
    else:
        print("\n====================================================\n")
        print("ERROR! IP不一致，无法猜测 ")
        print(ip_list1)
        print("对方 %s" % response_strings1)
        print("\n====================================================\n")

        return ("error !! 无法猜测",0)   


def guess_peer_ip_port_by_two(ask_gain1,ask_gain2,coturn_server1,coturn_server2,padding_type_port_add_num):

    response_strings1,ip_list1,port_list1 = cook_ask_gains(ask_gain1)
    response_strings2,ip_list2,port_list2 = cook_ask_gains(ask_gain2)
   
    if len(ip_list1) == 1 and len(ip_list2) ==1 and ip_list1[0] == ip_list2[0]:
        ip = ip_list1[0]
        max_port = max((max(port_list1),max(port_list2)))+padding_type_port_add_num
        print("\n====================================================\n")
        print("对方 MAPPED IP:%s" % ip)
        print("对方抚州 port[%s]" % ";".join( map(str,port_list1)))
        print("对方香港 port[%s]" % ";".join( map(str,port_list2)))
        if padding_type_port_add_num >0:
            print("端口号  = max  + %d" % padding_type_port_add_num)
        print("可能地址： [%s:%d]" %(ip,max_port))
        print("\n====================================================\n")

        return (ip,max_port)
    else:
        print("\n====================================================\n")
        print("ERROR! IP不一致，无法猜测 ")
        print(ip_list1)
        print(ip_list2)
        print("对方 抚州 %s" % response_strings1)
        print("对方 香港 %s" % response_strings2)
        print("\n====================================================\n")

        return ("error !! 无法猜测",0)   


def get_my_mapped_ports_string(my_mapped_addr_list):
    response = ""
    port_list =[]
    ip_list= []
    for l in my_mapped_addr_list:
        if l[0] not in response:
            response = "%s\n%s" %(response,l[0])
            ip_list.append(l[0])
        response = "%s\n%d" %(response,l[1])
        port_list.append(l[1])

    return response,port_list,ip_list



def get_my_probable_addr_by_one(my_mapped_addr_list1,padding_type_port_add_num):
    response1,port_list1,ip_list1 = get_my_mapped_ports_string(my_mapped_addr_list1)

    if len(ip_list1) == 1 :
        ip = ip_list1[0]
        port = max(port_list1) + padding_type_port_add_num
        print("我的 MAPPED IP:%s" % ip)
        print("我的 port[%s]" % ";".join(  map(str,port_list1)))
        if padding_type_port_add_num >0:
            print("MAX PORT = max + %d" % padding_type_port_add_num)
        print("MAX PORT [%d]" %(port))

        probable_ip = (ip,port)
        return probable_ip
    else:
        print("IP多个，无法打洞～～")
        print(response1)
        return ("error ! multi ip can not padding !!",0)

def get_my_probable_addr_by_two(my_mapped_addr_list1,my_mapped_addr_list2,padding_type_port_add_num):
    response1,port_list1,ip_list1 = get_my_mapped_ports_string(my_mapped_addr_list1)
    response2,port_list2,ip_list2 = get_my_mapped_ports_string(my_mapped_addr_list2)

    if len(ip_list1) == 1 and len(ip_list2) == 1 and ip_list1[0]==ip_list2[0]:
        ip = ip_list1[0]
        port = max((max(port_list1),max(port_list2))) + padding_type_port_add_num
        print("我的 MAPPED IP:%s" % ip)
        print("抚州 port[%s]" % ";".join(  map(str,port_list1)))
        print("香港 port[%s]" % ";".join( map(str,port_list2)))
        if padding_type_port_add_num >0:
            print("MAX PORT = max + %d" % padding_type_port_add_num)
        print("MAX PORT [%d]" %(port))

        probable_ip = (ip,port)
        return probable_ip
    else:
        print(response1)
        print(response2)
        return ("can not get probable my mapped addr!",0)

'''
@   打洞测试

'''

def start_test_pad_detect(ask_user,my_user,coturn_server,max_allocation_times = 10,padding_type_port_add_num=0):

    allocation_gain,my_mapped_addr,stun_server_cnn,allocation_times = step_allocate(max_allocation_times ,
                    coturn_server ,my_user,ask_user ,onwaiting= 0)

    logging.info("==== MY MAPPED ADDR")
    print(json.dumps(my_mapped_addr,indent=2))

    ask_gain = step_ask_user(stun_server_cnn)
    logging.info("======================= ASK USER MAPPED ADDR")
    print(json.dumps(ask_gain[STUN_ATTRIBUTE_RES_USER_INFO_MAPEED_ADDR],indent=2))

    #临时方案
    if max_allocation_times >0:
        padding_type_port_add_num = 1
    else:
        padding_type_port_add_num = 0

    guess_peer_addr = guess_peer_ip_port(ask_gain,allocation_gain,padding_type_port_add_num)

    logging.debug("##############################STARTING TO CONNECT USER peer_addr[%s:%d]..." % guess_peer_addr)

    #第四步 监听 来自 远方的呼唤

    test_connect_peer_loop(allocation_times,guess_peer_addr,my_user,timeout= 10)
            




def start_test_pad_detect_from_two_server(ask_user,my_user,
                        coturn_server1,coturn_server2,
                        max_allocation_times = 10,as_listener = 0,
                        padding_type_port_add_num = 0):
    
    allocation_gain1,my_mapped_addr1,stun_server_cnn1,allocation_times1 = (None,None,None,None)
    allocation_gain2,my_mapped_addr2,stun_server_cnn2,allocation_times2 = (None,None,None,None)

    # allocation 1 ask user 1
    allocation_gain1,my_mapped_addr1,stun_server_cnn1,allocation_times1 = step_allocate(max_allocation_times ,
                    coturn_server1 ,my_user,ask_user ,onwaiting= 0,allocation_times_stt= 0)
    

    # allocation 2 ask user 2
    allocation_gain2,my_mapped_addr2,stun_server_cnn2,allocation_times2 = step_allocate(max_allocation_times + allocation_times1 ,
                    coturn_server2 ,my_user,ask_user ,onwaiting= 0,allocation_times_stt= allocation_times1)


    ask_gain1 = step_ask_user(stun_server_cnn1)
    ask_gain2 = step_ask_user(stun_server_cnn2)

    # 获取打洞地址
    guess_peer_addr = guess_peer_ip_port_by_two(ask_gain1,ask_gain2,coturn_server1,coturn_server2,padding_type_port_add_num)

    # 获取自身可能的地址
    my_probable_addr = get_my_probable_addr_by_two(my_mapped_addr1,my_mapped_addr2,padding_type_port_add_num)

    logging.info("==========对方可能MAPPED地址 [%s:%d]" %(guess_peer_addr[0],guess_peer_addr[1] ))
    logging.info("==========自身可能MAPPED地址 [%s:%d]" %(my_probable_addr[0],my_probable_addr[1] ))
    
    if as_listener == 0 and "error" not in guess_peer_addr[0]: ###等待
        test_connect_peer_loop(allocation_times2,guess_peer_addr,my_user,timeout= 10)
    elif "error" in guess_peer_addr[0]:                         ### 猜测失败
        print("猜不到对方IP EXITING .........")
        sys.exit(-1)
    else: ## 主动请求

        if padding_type_port_add_num >0: #如果 padding_type_port_add_num 大于0 ，则新建 socket
            a_addr,new_socket = get_new_socket(allocation_times=allocation_times2 )
        else:
            new_socket = stun_server_cnn2.server_socket_fd
            a_addr = stun_server_cnn2.local_addr

        logging.debug("LISTENING [%s:%d] HOPE VISITER [%s:%d] my probable NAT [%s:%d] ...."
                % (a_addr[0],a_addr[1],guess_peer_addr[0],guess_peer_addr[1],
                my_probable_addr[0],my_probable_addr[1]))

        while True:
            try:
                new_socket.sendto(b"hello",guess_peer_addr)
                data,addr = new_socket.recvfrom(MESSAGE_MAX_LENGTH)
                logging.debug("RECIEVED FROM [%s:%d] data[%s]" % (addr[0],addr[1],data.hex()))
                print("TEST OK  EXITING  .....")
                sys.exit()
            except Exception as e:
                print(e)
                continue




def listen_socket(sock_fd,my_user,guess_peer_addr):
    global is_padding_continue

    logging.info("start to listening ~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    resp = bytes("i am [%s:%d]" % my_user,encoding = "utf-8")
    #sock_fd.server_socket_fd.settimeout(0)

    ping_ok_num = 0

    while True:
        lock.acquire()
        data,addr = sock_fd.server_socket_fd.recvfrom(1024)
        is_padding_continue = False

        print("========================")
        print("====TEST PADDING HOLE  OK !!!=====RECV_ADDR IS [%s:%d]  GUESS_ADDR[%s:%d]  MY_local_addr[%s:%d]" % (   
                    addr[0],addr[1],
                    guess_peer_addr[0],guess_peer_addr[1],
                    sock_fd.local_addr[0],sock_fd.local_addr[1]
                ))
        print(data)
        # if isinstance(data,bytes) == True:
        #     print(data.decode("utf-8"))
        print("========================")
        print("====== PLEASE INPUT \n\n")
        sleep(1)
        print("send back %s" % (resp.decode("utf-8")))
        sock_fd.server_socket_fd.sendto(resp,addr)


        ping_ok_num = ping_ok_num + 1 
        lock.release()



def thread_socket_listen(sock_fd,my_user,guess_peer_addr):

    t = threading.Thread(target=listen_socket, args=(sock_fd,my_user,guess_peer_addr,))
    t.start()
    t.join()


def step_send_data_loop(sock_fd,msg_send,peer_addr,times = 100):
    
    for i in range(times):
        #logging.info("send %s to [%s:%d]" %(msg_send,peer_addr[0],peer_addr[1]+i))
        new_addr = (peer_addr[0],peer_addr[1]+i)
        sock_fd.sendto(bytes(msg_send,encoding="utf-8"),new_addr)
        

def start_test_pad_detect_from_one_server(ask_user,my_user,
                        coturn_server1,
                        max_allocation_times = 1,as_listener = 0,
                        padding_type_port_add_num = 0,padding_hole_port_to = 100):
    
    global is_padding_continue
    
    # allocation 1 ask user 1
    allocation_gain1,my_mapped_addr1,stun_server_cnn1,allocation_times1 = step_allocate(max_allocation_times ,
                    coturn_server1 ,my_user,ask_user ,onwaiting= 0,allocation_times_stt= 0)
    

    #step_refresh(stun_server_cnn1,use_thread=1,wait_recv= 0)

    sleep(5)

    ask_gain1 = step_ask_user(stun_server_cnn1)

    # 获取打洞地址
    guess_peer_addr = guess_peer_ip_port_by_one(ask_gain1,coturn_server1,padding_type_port_add_num)

    # 获取自身可能的地址
    my_probable_addr = get_my_probable_addr_by_one(my_mapped_addr1,padding_type_port_add_num)

    logging.info("==========对方可能MAPPED地址 [%s:%d]" %(guess_peer_addr[0],guess_peer_addr[1] ))
    logging.info("==========自身可能MAPPED地址 [%s:%d]" %(my_probable_addr[0],my_probable_addr[1] ))


    #################################

    msg_to_send = "user[%d:%d]sayhello" % (my_user[0],my_user[1])
    TRY_MAX_PORT_NUM = 100

    msg_send_bytes = bytes(msg_to_send,encoding="utf-8")

    logging.info("LOOP START from[%s:%d] to [%s:%d]" 
                % (guess_peer_addr[0],guess_peer_addr[1],guess_peer_addr[0],guess_peer_addr[1]+TRY_MAX_PORT_NUM))
        
    if padding_hole_port_to >1000:
        i = 0 - padding_hole_port_to
    else:
        i = 0
    ping_ok_num = 0
    is_connect_ok = 0

    s = stun_server_cnn1.server_socket_fd
    s.setblocking(False)
    
    t1 = time.time()
    blk_time = 0.001
    loop_times = 0
    while True:
        # if loop_times > 5 :
        #     print("padding loop over 5, SADDLY FAIL,EXITING ...")
        #     break
        
        
        try:
            # c,addr = s.accept()
            # print( "Connection from: " + str(addr))
            s.setblocking(False)
            data,addr = stun_server_cnn1.server_socket_fd.recvfrom(MESSAGE_MAX_LENGTH) # , socket.MSG_DONTWAIT
            is_connect_ok = 1
            print("")
            print("====TEST PADDING HOLE  OK !!!=====RECV_ADDR IS [%s:%d]  GUESS_ADDR[%s:%d]  MY_local_addr[%s:%d]" % (   
                        addr[0],addr[1],
                        guess_peer_addr[0],guess_peer_addr[1],
                        stun_server_cnn1.local_addr[0],stun_server_cnn1.local_addr[1]
                    ))
            try:
                print(data.decode("utf-8"))
            except Exception:
                print(data)
            print("")
            print("")
            print("")

            if ping_ok_num == 0:
                if b"ping" not in data:
                    first_bytes = msg_send_bytes
                    logging.info("====== I am the first please input ~~~~~~~~~~~~~~~~~~~~~~~~~~~ \n\n")
                else:
                    first_bytes = b"ping"
                stun_server_cnn1.server_socket_fd.sendto(first_bytes,addr)
            else:
                send_data = sys.stdin.readline()
                send_bytes = bytes(send_data,encoding="utf-8")
                stun_server_cnn1.server_socket_fd.sendto(send_bytes,addr)
            ping_ok_num = ping_ok_num + 1 
            
        except socket.error :

            t2 = time.time()
            if t2 < t1 + blk_time:
                continue
            else:
                t1 = t2

            if is_connect_ok ==0:
                if guess_peer_addr[1]+i < 1000:
                    i = 1000 - guess_peer_addr[1]
                new_addr = (guess_peer_addr[0],guess_peer_addr[1]+i)
                logging.debug("send to [%s:%d]   orgin_port[%d] data[%s]" %(new_addr[0],new_addr[1],guess_peer_addr[1],msg_to_send))
                try:
                    stun_server_cnn1.server_socket_fd.sendto(msg_send_bytes,socket.MSG_DONTWAIT,new_addr)  
                except Exception as e:
                    logging.info(e)
                    #sleep(5)
                if ( i>0 and i % padding_hole_port_to ==0 ) or guess_peer_addr[1]+i >65000:
                    if padding_hole_port_to >1000:
                        i = 0 - padding_hole_port_to
                    else:
                        i=0
                    loop_times = loop_times +1
                else:
                    i = i+1
            else:
                continue
        # except Exception as e:
        #     print(e)
        #     sys.exit()







