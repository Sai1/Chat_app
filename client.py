import socket
import struct
import threading

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

def receive_messages(client_socket):
    while True:
        try:
            msg_type, message = receive_message(client_socket)
            if message:
                print(message)
            if msg_type is None:
                break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break


def send_message(client_socket, msg_type, message):
    message_bytes = message.encode('utf-8')
    msg_length = len(message_bytes)
    header = struct.pack('!II', msg_type, msg_length)
    client_socket.sendall(header + message_bytes)


def receive_message(client_socket):
    header = client_socket.recv(8)
    if len(header) < 8:
        return None, ""
    msg_type, msg_length = struct.unpack('!II', header)
    message = recv_all(client_socket, msg_length).decode('utf-8')
    return msg_type, message


def recv_all(sock, length):
    data = bytearray()
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def authenticate(client_socket):
    while True:
        action = input("Do you want to register or login? (Type 'register' or 'login'): ")
        if action == "register":
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            message = f"{username} {password}"
            send_message(client_socket, MESSAGE_TYPES['REGISTER'], message)
            _, response = receive_message(client_socket)
            print(response)

        elif action == "login":
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            message = f"{username} {password}"
            send_message(client_socket, MESSAGE_TYPES['LOGIN'], message)
            _, response = receive_message(client_socket)
            print(response)
            if "Login successful" in response:
                break


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(('127.0.0.1', 8002))

        authenticate(client_socket)

        threading.Thread(target=receive_messages, args=(client_socket,)).start()

        while True:
            print("Options: /history, /join, /leave, /create, /list, /private")
            message = input("Enter your message: ").strip().lower()
            if message == '/history':
                send_message(client_socket, MESSAGE_TYPES['HISTORY'], "")
            elif message == '/join':
                room_name = input("Enter the room name to join: ").strip()
                send_message(client_socket, MESSAGE_TYPES['JOIN_ROOM'], room_name)
            elif message == '/leave':
                send_message(client_socket, MESSAGE_TYPES['LEAVE_ROOM'], "")
            elif message == '/create':
                room_name = input("Enter the new room name: ").strip()
                send_message(client_socket, MESSAGE_TYPES['CREATE_ROOM'], room_name)
            elif message == '/list':
                send_message(client_socket, MESSAGE_TYPES['LIST_ROOMS'], "")
            elif message == '/private':
                recipient = input("Enter the recipient's username: ").strip()
                private_message = input("Enter your private message: ").strip()
                send_message(client_socket, MESSAGE_TYPES['PRIVATE_MESSAGE'], f"{recipient} {private_message}")
            else:
                send_message(client_socket, MESSAGE_TYPES['MESSAGE'], message)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
