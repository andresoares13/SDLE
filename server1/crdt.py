class CRDT: #PN counter
    def __init__(self, key,items):
        self.inc = {}   
        self.dec = {}
        self.key = key

        for update in items:
            self.inc[update[1]] = update[2]
            self.dec[update[1]] = update[3]


    def merge(self,other):
        for key in other.inc.keys():
            self.inc[key] = max(self.inc.get(key),other.inc.get(key))
            self.dec[key] = max(self.dec.get(key),other.dec.get(key))

    def quantityChange(self,other):
        change = {}
        for key in other.inc.keys():
            change[key] = abs(self.inc.get(key) - other.inc.get(key)) - abs(self.dec.get(key) - other.dec.get(key))
        return change

