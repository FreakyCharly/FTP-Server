#!/usr/bin/env python3
"""
All procedure with regards to command treatment is done as the FTP-RFC (959) especifies.


For easy callback translation, a dictionary will be used so, for example:
 - callback_dict = {"CDUP": cdup_callback}

So if client enters 'CDUP' command, server will get its callback function 
from the dictionary and execute it.


                                        ------------
FTP Model by RFC.                       |/--------\|
                                        ||        ||   ---------
                                        ||Interfaz|<-->|Usuario|
                                        |\----^---/|   ---------
              ----------                |     |    |
              |/------\|  Ordenes FTP   |/----V---\|
              ||Server|<---------------->|   User ||
              ||  PI  || Respuestas FTP ||    PI  ||
              |\--^---/|                |\----^---/|
              |   |    |                |     |    |
 ----------   |/--V---\|   Conexión     |/----V---\|  ----------
 |Sistema |<-->|Server|<---------------->|  User  |<-->|Sistema|
 |  de    |   ||      ||   de datos     ||        ||  |   de   |
 |ficheros|   || DTP  ||                ||   DTP  ||  |ficheros|
 ----------   |\------/|                |\--------/|  ----------
              ----------                -------------
                Server-FTP                   User-FTP
References:
https://www.adamsmith.haus/python/answers/how-to-call-a-function-by-its-name-as-a-string-in-python

"""


import threading, os, socket, time


cmds_available = {
    'USER': True,
    'PASS': True,
    'CWD': True,
    'REIN': True,
    'QUIT': True,
    'CDUP': True,
    'ACCT': True,
    'NOOP': True
}


class ClientSupporter(threading.Thread):
    """
    The idea is the following:
      --> Server accepts a client and creates a ClientSupporter
        --> ClientSupporter receives the client data (Socket reference and Address reference)
            and gets initialized.
      --> ClientSupporter welcomes the client.
      --> ClientSupporter calls for 'recv()' and waits for client actions, repeatedly.
        --> ClientSupporter will end when QUIT command is received.
    """
    CLIENT_MAX_SIZE_MSG = 256  # Buffer for client messages
    DEFAULT_DATA_PORT = 20
    

    def __init__(self, client_connection, client_address):
        self.cli_conn = client_connection
        self.cli_addr = client_address  # Both IP and Port number from client
        self.data_addr = client_address[0]
        self.data_port = self.DEFAULT_DATA_PORT

        self.parse = lambda a: a + '\r\n'

        self.user = None
        self.root_dir = os.path.abspath('.')
        self.curr_dir = self.root_dir

        threading.Thread.__init__(self)
    
    def run(self):
        conn = self.cli_conn
        parse = self.parse

        conn.send(parse('220 Carlos FTP Server (Version 0.5) ready'))
        while True:
            req = conn.recv(self.CLIENT_MAX_SIZE_MSG)
            if req:
                try:
                    # Get method callback
                    f = ''.join(req[:4])
                    
                    # If not recognised, respond and exit
                    if f not in cmds_available:
                        conn.send(parse('502 Method not implemented'))
                        break
                    
                    # Get callback as function
                    func = getattr(self, f.upper())

                    # Get params
                    txt = ''
                    if len(req) > 4:
                        txt = req[5:]

                    # Call function with its params
                    if len(txt) > 0:
                        func(txt)
                    else:
                        func()
                
                except:
                    # Function is recognised but couldn't be called properly
                    conn.send(parse('501 Parameter syntax error'))
            
            else:
                break
    
    """
    To be implemented (callbacks):
      --> Access control callbacks
           - USER
           - PASS
           - CWD -> To move amongst directories
           - REIN -> It resets to the point where USER has just been called
           - QUIT -> To close connection. Data socket must be empty, otherwise wait until it is.
           - CDUP (Optional) -> To change directory to parent's
           - ACCT (Optional) -> To move amongst users within a USER itself
      
      --> Transfer callbacks
            - 
    """
    def USER(self, msg):
        """
        User log-in.
        """
        self.user = msg
        self.cli_conn.send(self.parse('331 Password needed.'))
    
    def PASS(self, msg):
        """
        User password.
        Needed after USER.
        """
        self.cli_conn.send(self.parse(f'230 {self.user} connected.'))
    
    def QUIT(self):
        """
        Quit user, hence thread dies.
        """
        self.cli_conn.send(self.parse(f'221 Bye, {self.user}.'))
    
    def NOOP(self):
        """
        No operation.
        """
        self.cli_conn.send(self.parse('220 OK.'))
    
    def PORT(self, msg):
        """
        Set a PORT and a IP to create future Data channels.
        """
        data = msg.split(',')
        try:
            self.data_addr = '.'.join(data[:4])                 # Get IP
            self.data_port = (int(data[4]) << 8) + int(data[5]) # Get port
        except:
            self.cli_conn.send(self.parse('501 Parameter syntax error'))
        
        self.cli_conn.send(self.parse('200 PORT succesful.'))

    def LIST(self):
        """
        Returns same format as 'ls -l' from UNIX systems.
        """
        # Open data connection
        self.cli_conn.send(self.parse(f'150 Opening ASCII mode data connection for {self.curr_dir}.'))
        self.data_conn=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.data_conn.connect((self.data_addr,self.data_port))
        except:
            self.cli_conn.send(self.parse('425 Data conection cannot be opened.'))
        
        # Make up a 'ls -l' format type
        os.chdir(self.curr_dir)
        listed = os.listdir('.')
        item_parsed = ''
        base_mode = 'rwx'*3
        for item in listed:
            s = os.stat(item)
            final_mode = ''

            # Guess the 'r', 'w', 'x', '-' mode
            for i in len(base_mode):
                final_mode += ((s.st_mode >> (8-i)) & 1) and base_mode[i] or '-'
            
            # Type of file ('d' -> Directory, '-' -> Any other)
            dir = 'd' if os.path.isdir(item) else '-'
            
            # Date
            t = time.strftime(' %b %d %H:%M ', time.gmtime(s.st_mtime))
            
            # Parse full item
            item_parsed = dir + final_mode + ' 1 user group ' + str(s.st_size) + t + os.path.basename(item)
            # TODO '1 user group' must be obtained from os
            self.data_conn.send(self.parse(item_parsed))