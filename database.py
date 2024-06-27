import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = 'chat_db.sqlite'

def create_connection():
    return sqlite3.connect(DB_FILE)

def initialize_db():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name VARCHAR(255) NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER,
            sender_username VARCHAR(255) NOT NULL,
            recipient_username VARCHAR(255),
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (sender_username) REFERENCES users(username),
            FOREIGN KEY (recipient_username) REFERENCES users(username)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def room_exists(room_name):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rooms WHERE room_name=?", (room_name,))
        room = cursor.fetchone()
        print("room:", room)  # Debugging output
        cursor.close()
        conn.close()
        return room is not None
    except Exception as e:
        print(f"Error checking room existence: {e}")
        return False


def create_room(room_name):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        print("before")
        cursor.execute("INSERT INTO rooms (room_name) VALUES (?)", (room_name,))
        print("after")
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating room: {e}")
        return False



def user_exists(username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user is not None

def register_user(username,password):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.close()
        conn.close()
        return "Username already exists. Try another one."
    cursor.close()
    conn.close()
    return "Registration successful!"

def authenticate_user(username,password):
                      
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and check_password_hash(user[0], password):
        return True
    return False

def save_message(room_name, username, message):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM rooms WHERE room_name=?", (room_name,))
    room_id_tuple = cursor.fetchone()
    
    if room_id_tuple:
        (room_id,) = room_id_tuple
        cursor.execute("INSERT INTO messages (room_id, sender_username, message) VALUES (?, ?, ?)", (room_id, username, message))
        conn.commit()
    
    cursor.close()
    conn.close()

def get_message_history(room_name):
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM rooms WHERE room_name=?", (room_name,))
    room_id_tuple = cursor.fetchone()
    
    if room_id_tuple:
        (room_id,) = room_id_tuple
        cursor.execute("SELECT sender_username, message, timestamp FROM messages WHERE room_id=? ORDER BY timestamp", (room_id,))
        messages = cursor.fetchall()
    else:
        messages = []
    
    cursor.close()
    conn.close()
    return messages

def save_private_message(sender_username, recipient_username, message):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (sender_username, recipient_username, message) VALUES (?, ?, ?)", (sender_username, recipient_username, message))
    conn.commit()
    cursor.close()
    conn.close()

def get_private_messages(sender_username, recipient_username):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sender_username, message, timestamp
        FROM messages
        WHERE (sender_username=? AND recipient_username=?) OR (sender_username=? AND recipient_username=?)
        ORDER BY timestamp
    """, (sender_username, recipient_username, recipient_username, sender_username))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return messages


