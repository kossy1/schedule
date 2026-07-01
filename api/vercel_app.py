import sys
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from api.database import db
from api.auth import init_admin_user
from api.routes import bp
from api.admin_routes import admin_bp

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Register blueprints
app.register_blueprint(bp)
app.register_blueprint(admin_bp)

# Health check
@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return '', 200
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'API is running'
    }), 200

# Root endpoint
@app.route('/')
def index():
    return jsonify({
        'message': 'The Polytechnic Ibadan Scheduling API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'login': '/api/admin/login',
            'departments': '/api/admin/departments',
            'lecturers': '/api/admin/lecturers',
            'courses': '/api/admin/courses',
            'halls': '/api/admin/halls',
            'exams': '/api/admin/exams',
            'timetable': '/api/admin/timetable'
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Initialize admin user
with app.app_context():
    try:
        init_admin_user()
        print("✅ Admin user initialized")
    except Exception as e:
        print(f"⚠️ Admin initialization warning: {e}")

# Required for Vercel
application = app

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)