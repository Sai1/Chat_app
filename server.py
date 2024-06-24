import socket
import struct
import sys
import threading
from database import get_message_history, initialize_db, save_message,user_exists,register_user,authenticate_user



HOST = '0.0.0.0'
LISTENER_LIMIT = 5
usernames = {}
clients = []
rooms = {}  # Room dictionary to manage clients in different rooms

# Define message types
MESSAGE_TYPES = {
    'REGISTER': 1,
    'LOGIN': 2,
    'MESSAGE': 3,
    'BROADCAST': 4,
    'HISTORY': 5,
    'JOIN_ROOM': 6,
    'LEAVE_ROOM': 7,
    'CREATE_ROOM': 8,
    'LIST_ROOMS': 9,
    'PRIVATE_MESSAGE': 10
}

def handle_client(client_socket):
    current_room = None
    while True:
        try:
            header = client_socket.recv(8)  # Receive the fixed-size header
            if not header:
                break
            msg_type, msg_length = struct.unpack('!II', header)
            message = client_socket.recv(msg_length).decode('utf-8')
            print("www")
            # Receiving message from the client
            if msg_type == MESSAGE_TYPES['REGISTER']:
                username, password = message.split()
                if user_exists(username):
                    response= "Username already exists. Try another one."
                else:
                    response = register_user(username, password)
                    send_message(client_socket, MESSAGE_TYPES['REGISTER'], response)
            elif msg_type == MESSAGE_TYPES['LOGIN']:
                username, password = message.split()
                if authenticate_user(username, password):
                    usernames[client_socket] = username
                    response="Login successful"
                else:
                    response="Invalid username or password"

                print(f"Received from {username}: {message}")
                send_message(client_socket,MESSAGE_TYPES['LOGIN'],response)

            elif msg_type == MESSAGE_TYPES['MESSAGE']:
                if current_room and client_socket in usernames:
                    username = usernames[client_socket]
                    broadcast(f"{username}: {message}", client_socket, current_room)
                    save_message(username, message)
                else:
                    send_message(client_socket, MESSAGE_TYPES['MESSAGE'], "Error: Username not found or not in a room")

            elif msg_type == MESSAGE_TYPES['HISTORY']:
                messages = get_message_history()
                response = "\n".join([f"{timestamp} {username}: {msg}" for username, msg, timestamp in messages])
                send_message(client_socket, MESSAGE_TYPES['HISTORY'], response)

            elif msg_type == MESSAGE_TYPES['JOIN_ROOM']:
                room_name = message.strip()
                if current_room:
                    leave_room(client_socket, current_room)
                join_room(client_socket, room_name)
                current_room = room_name

            elif msg_type == MESSAGE_TYPES['LEAVE_ROOM']:
                if current_room:
                    leave_room(client_socket, current_room)
                    current_room = None

            elif msg_type == MESSAGE_TYPES['CREATE_ROOM']:
                room_name = message.strip()
                if room_name not in rooms:
                    rooms[room_name] = []
                    response = f"Room {room_name} created"
                else:
                    response = f"Room {room_name} already exists"
                send_message(client_socket, MESSAGE_TYPES['CREATE_ROOM'], response)

            elif msg_type == MESSAGE_TYPES['LIST_ROOMS']:
                room_list = "\n".join(rooms.keys())
                send_message(client_socket, MESSAGE_TYPES['LIST_ROOMS'], room_list)

            elif msg_type == MESSAGE_TYPES['PRIVATE_MESSAGE']:
                recipient, private_message = message.split(' ', 1)
                send_private_message(client_socket, recipient, private_message)

        except Exception as e:
            print(f"Error: {e}")
            break
    remove(client_socket)
    
def send_message(client_socket, msg_type, message):
    msg_length = len(message)
    header = struct.pack('!II', msg_type, msg_length)
    client_socket.sendall(header + message.encode('utf-8'))

# Broadcast message to all clients except the sender
def broadcast(message, connection,room_name):
    if room_name in rooms:
        for client in rooms[room_name]:
            if client != connection:
                try:
                    send_message(client,MESSAGE_TYPES['BROADCAST'],message)
                except Exception as e:
                    print(f"Error sending message to client: {e}")
                    remove(client)

def join_room(client_socket, room_name):
    if room_name not in rooms:
        rooms[room_name] = []
    rooms[room_name].append(client_socket)
    send_message(client_socket, MESSAGE_TYPES['JOIN_ROOM'], f"Joined room {room_name}")

def leave_room(client_socket, room_name):
    if room_name in rooms and client_socket in rooms[room_name]:
        rooms[room_name].remove(client_socket)
        send_message(client_socket, MESSAGE_TYPES['LEAVE_ROOM'], f"Left room {room_name}")

def send_private_message(sender_socket, recipient_username, message):
    recipient_socket = None
    for sock, username in usernames.items():
        if username == recipient_username:
            recipient_socket = sock
            break
    if recipient_socket:
        sender_username = usernames[sender_socket]
        send_message(recipient_socket, MESSAGE_TYPES['PRIVATE_MESSAGE'], f"Private message from {sender_username}: {message}")
    else:
        send_message(sender_socket, MESSAGE_TYPES['PRIVATE_MESSAGE'], "Error: User not found")


# Remove a client from the list
def remove(connection):
    if connection in clients:
        clients.remove(connection)
        username = usernames.pop(connection, None)
        if username:
            print(f"User {username} disconnected")

def main(port) :
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        return

    port = int(sys.argv[1])
    initialize_db()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, port))  
    server_socket.listen(LISTENER_LIMIT)
    print("Server started and listening on port ",port)
    
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            clients.append(client_socket)
            print(f"Connection established with {addr}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()
        except Exception as e:
            print(f"Error accepting connection: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)
    port = int(sys.argv[1]) 
    main(port)

	

 