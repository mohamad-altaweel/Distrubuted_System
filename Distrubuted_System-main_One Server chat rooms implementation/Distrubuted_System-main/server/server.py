import socket
import select
import threading
from broadcaster import Broadcaster
import json
import time
from chatRoom import  ChatRoom
class Server():

    def __init__(self, header_len, ip, port, broadcast_port) -> None:
        self.HEADER_LENGTH = header_len
        self.IP = ip
        self.PORT = int(port)
        self.__start_server()
        self.start_listening_broadcast(broadcast_port)
        self.chat_rooms_list=[]
    def __start_server(self):
        # Create a socket
        # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
        # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_ - socket option
        # SOL_ - socket option level
        # Sets REUSEADDR (as a socket option) to 1 on socket
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind, so server informs operating system that it's going to use given IP and port
        # For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
        self.server_socket.bind((self.IP, self.PORT))
        # This makes server listen to new connections
        self.server_socket.listen()
        # List of sockets for select.select()
        self.sockets_list = [self.server_socket]
        # List of connected clients - socket as a key, user header and name as data
        self.clients = {}
        print(f'Listening for connections on {self.IP}:{self.PORT}...')
        self.recieve_thread = threading.Thread(target=self.run_server, daemon = True)
        self.recieve_thread.start()

    # Handles message receiving
    def __receive_message(self, client_socket):
        try:
            # Receive our "header" containing message length, it's size is defined and constant
            message_header = client_socket.recv(self.HEADER_LENGTH)
      #     print(message_header)
            # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(message_header):
                return False
            # Convert header to int value
            message_length = int(message_header.decode('utf-8').strip())
            # Return an object of message header and message data
            return {'header': message_header, 'data': client_socket.recv(message_length)}
        except:
            # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
            # or just lost his connection
            # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
            # and that's also a cause when we receive an empty message
            print("False is returned here from exception")
            return False
    
    def __create_message(self, command, content):
        dict_msg = {"command":command, "content":content}
        return json.dumps(dict_msg, ensure_ascii=False).encode('utf8')
    
    def __handle_message(self,message):
        command = message['command']

        if command == "connect":
            client_ip = message['content']['ip']
            client_port = message['content']['port']
            client_name = message['content']['username']
            room_name=message['content']['groupname']
            existing_chat_room=self.serch_for_groupname(room_name,self.chat_rooms_list)

            if existing_chat_room is False:   # New chat room created
               print("This group name does not exist we are creating you a new group with name: " + room_name)
               new_chat_room= self.create_chat_room(room_name,self.IP,self.PORT,self.server_socket)
               self.update_chat_rooms_list(new_chat_room)
               new_chat_room.update_client_List(client_ip,client_port,client_name)
               assigned_server= {'ip': new_chat_room.server_ip, 'port': new_chat_room.server_port}

            else:
               existing_chat_room.update_client_List(client_ip, client_port, client_name)
               assigned_server = {'ip': existing_chat_room.server_ip, 'port': existing_chat_room.server_port}

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            time.sleep(5)
            send_message = self.__create_message("connect", {"IP": assigned_server["ip"], "PORT": assigned_server["port"]})
            s.sendto(send_message, (message['content']['ip'], message['content']['port']))
            s.close()
            print("Successfully connected")



        elif command == "create":
            room_name=message['content']
            print("Creating new chat room: " + room_name)
    #        new_chat_room= self.create_chat_room(room_name,self.IP,self.PORT)
    #        self.update_chat_rooms_list(new_chat_room)
    #        new_chat_room.update_clientList(user)
        elif command == "join":
            room_name=message['content']
            print("Joining an existing chat room: " + room_name)
    def run_server(self):
        while True:
            # Calls Unix select() system call or Windows select() WinSock call with three parameters:
            #   - rlist - sockets to be monitored for incoming data
            #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
            #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
            # Returns lists:
            #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
            #   - writing - sockets ready for data to be send through them
            #   - errors  - sockets with some exceptions
            # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            # Iterate over notified sockets
            for notified_socket in read_sockets:
                # If notified socket is a server socket - new connection, accept it
                if notified_socket == self.server_socket:
                    # Accept new connection
                    # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                    # The other returned object is ip/port set
                    client_socket, client_address = self.server_socket.accept()
                    # Client should send his name right away, receive it
                    user = self.__receive_message(client_socket)
                    # If False - client disconnected before he sent his name
                    if user is False:
                        continue
                    data=user['data'].decode('utf-8')
                    jason_data=json.loads(data)
                    chat_room = self.serch_for_groupname(jason_data['content']['groupname'], self.chat_rooms_list)
                    # Add accepted socket to select.select() list
                    self.sockets_list.append(client_socket)
                    # Also save username and username header
                    self.clients[client_socket] = user
                    chat_room.update_socket_List(client_socket, user)
                    print("\n")

                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, jason_data['content']['username']))
               #     self.print_chat_rooms_list(self.chat_rooms_list)
                # Else existing socket is sending a message
                else:
                    # Receive message
                    message = self.__receive_message(notified_socket)

                    # If False, client disconnected, cleanup
                    if message is False:
                        print('Closed connection from: {}'.format(self.clients[notified_socket]['data'].decode('utf-8')))
                        # Remove from list for socket.socket()
                        self.sockets_list.remove(notified_socket)
                        # Remove from our list of users
                        del self.clients[notified_socket]
                        continue
                    # Get user by notified socket, so we will know who sent the message
                    user = self.clients[notified_socket]
                    message_data=message["data"].decode("utf-8")
                    jason_message_data = json.loads(message_data)
                    chat_room = self.serch_for_groupname(jason_message_data['content']['groupname'], self.chat_rooms_list)
                    user_data=user["data"].decode("utf-8")
                    jason_user_data = json.loads(user_data)
                    print("\n")

                    print('Received message from {}: {}'.format(jason_user_data['content']['username'],jason_message_data['content']['message']))
                    # Iterate over connected clients and broadcast message
                    if jason_message_data['command']== "send":
                      for client_socket in chat_room.clients:
                      #    print(client_socket)
                          # But don't sent it to sender
                          if client_socket != notified_socket:
                             # Send user and message (both with their headers)
                             # We are reusing here message header sent by sender, and saved username header send by user when he connected

                             client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                    else:
                        self.__handle_message(jason_message_data,jason_user_data)
            # It's not really necessary to have this, but will handle some socket exceptions just in case
            for notified_socket in exception_sockets:
                # Remove from list for socket.socket()
                self.sockets_list.remove(notified_socket)
                # Remove from our list of users
                del self.clients[notified_socket]

    def start_listening_broadcast(self, BROADCAST_PORT) -> None:
        self.MY_HOST = socket.gethostname()
        self.MY_IP_BROADCAST = socket.gethostbyname(self.MY_HOST)
        self.BROADCAST_PORT = BROADCAST_PORT
        # Create a UDP socket
        self.bd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        self.bd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        self.bd_socket.bind(("", self.BROADCAST_PORT))
        print("Listening to broadcast messages")
        self.recieve_thread = threading.Thread(target=self.__start_receiving_broadcast, daemon = True)
        self.recieve_thread.start()
    
    def __start_receiving_broadcast(self):
        while True:
            data, addr = self.bd_socket.recvfrom(2048)
            decoded_data = json.loads(data.decode())
            print(decoded_data)
            if data:
                print("Received broadcast message:", decoded_data["command"], addr)
                self.__handle_message(decoded_data)
    
    def broadcast_message(self,ip, broadcast_message):
        # Send message on broadcast address
        # Create a UDP socket
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Enable broadcasting mode
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Send message on broadcast address
        broadcast_socket.sendto(str.encode(broadcast_message), (ip, self.BROADCAST_PORT))
        broadcast_socket.close()

    def create_chat_room(self, name,server_ip,server_port,server_socket):
        new_chat_room=ChatRoom(name,server_ip,server_port,server_socket)
        return new_chat_room
    def update_chat_rooms_list(self,chat_room):
        self.chat_rooms_list.append(chat_room)
    def serch_for_groupname(self,chat_room_name,chat_rooms_list):
        for chat_room in chat_rooms_list:
          if chat_room.name==chat_room_name:
              return chat_room
        return False
    def print_chat_rooms_list(self, chat_rooms_list):
        for chat_room in chat_rooms_list:
          print(chat_room.name+ ": "),print(*chat_room.clients)
