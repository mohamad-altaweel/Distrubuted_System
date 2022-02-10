class ChatRoom():

    def __init__(self, name, server_ip,server_port,server_socket):
        self.name=name
        self.server_ip = server_ip
        self.server_port = server_port
        self.clients_list_ip=[]
        self.clients_list_port=[]
        self.clients_list_name=[]
        self.sockets_list = [server_socket]
        self.clients = {}
    def add_client_List(self, client_ip,client_port,client_name):
        self.clients_list_ip.append(client_ip)
        self.clients_list_port.append(client_port)
        self.clients_list_name.append(client_name)

    def add_socket_List(self, client_socket,user):
        self.sockets_list.append(client_socket)
        self.clients[client_socket] = user