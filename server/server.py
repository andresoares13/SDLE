from flask import Flask, request, g, render_template
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import requests
import string
import random
import json

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

@app.route('/sync', methods=['POST'])
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

    validKey = False

    while not validKey:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name,password FROM List where password = ?",(password,))
        currentList = cursor.fetchone()
        if not currentList:
            validKey = True
            break
        else:
            characters = string.ascii_uppercase + string.digits
            password = ''.join(random.choice(characters) for _ in range(8))
          

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO List (name, password) VALUES (?, ?)", (name, password))
        cursor.execute("INSERT INTO UserList (name, list_key) VALUES (?, ?)", (user, password))
        for item in data['items']:
            cursor.execute("INSERT INTO Item (name, list_key, quantity) VALUES (?, ?, ?)", (item[1], item[2], item[3]))
        db.commit()
    finally:
        db.close()

    return password, 200


@app.route('/requestUpdates',methods = ['POST'])
def requestUpdates():
    failed = False
    data = request.get_json()
    username = data['name']
    port = data['port']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ListDeleteUpdate WHERE username = ?",(username,))
    listDeleteUpdates = cursor.fetchall()
    for update in listDeleteUpdates:
        response = requests.post(f'http://localhost:{port}/deleteListServerRequest', json={'key': update[1]})
        if response.status_code != 200:
            failed = True

    if failed:
        return "Failure",404
    else:
        return "Updated", 200

@app.route('/deleteListUpdate', methods=['POST'])
def addDeleteListUpdate():
    data = request.get_json()
    key = data['key']
    username = data['name']
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM UserList WHERE list_key = ?",(key,))
        users = cursor.fetchall()
        for user in users:
            if (user[0] != username):
                print("l")
                cursor.execute("INSERT INTO ListDeleteUpdate (username, list_key) VALUES (?, ?)", (user[0], key))
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute("DELETE FROM List WHERE password = ?", (key,))
        conn.commit()
    except:
        return "Could not Update", 404
    finally:
        cursor.close()
    
    return "List deleted", 200


    

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
            cursor.execute("SELECT * FROM Item where list_key = ?",(key,))
            rows = cursor.fetchall()
            if not rows:
                items = []
            else:
                items = [dict(row) for row in rows]
            db.commit()
            valid = True
            
    finally:
        db.close()

    if valid:
        response_data = {"list": list[0], "items": items}
        response_json = json.dumps(response_data)
        return response_json, 200
    else:
        return "List not found", 404 
    

if __name__ == '__main__':
    app.run(debug=True, port=5000)