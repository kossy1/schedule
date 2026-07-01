import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
import jwt
from flask import request, jsonify
from functools import wraps
from .database import db
from .config import Config

SECRET_KEY = Config.SECRET_KEY

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return salt + ":" + hash_obj.hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hashed version."""
    try:
        salt, hash_value = hashed.split(":")
        hash_obj = hashlib.sha256((salt + password).encode())
        return hmac.compare_digest(hash_obj.hexdigest(), hash_value)
    except:
        return False

def generate_token(user_id: str, username: str) -> str:
    """Generate JWT token."""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token: str) -> dict:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except:
        return None

def token_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        return f(payload, *args, **kwargs)
    return decorated

def init_admin_user():
    """Create default admin user if none exists."""
    try:
        if db:
            admin = db.users.find_one({'username': 'admin'})
            if not admin:
                hashed = hash_password('admin123')
                db.users.insert_one({
                    'username': 'admin',
                    'password': hashed,
                    'role': 'admin',
                    'created_at': datetime.utcnow().isoformat()
                })
                print("✅ Default admin created: username='admin', password='admin123'")
                return True
        return False
    except Exception as e:
        print(f"⚠️ Could not initialize admin: {e}")
        return False