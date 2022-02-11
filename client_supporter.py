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
"""


import socket, threading, os

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
    # CLIENT_MAX_SIZE_MSG = 1024  # Buffer for client messages


    def __init__(self, client_connection, client_address):
        self.client_conn = client_connection
        self.client_addr = client_address  # Both IP and Port number from client

        threading.Thread.__init__(self)
    
    def run(self):
        """
        Idea of algorithm to be implemented:

        1. Welcome the client (as especify in the RFC) (use of send())
        2. Infinite loop:
            2.1. Get the message from client (use of recv())
                2.1.1. If there's a message
                    2.1.1.1. Parse the message to separate command from arguments
                    2.1.1.2. Call the corresponding callback and send arguments if needed (try-except)
                        2.1.1.2.1. Send a 5XX error to user if callback makes an exception
                2.1.2. Otherwise
                    2.1.2.1. Break loop and exit (stop the thread)   
        """
    
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