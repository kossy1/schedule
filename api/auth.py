import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
import jwt
from flask import request, jsonify, current_app
from functools import wraps
from .database import db

# Secret key for JWT (use environment variable in production)
SECRET_KEY = "your-super-secret-key-change-this-in-production"

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return salt + ":" + hash_obj.hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hashed version."""
    salt, hash_value = hashed.split(":")
    hash_obj = hashlib.sha256((salt + password).encode())
    return hmac.compare_digest(hash_obj.hexdigest(), hash_value)

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
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        return f(payload, *args, **kwargs)
    return decorated

def init_admin_user():
    """Create default admin user if none exists."""
    admin = db.users.find_one({'username': 'admin'})
    if not admin:
        hashed = hash_password('admin123')
        db.users.insert_one({
            'username': 'admin',
            'password': hashed,
            'role': 'admin',
            'created_at': datetime.utcnow()
        })
        print("✅ Default admin created: username='admin', password='admin123'")