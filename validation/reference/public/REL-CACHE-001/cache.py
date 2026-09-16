from collections import OrderedDict

class Cache:
    def __init__(self, max_entries):
        if max_entries < 1:
            raise ValueError("max_entries must be positive")
        self.max_entries=max_entries
        self.data=OrderedDict()
    def set(self,key,value):
        if key in self.data:
            self.data.move_to_end(key)
        self.data[key]=value
        while len(self.data) > self.max_entries:
            self.data.popitem(last=False)
    def get(self,key):
        if key not in self.data:
            return None
        self.data.move_to_end(key)
        return self.data[key]
    def __len__(self):
        return len(self.data)
