#!/usr/bin/env python3

import socket, threading

from client_supporter import ClientSupporter

class FTPServer(threading.Thread):
    DEFAULT_CONTROL_PORT = 8887 #21
    LISTEN_QUEUE = 5

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', FTPServer.DEFAULT_CONTROL_PORT))
        self._running = True
        threading.Thread.__init__(self)
    
    def run(self):
        self.socket.listen(FTPServer.LISTEN_QUEUE)
        while self._running:
            try:
                c_conn, c_addr = self.socket.accept()
                if self._running:
                    th = ClientSupporter(c_conn, c_addr)
                    th.daemon = True
                    th.start()
            except:
                break
    
    def stop(self):
        self.socket.close()
        self._running = False

        # Salir del accept()
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 8887))
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