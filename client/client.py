import socket
import select
import errno
import sys
import threading
import json
from random import randrange

class Client():
    
    def __broadcast_sender(self):
        # Send message on broadcast address
        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enable broadcasting mode
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Send message on broadcast address
        #broadcast_socket.bind((self.IP,self.PORT))
        message = self.__create_message("connect", {"username":str(self.username),"ip":self.IP,"port":self.PORT})
        broadcast_socket.sendto(message, ('192.168.10.255', 3795))
        broadcast_socket.close()
    
    def __init__(self, header_length,ip, port, username):
        self.HEADER_LENGTH = header_length
        self.IP = ip
        self.PORT = int(port)
        self.username =  username.encode('utf-8')
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.start_connection()

    def start_connection(self):
        self.__broadcast_sender()
        self.initial_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.initial_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.initial_socket.bind((self.IP, self.PORT))
        data, addr = self.initial_socket.recvfrom(4096)
        decoded_data = json.loads(data.decode())

        self.client_socket.connect((decoded_data['content']['IP'], decoded_data['content']['PORT']))
        print("Successfully connected to", decoded_data['content']['IP'])
        # Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
        #self.client_socket.setblocking(False)
        self.recieve_thread = threading.Thread(target=self.receive_message, daemon = True)
        self.recieve_thread.start()

    def send_message(self,command,message):
        message = self.__create_message(command, message)
        self.client_socket.send(message)
    
    def __create_message(self, command, content):
        dict_msg = {"command":command, "content":content}
        return json.dumps(dict_msg, ensure_ascii=False).encode('utf8')
    
    def __handle_message(message):
        command = message['command']
        if command == "connected":
            print("Successfully connected")


    def receive_message(self):
        while True:
            try:
                # Now we want to loop over received messages (there might be more than one) and print them
                while True:
                    # Receive our "header" containing username length, it's size is defined and constant
                    username_header = self.client_socket.recv(self.HEADER_LENGTH)
                    # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
                    if not len(username_header):
                        print("\n")
                        print('Connection closed by the server')
                        sys.exit()
                    # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                    message_header = self.client_socket.recv(self.HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = self.client_socket.recv(message_length).decode('utf-8')
                    self.__handle_message(message)

            except IOError as e:
                # This is normal on non blocking connections - when there are no incoming data error is going to be raised
                # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
                # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
                # If we got different error code - something happened
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print("\n")
                    print('Reading error: {}'.format(str(e)))
                    sys.exit()

                # We just did not receive anything
                continue

            except Exception as e:
                # Any other exception - something happened, exit
                print("\n")
                print('Reading error: '.format(str(e)))
                sys.exit()






