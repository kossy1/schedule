import sys
import os
from flask import Flask
from flask_cors import CORS

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import bp
from api.database import db

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(bp)

@app.route('/')
def index():
    return {"message": "The Polytechnic Ibadan Scheduling API"}

# For local development
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)