

from p2p_definition import *
from p2pmsg_recv import allocation_recv_handle,dismessage
import json
from time import sleep

import threading

from p2p_allocation import *
from threading import Timer

from p2p_test import *

as_listener = 0

padding_hole_port_to = 1   #端口号从0加到 N

user_coturn_servers = [
    (None,0),
    ("192.168.1.191",3478),
    ("113.195.xxx.xxx",3488),
    ("xxx.xxx.245.148",3488),
    ("www.xxxx.com",3488)
]
default_coturn_server = user_coturn_servers[0]
server_no = 0
'''
    分别代表 user_id:xxxx_CHANNEL !!
'''
test_users={
    0:{"my_user":(11,1),"ask_user":(10,1) },    
    1:{"my_user":(10,1),"ask_user":(11,1)},
    2:{"my_user":(12,1),"ask_user":(11,1)},
    3:{"my_user":(11,1),"ask_user":(12,1)}
}

users_no = 0
test_turn_send = 1
test_p2p_send = 0
padding_type_port_add_num= 0   #打洞方式  0,  端口号不变， 1, 端口号加1

send_allocation_times = 1 # 发送ALLOCATION 次数
send_data = None
is_create_permission = 1 


def start():

    global as_listener,padding_type_port_add_num,send_allocation_times

    ask_user = test_users[users_no]["ask_user"]
    my_user = test_users[users_no]["my_user"]


    coturn_server1 = user_coturn_servers[2]
    coturn_server2 = user_coturn_servers[3]
    coturn_server = user_coturn_servers[server_no]

    # 中转测试～～～～～``
    start_test_turn_by_method_send(ask_user,my_user,coturn_server,max_allocation_times = 0)

    # 单服务器 打洞测试
    #start_test_pad_detect(ask_user,my_user,coturn_server,max_allocation_times = 10)


    #单服务器 打洞测试
    #start_test_pad_detect_from_one_server(ask_user,my_user,
    #            coturn_server,max_allocation_times = send_allocation_times,as_listener = as_listener,padding_type_port_add_num= padding_type_port_add_num,padding_hole_port_to = padding_hole_port_to)
    

    # 双服务器 打洞测试
    #start_test_pad_detect_from_two_server(ask_user,my_user,coturn_server1,coturn_server2,max_allocation_times = send_allocation_times,as_listener = as_listener,padding_type_port_add_num= padding_type_port_add_num)
    


 


def usage():
    print("usage: -c 1 -s 1 -d 'hello' ")
    print("-c 1 or 2            select a group users to test ")
    print("-d send_data         the data of METHOD_SEND ")
    print("-p                   create permission  ")
    print("-a                   client port add n , 打洞时，获取对方的端口号，是否加N ")
    print("-b                   allocation times ,  打洞时，发送allocation 的次数 ")
    print("-l as listener")
    print("-z the queue  端口号从0加到N")
    print("-s set coturn server 192.168.1.191 ")


def get_options():
    import getopt

    global onwaiting,send_data, \
            server_no,users_no, \
            is_create_permission, \
            test_users,padding_type_port_add_num,as_listener, \
            send_allocation_times,padding_hole_port_to
             

    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:b:u:c:whs:d:plz:", ["help", "output="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o,a in opts:
        if o == "-c":
            users_no=int(a)
            print(test_users[users_no]["ask_user"])
            logging.debug("set ask_user[%d:%d]" % test_users[users_no]["ask_user"])
            logging.debug("set my_user[%d:%d]" % test_users[users_no]["my_user"])
        elif o == "-w":
            onwaiting = 1
        elif o == "-a":
            padding_type_port_add_num = int(a)
        elif o == "-b":
            send_allocation_times = int(a)
        elif o == "-d":
            send_data = a        
        elif o == "-s":
            server_no=int(a)
        elif o == "-z":
            padding_hole_port_to = int(a)
        elif o == "-p":
            is_create_permission= 1
        elif o == "-l":
            as_listener = 1
        elif o == "-h":
            usage()
            return -1
        else:
            usage()
            return -1
    return 0


if __name__=="__main__":
    addglobals = lambda x: globals().update(x)
    r = get_options()

    if r == -1:
        logging.error("exiting ...")
    else:
        start()