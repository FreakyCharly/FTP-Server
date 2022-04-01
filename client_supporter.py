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
    'OPTS': True,
    'USER': True,
    'PASS': True,
    'REIN': True,
    'QUIT': True,
    'CDUP': True,
    'ACCT': True,
    'NOOP': True,
    'SYST': True,
    'PORT': True,
    'LIST': True,
    'NLST': True,
    'CWD': True
}
cmds_3_chars_0_args = {
    'PWD': True
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
    DEFAULT_DATA_PORT = 8888 #20
    NAV_FOLDER = '/nav'
    NAV_FOLDER_AS_REL_PATH = 'nav/'
    

    def __init__(self, client_connection, client_address):
        self.cli_conn = client_connection
        self.cli_addr = client_address  # Both IP and Port number from client
        self.data_addr = client_address[0]
        self.data_port = self.DEFAULT_DATA_PORT

        self.encoding = 'ascii'
        self.parse = lambda a: f'{a}\r\n'.encode(self.encoding)

        self.user = None
        self.root_dir = os.getcwd() + self.NAV_FOLDER
        self.curr_dir = self.root_dir
        self.depth_dir = 0
        os.chdir(self.root_dir)

        threading.Thread.__init__(self)
    
    def run(self):
        conn = self.cli_conn
        parse = self.parse


        print("Cliente conectado")
        conn.send(parse('220 Carlos FTP Server (Version 0.5) ready'))
        while True:
            req = conn.recv(self.CLIENT_MAX_SIZE_MSG).decode(self.encoding)[:-2]
            print(f'Recibido: _{req}_')
            if req:
                try:
                    # Get method callback
                    if len(req) == 3 and ''.join(req) not in cmds_3_chars_0_args:
                        conn.send(parse('502 Method not implemented'))
                        break
                    
                    f = ''.join(req[:4])
                    if f[-1] == ' ':
                        f = f[:3]
                    
                    # If not recognised, respond and exit
                    if f not in cmds_available:
                        conn.send(parse('502 Method not implemented'))
                        break

                    # Get callback as function
                    func = getattr(self, f.upper())

                    # Get params
                    txt = ''
                    if len(f) == 4 and len(req) > 4:
                        txt = req[5:]
                    elif len(f) == 3 and len(req) > 3:
                        txt = req[4:]

                    # Call function with its params
                    func(txt)
                
                except Exception as e:
                    print(e)
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
    def OPTS(self, msg):
        args = msg.split(" ")
        if len(args) == 2:
            if args[1] == 'ON':
                if args[0] == 'UTF8':
                    self.encoding = 'utf-8'
                    self.cli_conn.send(self.parse('200 Mode turned to UTF8.'))
                    return
        
        self.cli_conn.send(self.parse('504 Not implemented for those parameters.'))
    
    def USER(self, msg):
        """
        User log-in.
        """
        self.user = msg
        self.cli_conn.send(self.parse('331 Password needed.'))
    
    def PASS(self, _):
        """
        User password.
        Needed after USER.
        """
        self.cli_conn.send(self.parse('230 User connected, please continue.'))
    
    def QUIT(self, _):
        """
        Quit user, hence thread dies.
        """
        self.cli_conn.send(self.parse(f'221 Bye.'))
    
    def NOOP(self, _):
        """
        No operation.
        """
        self.cli_conn.send(self.parse('220 OK.'))
    
    def SYST(self, _):
        """
        Give information about the server.
        """
        self.cli_conn.send(self.parse('215 CarlosFTPServer system type.'))

    def CWD(self, msg):
        # Get depth aimed by client
        path = msg.split('/')
        depth_aimed = 0
        for item in path:
            if item == '..': 
                depth_aimed -= 1
            elif item != '':        # Avoid '/' character ('' by split)
                depth_aimed += 1

        # Get current depth
        curr = self.curr_dir.split('/')
        root = self.root_dir.split('/')
        act_depth = len(curr) - len(root)

        """
        If total_depth is negative or depth_aimed is negative and the query starts with /<path_remaining>,
        then reject the query from client.
        """
        tot_depth = act_depth + depth_aimed
        if  (tot_depth < 0) or \
            (path[0] == '' and depth_aimed < 0):
            self.cli_conn.send(self.parse('450 Not available, access forbidden.'))
            return

        if msg == '/':
            msg=self.root_dir
        elif msg[0] == '/':
            msg=self.root_dir + msg
        
        try:
            os.chdir(msg)
        except OSError:
            self.cli_conn.send(self.parse('501 Incorrect path.'))
            return

        self.curr_dir = os.getcwd()
        self.cli_conn.send(self.parse('250 OK.'))

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

    def LIST(self, _):
        """
        Returns same format as 'ls -l' from UNIX systems.
        @TODO Poder hacer ls sobre un directorio o archivo dado
        """
        s = self._get_actual_rel_path()

        # Open data connection
        self.cli_conn.send(self.parse(f'150 Opening ASCII mode data connection for {s}.'))
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
            for i in range(1, len(base_mode)):
                final_mode += ((s.st_mode >> (8-i)) & 1) and base_mode[i] or '-'
            
            # Type of file ('d' -> Directory, '-' -> Any other)
            dir = 'd' if os.path.isdir(item) else '-'
            
            # Date
            t = time.strftime(' %b %d %H:%M ', time.gmtime(s.st_mtime))
            
            # Parse full item
            item_parsed = dir + final_mode + ' 1 user group ' + str(s.st_size) + t + os.path.basename(item)
            # TODO '1 user group' must be obtained from os
            self.data_conn.send(self.parse(item_parsed))
        
        self.data_conn.close()
        self.cli_conn.send(self.parse('226 Closing data connection.'))
    
    def NLST(self, _):
        """
        Returns file and directory names.
        @TODO Poder hacer ls sobre un directorio o archivo dado
        """
        s = self._get_actual_rel_path()
        # Open data connection
        self.cli_conn.send(self.parse(f'150 Opening ASCII mode data connection for {s}.'))
        self.data_conn=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.data_conn.connect((self.data_addr,self.data_port))
        except:
            self.cli_conn.send(self.parse('425 Data conection cannot be opened.'))

        # Make up a 'ls -l' format type
        os.chdir(self.curr_dir)
        listed = os.listdir('.')

        for item in listed:
            self.data_conn.send(self.parse(item))
        
        self.data_conn.close()
        self.cli_conn.send(self.parse('226 Closing data connection.'))
    
    def _get_actual_rel_path(self):
        """
        Get depth + build rel. path from <root>/.
        """
        curr = self.curr_dir.split('/')
        root = self.root_dir.split('/')
        j = len(root)
        s = self.NAV_FOLDER_AS_REL_PATH
        for i in range(1, len(curr)-j+1):
            s += curr[j-1+i] + '/'
        
        return s