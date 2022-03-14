#!/usr/bin/env python3

import socket, threading

from client_supporter import ClientSupporter

class FTPServer(threading.Thread):
    DEFAULT_CONTROL_PORT = 21
    LISTEN_QUEUE = 5

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', FTPServer.DEFAULT_CONTROL_PORT))
        threading.Thread.__init__(self)
    
    def run(self):
        self.socket.listen(FTPServer.LISTEN_QUEUE)
        while True:
            ClientSupporter.start()
            """
            Create child thread to handle client.
            Make the thread a daemon.
            Call start() from thread.
            """
    
    def stop(self):
        self.socket.close()

if __name__ == '__main__':
    server = FTPServer()
    server.start()
    server.stop()