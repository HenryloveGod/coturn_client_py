from p2p_utils import *

import ipaddress



'''
=============================================

    METHOD 消息类型处理

=============================================
'''

# def stun_method_binding_handle():
#     pass

# def stun_method_allocation_handle():
#     pass

# def stun_method_eotu_ask_user_handle():
#     pass


# def stun_method_refresh_handle():
#     pass

# def stun_method_send_handle():
#     pass

# def stun_method_data_handle():
#     pass

# def stun_method_create_permission_handle():
#     pass
# def stun_method_connect_handle():
#     pass

# def stun_method_unknow():
#     pass



'''
=============================================

    DATA数据类型处理

=============================================
'''

pass


'''
=============================================

    DATA拼装数据处理

=============================================
'''
'''
    拼接数据到msg_buf中
@msg_buf 
@sttp       msg_buf起始位置
@data_type  数据类型
@addr       (ip,port)
    return (msg_buf,length+header)
'''

def set_addr_to_msg_buf(msg_buf,sttp,data_type,addr):

    length = 8
    addr_buf = covert_addr_to_buf_array(addr)
    data_buf = set_data_type_buf_array(data_type,length,addr_buf)
    msg_buf = set_buf_to_msg_buf(msg_buf,sttp,data_buf,12)

    return (msg_buf,sttp+12)


def set_method_data_to_msg_buf(msg_buf,sttp,data_type,buf):

    buf_len = len(buf)  # no more than 256
    if buf_len >255:
        print("error ! method send data length over 255 %d ,exiting ...." % buf_len)
        sys.exit(-1)
    
    msg_buf = set_int_to_msg_buf(msg_buf,sttp,data_type,2)
    msg_buf = set_int_to_msg_buf(msg_buf,sttp+2,buf_len,2)
    msg_buf = set_buf_to_msg_buf(msg_buf,sttp+4,buf,buf_len)

    return (msg_buf,sttp+ 4 + buf_len)


'''
    拼接数据类型为整型的数据到msg_buf中
@msg_buf 
@sttp       msg_buf起始位置
@data_type  数据类型
@value      int
@bit_num    
    return (msg_buf,length+header)
'''

def set_data_int_to_msg_buf(msg_buf,sttp,data_type,value,bit_num):

    msg_buf = set_int_to_msg_buf(msg_buf,sttp,data_type,2)
    msg_buf = set_int_to_msg_buf(msg_buf,sttp+2,bit_num,2)
    msg_buf = set_int_to_msg_buf(msg_buf,sttp+4,value,bit_num)

    return (msg_buf,sttp+4+bit_num)

'''
    同上，设定整数类型位数4
'''
def set_data_int32_to_msg_buf(msg_buf,sttp,data_type,value):
    return set_data_int_to_msg_buf(msg_buf,sttp,data_type,value,4)


'''
    拼接数据类型为整型的数据到msg_buf中
@msg_buf 
@sttp       msg_buf起始位置
@data_type  数据类型
@user       (user_id,user_pwd)    
    return (msg_buf,length+header)
'''

def set_ask_user_to_msg_buf(msg_buf,sttp,data_type,user):

    length = 8
    msg_buf = set_int_to_msg_buf(msg_buf,sttp,data_type,2)
    msg_buf = set_int_to_msg_buf(msg_buf,sttp+2,length,2)
    msg_buf = set_int_to_msg_buf(msg_buf,sttp+4,user[0],4)
    msg_buf = set_int_to_msg_buf(msg_buf,sttp+8,user[1],4)
    return (msg_buf,sttp+12)


## 拼装数据类型，长度，value，
def set_data_type_buf_array(data_type,length,value_buf):

    buf = bytearray(length + 4)
    set_int_to_msg_buf(buf,0,data_type,2)
    set_int_to_msg_buf(buf,2,length,2)
    set_buf_to_msg_buf(buf,4,value_buf,length)
    return buf


'''
    设置报文长度，最终结果
@msg    (msg_buf,长度-含STUN_HEADER_LENGTH)
'''
def set_msg_buf_size_final(msg):

    msg_buf = set_int_to_msg_buf(msg[0],2,msg[1]-STUN_HEADER_LENGTH,2)

    return msg_buf[:msg[1]]


'''
    报头初始化
@user_id    用户id
@pwd        用户密码
    return msg_buf_header 返回报头20个字节
'''
def stun_init_header(msg_type,my_user,set_random = None):
    #logging.debug("stun init with user[%d:%d]"%my_user)
    msg_buf_header=bytearray(STUN_HEADER_LENGTH)
    msg_buf_header=set_int_to_msg_buf(msg_buf_header,0,msg_type,2)    #消息类型
    if set_random !=None:
        msg_buf_header=set_int_to_msg_buf(msg_buf_header,8,set_random,4)
    msg_buf_header=set_int_to_msg_buf(msg_buf_header,12,my_user[0],4)   #用户ID
    msg_buf_header=set_int_to_msg_buf(msg_buf_header,16,my_user[1],4)       #用户密码

    return msg_buf_header
