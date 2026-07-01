import os
from dotenv import load_dotenv

# Only load .env locally, not on Vercel
if not os.getenv('VERCEL'):
    load_dotenv()

class Config:
    MONGODB_URI = os.getenv("MONGODB_URI")
    DB_NAME = os.getenv("DB_NAME", "polytechnic_scheduler")
    
    @staticmethod
    def get_mongodb_uri():
        uri = Config.MONGODB_URI
        if not uri:
            raise ValueError("MONGODB_URI environment variable is not set")
        return uri