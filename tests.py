import os
import time
import random
import unittest

import storage
import server
import client

class TestSync(unittest.TestCase):
    serverStorageName = 'server.json'
    clientStorageName = 'client.json'

    def setUp(self):
        self.server = server.Server(self.serverStorageName)
        self.client = client.Client(self.clientStorageName)

    def tearDown(self):
        if os.path.exists(self.serverStorageName):
            os.remove(self.serverStorageName)
        if os.path.exists(self.clientStorageName):
            os.remove(self.clientStorageName)

    def testSync1(self):
        # server created
        for name in ['johnny', 'depp', 'brad', 'pitt','foo']:
            self.server.post({'name':name})
        self.client.sync(self.server)
        self.checkSync()
        # server created and updated
        self.server.put(4, {'name':'pit', 'age':33})
        self.client.sync(self.server)
        self.checkSync()
        # server created and updated and deleted
        self.server.delete(5)
        self.client.sync(self.server)
        self.checkSync()
        # client updated
        self.client.update(4, {'age':66})
        self.client.sync(self.server)
        self.checkSync()
        # client created
        self.client.create({'name':'my local object'})
        self.client.sync(self.server)
        self.checkSync()
        # client deleted
        self.client.delete(1)
        self.client.sync(self.server)
        self.checkSync()
        # here comes random test
        # randomly choose server/client to store
        # randomly do action create/update/delete
        for i in range(1000):
            server_or_client = random.randint(0, 1)
            if server_or_client == 0:
                create_or_update_or_delete = random.randint(0, 10)
                if create_or_update_or_delete < 6:
                    new_obj = self.generateRandomObject() # randomly generate object
                    self.server.post(new_obj)
                elif create_or_update_or_delete < 9:
                    all_objects_on_server = self.server.storage.read_all()
                    if len(all_objects_on_server) != 0:
                        old_obj = random.choice(all_objects_on_server)
                        if not old_obj['deleted']:
                            self.server.put(old_obj['key'], self.generateRandomObject())
                else:
                    all_objects_on_server = self.server.storage.read_all()
                    if len(all_objects_on_server) != 0:
                        old_obj = random.choice(all_objects_on_server)
                        self.server.delete(old_obj['key'])
            else:
                create_or_update_or_delete = random.randint(0, 10)
                if create_or_update_or_delete < 6:
                    new_obj = self.generateRandomObject() # randomly generate object
                    self.client.create(new_obj)
                elif create_or_update_or_delete < 9:
                    all_objects_on_client = self.client.storage.read_all()
                    if len(all_objects_on_client) != 0:
                        old_obj = random.choice(all_objects_on_client)
                        if not old_obj['deleted']:
                            self.client.update(old_obj['key'], self.generateRandomObject())
                else:
                    all_objects_on_client = self.client.storage.read_all()
                    if len(all_objects_on_client) != 0:
                        old_obj = random.choice(all_objects_on_client)
                        self.client.delete(old_obj['key'])
            sync = random.randint(0, 1)
            if sync:
                self.client.sync(self.server)
                self.checkSync()

    def checkSync(self):
        for server_obj in self.server.storage.read_all():
            if not server_obj['deleted']:
                client_obj = self.client.storage.read(server_key=server_obj['key'])
                del client_obj['dirty']
                client_obj['key'] = client_obj['server_key']
                del client_obj['server_key']
                self.assertEquals(client_obj, server_obj)

    def generateRandomObject(self):
        name = random.choice(['bob', 'sapp', 'jeep', 'head', 'dog', 'cat', 'mice', 'kid', 'horse', 'goat', 'camel', 'phone'])
        age = random.randint(10, 100)
        colour = random.choice(['white', 'dark', 'blue', 'black', 'grey', 'green', 'pink', 'yellow', 'red'])
        return {
            'name': name,
            'age': age,
            'colour': colour
        }

    def dumpClientAndServer(self, message):
        print '*'*40, message, '*'*40
        print 'Server:'
        self.dump(self.server.storage)
        print 'Client:'
        self.dump(self.client.storage)

    def dump(self, storage):
        sorted_objects = sorted(storage.read_all(), key=lambda obj:obj['key'])
        for obj in sorted_objects:
            print '\tkey:', obj['key']
            for attr in sorted(obj.keys()):
                if attr != 'key':
                    print '\t\t', attr, ':', obj[attr]

if __name__ == '__main__':
    unittest.main(failfast=True)
