create-databases:
	rm -f client1/client.db
	rm -f client2/client.db
	rm -f server1/server.db
	rm -f loadBalancer/loadBalancer.db
	touch client.db
	touch server.db
	touch loadBalancer.db
	sqlite3 loadBalancer.db < create.sql
	sqlite3 client.db < create.sql
	sqlite3 server.db < create.sql
	cp client.db client1/
	cp client.db client2/
	cp server.db server1/
	cp loadBalancer.db loadBalancer/
	rm client.db
	rm loadBalancer.db
	cp client1/client.db client2/client.db
