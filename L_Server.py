import socket
import time
from random import randrange


def BroadCast_Sender(IP):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Enable broadcasting mode
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    server.settimeout(0.2)
    # print('randrange(2))
    message = "127.0.0." + str(IP)
    message = message.encode('utf-8')
#    while True:
    server.sendto(message, ('<broadcast>', 37020))
    print("message sent!")
#       time.sleep(1)
def BroadCast_Listener():
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Enable broadcasting mode
    client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client.bind(("", 37020))
#    while True:
        # Thanks @seym45 for a fix
    data, addr = client.recvfrom(1024)
    return data
while True:
    data=BroadCast_Listener()
#    if  len(data):
    print(data)
    server_sel = randrange(4)
    if server_sel == 0:
        server_sel = 1
    print(server_sel)
    BroadCast_Sender(server_sel)