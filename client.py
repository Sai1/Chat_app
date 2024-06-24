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

# Function to receive messages from the server
def receive_messages(client_socket):
    while True:
        try:
            header = client_socket.recv(8) 
            if not header:
                break
            msg_type, msg_length = struct.unpack('!II', header)
            message = client_socket.recv(msg_length).decode('utf-8')
            if message:
                print(message)
            else:
                break
        except Exception as e:
            print(f"Error : {e}")
            break
def send_message(client_socket, msg_type, message):
    msg_length=len(message)
    header = struct.pack('!II', msg_type, msg_length) # this is application layer header and later OS adds TCp header on top and then IP header  (IP header + TCP header + your message) 

    #[IP Header][TCP Header][Custom Header][Message Content]

    client_socket.sendall(header + message.encode('utf-8'))

def receive_message(client_socket):
    try:
        header = client_socket.recv(8)
        if len(header) < 8:
            return ""
        msg_type, msg_length = struct.unpack('!II', header)
        message = client_socket.recv(msg_length).decode('utf-8')
        return message
    except Exception as e:
        print(f"Error receiving message: {e}")
        return ""

def request_history(client_socket):
    send_message(client_socket, MESSAGE_TYPES['HISTORY'], "")
    response = receive_message(client_socket)
    print("Chat history:")
    print(response)


def authenticate(client_socket):
    while True:
        action = input("Do you want to register or login? (Type 'register' or 'login')")
        if action =="register":
            username=input("enter username").strip()
            password = input("Enter password").strip()
            message= f"{username} {password}"
            send_message(client_socket, MESSAGE_TYPES['REGISTER'], message)
            #client_socket.send(f"/register {username} {password}".encode('utf-8'))  
            #response = client_socket.recv(1024).decode('utf-8')
            response = receive_message(client_socket)
            print(response)
            
        elif action =="login":
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            message = f"{username} {password}"
            send_message(client_socket, MESSAGE_TYPES['LOGIN'], message)
            response = receive_message(client_socket)
            print(response)
            if "Login successful" in response:
                break

     

# Main function to start the client
def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(('127.0.0.1',80))
        
        authenticate(client_socket)
        
        def join_room():
            room_name = input("Enter the room name to join: ").strip()
            send_message(client_socket, MESSAGE_TYPES['JOIN_ROOM'], room_name) 

        def leave_room():
            send_message(client_socket, MESSAGE_TYPES['LEAVE_ROOM'], "")

        def create_room():
            room_name = input("Enter the new room name: ").strip()
            send_message(client_socket, MESSAGE_TYPES['CREATE_ROOM'], room_name)

        def list_rooms():
            send_message(client_socket, MESSAGE_TYPES['LIST_ROOMS'], "")
            response = receive_message(client_socket)
            print("Available rooms:")
            print(response)
        
        def send_private_message():
            recipient = input("Enter the recipient's username: ").strip()
            message = input("Enter your private message: ").strip()
            send_message(client_socket, MESSAGE_TYPES['PRIVATE_MESSAGE'], f"{recipient} {message}")
    
        # Start a thread to receive messages
        threading.Thread(target=receive_messages, args=(client_socket,)).start()
        
        while True:
            print("Options: /history, /join, /leave, /create, /list, /private")
            message = input("Enter your message: ")
            if message.lower() == '/history':
                request_history(client_socket)
            elif message.lower() == '/join':
                join_room()
            elif message.lower() == '/leave':
                leave_room()
            elif message.lower() == '/create':
                create_room()
            elif message.lower() == '/list':
                list_rooms()
            elif message.lower() == '/private':
                send_private_message()
            else:
                send_message(client_socket, MESSAGE_TYPES['MESSAGE'], message)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
