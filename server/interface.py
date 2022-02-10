from server import Server

PROGRAM_RUNNING = True
server = None

def read_command():
    val = input("Enter Command: ")
    global server
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
    elif val.startswith('elect'):
        server.trigger_election()
    else:
        print('Invalid command')

print("Welcome to TikTok Chat Server")
try:
    while(PROGRAM_RUNNING):
        read_command()
except KeyboardInterrupt:
    server.shutdown()
