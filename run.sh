#!/bin/bash

run_in_terminal() {
    local title="$1"
    local command="$2"
    gnome-terminal -- bash -c "$command" --title="$title" &
}

# Close all terminals opened by this script
pkill -f "bash -c .*--title="

# Open a terminal in /client1 and run client.py
run_in_terminal "Client 1" "cd client1 && python3 client.py; read"

# Open a terminal in /client2 and run client.py
run_in_terminal "Client 2" "cd client2 && python3 client.py; read"

# Open a terminal in /server and run server.py
run_in_terminal "Server" "cd server1 && python3 server.py; read"

# Open a terminal in /server and run server.py
run_in_terminal "Server" "cd server2 && python3 server.py; read"

# Open a terminal in /server and run server.py
run_in_terminal "Server" "cd server3 && python3 server.py; read"

run_in_terminal "Load Balancer" "cd loadBalancer1 && python3 loadBalancer.py; read"

run_in_terminal "Load Balancer" "cd loadBalancer2 && python3 loadBalancer.py; read"

run_in_terminal "Load Balancer" "cd loadBalancer3 && python3 loadBalancer.py; read"
