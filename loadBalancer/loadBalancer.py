from flask import Flask, request
import requests

app = Flask(__name__)

# List of server addresses
SERVERS = ["http://127.0.0.1:5001", "http://127.0.0.1:5002"]
CURRENT_SERVER_INDEX = 0

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    global CURRENT_SERVER_INDEX
    server_url = SERVERS[CURRENT_SERVER_INDEX]
    CURRENT_SERVER_INDEX = (CURRENT_SERVER_INDEX + 1) % len(SERVERS)

    url = f"{server_url}/{path}"

    if request.method == 'GET':
        response = requests.get(url, params=request.args)
    elif request.method == 'POST':
        response = requests.post(url, json=request.get_json())
    elif request.method == 'PUT':
        response = requests.put(url, json=request.get_json())
    elif request.method == 'DELETE':
        response = requests.delete(url)

    return response.content, response.status_code, response.headers.items()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
