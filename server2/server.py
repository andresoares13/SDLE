from flask import Flask, request, g, render_template
import sqlite3
import requests
import string
import random
import json
from crdt import CRDT
from copy import deepcopy

app = Flask(__name__)

DATABASE_FILE = "server.db"



# Function to get a new database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
        db.row_factory = sqlite3.Row  # Enable row_factory to work with rows as dictionaries
    return db

def addNewItems(key,items,cursor):
    cursor.execute("SELECT name FROM Item WHERE list_key = ?",(key,))
    currentItemsRows = cursor.fetchall()
    currentItems = []
    if currentItemsRows:
        for item in currentItemsRows:
            currentItems.append(item[0])


    for item in items:
        if item[1] not in currentItems:
            if (item[2] - item[3] > 0):
                quantity = item[2] - item[3]
                cursor.execute("INSERT INTO Item (name, list_key, quantity) VALUES (?, ?, ?)", (item[1], key, 0))

            cursor.execute("INSERT INTO ItemIncreaseDict (list_key, item, quantity) VALUES (?, ?, ?)", 
            (key,item[1], 0))
            cursor.execute("INSERT INTO ItemDecreaseDict (list_key, item, quantity) VALUES (?, ?, ?)", 
            (key,item[1], 0))
            get_db().commit()
    


def updateItemsQuantities(key,change,cursor):
    sql_query = "SELECT name,quantity FROM Item WHERE list_key = ? AND name IN ({seq})".format(seq=','.join(['?']*len(list(change.keys()))))
    cursor.execute(sql_query, [key] + list(change.keys()))
    items = cursor.fetchall()
    for item in items:
        new = change[item[0]] + item[1]
        cursor.execute("UPDATE Item SET quantity = ? WHERE name = ? AND list_key = ?", (new, item[0], key))
    


def updateDBDicts(list,crdt,cursor):
    for item in crdt.inc.keys():
        cursor.execute("UPDATE ItemIncreaseDict SET quantity = ? WHERE list_key = ? AND item = ?",
        (crdt.inc.get(item), list, item))
        cursor.execute("UPDATE ItemDecreaseDict SET quantity = ? WHERE list_key = ? AND item = ?",
        (crdt.dec.get(item), list, item))
    get_db().commit()

def getDictQuantity(I, list, cursor):
    if I:
        cursor.execute("SELECT quantity,item FROM ItemIncreaseDict WHERE list_key = ?", (list,))
        dic = cursor.fetchall()
    else:
        cursor.execute("SELECT quantity,item FROM ItemDecreaseDict WHERE list_key = ?", (list,))
        dic = cursor.fetchall()

    return dic


def getDictQuantityItem(I, list, item, cursor):
    if I:
        cursor.execute("SELECT quantity FROM ItemIncreaseDict WHERE list_key = ? AND item = ?", (list,item))
        quantity = cursor.fetchone()
    else:
        cursor.execute("SELECT quantity FROM ItemDecreaseDict WHERE list_key = ? AND item = ?", (list,item))
        quantity = cursor.fetchone()

    return quantity[0]


def getCRDT(key,cursor):
    increase = getDictQuantity(True,key,cursor)
    decrease = getDictQuantity(False,key,cursor)
    items = []
    for i in range(len(increase)):
        items.append([key,increase[i][1],increase[i][0],decrease[i][0]])
    return CRDT(key,items)


def existsItemUpdate(user, list, item,cursor):
    cursor.execute("SELECT * FROM ItemChangeUpdate WHERE username = ? AND list_key = ? AND item = ?", (user,list,item))
    update = cursor.fetchone()
    if (update):
        return True
    else:
        return False

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


@app.route('/add_existing_user', methods=['POST'])
def add_existing_user_route():
    data = request.get_json()
    name = data['name']
    password = data['password']
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM User WHERE name = ? AND password = ?", (name, password))
        user = cursor.fetchone()
        if user:
            cursor.execute("SELECT list_key from UserList WHERE name = ?",(name,))
            lists = cursor.fetchall()
            listsKeys = []
            for list in lists:
                listsKeys.append(list[0])

            response_data = {"lists": listsKeys}
            response_json = json.dumps(response_data)
            return response_json, 200
        else:
            return "User not found", 404
    finally:
        db.close()


@app.route('/deleteUser', methods=['POST'])
def delete_user():
    data = request.get_json()
    username = data['username']
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('PRAGMA foreign_keys = ON')
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
            cursor.execute("INSERT INTO ItemIncreaseDict (list_key, item, quantity) VALUES (?, ?, ?)", 
            (item[2],item[1], 0))
            cursor.execute("INSERT INTO ItemDecreaseDict (list_key, item, quantity) VALUES (?, ?, ?)", 
            (item[2],item[1], 0))
        db.commit()
    finally:
        db.close()

    return password, 200


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
            
            inc = {}
            dec = {}
            for item in rows:
                inc[item[1]] = getDictQuantityItem(True,item[2],item[1],cursor)
                dec[item[1]] = getDictQuantityItem(False,item[2],item[1],cursor)
            print(inc,dec)
            db.commit()
            valid = True
            
    finally:
        db.close()

    if valid:
        response_data = {"list": list[0], "items": items, "inc":inc, "dec":dec}
        response_json = json.dumps(response_data)
        return response_json, 200
    else:
        return "List not found", 404 
    

@app.route('/itemsChangeUpdate', methods=['POST'])
def itemsChange():
    data = request.get_json()
    items = data['items']
    user = data['name']
    try:
        cursor = get_db().cursor()
        for key, value in items.items():
            userCRDT = CRDT(key,value)
            addNewItems(key,value,cursor)
            serverCRDT = getCRDT(key,cursor)
            oldCRDT = deepcopy(serverCRDT)
            serverCRDT.merge(userCRDT)
            change = serverCRDT.quantityChange(oldCRDT)
            updateItemsQuantities(key,change,cursor)
            updateDBDicts(key,serverCRDT,cursor)
            for item in value:
                cursor.execute("SELECT name FROM UserList WHERE list_key = ?",(key,))
                users = cursor.fetchall()
                for username in users:
                    if username[0] != user and not existsItemUpdate(username[0],item[0],item[1],cursor):
                        cursor.execute("INSERT INTO ItemChangeUpdate (username, list_key, item) VALUES (?, ?, ?)", 
                        (username[0], key,item[1]))
            get_db().commit()

            return "Items updated", 200
    except Exception as e:
        print(e)
        return "Item updates not handled correctly", 404 
    
    finally:
        cursor.close()



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

    cursor.execute("SELECT list_key,item FROM ItemChangeUpdate WHERE username = ? ORDER BY list_key",(username,))
    itemUpdates = cursor.fetchall()
    items = {}
    for update in itemUpdates:
        increase = getDictQuantityItem(True,update[0],update[1],cursor)
        decrease = getDictQuantityItem(False,update[0],update[1],cursor)
        if items.get(update[0]):
            items[update[0]].append([update[0],update[1],increase,decrease])
        else:
            items[update[0]] = []
            items[update[0]].append([update[0],update[1],increase,decrease])
        
    itemsData = {'items':items}
    response = requests.post(f'http://localhost:{port}/updateItemsServerRequest', json=itemsData)
    if response.status_code !=200:
        failed = True

    
    

    if failed:

        return "Failure",404
    else:
        if (itemUpdates):
            #cursor.execute("DELETE FROM ItemChangeUpdate WHERE username = ?",(username,))
            get_db().commit()

        return "Updated", 200
    
    

if __name__ == '__main__':
    app.run(debug=True, port=5002)