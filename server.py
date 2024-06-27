import socket
import struct
import sys
import threading
from database import create_connection, create_room, get_message_history, initialize_db, room_exists, save_message, user_exists, register_user, authenticate_user

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
    'PRIVATE_MESSAGE': 10,
    'DISCONNECT': 11
}

def handle_client(client_socket):
    current_room = None
    try:
        while True:
            header = client_socket.recv(8)  # Receive the fixed-size header
            if not header:
                break
            msg_type, msg_length = struct.unpack('!II', header)
            message = client_socket.recv(msg_length).decode('utf-8')

            if msg_type == MESSAGE_TYPES['REGISTER']:
                username, password = message.split()
                if user_exists(username):
                    response = "Username already exists. Try another one."
                else:
                    response = register_user(username, password)
                send_message(client_socket, MESSAGE_TYPES['REGISTER'], response)

            elif msg_type == MESSAGE_TYPES['LOGIN']:
                username, password = message.split()
                if authenticate_user(username, password):
                    usernames[client_socket] = username
                    response = "Login successful"
                else:
                    response = "Invalid username or password"
                send_message(client_socket, MESSAGE_TYPES['LOGIN'], response)

            elif msg_type == MESSAGE_TYPES['MESSAGE']:
                if current_room and client_socket in usernames:
                    username = usernames[client_socket]
                    save_message(current_room, username, message)
                    broadcast(f"{username}: {message}", client_socket, current_room)
                else:
                    send_message(client_socket, MESSAGE_TYPES['MESSAGE'], "Error: Username not found or not in a room, Join room")

            elif msg_type == MESSAGE_TYPES['HISTORY']:
                if current_room:
                    messages = get_message_history(current_room)
                    response = "\n".join([f"{timestamp} {username}: {msg}" for username, msg, timestamp in messages])
                    send_message(client_socket, MESSAGE_TYPES['HISTORY'], response)
                else:
                    send_message(client_socket, MESSAGE_TYPES['HISTORY'], "Error: Not in a room")

            elif msg_type == MESSAGE_TYPES['JOIN_ROOM']:
                room_name = message.strip()
                if room_exists(room_name):
                    current_room = room_name
                    print("joined")
                    response = f"Joined room {room_name}"
                else:
                    response = f"Error: Room {room_name} does not exist. Use /create to create a new room."
                send_message(client_socket, MESSAGE_TYPES['JOIN_ROOM'], response)
                print("sent")

            elif msg_type == MESSAGE_TYPES['LEAVE_ROOM']:
                current_room = None
                send_message(client_socket, MESSAGE_TYPES['LEAVE_ROOM'], "Left the room")

            elif msg_type == MESSAGE_TYPES['CREATE_ROOM']:
                room_name = message.strip()
                try:
                    if room_exists(room_name):
                        response = f"Room {room_name} already exists"
                    else:
                        if create_room(room_name):
                            response = f"Room {room_name} created, enter /join to join it"
                        else:
                            response = f"Error creating room {room_name}"
                    send_message(client_socket, MESSAGE_TYPES['CREATE_ROOM'], response)
                except Exception as e:
                    send_message(client_socket, MESSAGE_TYPES['CREATE_ROOM'], f"Error creating room: {e}")

            elif msg_type == MESSAGE_TYPES['LIST_ROOMS']:
                try:
                    conn = create_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT room_name FROM rooms")
                    rooms_list = cursor.fetchall()
                    cursor.close()
                    conn.close()
                    room_list = "\n".join([room[0] for room in rooms_list]) if rooms_list else "No rooms available"
                    send_message(client_socket, MESSAGE_TYPES['LIST_ROOMS'], room_list)
                except Exception as e:
                    send_message(client_socket, MESSAGE_TYPES['LIST_ROOMS'], f"Error retrieving room list: {e}")

            elif msg_type == MESSAGE_TYPES['PRIVATE_MESSAGE']:
                recipient, private_message = message.split(' ', 1)
                send_private_message(client_socket, recipient, private_message)

            elif msg_type == MESSAGE_TYPES['DISCONNECT']:
                break

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        remove(client_socket)

def send_message(client_socket, msg_type, message):
    message_bytes = message.encode('utf-8')
    msg_length = len(message_bytes)
    header = struct.pack('!II', msg_type, msg_length)
    client_socket.sendall(header + message_bytes)

def broadcast(message, connection, room_name):
    if room_name in rooms:
        for client in rooms[room_name]:
            if client != connection:
                try:
                    send_message(client, MESSAGE_TYPES['BROADCAST'], message)
                except Exception as e:
                    print(f"Error sending message to client: {e}")
                    remove(client)

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

def remove(connection):
    if connection in clients:
        clients.remove(connection)
        username = usernames.pop(connection, None)
        if username:
            print(f"User {username} disconnected")
        connection.close()

def main(port):
    initialize_db()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, port))
    server_socket.listen(LISTENER_LIMIT)
    print(f"Server started and listening on port {port}")

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
