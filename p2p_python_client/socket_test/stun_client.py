import stun
nat_type, external_ip, external_port = stun.get_ip_info(stun_host='192.168.1.191',stun_port=8898)

print(nat_type)
print(external_ip)
print(external_port)
