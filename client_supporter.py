#!/usr/bin/env python3
"""
Author: Carlos Anivarro Batiste

All procedure with regards to command treatment is done as the FTP-RFC (959) especifies.

For easy callback security, a dictionary will be used so, for example:
 - cmds_available = {"RETR": True, "CWD": False}

So if client enters 'RETR' command, server will get its callback function and execute it
safely. Otherwise, will promt an error telling cmd is not implemented.


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

users = {
    'eps': 'eps'
}

cmds_available = {
    'HELP': True,
    'OPTS': True,
    'TYPE': True,
    'USER': True,
    'PASS': True,
    'REIN': True,
    'QUIT': True,
    'CDUP': True,
    'ACCT': False,
    'NOOP': True,
    'SYST': True,
    'PORT': True,
    'LIST': True,
    'NLST': True,
    'RETR': True,
    'STOR': True,
    'APPE': True,
    'DELE': True,
    'RNFR': True,
    'RNTO': True,
    'RMD': True,
    'MKD': True,
    'CWD': True,
}
cmds_3_chars_0_args = {
    'PWD': True
}

ASCII = 'ascii'
UTF8 = 'utf-8'

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
    CLIENT_MAX_SIZE_MSG = 256   # Buffer for client messages
    READ_SIZE = 1024            # Buffer for reading files
    WRITE_SIZE = 1024           # Buffer for writing files
    DEFAULT_DATA_PORT = 8888    #20
    NAV_FOLDER = '/nav'
    NAV_FOLDER_AS_REL_PATH = 'nav/'
    

    def __init__(self, client_connection, client_address, server_dir):
        self.cli_conn = client_connection
        self.cli_addr = client_address  # Both IP and Port number from client
        self.data_addr = client_address[0]
        self.data_port = self.DEFAULT_DATA_PORT

        self.encoding = ASCII
        self.binary = False
        self.parse = lambda a: f'{a}\r\n'.encode(self.encoding)         # For control port data
        self.parse_code = lambda a: f'{a}\r\n'.encode(self.encoding)    # For response code
        self.parse_item = lambda a: f'{a}\r\n'.encode(self.encoding)    # For LST and NLST
        self.decode = lambda a: a.decode(self.encoding)

        self.file_to_rename = None
        self.user = None
        self.root_dir = server_dir + self.NAV_FOLDER
        self.curr_dir = self.root_dir
        os.chdir(self.root_dir)

        self._quit = False
        threading.Thread.__init__(self)
    
    def run(self):
        conn = self.cli_conn
        parse = self.parse_code


        print(f"[{threading.get_ident()}] Cliente conectado")
        conn.send(parse('220 Carlos FTP Server (Version 0.5) ready'))
        while self._quit is False:
            req = self.decode(conn.recv(self.CLIENT_MAX_SIZE_MSG))[:-2]
            print(f"[{threading.get_ident()}] Recibido: _{req}_")
            if req:
                try:
                    # Get method callback
                    # Ensure the 3 char CMDs non-parametrized are available
                    if len(req) == 3 and ''.join(req) not in cmds_3_chars_0_args:
                        conn.send(parse('502 Method not implemented'))
                        continue
                    
                    f = ''.join(req[:4])
                    if f[-1] == ' ':    # Get the 3 char CMDs parametrized
                        f = f[:3]
                    
                    # If not recognised, respond and exit
                    exit = False
                    if f not in cmds_available:
                        exit = True
                    if f in cmds_available:
                        if cmds_available[f] is False:
                            exit = True
                    if exit:
                        conn.send(parse('502 Method not implemented'))
                        continue

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
                    continue
            
            else:
                break
        print(f"[{threading.get_ident()}] Cliente desconectado")
    
    def HELP(self, msg):
        # Just accept the generic HELP cmd
        if msg:
            self.cli_conn.send(self.parse_code('501 No parameters accepted.'))
            return

        # Loop through all cmds available
        desc = '211 Commands implemented: '
        for c in cmds_available.keys():
            if cmds_available[c] is True:
                desc += c + ', '
        for c in cmds_3_chars_0_args.keys():
            if cmds_3_chars_0_args[c] is True:
                desc += c + ', '
        
        desc = desc[:-2] + '.'  # Replace last ', ' substring to '.'

        self.cli_conn.send(self.parse(desc))

    def OPTS(self, msg):
        args = msg.split(" ")
        if len(args) == 2:
            if args[1] == 'ON':
                if args[0] == 'UTF8':
                    self.encoding = UTF8
                    self.binary = False
                    self.cli_conn.send(self.parse_code('200 Mode turned to UTF8.'))
                    return
        
        self.cli_conn.send(self.parse_code('504 Not implemented for those parameters.'))
    
    def USER(self, msg):
        """
        User log-in.
        """
        if msg not in users:
            self.cli_conn.send(self.parse_code('530 User doesn\'t exist.'))
            return

        self.user = msg
        self.cli_conn.send(self.parse_code('331 Password needed.'))
    
    def PASS(self, msg):
        """
        User password.
        Needed after USER.
        """
        if self.user is None:       # USER cmd not used
            self.cli_conn.send(self.parse_code('503 Incorrect sequence.'))
            return
        if self.user not in users:  # USER not accepted
            self.cli_conn.send(self.parse_code('530 User not connected.'))
            return
        if users[self.user] != msg: # Wrong password
            self.cli_conn.send(self.parse_code('530 Wrong password.'))
            return
            
        self.cli_conn.send(self.parse_code('230 User connected, please continue.'))
    
    def REIN(self, msg):
        if msg:
            self.cli_conn(self.parse_code('502 Syntax error.'))
            return

        self.data_port = self.DEFAULT_DATA_PORT
        self.curr_dir = self.root_dir
        os.chdir(self.root_dir)
        self.encoding = ASCII
        self.binary = False
        self.user = None
        self.cli_conn.send(self.parse_code(f'220 Service prepared for new user.'))

    def QUIT(self, msg):
        """
        Quit user, hence thread dies.
        """
        if msg:
            self.cli_conn(self.parse_code('502 Syntax error.'))
            return
        
        self._quit = True
        self.cli_conn.send(self.parse_code(f'221 Bye.'))
    
    def NOOP(self, msg):
        """
        No operation.
        """
        if msg:
            self.cli_conn(self.parse_code('502 Syntax error.'))
            return

        self.cli_conn.send(self.parse_code('220 OK.'))
    
    def SYST(self, msg):
        """
        Give information about the server.
        """
        if msg:
            self.cli_conn(self.parse_code('502 Syntax error.'))
            return

        self.cli_conn.send(self.parse_code('215 CarlosFTPServer system type.'))

    def CDUP(self, msg):
        """
        Change to parent directory.
        """
        if msg:
            self.cli_conn(self.parse_code('502 Syntax error.'))
            return
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return

        depth_aimed, tot_depth = self._get_depth(['..'])
        if tot_depth < 0:
            self.cli_conn.send(self.parse_code('450 Not available, access forbidden.'))
            return

        os.chdir('..')
        self.curr_dir = os.getcwd()
        self.cli_conn.send(self.parse_code('200 OK.'))

    def CWD(self, msg):
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return

        # Get depth aimed by client
        path = msg.split('/')
        depth_aimed, tot_depth = self._get_depth(path)

        """
        If total_depth is negative or depth_aimed is negative and the query starts with /<path_remaining>,
        then reject the query from client.
        """
        if  (tot_depth < 0) or \
            (path[0] == '' and depth_aimed < 0):
            self.cli_conn.send(self.parse_code('450 Not available, access forbidden.'))
            return

        if msg == '/':
            msg=self.root_dir
        elif msg[0] == '/':
            msg=self.root_dir + msg
        
        try:
            os.chdir(msg)
        except OSError:
            self.cli_conn.send(self.parse_code('501 Incorrect path.'))
            return

        self.curr_dir = os.getcwd()
        self.cli_conn.send(self.parse_code('250 OK.'))

    def PORT(self, msg):
        """
        Set a PORT and a IP to create future Data channels.
        """
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return

        data = msg.split(',')
        try:
            self.data_addr = '.'.join(data[:4])                 # Get IP
            self.data_port = (int(data[4]) << 8) + int(data[5]) # Get port
        except:
            self.cli_conn.send(self.parse_code('501 Parameter syntax error'))
        
        self.cli_conn.send(self.parse_code('200 PORT succesful.'))

    def LIST(self, msg):
        """
        Returns same format as 'ls -l' from UNIX systems.
        """
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return


        # Make up a 'ls -l' format type
        listed = os.listdir('.')
        if msg:
            # Operate path of the directory
            path = msg.split('/')

            # Ensure depth aimed by user is correct
            depth_aimed, tot_depth = self._get_depth(path)
            if  tot_depth < 0 or \
                (path[0] == '' and depth_aimed < 0):
                self.cli_conn.send(self.parse_code('550 Not available, access forbidden.'))
                return

            if msg == '/':
                msg=self.root_dir
            elif msg[0] == '/':
                msg=self.root_dir + msg

            # Verify path exists
            msg_path = '/'.join(path)
            if msg_path != '' and not os.path.exists(msg_path):
                self.cli_conn.send(self.parse_code('501 Path incorrect.'))
                return

            # Verify user is listing a directory
            if not os.path.isdir(msg):
                self.cli_conn.send(self.parse_code('550 Not a directory.'))
                return
            
            # Swap to new directory
            listed = os.listdir(msg)
            if msg[-1] != '/': msg += '/'

        # Open data connection
        self.cli_conn.send(self.parse_code(f'150 Opening ASCII mode data connection.'))
        self.data_conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.data_conn.connect((self.data_addr,self.data_port))
        except:
            self.cli_conn.send(self.parse_code('425 Data conection cannot be opened.'))
            return

        item_parsed = ''
        base_mode = 'rwx'*3
        try:
            for item in listed:
                s = os.stat(msg+item)
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
                self.data_conn.send(self.parse_item(item_parsed))
        except Exception as e:
            print(e)
            self.data_conn.close()
            self.cli_conn.send(self.parse_code('451 Interrupted. Local error.'))
            return

        
        self.data_conn.close()
        self.cli_conn.send(self.parse_code('226 Closing data connection.'))
    
    def NLST(self, msg):
        """
        Returns file and directory names.
        """
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return

        # Make up a 'ls -l' format type
        listed = os.listdir('.')
        if msg:
            # Operate path of the directory
            path = msg.split('/')

            # Ensure depth aimed by user is correct
            depth_aimed, tot_depth = self._get_depth(path)
            if  tot_depth < 0 or \
                (path[0] == '' and depth_aimed < 0):
                self.cli_conn.send(self.parse_code('550 Not available, access forbidden.'))
                return

            if msg == '/':
                msg=self.root_dir
            elif msg[0] == '/':
                msg=self.root_dir + msg

            # Verify path exists
            msg_path = '/'.join(path)
            if msg_path != '' and not os.path.exists(msg_path):
                self.cli_conn.send(self.parse_code('501 Path incorrect.'))
                return

            # Verify user is listing a directory
            if not os.path.isdir(msg):
                self.cli_conn.send(self.parse_code('550 Not a directory.'))
                return
            
            # Swap to new directory
            listed = os.listdir(msg)
            if msg[-1] != '/': msg += '/'

        # Open data connection
        self.cli_conn.send(self.parse_code(f'150 Opening ASCII mode data connection.'))
        self.data_conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.data_conn.connect((self.data_addr,self.data_port))
        except:
            self.cli_conn.send(self.parse_code('425 Data conection cannot be opened.'))
            return

        for item in listed:
            self.data_conn.send(self.parse_item(item))
        
        self.data_conn.close()
        self.cli_conn.send(self.parse_code('226 Closing data connection.'))
    
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
    
    def _get_depth(self, path_aimed):
        """
        Returns a tuple (depth_aimed, total_depth) so the function
        calling can decide what to do.
        """
        # Get current depth
        curr = self.curr_dir.split('/')
        root = self.root_dir.split('/')
        act_depth = len(curr) - len(root)
        
        # Get depth aimed by client
        depth_aimed = 0
        for item in path_aimed:
            if item == '..': 
                depth_aimed -= 1
            elif item != '':        # Avoid '/' character ('' by split)
                depth_aimed += 1
            if -depth_aimed > act_depth:
                return -1, -1

        tot_depth = act_depth + depth_aimed
        return depth_aimed, tot_depth
    
    def TYPE(self, msg):
        """
        Change file format tranfer.
        """
        if msg.lower() == 'i':      # Binary
            self.binary = True
            self.cli_conn.send(self.parse_code('200 Binary mode enabled.'))
            return
        elif msg.lower() == 'a':    # ASCII
            self.encoding = ASCII
            self.binary = False
            self.cli_conn.send(self.parse_code('200 ASCII mode enabled.'))
            return

        self.cli_conn.send(self.parse_code('504 Not implemented for that format.'))

    def RETR(self, msg):
        """
        Send file content to client.
        """
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return
        
        # Verify path exists
        if not os.path.exists(msg):
            self.cli_conn.send(self.parse_code('501 File not found.'))
            return

        # Verify user is retrieving a file
        if os.path.isdir(msg):
            self.cli_conn.send(self.parse_code('450 Not a file.'))
            return

        # Open data connection
        self.cli_conn.send(self.parse_code('150 Opening data connection.'))
        self.data_conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.data_conn.connect((self.data_addr,self.data_port))
        except:
            self.cli_conn.send(self.parse_code('425 Data conection cannot be opened.'))
            return

        # Send data
        try:
            if self.binary is False:
                with open(msg, 'r') as f:
                    data = f.read(self.READ_SIZE)
                    while data:
                        self.data_conn.send(data.encode(self.encoding))
                        data = f.read(self.READ_SIZE)
            else:
                with open(msg, 'rb') as f:
                    data = f.read(self.READ_SIZE)
                    while data:
                        self.data_conn.send(data)
                        data = f.read(self.READ_SIZE)
        except:
            self.data_conn.close()
            bin = 'disabled' if self.binary is False else 'enabled'
            desc = f'450 Binary mode is {bin}. Cannot send requested file.'
            self.cli_conn.send(self.parse_code(desc))
            return
        
        # Close data connection
        self.data_conn.close()
        self.cli_conn.send(self.parse_code('250 File transferred succesfully.'))

    def STOR(self, msg):
        """
        Create a file or replace its content with new data.
        """
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return
        
        # Operate path of the file to append
        path = msg.split('/')
        path.pop()

        # Ensure depth aimed by user is correct
        _, tot_depth = self._get_depth(path)
        if tot_depth < 0:
            self.cli_conn.send(self.parse_code('450 Not available, access forbidden.'))
            return

        # Verify path exists
        msg_path = '/'.join(path)
        if msg_path != '' and not os.path.exists(msg_path):
            self.cli_conn.send(self.parse_code('501 Path incorrect.'))
            return

        # Open data connection
        self.cli_conn.send(self.parse_code('150 Opening data connection.'))
        self.data_conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.data_conn.connect((self.data_addr,self.data_port))
        except:
            self.cli_conn.send(self.parse_code('425 Data conection cannot be opened.'))
            return
        
        # Get file transferred by user
        try:
            self._store_file(msg)
        except OSError as e:
            if e.errno == 21:
                desc = f'450 Aiming a directory. Cannot store requested file.'
                self.cli_conn.send(self.parse_code(desc))
                self.data_conn.close()
                return
        except:
                bin = 'disabled' if self.binary is False else 'enabled'
                desc = f'450 Binary mode is {bin}. Cannot store requested file.'
                self.cli_conn.send(self.parse_code(desc))
                self.data_conn.close()
                return

        # Close data connection
        self.data_conn.close()
        self.cli_conn.send(self.parse_code('250 File transferred succesfully.'))
    
    def _store_file(self, msg):
        """
        Private function to store given content.
        """
        # Store ASCII/UTF-8/... file (.txt, .php, ...)
        if self.binary is False:
            with open(msg, 'w') as f:
                data = self.decode(self.data_conn.recv(self.WRITE_SIZE))
                f.write(data)
                while data:
                    data = self.decode(self.data_conn.recv(self.WRITE_SIZE))
                    f.write(data)
        
        # Store BINARY file (.jpeg, .mp4, ...)
        else:
            with open(msg, 'wb') as f:
                data = self.data_conn.recv(self.WRITE_SIZE)
                f.write(data)
                while data:
                    data = self.data_conn.recv(self.WRITE_SIZE)
                    f.write(data)

    def APPE(self, msg):
        """
        Append content to an existing or new file.
        """
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return

        # Operate path of the file to append
        path = msg.split('/')
        path.pop()

        # Ensure depth aimed by user is correct
        _, tot_depth = self._get_depth(path)
        if tot_depth < 0:
            self.cli_conn.send(self.parse_code('450 Not available, access forbidden.'))
            return

        # Verify path exists
        msg_path = '/'.join(path)
        if msg_path != '' and not os.path.exists(msg_path):
            self.cli_conn.send(self.parse_code('501 Path incorrect.'))
            return

        # Open data connection
        self.cli_conn.send(self.parse_code('150 Opening data connection.'))
        self.data_conn = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            self.data_conn.connect((self.data_addr,self.data_port))
        except:
            self.cli_conn.send(self.parse_code('425 Data conection cannot be opened.'))
            return
        
        # Get file transferred by user
        try:
            self._append_file(msg)
        except OSError as e:
            if e.errno == 21:
                desc = f'450 Aiming a directory. Cannot append requested file.'
                self.cli_conn.send(self.parse_code(desc))
                self.data_conn.close()
                return
        except:
                bin = 'disabled' if self.binary is False else 'enabled'
                desc = f'450 Binary mode is {bin}. Cannot append requested file.'
                self.cli_conn.send(self.parse_code(desc))
                self.data_conn.close()
                return

        # Close data connection
        self.data_conn.close()
        self.cli_conn.send(self.parse_code('250 File transferred succesfully.'))
    
    def _append_file(self, msg):
        """
        Private function to store given content.
        """
        # Append to ASCII/UTF-8/... file (.txt, .php, ...)
        if self.binary is False:
            with open(msg, 'a') as f:
                data = self.decode(self.data_conn.recv(self.WRITE_SIZE))
                f.write(data)
                while data:
                    data = self.decode(self.data_conn.recv(self.WRITE_SIZE))
                    f.write(data)
        
        # Append to BINARY file (.jpeg, .mp4, ...)
        else:
            with open(msg, 'ab') as f:
                data = self.data_conn.recv(self.WRITE_SIZE)
                f.write(data)
                while data:
                    data = self.data_conn.recv(self.WRITE_SIZE)
                    f.write(data)

    def RNFR(self, msg):
        """
        Get and prepare the file to rename.
        """
        # Check user is logged
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return
        
        # Operate path of the directory
        path = msg.split('/')
        path.pop()

        # Ensure depth aimed by user is correct
        _, tot_depth = self._get_depth(path)
        if  tot_depth < 0:
            self.cli_conn.send(self.parse_code('550 Not available, access forbidden.'))
            return

        if msg == '/':
            msg=self.root_dir
        elif msg[0] == '/':
            msg=self.root_dir + msg

        # Verify path exists
        msg_path = '/'.join(path)
        if msg_path != '' and not os.path.exists(msg_path):
            self.cli_conn.send(self.parse_code('501 Path incorrect.'))
            return

        # Verify user is deleting a file
        if not os.path.isfile(msg):
            self.cli_conn.send(self.parse_code('450 Not a file.'))
            return

        self.file_to_rename = msg
        self.cli_conn.send(self.parse_code('350 File selected.'))

    def RNTO(self, msg):
        """
        Rename the file selected.
        Needed after RNFR.
        """
        if self.file_to_rename is None:
            self.cli_conn.send(self.parse_code('503 Incorrect sequence.'))
        
        os.rename(self.file_to_rename, msg)
        self.file_to_rename = None  # Reset

        self.cli_conn.send(self.parse_code('250 File renamed succesfully.'))

    def DELE(self, msg):
        """
        Delete file.
        """
        # Check user is logged
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return
        
        # Operate path of the directory
        path = msg.split('/')
        path.pop()

        # Ensure depth aimed by user is correct
        _, tot_depth = self._get_depth(path)
        if  tot_depth < 0:
            self.cli_conn.send(self.parse_code('550 Not available, access forbidden.'))
            return

        if msg == '/':
            msg=self.root_dir
        elif msg[0] == '/':
            msg=self.root_dir + msg

        # Verify path exists
        msg_path = '/'.join(path)
        if msg_path != '' and not os.path.exists(msg_path):
            self.cli_conn.send(self.parse_code('501 Path incorrect.'))
            return

        # Verify user is deleting a file
        if not os.path.isfile(msg):
            self.cli_conn.send(self.parse_code('450 Not a file.'))
            return
        
        # Delete file
        os.remove(msg)

        self.cli_conn.send(self.parse_code('250 File deleted succesfully.'))
    
    def RMD(self, msg):
        """
        Delete directory.
        """
        # Check user is logged
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return
        
        # Operate path of the directory
        path = msg.split('/')
        path.pop()

        # Ensure depth aimed by user is correct
        _, tot_depth = self._get_depth(path)
        if  tot_depth < 0:
            self.cli_conn.send(self.parse_code('550 Not available, access forbidden.'))
            return

        if msg == '/':
            msg=self.root_dir
        elif msg[0] == '/':
            msg=self.root_dir + msg

        # Verify path exists
        msg_path = '/'.join(path)
        if msg_path != '' and not os.path.exists(msg_path):
            self.cli_conn.send(self.parse_code('501 Path incorrect.'))
            return

        # Verify user is deleting a directory
        if not os.path.isdir(msg):
            self.cli_conn.send(self.parse_code('550 Not a directory.'))
            return
        
        # Delete directory
        os.rmdir(msg)

        self.cli_conn.send(self.parse_code('250 Directory deleted succesfully.'))
    
    def MKD(self, msg):
        """
        Create directory.
        """
        # Check user is logged
        if self.user is None:
            self.cli_conn.send(self.parse_code('530 Not connected.'))
            return
        
        # Operate path of the directory
        path = msg.split('/')
        path.pop()

        # Ensure depth aimed by user is correct
        _, tot_depth = self._get_depth(path)
        if  tot_depth < 0:
            self.cli_conn.send(self.parse_code('550 Not available, access forbidden.'))
            return

        if msg == '/':
            msg=self.root_dir
        elif msg[0] == '/':
            msg=self.root_dir + msg

        # Verify path exists
        msg_path = '/'.join(path)
        if msg_path != '' and not os.path.exists(msg_path):
            self.cli_conn.send(self.parse_code('501 Path incorrect.'))
            return
        
        # Create directory
        os.mkdir(msg)

        self.cli_conn.send(self.parse_code('250 Directory created succesfully.'))