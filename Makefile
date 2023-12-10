create-databases:
	rm -f client1/client.db
	rm -f client2/client.db
	rm -f server1/server.db
	rm -f server2/server.db
	rm -f server3/server.db
	rm -f loadBalancer1/loadBalancer.db
	rm -f loadBalancer2/loadBalancer.db
	rm -f loadBalancer3/loadBalancer.db
	touch client.db
	touch server.db
	touch loadBalancer.db
	sqlite3 loadBalancer.db < create.sql
	sqlite3 client.db < create.sql
	sqlite3 server.db < create.sql
	cp client.db client1/
	cp client.db client2/
	cp server.db server1/
	cp server.db server2/
	cp server.db server3/
	cp loadBalancer.db loadBalancer1/
	cp loadBalancer.db loadBalancer2/
	cp loadBalancer.db loadBalancer3/
	rm client.db
	rm loadBalancer.db
	rm server.db
	cp client1/client.db client2/client.db
