run_client:
	python3 client1/client.py &
	python3 client2/client.py &

run_server:
	python3 server/server.py &

run_db:
	rm -f client1/client.db
	rm -f client2/client.db
	rm -f server/server.db
	touch client.db
	touch server.db
	sqlite3 client.db < create.sql
	sqlite3 server.db < create.sql
	cp client.db client1/
	cp client.db client2/
	mv server.db server
	rm client.db
	cp client1/client.db client2/client.db