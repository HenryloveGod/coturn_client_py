from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket


pong={

}

class SimpleEcho(WebSocket):

    def handleMessage(self):
        # echo message back to client
        print(self.data)
        self.sendMessage(self.data)
        #self.sendMessage()


    def handleConnected(self):
        print(self.address, 'connected')

    def handleClose(self):
        print(self.address, 'closed')

server = SimpleWebSocketServer('ws.eotu.com/kurento', 80, SimpleEcho)
server.serveforever()