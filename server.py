import copy
import time
import storage

clone = copy.deepcopy

class Server:
    ''' Server simulation '''
    def __init__(self, storage_name):
        self.storage = storage.Storage(storage_name)

    def post(self, obj):
        obj['ts'] = time.time()
        obj['deleted'] = False
        key = self.storage.create(obj)
        return self.storage.read(key=key)

    def get(self, key=None, timestamp=None):
        ''' return objects changed after timestamp or return object with the key. '''
        if timestamp is not None:
            objects = [ ]
            for obj in self.storage.read_all():
                if obj['ts'] > timestamp:
                    objects.append(obj)
            return objects
        if key is not None:
            return self.storage.read(key=key)
        return self.storage.read_all()

    def put(self, key, obj):
        old_obj = self.storage.read(key=key)
        obj['ts'] = time.time()
        obj['deleted'] = old_obj['deleted']
        self.storage.update(key, obj)
        return self.storage.read(key=key)

    def delete(self, key):
        obj = self.storage.read(key=key)
        obj['ts'] = time.time()
        obj['deleted'] = True
        self.storage.update(key, obj)

