import os
import sqlite3
import hashlib
import requests
from flask import Flask, render_template, request, redirect, url_for, g
import string
import random
import json



app = Flask(__name__)
app.secret_key = 'order66'

DATABASE_FILE = "client.db"

SERVER_URL = "http://localhost:5000" 

session = {}

items = ["eggs", "milk", "bread", "apples", "bananas", "chicken", "rice", "potatoes", "tomatoes", "cheese", "pasta", "lettuce", "onions", "carrots", "cereal"]


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
        cursor = get_cursor()
        cursor.execute("SELECT * FROM User WHERE name = ? AND password = ?", (name, hashed_password))
        user = cursor.fetchone()
        print("User added on the server.")
        session['username'] = name
        session['id'] = str(user[0])
        session['message'] = 'User Created'
        session['hash'] = hashed_password
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
    message = ""
    cursor = get_cursor()
    cursor.execute("SELECT * FROM User WHERE name = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()
    if user:
        session['username'] = username
        session['id'] = str(user[0])
        session['hash'] = hashed_password
        message = "Login Sucessfull!"  
        session['message'] = message
        return redirect(url_for('user_page'))
    else:
        message = "Wrong username or password"  
        session['message'] = message
        return redirect(url_for('index'))
    


def sendUpdates():
    allSent = True
    cursor = get_cursor()
    cursor.execute("SELECT * FROM ListDeleteUpdate")
    listDeleteUpdates = cursor.fetchall()
    for update in listDeleteUpdates:
        data = {'name':update[0],'key':update[1]}
        response = requests.post(f"{SERVER_URL}/deleteListUpdate", json=data)
        if response.status_code == 200:
            try:
                cursor.execute("DELETE FROM ListDeleteUpdate WHERE username = ? AND list_key = ?", (update[0], update[1]))
                get_db().commit()
            except Exception as e:
                print(e)
                allSent = False
                continue
        else:
            allSent = False
    cursor.close()
    return allSent


def receiveUpdates():
    allReceived = True
    data = {'name':session['username'],'port':port}
    response = requests.post(f"{SERVER_URL}/requestUpdates", json=data)
    if response.status_code != 200:
        allReceived = False
    return allReceived


    

    
    
    

@app.route('/sync',methods=['POST'])
def sync():
    username = session['username']
    hashed = session['hash']
    data = {'name': username, 'password': hashed}
    response = requests.post(f"{SERVER_URL}/sync", json=data)
    if response.status_code == 200:
        if sendUpdates() and receiveUpdates():
            session['message'] = 'Sucessfully Synced!'
            return redirect(url_for('user_page'))
        else:
            session['message'] = 'Sync Failed'
            return redirect(url_for('user_page')) 
    else:
        session['message'] = 'Sync Failed'
        return redirect(url_for('user_page'))  



    
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('id',None)
    session.pop('hash',None)
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
        cursor.execute("SELECT List.name,password,shared FROM UserList,List where list_key = List.password AND UserList.name = ?",(session['username'],))
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
        cursor.execute("SELECT name,password,shared FROM List where password = ?",(list_key,))
        currentList = cursor.fetchone()
        cursor.execute("SELECT * FROM Item where list_key = ?",(list_key,))
        items = cursor.fetchall()
    finally:
        cursor.close()
    message = session.pop('message', '') 
    return render_template('list_page.html',list=currentList,message=message,items=items)


@app.route('/addList', methods=['POST'])
def addList():
    name = request.form['listName']
    characters = string.ascii_uppercase + string.digits
    key = ''.join(random.choice(characters) for _ in range(8))
    try:
        cursor = get_cursor()
        cursor.execute("INSERT INTO List (name, password) VALUES (?, ?)", (name, key))
        cursor.execute("INSERT INTO UserList (name, list_key) VALUES (?, ?)", (session['username'], key,))
        get_db().commit()
    finally:
        cursor.close()
    session['message'] = 'List ' + name + ' added!'
    return redirect(url_for('list_page', key=key))



@app.route('/shareList',methods = ['POST'])
def shareList():
    name = request.form['name']
    key = request.form['key']
    cursor = get_cursor()
    cursor.execute("SELECT * FROM Item where list_key = ?",(key,))
    items = cursor.fetchall()
    if not items:
        items = []
    data = {'name':name,'user':session['username'],'key':key,'items': items}
    response = requests.post(f"{SERVER_URL}/add_list", json=data)
    if response.status_code == 200:
        try:
            cursor = get_cursor()
            cursor.execute("UPDATE List SET password = ?, shared = 1 WHERE name = ?", (response.text, name))
            cursor.execute("UPDATE UserList SET list_key = ? WHERE name = ? AND list_key = ?", (response.text, session['username'], key))
            get_db().commit()
        finally:
            cursor.close()
        session['message'] = 'List ' + name + ' can now be shared!'
        return redirect(url_for('list_page', key=response.text))
    else:
        session['message'] = 'List ' + name + ' could not be shared'
        return redirect(url_for('list_page', key=key))


@app.route('/deleteList', methods=['POST'])
def delete_list_route():
    key = request.form['key']
    try:
        cursor = get_cursor()
        cursor.execute("SELECT shared FROM List where password = ?",(key,))
        currentList = cursor.fetchone()
        if (currentList[0] == 1):
            cursor.execute("INSERT INTO ListDeleteUpdate (username, list_key) VALUES (?, ?)", (session['username'], key))
        cursor.execute('PRAGMA foreign_keys = ON')    
        cursor.execute("DELETE FROM List WHERE password = ?", (key,))
        get_db().commit()
        session['message'] = 'List ' + request.form['name'] + ' has been deleted!'
        
        return redirect(url_for('user_page'))
    except:
        session['message'] = 'Could not delete List'
        return redirect(url_for('user_page')) 
    finally:
        cursor.close()
        
    

    
    

@app.route('/deleteListServerRequest',methods=['POST'])
def delete_list_serverRequest():
    data = request.get_json()
    key = data['key']
    cursor = get_cursor()
    cursor.execute('PRAGMA foreign_keys = ON')
    cursor.execute("DELETE FROM List WHERE password = ?", (key,))
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
                response_data = json.loads(response.text)
                list_value = response_data["list"]
                items = response_data["items"]
                cursor.execute("INSERT INTO List (name, password,shared) VALUES (?, ? ,?)", (list_value, key,1))
                cursor.execute("INSERT INTO UserList (name, list_key) VALUES (?, ?)", (session['username'], key))
                for item in items:
                    cursor.execute("INSERT INTO Item (name, list_key, quantity) VALUES (?, ?, ?)", (item['name'], item['list_key'], item['quantity']))
                get_db().commit()
        finally:
            cursor.close()
        session['message'] = 'List ' + response_data["list"] + ' added!'
        return redirect(url_for('list_page', key=key))
    session['message'] = 'Could not add List'
    return redirect(url_for('user_page'))




@app.route('/add_item', methods=['GET', 'POST'])
def add_item_page():
    if 'username' not in session:
        return redirect(url_for('index'))

    list_key = request.args.get('key')
    
    if request.method == 'POST':
        selected_items = request.form.getlist('item')
        key = request.form['key']
        quantity = request.form['quantity']        

        try:
            cursor = get_cursor()
            for item in selected_items:
                cursor.execute("SELECT quantity from Item WHERE name = ? and list_key = ?",(item,key))
                existingItem = cursor.fetchone()
                if existingItem:
                    newQuant = existingItem[0] + int(quantity)
                    cursor.execute("UPDATE Item SET quantity = ? WHERE name = ? AND list_key = ?", (newQuant, item, key))
                else:
                    cursor.execute("INSERT INTO Item (name, list_key, quantity) VALUES (?, ?, ?)", (item, key, quantity))
            get_db().commit()
            session['message'] = 'Items added successfully!'
            return redirect(url_for('add_item_page', key=key))
        except Exception as e:
            print(e)
            session['message'] = 'Failed to add items.'
        finally:
            cursor.close()


    try:
        cursor = get_cursor()
        cursor.execute("SELECT name, password, shared FROM List where password = ?", (list_key,))
        current_list = cursor.fetchone()
    finally:
        cursor.close()
    
    message = session.pop('message', '')
    
    
    return render_template('add_item_page.html', list=current_list, items=items, message=message)






@app.route('/delete_item', methods=['POST', 'GET'])
def delete_item_page():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    list_key = request.args.get('key')
    
    if request.method == 'POST':
        key = request.form['key']
        item = request.form['name']

        try:
            cursor = get_cursor()
            cursor.execute("DELETE FROM Item WHERE name = ? and list_key = ?", (item, key))
            get_db().commit()
            session['message'] = 'Item deleted successfully!'
            return redirect(url_for('list_page', key=key))
        except Exception as e:
            print(e)
            session['message'] = 'Failed to delete item.'
        finally:
            cursor.close()


    try:
        cursor = get_cursor()
        cursor.execute("SELECT name, password, shared FROM List where password = ?", (list_key,))
        current_list = cursor.fetchone()
    finally:
        cursor.close()
    
    message = session.pop('message', '')
    
    return render_template('list_page.html',list=current_list,message=message,items=items)
    


if __name__ == '__main__':
    script_directory = os.path.dirname(os.path.abspath(__file__))
    folder_name = os.path.basename(script_directory)
    if (folder_name == 'client1'):
        port = 8000
    else:
        port = 9000

    app.run(debug=True,port=port)
