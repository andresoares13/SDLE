import os
import sqlite3
import hashlib
import requests
from flask import Flask, render_template, request, redirect, url_for, g


app = Flask(__name__)

DATABASE_FILE = "client.db"

SERVER_URL = "http://localhost:5000" 

if not os.path.exists(DATABASE_FILE):
    os.system(f"sqlite3 {DATABASE_FILE} < create.sql")


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
    return db

def get_cursor():
    return get_db().cursor()

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def add_user(name, password):
    hashed_password = hash_password(password)
    cursor = get_cursor()
    cursor.execute("INSERT INTO User (name, password) VALUES (?, ?)", (name, hashed_password))
    get_db().commit()
    data = {'name': name, 'password': hashed_password}
    response = requests.post(f"{SERVER_URL}/add_user", json=data)
    if response.status_code == 200:
        print("User added on the server.")
    else:
        print("Failed to add user on the server.")



def display_users():
    cursor = get_cursor()
    cursor.execute("SELECT name FROM User")
    users = cursor.fetchall()
    if not users:
        return None
    else:
        return [user[0] for user in users]


def log_in(username, password):
    hashed_password = hash_password(password)
    cursor = get_cursor()
    cursor.execute("SELECT * FROM User WHERE name = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()
    if user:
        data = {'name': username, 'password': hashed_password}
        response = requests.post(f"{SERVER_URL}/login", json=data)
        if response.status_code == 200:
            print("Connected to server")
        else:
            print("Login failed")
        return "Connected to server"
    else:
        return "Login failed"
    

@app.route('/')
def index():
    users = display_users()
    return render_template('index.html', users=users)


@app.route('/add_user', methods=['POST'])
def add_user_route():
    name = request.form['name']
    password = request.form['password']
    add_user(name, password)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True,port=8080)
