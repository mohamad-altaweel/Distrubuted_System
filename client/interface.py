import re
from client import Client

SERVER_IP_SET = False
SERVER_IP = ''
SERVER_PORT_SET = False
SERVER_PORT = ''
PROGRAM_RUNNING = True
USERNAME = 'root'

def read_server_ip():
    val = input("Enter The IP address: ")
    found = re.search(r'^\d+\.\d+\.\d+\.\d+$', val)
    if found:
        global SERVER_IP_SET
        global SERVER_IP
        SERVER_IP_SET = True
        SERVER_IP = val
    else:
        print('Server ip format is invalid')

def read_server_port():
    val = input("Enter The port address: ")
    found = re.search(r'^\d+$', val)
    if found:
        global SERVER_PORT_SET
        global SERVER_PORT
        SERVER_PORT_SET = True
        SERVER_PORT = val
    else:
        print('Server port format is invalid')

def read_command(client):
    val = input("Enter Command: ")
    if val.startswith('create'):
        print('Create group')
    elif val.startswith('send'):
        print('Send message')
        message = input("Type the message: ")
        client.send_message("send",message)
    elif val.startswith('join'):
        print('join a group')
    elif val.startswith('exit'):
        global PROGRAM_RUNNING
        PROGRAM_RUNNING = False
        print('Bye bye...')
    else:
        print('Invalid command')

print("Welcome to TikTok Chat application")
while(not(SERVER_IP_SET)):
    read_server_ip()
while(not(SERVER_PORT_SET)):
    read_server_port()
USERNAME = input("type your username: ")
client = Client(10,SERVER_IP,SERVER_PORT,USERNAME)
while(PROGRAM_RUNNING):
    read_command(client)