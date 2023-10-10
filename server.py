from flask import Flask, request, g
import sqlite3

app = Flask(__name__)

DATABASE_FILE = "server.db"

# Function to get a new database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
        db.row_factory = sqlite3.Row  # Enable row_factory to work with rows as dictionaries
    return db

@app.route('/')
def index():
    return "Server is running"

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data['name']
    password = data['password']

    # Insert the user into the server's database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO User (name, password) VALUES (?, ?)", (name, password))
    db.commit()

    return "User created on the server"

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['name']
    password = data['password']

    # Verify the user's credentials
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM User WHERE name = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        return "Connected to server", 200
    else:
        return "Login failed", 401

@app.route('/add_user', methods=['POST'])
def add_user_route():
    data = request.get_json()
    name = data['name']
    password = data['password']

    # Insert the user into the server's database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO User (name, password) VALUES (?, ?)", (name, password))
    db.commit()

    return "User added on the server", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)