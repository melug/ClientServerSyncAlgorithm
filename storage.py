import os
import os.path
import json
import time
import copy

class Storage:
    ''' Storage simulation for both server and client. '''

    def __init__(self, filename):
        self.filename = filename
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                self.objects = json.loads(f.read())
        else:
            self.objects = { }

    def next_key(self):
        keys = self.objects.keys()
        max_key = (keys and max(keys)) or 0
        return max_key + 1

    def create(self, obj):
        ''' key, ts might be originated from server. '''
        key = self.next_key()
        obj['key'] = key
        self.objects[key] = obj
        self.store_locally()
        return key

    def read(self, **kwargs):
        ''' not responsible for futher operations on the object. '''
        if 'key' in kwargs:
            return copy.deepcopy(self.objects[kwargs['key']])
        for obj in self.objects.values():
            matches = True
            for k, v in kwargs.items():
                if k not in obj or obj[k]!=v:
                    matches = False
                    break
            if matches:
                return copy.deepcopy(obj)
        raise KeyError

    def update(self, key, obj):
        obj['key'] = key
        self.objects[key] = obj
        self.store_locally()

    def store_locally(self):
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.objects, indent=4))

    def read_all(self):
        return copy.deepcopy(self.objects.values())
    
