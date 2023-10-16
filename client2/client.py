import os
import sqlite3
import hashlib
import requests
from flask import Flask, render_template, request, redirect, url_for, g
import string
import random




app = Flask(__name__)
app.secret_key = 'order66'

DATABASE_FILE = "client.db"

SERVER_URL = "http://localhost:5000" 

session = {}





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
    data = {'name': name, 'password': hashed_password,'port': port}
    response = requests.post(f"{SERVER_URL}/add_user", json=data)
    if response.status_code == 200:
        cursor = get_cursor()
        cursor.execute("INSERT INTO User (name, password) VALUES (?, ?)", (name, hashed_password))
        get_db().commit()
        cursor = get_cursor()
        cursor.execute("SELECT * FROM User WHERE name = ? AND password = ?", (name, hashed_password))
        user = cursor.fetchone()
        print("User added on the server.")
        session['username'] = name
        session['id'] = str(user[0])
        session['message'] = 'User Created'
        return redirect(url_for('user_page'))
    else:
        return redirect(url_for('index'))



def display_users():
    cursor = get_cursor()
    cursor.execute("SELECT name FROM User")
    users = cursor.fetchall()
    if not users:
        message = session.pop('message', '') 
        return render_template('index.html', user=None,message=message)
    else:
        if 'username' in session:
            return redirect(url_for('user_page'))
        else:
            message = session.pop('message', '') 
            return render_template('index.html', users=[user[0] for user in users],message = message)

@app.route('/log_in', methods=['POST'])
def log_in():
    username = request.form['username']
    password = request.form['password']
    hashed_password = hash_password(password)
    
    data = {'name': username, 'password': hashed_password,'port':port}
    response = requests.post(f"{SERVER_URL}/log_in", json=data)
    message = ""
    if response.status_code == 200:
        cursor = get_cursor()
        cursor.execute("SELECT * FROM User WHERE name = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            session['username'] = username
            session['id'] = str(user[0])
            message = "Connected to server"  
        else:
            message = "Could not connect to server"  
        session['message'] = message
        return redirect(url_for('user_page'))
    else:
        session['message'] = 'Login Failed'
        return redirect(url_for('index'))  
        
    
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('id',None)
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
        cursor.execute("SELECT List.name,password FROM UserList,List where list_key = List.password AND UserList.name = ?",(session['username'],))
        lists = cursor.fetchall()
        message = session.pop('message', '') 
        return render_template('user.html', lists=lists, message=message,user=session['username'])
    else:
        return redirect(url_for('index'))
    
@app.route('/list_page', methods=['GET'])
def list_page():
    list_key = request.args.get('key')
    try:
        cursor = get_cursor()
        cursor.execute("SELECT name,password FROM List where password = ?",(list_key,))
        currentList = cursor.fetchone()
        cursor.execute("SELECT * FROM Item where list_key = ?",(list_key,))
    finally:
        cursor.close()
    message = session.pop('message', '') 
    return render_template('list_page.html',list=currentList,message=message)


@app.route('/addList', methods=['POST'])
def addList():
    name = request.form['listName']
    characters = string.ascii_uppercase + string.digits
    key = ''.join(random.choice(characters) for _ in range(8))
    data = {'name': name, 'key': key,'user':session['username']}
    response = requests.post(f"{SERVER_URL}/add_list", json=data)
    if response.status_code == 200:
        try:
            cursor = get_cursor()
            cursor.execute("INSERT INTO List (name, password) VALUES (?, ?)", (name, key))
            cursor.execute("INSERT INTO UserList (name, list_key) VALUES (?, ?)", (session['username'], key,))
            get_db().commit()
        finally:
            cursor.close()
        session['message'] = 'List ' + name + ' added!'
        return redirect(url_for('list_page', key=key))
    session['message'] = 'Could not add List'
    return redirect(url_for('user_page'))


@app.route('/deleteList', methods=['POST'])
def delete_list_route():
    key = request.form['key']
    data = {'key': key}
    response = requests.post(f"{SERVER_URL}/deleteList", json=data)
    if response.status_code == 200:
        cursor = get_cursor()
        cursor.execute("DELETE FROM List WHERE password = ?", (key,))
        cursor.execute("DELETE FROM UserList WHERE list_key = ?", (key,))
        get_db().commit()
        session['message'] = 'List ' + request.form['name'] + ' has been deleted!'
        return redirect(url_for('user_page'))
    else:
        session['message'] = 'Could not delete List'
        return redirect(url_for('user_page')) 
    

@app.route('/deleteListServerRequest',methods=['POST'])
def delete_list_serverRequest():
    data = request.get_json()
    key = data['key']
    cursor = get_cursor()
    cursor.execute("DELETE FROM List WHERE password = ?", (key,))
    cursor.execute("DELETE FROM UserList WHERE list_key = ?", (key,))
    get_db().commit()    
    return "List deleted", 200
    
@app.route('/addExistingList', methods=['POST'])
def addExistingList():
    key = request.form['listKey']
    data = {'key': key,'user':session['username']}
    response = requests.post(f"{SERVER_URL}/add_existingList", json=data)
    if response.status_code == 200:
        try:
            cursor = get_cursor()
            cursor.execute("SELECT * FROM List WHERE password = ?",(key,))
            list = cursor.fetchone()
            if list:
                cursor.execute("INSERT INTO UserList (name, list_key) VALUES (?, ?)", (session['username'], key))
                get_db().commit()
            else:
                cursor.execute("INSERT INTO List (name, password) VALUES (?, ?)", (response.text, key))
                cursor.execute("INSERT INTO UserList (name, list_key) VALUES (?, ?)", (session['username'], key))
                get_db().commit()
        finally:
            cursor.close()
        session['message'] = 'List ' + response.text + ' added!'
        return redirect(url_for('list_page', key=key))
    session['message'] = 'Could not add List'
    return redirect(url_for('user_page'))

if __name__ == '__main__':
    script_directory = os.path.dirname(os.path.abspath(__file__))
    folder_name = os.path.basename(script_directory)
    if (folder_name == 'client1'):
        port = 8000
    else:
        port = 9000

    app.run(debug=True,port=port)
