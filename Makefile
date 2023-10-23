create-databases:
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
