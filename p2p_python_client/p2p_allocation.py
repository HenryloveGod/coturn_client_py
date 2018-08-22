from p2p_utils import *

from p2p_definition import *

from p2pmsg_recv import *

from time import sleep



class stun_allocation_class:

    coturn_server = None
    my_user = None
    ask_user = None
    onwaiting=0

    local_addr = None
    server_socket_fd =None

    MAX_ALLOCATION_TIMES = 10  # 尝试发送3次直到获取到NAT地址
    allocate_number = 0


    def __init__(self,coturn_server,onwaiting = 0,my_user=(10,1),ask_user=(11,1),max_allocation_times = 3):
        self.coturn_server = coturn_server
        self.my_user = my_user
        self.ask_user = ask_user
        self.onwaiting = onwaiting
        self.MAX_ALLOCATION_TIMES = max_allocation_times



      
    def method_create_permission_start(self,peer_addr):
        #初始化报头
        msg_buf = bytearray(MESSAGE_MAX_LENGTH)
        msg_buf_header = stun_init_header(STUN_METHOD_CREATE_PERMISSION,self.my_user)       
        msg_buf = set_buf_to_msg_buf(msg_buf,0,msg_buf_header,STUN_HEADER_LENGTH)

        #添加peer地址
        msg = set_data_to_msg_buf(msg_buf,STUN_HEADER_LENGTH,STUN_ATTRIBUTE_XOR_PEER_ADDRESS,peer_addr)
   
        #设置msg_buf长度值
        msg_to_send = set_msg_buf_size_final(msg)
        logging.debug("method_send_start start to send \n[%s]" % msg_to_send.hex())

        #开始发送
        self.server_socket_fd.sendto(msg_to_send,self.coturn_server)
        while True:
            data,recv_addr = self.server_socket_fd.recvfrom(MESSAGE_MAX_LENGTH)
            logging.debug("recieved from[%s:%d] [%s]" %(recv_addr[0],recv_addr[1],data.hex()))

            return data



    '''
        中转数据，server为空，则直接p2p发送，否则server中转
    @ server  coturn_server服务器地址
    @ peer_addr peer地址
    
    '''

    def method_bind_start(self):
        #初始化报头
        msg_buf = bytearray(STUN_HEADER_LENGTH)
        msg_buf_header = stun_init_header(STUN_METHOD_BINDING,self.my_user)       
        msg_buf = set_buf_to_msg_buf(msg_buf,0,msg_buf_header,STUN_HEADER_LENGTH)

        #开始发送
        self.server_socket_fd.sendto(msg_buf,self.coturn_server)
        while True:
            data,recv_addr = self.server_socket_fd.recvfrom(MESSAGE_MAX_LENGTH)
            logging.debug("recieved from [%s:%d] data[%s]" %(recv_addr[0],recv_addr[1], data.hex()))

            return data


    def method_refresh_start(self,wait_recv = 1):
        #初始化报头
        msg_buf = bytearray(STUN_HEADER_LENGTH)
        msg_buf_header = stun_init_header(STUN_METHOD_REFRESH,self.my_user)       
        msg_buf = set_buf_to_msg_buf(msg_buf,0,msg_buf_header,STUN_HEADER_LENGTH)

        #开始发送
        self.server_socket_fd.sendto(msg_buf,self.coturn_server)
        if wait_recv ==1 :
            while True:
                data,recv_addr = self.server_socket_fd.recvfrom(MESSAGE_MAX_LENGTH)
                logging.debug("recieved from [%s:%d] data[%s]" %(recv_addr[0],recv_addr[1], data.hex()))
                return data
        




    '''
        中转数据，server为空，则直接p2p发送，否则server中转
    @ server  coturn_server服务器地址
    @ peer_addr peer地址
    
    '''

    def method_send_start(self,send_data,ask_user,server = None,is_wait = 1):

        #初始化报头
        msg_buf = bytearray(MESSAGE_MAX_LENGTH)
        msg_buf_header = stun_init_header(STUN_METHOD_SEND,self.my_user)       
        msg_buf = set_buf_to_msg_buf(msg_buf,0,msg_buf_header,STUN_HEADER_LENGTH)

        #添加peer地址
        #msg = set_data_to_msg_buf(msg_buf,STUN_HEADER_LENGTH,STUN_ATTRIBUTE_XOR_PEER_ADDRESS,peer_addr)
    
        if ask_user !=None:
            print("METHOD SEND 现在改peer addr 为 askuser")
        
        msg = set_data_to_msg_buf(msg_buf,STUN_HEADER_LENGTH,STUN_ATTRIBUTE_ASK_USERID_INFO,ask_user)


        #添加发送的数据
        msg = set_data_to_msg_buf(msg_buf,msg[1],STUN_ATTRIBUTE_DATA,send_data)
   
        #设置msg_buf长度值
        msg_to_send = set_msg_buf_size_final(msg)


        # if is_wait == 0:
        #     return None
        while True:
            try:
                #开始发送
                if server !=None:
                    self.server_socket_fd.sendto(msg_to_send,server)
                    logging.debug("METHOD SEND  server[%s:%d] with ask_user[%d:%d] data[%s] " %
                        (
                            server[0],server[1],
                            ask_user[0],ask_user[1],
                            msg_to_send.hex()) 
                        )
                else:
                    print("METHOD SEND NO SERVER")
                    sys.exit()

                self.server_socket_fd.settimeout(5)
                data,recv_addr = self.server_socket_fd.recvfrom(MESSAGE_MAX_LENGTH)
                if server !=None:
                    logging.debug("RECIEVED from[%s:%d] [%s]" %(recv_addr[0],recv_addr[1], data.hex()))
                else:
                    logging.debug("P2P SEND recieved from[%s:%d]\n[%s]" %(recv_addr[0],recv_addr[1], data.hex()))

                method_send_gain = method_send_callback(data)
                return method_send_gain
            except Exception as e:
                logging.error(e)
                continue



    def method_eotu_ask_user_start(self,sequence = 0,ask_user=None):
        logging.debug("###############EOTU ASK USER server[%s:%d] times[%d]" % (self.coturn_server[0],self.coturn_server[1],sequence))
        new_socket = self.server_socket_fd 
        if new_socket  == None:
            self.local_addr,new_socket  = get_new_socket()
            self.server_socket_fd = new_socket
            logging.debug("get local addr [%s:%d]" %(self.local_addr[0],self.local_addr[1]) )
        #初始化报头
        msg_buf = bytearray(MESSAGE_MAX_LENGTH)
        msg_buf_header = stun_init_header(STUN_METHOD_EOTU_ASK_USER,self.my_user)       
        msg_buf = set_buf_to_msg_buf(msg_buf,0,msg_buf_header,STUN_HEADER_LENGTH)

        if ask_user ==None:
            ask_user = self.ask_user

        if ask_user !=None:
            msg = set_data_to_msg_buf(msg_buf,STUN_HEADER_LENGTH,STUN_ATTRIBUTE_ASK_USERID_INFO,ask_user)
            logging.debug("Add ask user (%d %d)" % ask_user)
        else:
            logging.error("ask user is None ,exiting ....")
            sys.exit()

        #设置msg_buf长度值
        msg_to_send = set_msg_buf_size_final(msg)
        logging.debug("EOTU_ASK_USER START ! send data [%s]" %msg_to_send.hex())
        #开始发送
        new_socket.sendto(msg_to_send,self.coturn_server)

        # signal.signal(signal.SIGALRM, timeout_handle)
        # signal.alarm(5)

        ask_gain = None

        new_socket.settimeout(5)
        while True:
            try:
                data,recv_addr = new_socket.recvfrom(MESSAGE_MAX_LENGTH)
                logging.debug("EOTU_ASK_USER RECIEVED from [%s:%d] data[%s]" %(recv_addr[0],recv_addr[1], data.hex()))          
                if len(data)<20 or data[0] not in [0x00,0x01] or recv_addr[0] != self.coturn_server[0]:
                    print("got wrong msg target from [%s:%d] data[%s]" %(recv_addr[0],recv_addr[1],data))
                    continue
                else:
                    ask_gain = method_eotu_ask_user_recv_handle(data)
                    break
            except Exception as e:
                print(e)
                print("try next allocation")

        #signal.alarm(0)
        new_socket.settimeout(0)

        

        while (sequence < self.MAX_ALLOCATION_TIMES) :
            sequence = sequence +1
            if ask_gain==None or  STUN_ATTRIBUTE_RES_USERID_INFO not in  ask_gain:
                #重新上线
                #new_socket.close()  #最近一次socket 不关闭
                logging.debug("Got NO STUN_ATTRIBUTE_RES_USERID_INFO , request server again ....")
                sleep(5)
                ask_gain = self.method_eotu_ask_user_start(sequence= sequence)
            
            else:
                return ask_gain

        logging.debug("EOTU_ASK_USER OVER TIMES [%d], EXITING ....." % sequence)
        sys.exit(-1)


    def allocation_start(self,allocation_times,sequence = 0,ask_user=None):

        logging.debug("################ALLOCATION START !  server[%s:%d]" % (self.coturn_server[0],self.coturn_server[1]))
        
        new_socket = self.server_socket_fd 
        if new_socket  == None:
            self.local_addr,new_socket  = get_new_socket(allocation_times = allocation_times)
            self.server_socket_fd = new_socket
            logging.debug("get local bind addr [%s:%d]" %(self.local_addr[0],self.local_addr[1]) )
        
        #初始化报头
        msg_buf = bytearray(MESSAGE_MAX_LENGTH)
        if allocation_times ==0:
            msg_buf_header = stun_init_header(STUN_METHOD_ALLOCATE,self.my_user,set_random=0xffffffff)
        else:
            msg_buf_header = stun_init_header(STUN_METHOD_ALLOCATE,self.my_user)       
        msg_buf = set_buf_to_msg_buf(msg_buf,0,msg_buf_header,STUN_HEADER_LENGTH)

        #添加本地地址
        if self.local_addr !=None:
            msg = set_data_to_msg_buf(msg_buf,STUN_HEADER_LENGTH,STUN_ATTRIBUTE_EOTU_LOCAL_ADDR,self.local_addr)

        #设置REQUESTED_TRANSPORT  默认UDP ， 值为17
        msg = set_data_to_msg_buf(msg_buf,msg[1],STUN_ATTRIBUTE_REQUESTED_TRANSPORT,0x11000000)
        msg = set_data_to_msg_buf(msg_buf,msg[1],STUN_ATTRIBUTE_REQUESTED_ADDRESS_FAMILY,0x01000000)

        if ask_user !=None:
            msg = set_data_to_msg_buf(msg_buf,msg[1],STUN_ATTRIBUTE_ASK_USERID_INFO,ask_user)
            logging.debug("Add ask user (%d %d)" % ask_user)

        #设置msg_buf长度值
        msg_to_send = set_msg_buf_size_final(msg)
        logging.debug("ALLOCATION send data [%s]" %msg_to_send.hex())




        while (sequence < self.MAX_ALLOCATION_TIMES):
            sequence = sequence +1
            try:
                #开始发送
                new_socket.sendto(msg_to_send,self.coturn_server)
                allocation_gain=None

                #new_socket.settimeout(5.0)
                data,recv_addr = new_socket.recvfrom(MESSAGE_MAX_LENGTH)

                logging.debug("ALLOCATION RECIEVED from [%s:%d] data[%s]" %(recv_addr[0],recv_addr[1], data.hex()))
                allocation_gain = allocation_recv_handle(data)

                if allocation_gain and  STUN_ATTRIBUTE_XOR_RELAYED_ADDRESS not in  allocation_gain:
                    print("------no RELAYED ADDR---Try again --------")
                    continue
                else:
                    return allocation_gain

            except OSError as e:
                print(e.args[0])
                print("---------Try again --------")
                continue
            except Exception as e:
                print(e.args[0])
                sys.exit()

        logging.debug("ALLOCATE TRY TIMES [%d], GET NO STUN_ATTRIBUTE_XOR_RELAYED_ADDRESS,  EXITING ....." % sequence)
        sys.exit(-1)
        




