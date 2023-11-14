from flask import Flask, request
import sys
import requests
import json

app = Flask(__name__)

servers = {"http://localhost:5000":0, "http://localhost:5001":0,"http://localhost:5002":0}

serversNum = len(servers)

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

    response = requests.post(f"{choice}{route}", json=jsonData)

    responseDic = {"text":response.text, "status":response.status_code} 

    response_json = json.dumps(responseDic)

    return response_json, 200

if __name__ == '__main__':
    app.run(debug=True, port=7000)