from pymongo import MongoClient
from api.config import Config

# Use try/except for better error handling
try:
    client = MongoClient(Config.MONGODB_URI)
    db = client[Config.DB_NAME]
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    db = None