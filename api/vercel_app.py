import sys
import os
import json
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from datetime import datetime

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
try:
    from api.config import Config
    from api.database import db, client
    from api.auth import init_admin_user
    from api.routes import bp
    from api.admin_routes import admin_bp
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    # Create minimal app for testing
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/api/health')
    def health():
        return jsonify({"status": "ok", "message": "API is running"})
    
    @app.route('/')
    def index():
        return jsonify({
            "message": "The Polytechnic Ibadan Scheduling API",
            "status": "running"
        })
    
    # Export for Vercel
    application = app
    app.debug = False
    sys.exit(0)

# Create Flask app
app = Flask(__name__)

# Configure CORS properly
CORS(app, 
     resources={
         r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"]
         }
     })

# Register blueprints
app.register_blueprint(bp)
app.register_blueprint(admin_bp)

# Health check endpoint
@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health_check():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        # Test database connection
        db_status = 'connected' if db else 'disconnected'
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'timestamp': datetime.utcnow().isoformat(),
            'environment': 'vercel'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Root endpoint
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'The Polytechnic Ibadan Scheduling API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'admin_login': '/api/admin/login',
            'courses': '/api/admin/courses',
            'lecturers': '/api/admin/lecturers',
            'halls': '/api/admin/halls',
            'exams': '/api/admin/exams',
            'timetable': '/api/admin/timetable',
            'public_timetable': '/api/timetable/latest'
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

# This is required for Vercel
app.debug = False

# Export app for Vercel
application = app

# For local testing
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)