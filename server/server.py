from flask import Flask, request, g, render_template
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import requests

app = Flask(__name__)

DATABASE_FILE = "server.db"

userPorts = {}

# Function to get a new database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
        db.row_factory = sqlite3.Row  # Enable row_factory to work with rows as dictionaries
    return db

@app.route('/')
def index():
    cursor = get_db().cursor()
    cursor.execute("SELECT name, password FROM List")
    lists = cursor.fetchall()
    return render_template('server.html', lists=lists)


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

@app.route('/log_in', methods=['POST'])
def login():
    data = request.get_json()
    username = data['name']
    password = data['password']
    userPorts[username] = data['port']
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
    userPorts[name] = data['port']
    # Insert the user into the server's database
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO User (name, password) VALUES (?, ?)", (name, password))
        db.commit()
    finally:
        db.close()

    return "User added on the server", 200

@app.route('/deleteUser', methods=['POST'])
def delete_user():
    data = request.get_json()
    username = data['username']
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM User WHERE name = ?", (username,))
        conn.commit()
        conn.close()
        return "User deleted", 200  # Return a success response
    except:
        return "User not found", 404  # Return a not found response if the user is not found
    

@app.route('/add_list', methods=['POST'])
def add_list_route():
    data = request.get_json()
    name = data['name']
    password = data['key']
    user = data['user']

    # Insert the user into the server's database
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO List (name, password) VALUES (?, ?)", (name, password))
        cursor.execute("INSERT INTO UserList (name, list_key) VALUES (?, ?)", (user, password))
        db.commit()
    finally:
        db.close()

    return "List added on the server", 200


def send_post_request(port,key):
    try:
        response = requests.post(f'http://localhost:{port}/deleteListServerRequest', json={'key': key})
        if response.status_code == 200:
            return True  # Request successful
    except requests.exceptions.RequestException:
        pass  # Handle request errors, if any
    return False  # Request failed


@app.route('/deleteList', methods=['POST'])
def delete_list():
    data = request.get_json()
    key = data['key']
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM UserList WHERE list_key = ?",(key,))
        users = cursor.fetchall()
        for user in users:
            print(user[0])
            if user[0] not in userPorts:
                print(userPorts)
                try:
                    db = get_db()
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO ListDeleteUpdate (username, list_key) VALUES (?, ?)", (user[0], key))
                    db.commit()
                finally:
                    cursor.close()
        max_threads = len(userPorts) + 1
        with ThreadPoolExecutor(max_threads) as executor:
            results = list(executor.map(send_post_request, userPorts.values(),[key] * len(userPorts)))

        print("he")
        for username, result in zip(userPorts.keys(), results):
            if not result:
                db = get_db()
                cursor = db.cursor()
                cursor.execute("INSERT INTO ListDeleteUpdate (username, list_key) VALUES (?, ?)", (username, key))
                db.commit()
        cursor.execute("DELETE FROM List WHERE password = ?", (key,))
        conn.commit()
        conn.close()
        return "List deleted", 200  
    except Exception as e:
        print(e)
        return "List not found", 404  
    

    

@app.route('/add_existingList', methods=['POST'])
def add_existingList_route():
    data = request.get_json()
    key = data['key']
    user = data['user']
    valid = False

    # Insert the user into the server's database
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name FROM List WHERE password = ?",(key,))
        list = cursor.fetchone()
        if list:
            cursor.execute("INSERT INTO UserList (name, list_key) VALUES (?, ?)", (user, key))
            db.commit()
            valid = True
            
    finally:
        db.close()

    if valid:
        return list[0], 200
    else:
        return "List not found", 404 
    

if __name__ == '__main__':
    app.run(debug=True, port=5000)