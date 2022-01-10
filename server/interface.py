

PROGRAM_RUNNING = True

def read_command():
    val = input("Enter Command: ")
    if val.startswith('start'):
        print('Starting Server....')
    elif val.startswith('exit'):
        global PROGRAM_RUNNING
        PROGRAM_RUNNING = False
        print('Bye bye...')
    else:
        print('Invalid command')

print("Welcome to TikTok Chat Server")
while(PROGRAM_RUNNING):
    read_command()