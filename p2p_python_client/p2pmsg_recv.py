from p2p_definition import *

import json

class addr_attr:
    ipbytes = None
    ipstr = None
    portbytes = None
    family = None
    length = None
    des = None
    type_bytes = None

    def __init__(self,length,addr_data,data_type_int,data_type):
        self.family = addr_data[0:2]
        self.portbytes = addr_data[2:4]
        self.port = bytes_to_int(self.portbytes)
        self.ipbytes = addr_data[4:8]
        self.ipstr = ".".join(list(map(str,self.ipbytes)))
        self.length = length
        self.des = data_des[data_type_int]
        self.type_bytes = data_type.hex()

    def __str__(self):

        j = {
            "ip":self.ipstr,
            "port":self.port,
            #"family":self.family.hex(),
            "des":self.des,
            "type":self.type_bytes
            }
        return json.dumps(j)


class user_info_attr:
    user_id = None
    user_pwd = None
    length = None
    des = None
    type_bytes = None

    def __init__(self,length,data,data_type_int,data_type):
        self.user_id = data[:4]
        self.user_pwd = data[4:8]
        self.des = data_des[data_type_int]
        self.type_bytes = data_type.hex()

    def __str__(self):

        j = {
            "user_id":self.user_id.hex(),
            "user_pwd":self.user_pwd.hex(),
            "des":self.des,
            "type":self.type_bytes
        }
 
        return json.dumps(j)

class value_info_attr:
    value = None
    length = None
    des = None
    type_bytes = None

    def __init__(self,length,data,data_type_int,data_type):
        self.value=data
        self.length = length
        self.des = data_des[data_type_int]
        self.type_bytes = data_type.hex()

    def __str__(self):
        des_str = None
        try:
            des_str = self.value.decode("utf-8")
        except:
            des_str = self.value.hex()
        j =  {
            "value":des_str,
            "value_bytes":self.value.hex(),
            "des":self.des,
            "type":self.type_bytes
        }
        return json.dumps(j)

class error_code_attr:
    code = None
    string = None
    des = None
    type_bytes = None

    def __init__(self,length,data,data_type_int,data_type):
        self.code = bytes_to_int(data[0:4])
        

        try:
            self.string = data[4:].decode('utf-8')
            print("error code %08x ,error[%s]" % (self.code,self.string) )
            print(self.string)
        except Exception as e:
            print(e)
            sys.exit()
            self.string = data[4:].hex()
        self.length = length
        self.des = data_des[data_type_int]
        self.type_bytes = data_type.hex()

    def __str__(self):
        j =  {
            "code":self.code,
            "string":self.string,
            "des":self.des,
            "type":self.type_bytes
        }
        return json.dumps(j)

data_attr_funcs={
    STUN_ATTRIBUTE_EOTU_LOCAL_ADDR:addr_attr,
    STUN_ATTRIBUTE_RES_USER_INFO_MAPEED_ADDR:addr_attr,
    STUN_ATTRIBUTE_RES_USER_INFO_RELAYED_ADDR:addr_attr,
    STUN_ATTRIBUTE_RES_USER_INFO_REAL_ADDR:addr_attr,
    STUN_ATTRIBUTE_RES_USERID_INFO:user_info_attr,
    STUN_ATTRIBUTE_ERROR_CODE:error_code_attr,
    STUN_ATTRIBUTE_XOR_RELAYED_ADDRESS:addr_attr,
    STUN_ATTRIBUTE_XOR_MAPPED_ADDRESS:addr_attr,
    STUN_ATTRIBUTE_NONCE:value_info_attr,
    STUN_ATTRIBUTE_REALM:value_info_attr,
    STUN_ATTRIBUTE_LIFETIME:value_info_attr,
    STUN_ATTRIBUTE_XOR_PEER_ADDRESS:addr_attr,
    STUN_ATTRIBUTE_DATA:value_info_attr,
    STUN_ATTRIBUTE_REQUESTED_TRANSPORT:value_info_attr,
    STUN_ATTRIBUTE_REQUESTED_ADDRESS_FAMILY:value_info_attr,
}


class dismessage:

    msg_type = None
    user_id = None
    msg_length = None
    data_list = {}

    def __init__(self,data):
        self.msg_type = data[0:2]
        self.msg_length = data[2:4]
        self.user_id = data[12:16]
        self.user_pwd = data[16:20]
        self.data_list = {}
        self.get_data_list(data)


    def get_data_type(self,next_data):

        if len(next_data) <5:
            logging.error("illegle")
            sys.exit()

        data_type = next_data[0:2]
        data_type_int = bytes_to_int(next_data[0:2])

        data_length = bytes_to_int(next_data[2:4])

        if len(next_data) < 4 + data_length:
            logging.error("total len [%d]" % len(next_data))
            logging.error("message demand len [%d]" % (4+data_length))
            logging.error("get data type length error [%s] ,Exiting ...." % next_data.hex())
            #sys.exit(-1)
            return (data_type_int,next_data,None)

        data_value = next_data[4:(data_length + 4)]
        data_attr = None
        
        if data_type_int in data_attr_funcs:
            func = data_attr_funcs[data_type_int]
            if func is not None:
                data_attr = data_attr_funcs[data_type_int](data_length,data_value,data_type_int,data_type)
            else:
                data_attr = [data_value]
        else:
            logging.error("ATTR[%s] no function to get value [%s]" %(data_type.hex(),data_value.hex()))
            data_attr = data_value.hex()

        next_data = next_data[(data_length + 4):]
        return (data_type_int,data_attr,next_data)

    def get_data_list(self,data):

        next_data = data[20:]
        while(next_data):
            data_type_int,data_attr,next_data = self.get_data_type(next_data)
            if None in (data_type_int,data_attr):
                break
            if not data_type_int in self.data_list:
                self.data_list[data_type_int]=[]
                self.data_list[data_type_int].append(data_attr)
            else:
                self.data_list[data_type_int].append(data_attr)

def debug_recv(msg):

    j={}
    for d in msg.data_list:
        if d == None:
            logging.error("get nothing for recieved data")
            sys.exit()
        j[d]=[]
        dobj = msg.data_list[d]
        if isinstance(dobj,list):
            for obj_c in dobj:
                if isinstance(obj_c,object):
                    try:
                        j[d].append(json.loads(str(obj_c)))
                    except Exception as e:
                        logging.info(e)
                        j[d].append(obj_c)
                else:
                    print("================what error !?")
                    j[d].append(obj_c)                
        else:
            print("================what error !?")
            j[d].append(json.loads(dobj))

    #print(json.dumps(j,indent = 2))
    return j

def get_json_from_msg_data(data):

    msg = dismessage(data)
    return debug_recv(msg)

def addr_attrs_set_to_gain(gain,addr_attr_list,addr_type):
    is_ok = 0
    for attr in addr_attr_list:
        if attr.ipstr != "0.0.0.0":
            gain[addr_type].append(attr)
            logging.info("GET %s addr[%s:%d]" %(addr_type,attr.ipstr,attr.port))
            is_ok = 1

    return gain,is_ok



'''
    allocate recv 处理
'''
def allocation_recv_handle(data):

    logging.debug("ready to format recieved data")
    msg = dismessage(data)
    return debug_recv(msg)

'''
    方法同allocation_recv_handle
'''

def method_send_callback(data):
    
    return allocation_recv_handle(data)

#   EOTU ASK USER

def method_eotu_ask_user_recv_handle(data):
    return allocation_recv_handle(data) 



if  __name__ == "__main__":

    data = sys.argv[1]
    data_bytes = bytes(data,encoding = "utf-8")
    j = get_json_from_msg_data(data_bytes)
    
    print(json.dumps(j,indent=2))