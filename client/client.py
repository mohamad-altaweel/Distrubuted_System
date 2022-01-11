import socket
import select
import errno
import sys
import threading
import time
from random import randrange

class Client():
    
    def __broadcast_sender(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enable broadcasting mode
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        server.settimeout(0.2)
        message = b"I'm a new user"
        server.sendto(message, ('<broadcast>', 37020))
    
    def __broadcast_listener(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enable broadcasting mode
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("127.0.0.1", 37020))
        data, addr = client.recvfrom(1024)
        return data

    def __init__(self, header_length,ip, port, username):
        self.HEADER_LENGTH = header_length
        self.IP = ip
        self.PORT = int(port)
        self.username =  username.encode('utf-8')
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.start_connection()

    def start_connection(self):
        self.__broadcast_sender()
        self.client_socket.connect((self.IP, self.PORT))
        # Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
        self.client_socket.setblocking(False)
        username_header = f"{len(self.username):<{self.HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(username_header + self.username)
        self.recieve_thread = threading.Thread(target=self.receive_message, daemon = True)
        self.recieve_thread.start()

    def send_message(self,message):
        message = message.encode('utf-8')
        message_header = f"{len(message):<{self.HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(message_header + message)
    


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

                    # Now do the same for message (as we received username, we received whole message, there's no need to check if it has any length)
                    message_header = self.client_socket.recv(self.HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = self.client_socket.recv(message_length).decode('utf-8')

                    # Print message
                    print("\n")
                    print(f'{username} > {message}')

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






