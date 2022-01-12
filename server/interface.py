from server import Server

PROGRAM_RUNNING = True

def read_command():
    val = input("Enter Command: ")
    if val.startswith('start'):
        ip = input('Enter ip address: ')
        port = int(input("Enter port: "))
        broadcast_port = int(input("Enter broadcast port: "))
        print('Starting Server....')
        server = Server(10,ip,port, broadcast_port)
    elif val.startswith('exit'):
        global PROGRAM_RUNNING
        PROGRAM_RUNNING = False
        print('Bye bye...')
    else:
        print('Invalid command')

print("Welcome to TikTok Chat Server")
while(PROGRAM_RUNNING):
    read_command()