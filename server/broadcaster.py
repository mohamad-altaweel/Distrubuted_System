import socket
import threading
import json 

class Broadcaster():

    def __init__(self, BROADCAST_PORT) -> None:
        self.MY_HOST = socket.gethostname()
        self.MY_IP = socket.gethostbyname(self.MY_HOST)
        self.BROADCAST_PORT = BROADCAST_PORT
        # Create a UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the socket to broadcast and enable reusing addresses
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind socket to address and port
        self.socket.bind(('', self.BROADCAST_PORT))
        print("Listening to broadcast messages")
        self.recieve_thread = threading.Thread(target=self.__start_receiving, daemon = True)
        self.recieve_thread.start()
    
    def __start_receiving(self):
        while True:
            data, addr = self.socket.recvfrom(2048)
            decoded_data = json.loads(data.decode())
            print(decoded_data)
            if data:
                print("Received broadcast message:", decoded_data["command"], addr)
                self.__handle_message(decoded_data)
    
    def __handle_message(self,message):
        command = message['command']
        if command == "connect":
            print("Successfully connected")


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

