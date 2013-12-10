import copy
import time
import storage

class Client:
    ''' acts locally, when sync method is called it will sync with server. 
    dirty       - locally modified flag
    server_key  - key on the server
    deleted     - object is locally deleted
    '''
    
    def __init__(self, local_storage):
        self.storage = storage.Storage(local_storage)

    def create(self, obj):
        obj['dirty'] = True
        obj['server_key'] = None
        obj['deleted'] = False
        obj['ts'] = 0
        key = self.storage.create(obj)
        return key

    def read(self, key):
        return self.storage.read(key=key)

    def update(self, key, obj):
        old_obj = self.read(key)
        obj['dirty'] = True
        obj['ts'] = old_obj['ts']
        obj['deleted'] = old_obj['deleted']
        obj['server_key'] = old_obj['server_key']
        self.storage.update(key, obj)

    def delete(self, key):
        obj = self.storage.read(key=key)
        if obj['server_key']: # originated from server
            obj['dirty'] = True
            obj['deleted'] = True
            self.storage.update(key, obj)
        else:
            del self.storage.objects[obj['key']]

    def _get_max_ts(self):
        max_ts = 0
        for obj in self.storage.read_all():
            if obj['ts'] > max_ts: max_ts = obj['ts']
        return max_ts

    def sync(self, server):
        # download part
        max_ts = self._get_max_ts()
        newer_objects = server.get(timestamp=max_ts)
        for server_obj in newer_objects:
            local_obj = None
            try:
                local_obj = self.storage.read(server_key=server_obj['key'])
            except KeyError:
                pass
            if local_obj: # we have same object locally.
                server_obj['dirty'] = False
                server_obj['server_key'] = server_obj['key']
                if 'deleted' in server_obj and server_obj['deleted']:
                    obj = self.storage.read(server_key=server_obj['key'])
                    del self.storage.objects[obj['key']]
                elif 'dirty' in local_obj and local_obj['dirty']:
                    if server_obj['ts'] > local_obj['ts']: # conflict resolution. based on timestamp
                        self.storage.update(server_obj['key'], server_obj)
                else:
                    self.storage.update(local_obj['key'], server_obj)
            else: # we do not have the object.
                if not server_obj['deleted']:
                    temp_obj = server_obj
                    temp_obj['server_key'] = server_obj['key']
                    temp_obj['dirty'] = False
                    self.storage.create(temp_obj)
        # upload part, send dirty objects to server. assume client cannot delete.
        objects_to_send = [ ]
        objects_to_update = [ ]
        objects_to_delete = [ ]
        for local_obj in self.storage.read_all():
            if local_obj['dirty']:
                if local_obj['server_key']: # object is originated from server
                    if local_obj['deleted']:
                        objects_to_delete.append(local_obj)
                    else:
                        objects_to_update.append(local_obj)
                else:
                    if not local_obj['deleted']:
                        objects_to_send.append(local_obj)
        for obj in objects_to_send:
            temp_obj = copy.deepcopy(obj)
            del obj['dirty']
            del obj['server_key']
            server_obj = server.post(obj)
            server_obj['dirty'] = False
            server_obj['server_key'] = server_obj['key']
            self.storage.update(temp_obj['key'], server_obj)
        for obj in objects_to_update:
            temp_obj = copy.deepcopy(obj)
            del obj['dirty']
            del obj['server_key']
            server_obj = server.put(temp_obj['server_key'], obj)
            server_obj['dirty'] = False
            server_obj['server_key'] = temp_obj['server_key']
            self.storage.update(temp_obj['key'], server_obj)
        for obj in objects_to_delete:
            server.delete(obj['server_key'])
            del self.storage.objects[obj['key']]

