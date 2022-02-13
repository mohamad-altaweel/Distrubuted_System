import socket
import select
import threading
import json
import time
from ast import literal_eval as make_tuple
from chatRoom import  ChatRoom
import random
import sys

class Server():

    def __init__(self, header_len, ip, port, broadcast_port) -> None:
        self.HEADER_LENGTH = header_len
        self.IP = ip
        self.PORT = int(port)
        self.BROADCAST_PORT = int(broadcast_port)
        self.leader = False
        self.participant = False
        self.leader_id = "" 
        self.servers= {}
        self.servers[(self.IP,self.PORT)] = []
        self.__start_server()
        self.start_listening_broadcast(self.BROADCAST_PORT)
        self.chat_rooms_list=[]
        msg = self.__create_message("join-server",[(self.IP,self.PORT)])
        self.broadcast_message("192.168.10.255",msg)
        time.sleep(3)
        if len(self.servers) == 1:
            print("Noone is a leader, I will take the lead")
            self.leader = True
            self.leader_id = self.IP
            msg = self.__create_message("leader-id",self.IP)
            self.broadcast_message("192.168.10.255",msg)
        

    def __start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.IP, self.PORT))
            self.server_socket.listen()
            self.sockets_list = [self.server_socket]
            self.clients = {}
            print(f'Listening for connections on {self.IP}:{self.PORT}...')
            self.recieve_thread = threading.Thread(target=self.run_server, daemon = True)
            self.recieve_thread.start()
        except KeyboardInterrupt:
            self.shutdown()
            sys.exit()

    def __receive_message(self, client_socket):
        try:
            message_header = client_socket.recv(self.HEADER_LENGTH)
            if not len(message_header):
                return False
            message_length = int(message_header.decode('utf-8').strip())
            return {'header': message_header, 'data': client_socket.recv(message_length)}
        except:
            return False
    
    def __create_message(self, command, content):
        dict_msg = {"command":command, "content":content}
        return json.dumps(dict_msg, ensure_ascii=False).encode('utf8')
    
    def __handle_message(self,message,addr,client_socket=None):
        command = message['command']
        if command == "connect-init" and self.leader:
            client_ip = message['content']['ip']
            client_port = message['content']['port']
            client_name = message['content']['username']
            room_name=message['content']['groupname']
            x = self.get_chat_rooms_names()
            print(x)
            if room_name in x:   # New chat room created
                server_chosen = self.find_room(room_name)
                assigned_server= {'ip': server_chosen[0], 'port': server_chosen[1]}
            else:
               print("This group name does not exist we are creating you a new group with name: " + room_name)
               server_chosen = random.choice(list(self.servers.keys()))
               self.servers[server_chosen] = room_name
               assigned_server= {'ip': server_chosen[0], 'port': server_chosen[1]}
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            time.sleep(5)
            send_message = self.__create_message("connect", {"IP":assigned_server['ip'],"PORT":assigned_server['port']})
            s.sendto(send_message, (message['content']['ip'],message['content']['port']))
            s.close()
        elif command == "connect":
            client_ip = message['content']['ip']
            client_port = message['content']['port']
            client_name = message['content']['username']
            room_name=message['content']['groupname']
            existing_chat_room=self.serch_for_groupname(room_name,self.chat_rooms_list)
            if existing_chat_room is False:   # New chat room created
               print("This group name does not exist we are creating you a new group with name: " + room_name)
               new_chat_room= self.create_chat_room(room_name,self.IP,self.PORT,self.server_socket)
               self.update_chat_rooms_list(new_chat_room)
               new_chat_room.add_client_List(client_ip,client_port,client_name)
               new_chat_room.add_socket_List(client_socket, client_name)
            else:
                print("Hallloooooooooo")
                existing_chat_room.add_client_List(client_ip, client_port, client_name)
                existing_chat_room.add_socket_List(client_socket, client_name)
        elif command == "create":
            room_name=message['content']
            print("Creating new chat room: " + room_name)
        elif command == "join":
            room_name=message['content']
            print("Joining an existing chat room: " + room_name)
        elif command == "join-server":
            self.servers[tuple(message['content'][0])] = []
            print("A new member joined the team {}".format(message['content']))
            if self.leader:
                print(self.servers)
                msg = self.__create_message("synchronoize",self.to_json(self.servers))
                self.broadcast_message("192.168.10.255",msg)
                msg_leader = self.__create_message("leader-id",self.IP)
                self.broadcast_message("192.168.10.255",msg_leader)
        elif command == "synchronoize":
            self.__parse_keys_to_tuple(message['content'])
            print(message['content'])
            self.servers = self.merge_two_dicts(self.servers,message['content'] )
        elif command == "leader-id":
            leader_server = message['content']
            if self.IP == leader_server:
                pass
            else:
                self.leader_id = leader_server
                print("The current boss is {}".format(self.leader_id))
        elif command == "start-election":
            self.in_election = True
            members = message['content']
            election_thread = threading.Thread(target=self.start_election, args=(members,), daemon = True)
            election_thread.start()
        elif command == "delete":
            to_delete = make_tuple(str(message['content']))
            del self.servers[tuple(to_delete)]
            print(self.servers)


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
                    # Add accepted socket to select.select() list
                    self.sockets_list.append(client_socket)
                    # Also save username and username header
                    self.clients[client_socket] = user
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
                    print(jason_message_data)
                    print('Received message from {}: {}'.format(jason_user_data['content']['username'],jason_message_data['content']))
                    # Iterate over connected clients and broadcast message
                    if jason_message_data['command'] == "send" and chat_room is not False:
                      for client_socket in chat_room.clients:
                      #    print(client_socket)
                          # But don't sent it to sender
                          if client_socket != notified_socket:
                             # Send user and message (both with their headers)
                             # We are reusing here message header sent by sender, and saved username header send by user when he connected

                             client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                    elif jason_message_data['command'] == "exit":
                        for client_socket in chat_room.clients:
                            #    print(client_socket)
                            # But don't sent it to sender
                            if client_socket != notified_socket:
                                # Send user and message (both with their headers)
                                # We are reusing here message header sent by sender, and saved username header send by user when he connected
                                client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                    else:
                        self.__handle_message(jason_message_data,jason_user_data,client_socket=client_socket)
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
        self.bd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.bd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bd_socket.bind(('', self.BROADCAST_PORT))
        print("Listening to broadcast messages")
        self.recieve_thread = threading.Thread(target=self.__start_receiving_broadcast, daemon = True)
        self.recieve_thread.start()
    
    def __start_receiving_broadcast(self):
        while True:
            data, addr = self.bd_socket.recvfrom(2048)
            decoded_data = json.loads(data.decode())
            if data:
                print("Received broadcast message:", decoded_data["command"], addr)
                self.__handle_message(decoded_data,addr)
    
    def broadcast_message(self,ip, broadcast_message):
        broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_socket.sendto(broadcast_message, (ip, self.BROADCAST_PORT))
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
    
    def get_chat_rooms_names(self):
        result = []
        for server in self.servers:
            result.append(self.servers[server])
        return result

    def merge_two_dicts(self,x, y):
        z = x.copy()   # start with keys and values of x
        z.update(y)    # modifies z with keys and values of y
        return z

    def find_room(self,roomname):
        for server in self.servers:
            if roomname in self.servers[server]:
                return server

    def key_to_json(self,data):
        if data is None or isinstance(data, (bool, int, str)):
            return data
        if isinstance(data, (tuple, frozenset)):
            return str(data)
        raise TypeError

    def to_json(self,data):
        if data is None or isinstance(data, (bool, int, tuple, range, str, list)):
            return data
        if isinstance(data, (set, frozenset)):
            return sorted(data)
        if isinstance(data, dict):
            return {self.key_to_json(key): self.to_json(data[key]) for key in data}
        raise TypeError
    
    def trigger_election(self, withoutSelf = False):
        members = self.__get_server_member()
        members_to_send = self.__get_server_member()
        print(members)
        mid = self.IP
        if withoutSelf:
            mid = "0"
            members_to_send.remove(self.IP)
        msg_leader = self.__create_message("start-election",members_to_send)
        self.broadcast_message("192.168.10.255",msg_leader)
        election_message = {"mid":mid, "isLeader":False}
        ring_trigger_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ring = self.form_ring(members)
        neighbour = self.get_neighbour(ring, self.IP, 'left')
        time.sleep(2)
        self.participant = True
        ring_trigger_socket.sendto(json.dumps(election_message).encode(), (neighbour,10001))
        ring_trigger_socket.close()

    def __get_server_member(self):
        result = []
        servers_list = list(self.servers.keys())
        print(servers_list)
        for server in servers_list:
            result.append(server[0])
        return result

    def start_election(self, members):
        # Buffer size
        buffer_size = 1024
        # Create a UDP socket
        ring_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ring_socket.bind((self.IP, 10001))
        ring = self.form_ring(members)
        neighbour = self.get_neighbour(ring, self.IP, 'left')
        print('Participant is up and running at {}:{}'.format(self.IP, 10001))
        while True:
            data, address = ring_socket.recvfrom(buffer_size)
            election_message = json.loads(data.decode())
            if election_message['isLeader']:
                if self.leader and not election_message['mid'] == self.IP:
                    print("I am giving up")
                    self.leader = False
                self.leader_id = election_message['mid']
                # forward received election message to left neighbour
                self.participant = False
                ring_socket.sendto(json.dumps(election_message).encode(), (neighbour, 10001))
                print("Closing election thread")
                ring_socket.close()
                break
            elif election_message['mid'] < self.IP and not self.participant:
                new_election_message = {
                    "mid": self.IP,
                    "isLeader": False
                }
                self.participant = True
                # send received election message to left neighbour
                ring_socket.sendto(json.dumps(new_election_message).encode(), (neighbour, 10001))
            elif election_message['mid'] > self.IP and not self.participant:
                # send received election message to left neighbour
                self.participant = True
                ring_socket.sendto(json.dumps(election_message).encode(), (neighbour, 10001))
            elif election_message['mid'] == self.IP:
                print("I am the new boss here")
                new_election_message = {
                    "mid": self.IP,
                    "isLeader": True
                }
                # send new election message to left neighbour
                self.participant = False
                self.leader_id = self.IP
                self.leader = True
                ring_socket.sendto(json.dumps(new_election_message).encode(), (neighbour, 10001))

    def form_ring(self,members):
        sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
        sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
        return sorted_ip_ring


    def get_neighbour(self, ring, current_node_ip, direction='left'):
        current_node_index = ring.index(current_node_ip) if current_node_ip in ring else -1
        if current_node_index != -1:
            if direction == 'left':
                if current_node_index + 1 == len(ring):
                    return ring[0]
                else:
                    return ring[current_node_index + 1]
            else:
                if current_node_index == 0:
                    return ring[len(ring) - 1]
                else:
                    return ring[current_node_index - 1]
        else:
            return None
    
    def __parse_keys_to_tuple(self, dictionary):
        for key in list(dictionary.keys()):
            val = dictionary[key]
            del dictionary[key]
            dictionary[make_tuple(str(key))] = val
    
    def shutdown(self):
        msg = self.__create_message("delete",(self.IP, self.PORT))
        if self.leader:
            self.trigger_election(withoutSelf=True)
        self.broadcast_message("192.168.10.255",msg)