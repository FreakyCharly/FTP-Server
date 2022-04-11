#!/usr/bin/env python3

import socket, threading, os

from client_supporter import ClientSupporter

class FTPServer(threading.Thread):
    MY_IP = '127.0.0.1'
    DEFAULT_CONTROL_PORT = 8887 #21
    LISTEN_QUEUE = 5

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', FTPServer.DEFAULT_CONTROL_PORT))
        self._running = True
        self._server_dir = os.getcwd()
        threading.Thread.__init__(self)
    
    def run(self):
        self.socket.listen(FTPServer.LISTEN_QUEUE)
        while self._running:
            try:
                c_conn, c_addr = self.socket.accept()
                if self._running:
                    th = ClientSupporter(c_conn, c_addr, self._server_dir)
                    th.daemon = True
                    th.start()
            except Exception as e:
                print(e)
                break
    
    def stop(self):
        self._running = False

        # Salir del accept()
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.connect((self.MY_IP, self.DEFAULT_CONTROL_PORT))
        self.socket.close()
        sock.close()

if __name__ == '__main__':
    # Iniciar servidor FTP
    print(f'Iniciando servidor FTP en el puerto {FTPServer.DEFAULT_CONTROL_PORT}...')
    svr = FTPServer()
    svr.daemon = True
    svr.start()
    
    # Esperar a cancelacion
    try:
        input('Servidor en marcha. Pulse cualquier tecla para parar...\n')
    except EOFError:
        pass
    print('Cerrando servidor...')
    svr.stop()
    svr.join()