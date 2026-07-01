import sys
import os
from flask import Flask
from flask_cors import CORS

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import bp
from api.admin_routes import admin_bp
from api.database import db
from api.auth import init_admin_user

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(bp)
app.register_blueprint(admin_bp)

@app.route('/')
def index():
    return {"message": "The Polytechnic Ibadan Scheduling API"}

# Initialize admin user on startup
with app.app_context():
    init_admin_user()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)