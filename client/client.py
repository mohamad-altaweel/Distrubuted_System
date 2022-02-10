import socket
import select
import errno
import sys
import threading
import json
from random import randrange
import time 

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
        broadcast_socket.settimeout(0.2)
        message = self.__create_message("connect-init", {"username":str(self.username),"ip":self.IP,"port":self.PORT, "groupname":str(self.groupname)})
        broadcast_socket.sendto(message, ('<broadcast>', 3795))
        print("Broadcast message sent!")
        broadcast_socket.close()

    
    def __init__(self, header_length,ip, port, username, groupname):
        self.HEADER_LENGTH = header_length
        self.IP = ip
        self.PORT = int(port)
        self.username =  username.encode('utf-8')
        self.groupname = groupname.encode('utf-8')
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.start_connection()


    def start_connection(self):
        count = 0
        while not self.connected and count < 2:
            try:
                self.__broadcast_sender()
                self.initial_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.initial_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.initial_socket.bind((self.IP, self.PORT))
                data, addr = self.initial_socket.recvfrom(4096)
                decoded_data = json.loads(data.decode())
                self.connected = True
            except socket.error as msg:
                print("Failed to broadcast a new connection")
                print("Socket Error: {}".format(msg))
                print("Trying to reconnect...")
                count = count + 1
        if self.connected:
                self.client_socket.connect((decoded_data['content']['IP'], int(decoded_data['content']['PORT'])))
                print("Successfully connected to", decoded_data['content']['IP'])
                time.sleep(0.5)
                self.send_message("connect", {"username":str(self.username),"ip":self.IP,"port":self.PORT, "groupname":str(self.groupname)})
                self.send_message("connect", {"username":str(self.username),"ip":self.IP,"port":self.PORT, "groupname":str(self.groupname)})
                self.recieve_thread = threading.Thread(target=self.receive_message, daemon = True)
                self.recieve_thread.start()
        else:
            print("Please try again")

    def send_message(self,command,message):
        message = self.__create_message(command, message)
        message_header = f"{len(message):<{self.HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(message_header+message)
    
    def __create_message(self, command, content):
        dict_msg = {"command":command, "content":content}
        return json.dumps(dict_msg, ensure_ascii=False).encode('utf8')
    
    def __handle_message(self,message,username):
        command = message['command']
        if command == "connected":
            print("Successfully connected")
        elif command == "send":
            # Print message
            print("\n")
            print(username['content']['username'] + ' : ' + message['content']['message'] )
        elif command == "exit":
            print(username['content']['username'] + " has lift the chat room")


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
                    # Convert header to int value
                    username_length = int(username_header.decode('utf-8').strip())
                    # Receive and decode username
                    username = self.client_socket.recv(username_length).decode('utf-8')
                    jason_username = json.loads(username)
                    # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                    message_header = self.client_socket.recv(self.HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = self.client_socket.recv(message_length).decode('utf-8')
                    jason_message=json.loads(message)
                    self.__handle_message(jason_message,jason_username)

            except IOError as e:
                # This is normal on non blocking connections - when there are no incoming data error is going to be raised
                # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
                # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
                # If we got different error code - something happened
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print("\n")
                    print('Reading error: {}'.format(str(e)))
                    print("Connection error")
                    self.connected = False
                    self.client_socket.close()
                    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.start_connection()
                    break
            except Exception as e:
                # Any other exception - something happened, exit
                print("\n")
                print('Reading error: '.format(str(e)))
                print("Connection error")
                self.connected = False
                self.client_socket.close()
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.start_connection()
                break



   