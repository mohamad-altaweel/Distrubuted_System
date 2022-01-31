import socket
import json 

def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    print(sorted_binary_ring)
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    print(sorted_ip_ring)
    return sorted_ip_ring


def get_neighbour(ring, current_node_ip, direction='left'):
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


members = ['192.168.0.1', '130.234.204.2', '130.234.203.2', '130.234.204.1', '182.4.3.111']
print(members)
ring = form_ring(members)
neighbour = get_neighbour(ring, '130.234.203.2', 'left')
print(neighbour)

my_uid = '130.234.203.2'
ring_port = 10001
leader_id = ''

# Buffer size
buffer_size = 1024

# Create a UDP socket
ring_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ring_socket.bind((my_uid, ring_port))

print('Participant is up and running at {}:{}'.format(my_uid, ring_port))

while True:
    data, address = ring_socket.recvfrom(buffer_size)
    election_message = json.loads(data.decode())

    if election_message['isLeader']:
        leader_uid = election_message['mid']
        # forward received election message to left neighbour
        participant = False
        ring_socket.sendto(json.dumps(election_message), neighbour)
        
    if election_message['mid'] < my_uid and not participant:
        new_election_message = {
            "mid": my_uid,
            "isLeader ": False
        }
        participant = True
        # send received election message to left neighbour
        ring_socket.sendto(json.dumps(new_election_message), neighbour)
    elif election_message['mid'] > my_uid:
        # send received election message to left neighbour
        participant = True
        ring_socket.sendto(json.dumps(election_message), neighbour)
    elif election_message['mid'] == my_uid:
        leader_uid = my_uid
        new_election_message = {
            "mid": my_uid,
            "isLeader ": True
        }
        # send new election message to left neighbour
        participant = False
        ring_socket.sendto(json.dumps(new_election_message), neighbour)

