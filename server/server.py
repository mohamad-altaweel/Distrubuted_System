import socket
import select
import threading
import json
import time

class Server():

    def __init__(self, header_len, ip, port, broadcast_port) -> None:
        self.HEADER_LENGTH = header_len
        self.IP = ip
        self.PORT = int(port)
        self.BROADCAST_PORT = int(broadcast_port)
        self.leader = False
        self.servers = set()
        self.servers.add((self.IP,self.PORT))
        self.__start_server()
        self.start_listening_broadcast(self.BROADCAST_PORT)
        msg = self.__create_message("join",[(self.IP,self.PORT)])
        self.broadcast_message("192.168.10.255",msg)
        time.sleep(3)
        if len(self.servers) == 1:
            print("noone is a leader, I will take the lead")
            self.leader = True

    def __start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.IP, self.PORT))
        self.server_socket.listen()
        self.sockets_list = [self.server_socket]
        self.clients = {}
        print(f'Listening for connections on {self.IP}:{self.PORT}...')
        self.recieve_thread = threading.Thread(target=self.run_server, daemon = True)
        self.recieve_thread.start()

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
    
    def __handle_message(self,message,addr):
        command = message['command']
        if command == "connect":
            print("Successfully connected")
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            time.sleep(5)
            send_message = self.__create_message("connect", {"IP":self.IP,"PORT":self.PORT})
            s.sendto(send_message, (message['content']['ip'],message['content']['port']))
            s.close()
        elif command == "create":
            pass
        elif command == "join":
            self.servers.add(tuple(message['content'][0]))
            print("A new member joined the team {}".format(message['content']))
            if self.leader:
                print(self.servers)
                msg = self.__create_message("synchronoize",list(self.servers))
                self.broadcast_message("192.168.10.255",msg)
        elif command == "synchronoize":
            print(message['content'])
            for serv in message['content']:
                self.servers.update([tuple(serv)])

    def run_server(self):
        while True:
            read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
            for notified_socket in read_sockets:
                if notified_socket == self.server_socket:
                    client_socket, client_address = self.server_socket.accept()
                    user = self.__receive_message(client_socket)
                    print(user)
                    if user is False:
                        continue
                    self.sockets_list.append(client_socket)
                    self.clients[client_socket] = user
                    print("\n")
                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
                else:
                    message = self.__receive_message(notified_socket)
                    if message is False:
                        print('Closed connection from: {}'.format(self.clients[notified_socket]['data'].decode('utf-8')))
                        self.sockets_list.remove(notified_socket)
                        del self.clients[notified_socket]
                        continue
                    user = self.clients[notified_socket]
                    print("\n")
                    print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
                    for client_socket in self.clients:
                        if client_socket != notified_socket:
                            client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

            for notified_socket in exception_sockets:
                self.sockets_list.remove(notified_socket)
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