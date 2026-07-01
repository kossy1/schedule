import os
from pymongo import MongoClient
from datetime import datetime

# Get MongoDB URI from environment
MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = os.getenv('DB_NAME', 'polytechnic_scheduler')

# Initialize client
client = None
db = None

try:
    if MONGODB_URI:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        client.admin.command('ping')
        print(f"✅ MongoDB connected to: {DB_NAME}")
    else:
        print("⚠️ MONGODB_URI not set, using in-memory database")
        # Create in-memory database for testing
        from collections import defaultdict
        
        class MemoryCollection:
            def __init__(self, name):
                self.name = name
                self.data = []
                self.counter = 0
                
            def find(self, query=None, projection=None):
                return self.data
                
            def find_one(self, query=None, projection=None, sort=None):
                if not self.data:
                    return None
                if query:
                    for item in self.data:
                        if all(item.get(k) == v for k, v in query.items()):
                            return item
                return self.data[0] if self.data else None
                
            def insert_one(self, doc):
                doc['_id'] = self.counter
                self.counter += 1
                self.data.append(doc)
                return type('obj', (object,), {'inserted_id': doc['_id']})
                
            def insert_many(self, docs):
                for doc in docs:
                    doc['_id'] = self.counter
                    self.counter += 1
                    self.data.append(doc)
                return len(docs)
                
            def update_one(self, query, update):
                for item in self.data:
                    if all(item.get(k) == v for k, v in query.items()):
                        for k, v in update.get('$set', {}).items():
                            item[k] = v
                        return type('obj', (object,), {'matched_count': 1, 'modified_count': 1})
                return type('obj', (object,), {'matched_count': 0, 'modified_count': 0})
                
            def delete_one(self, query):
                for i, item in enumerate(self.data):
                    if all(item.get(k) == v for k, v in query.items()):
                        self.data.pop(i)
                        return type('obj', (object,), {'deleted_count': 1})
                return type('obj', (object,), {'deleted_count': 0})
                
            def delete_many(self, query):
                count = len(self.data)
                self.data = []
                return type('obj', (object,), {'deleted_count': count})
                
            def count_documents(self, query=None):
                return len(self.data)
        
        class MemoryDB:
            def __init__(self):
                self.collections = {}
                
            def __getitem__(self, name):
                if name not in self.collections:
                    self.collections[name] = MemoryCollection(name)
                return self.collections[name]
            
            def __getattr__(self, name):
                return self[name]
        
        db = MemoryDB()
        
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
    # Use in-memory database as fallback
    class MemoryCollection:
        def __init__(self, name):
            self.name = name
            self.data = []
            self.counter = 0
            
        def find(self, query=None, projection=None):
            return self.data
            
        def find_one(self, query=None, projection=None, sort=None):
            if not self.data:
                return None
            if query:
                for item in self.data:
                    if all(item.get(k) == v for k, v in query.items()):
                        return item
            return self.data[0] if self.data else None
            
        def insert_one(self, doc):
            doc['_id'] = self.counter
            self.counter += 1
            self.data.append(doc)
            return type('obj', (object,), {'inserted_id': doc['_id']})
            
        def insert_many(self, docs):
            for doc in docs:
                doc['_id'] = self.counter
                self.counter += 1
                self.data.append(doc)
            return len(docs)
            
        def update_one(self, query, update):
            for item in self.data:
                if all(item.get(k) == v for k, v in query.items()):
                    for k, v in update.get('$set', {}).items():
                        item[k] = v
                    return type('obj', (object,), {'matched_count': 1})
            return type('obj', (object,), {'matched_count': 0})
            
        def delete_one(self, query):
            for i, item in enumerate(self.data):
                if all(item.get(k) == v for k, v in query.items()):
                    self.data.pop(i)
                    return type('obj', (object,), {'deleted_count': 1})
            return type('obj', (object,), {'deleted_count': 0})
            
        def delete_many(self, query):
            count = len(self.data)
            self.data = []
            return type('obj', (object,), {'deleted_count': count})
            
        def count_documents(self, query=None):
            return len(self.data)
    
    class MemoryDB:
        def __init__(self):
            self.collections = {}
            
        def __getitem__(self, name):
            if name not in self.collections:
                self.collections[name] = MemoryCollection(name)
            return self.collections[name]
        
        def __getattr__(self, name):
            return self[name]
    
    db = MemoryDB()