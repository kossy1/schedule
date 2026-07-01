import os
from dotenv import load_dotenv

# Load .env only if it exists
if os.path.exists('.env'):
    load_dotenv()

class Config:
    # JWT Secret Key
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI')
    DB_NAME = os.getenv('DB_NAME', 'polytechnic_scheduler')
    
    # Session Secret (optional)
    SESSION_SECRET = os.getenv('SESSION_SECRET', SECRET_KEY)
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.SECRET_KEY:
            raise ValueError("❌ SECRET_KEY is not set in environment variables!")
        if not cls.MONGODB_URI:
            print("⚠️  MONGODB_URI not set. Using mock database.")
        return True

# Validate on import
Config.validate()