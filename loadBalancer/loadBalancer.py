from flask import Flask, request, g
import sys
import requests
import json
import sqlite3

app = Flask(__name__)

servers = {"http://localhost:5000":0, "http://localhost:5001":0,"http://localhost:5002":0}

serversNum = len(servers)

DATABASE_FILE = "loadBalancer.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_FILE)
    return db

def get_cursor():
    return get_db().cursor()

@app.route('/findServer', methods=['POST'])
def find_server():
    data = request.get_json()
    route = list(data.keys())[0]
    jsonData = data[route]
    min = sys.maxsize
    choice = None
    for server, value in servers.items():
        ratio = value / serversNum
        if ratio < min:
            min = ratio
            choice = server

    if (route == '/add_list'):
        id = list(servers).index(choice) + 1
        if (id == 1):
            id2 = 2
            id3 = 3
        elif (id == 10):
            id2 = 8
            id3 = 9
        else:
            id2 = id - 1
            id3 = id + 1

        serverList = [id,id2,id3]
        
        jsonData['servers'] = serverList
        jsonData['postUpdate'] = 1

        correct = True
        keyDecision = False


        if not keyDecision:  #first server to receive this decides the correct list key
            jsonData['correctKey'] = 1
            keyDecision = True
        else:
            jsonData['correctKey'] = 0

        response = requests.post(f"{choice}{route}", json=jsonData)
        responseDic = {"text":response.text, "status":response.status_code} 
        response_json = json.dumps(responseDic)

        if (response.status_code != 200):
            correct = False
     
        if (correct):
            cursor = get_cursor()
            for server in serverList:
                cursor.execute("INSERT INTO ServerListAssign (server, list_key) VALUES (?,?)",(server,jsonData['key']))
            get_db().commit()
            return response_json, response.status_code
        else:
            return response_json, 404
    
    else:


        response = requests.post(f"{choice}{route}", json=jsonData)

        responseDic = {"text":response.text, "status":response.status_code} 

        response_json = json.dumps(responseDic)

        return response_json, response.status_code

if __name__ == '__main__':
    app.run(debug=True, port=7000)