import socketserver

class echorequestserver(socketserver.BaseRequestHandler):
    def handle(self):
        print('服务端启动...')
        conn = self.request
        print('获得连接：', self.client_address)
        while True:
            client_data = conn.recv(1024)
            if not client_data:
                print('断开连接')
                break
            print(client_data.decode('utf-8'))
            print('开始发送...')
            conn.sendall(client_data)
            
if __name__ == '__main__':
    server =socketserver.TCPServer(("127.0.0.1", 8000),echorequestserver)  # 使用处理单连接的TCPServer
    server.serve_forever()