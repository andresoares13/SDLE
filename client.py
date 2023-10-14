import os
import sqlite3
import hashlib
import requests
from flask import Flask, render_template, request, redirect, url_for, g,session


app = Flask(__name__)
app.secret_key = 'order66'

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
    data = {'name': name, 'password': hashed_password}
    response = requests.post(f"{SERVER_URL}/add_user", json=data)
    if response.status_code == 200:
        cursor = get_cursor()
        cursor.execute("INSERT INTO User (name, password) VALUES (?, ?)", (name, hashed_password))
        get_db().commit()
        print("User added on the server.")
        session['username'] = name
        return redirect(url_for('user_page',message='User Created'))
    else:
        return redirect(url_for('index'))



def display_users():
    cursor = get_cursor()
    cursor.execute("SELECT name FROM User")
    users = cursor.fetchall()
    if not users:
        return render_template('index.html', user=None)
    else:
        if 'username' in session:
            message = ""
            print(session)
            return redirect(url_for('user_page',message=message))
        else:
            return render_template('index.html', user=users[0][0])

@app.route('/log_in', methods=['POST'])
def log_in():
    username = request.form['username']
    password = request.form['password']
    hashed_password = hash_password(password)
    cursor = get_cursor()
    cursor.execute("SELECT * FROM User WHERE name = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()
    if user:
        session['username'] = username
        data = {'name': username, 'password': hashed_password}
        response = requests.post(f"{SERVER_URL}/log_in", json=data)
        message = ""
        if response.status_code == 200:
            message = "Connected to server"  
        else:
            message = "Could not connect to server"  
        session['message'] = message
        return redirect(url_for('user_page'))
        
    else:
        return "Login failed"
    
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))  

@app.route('/')
def index():
    return display_users()


@app.route('/add_user', methods=['POST'])
def add_user_route():
    name = request.form['name']
    password = request.form['password']
    return add_user(name, password)

@app.route('/deleteUser', methods=['POST'])
def delete_user():
    if 'username' in session:
        username = session['username']  
        data = {'username': username}
        response = requests.post(f"{SERVER_URL}/deleteUser", json=data)
        if response.status_code == 200:
            session.pop('username', None)
            cursor = get_cursor()
            cursor.execute("DELETE FROM User WHERE name = ?", (username,))
            get_db().commit()
            return redirect(url_for('index'))  
    return redirect(url_for('index'))  

@app.route('/user_page')
def user_page():
    if 'username' in session:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM List")
        lists = cursor.fetchall()
        message = session.pop('message', '')  # Get the message from the session
        return render_template('user.html', lists=lists, message=message,user=session['username'])
    else:
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True,port=8080)
