from flask import Blueprint, request, jsonify
from api.scheduler import GeneticScheduler
from api.database import db

bp = Blueprint('api', __name__)

@bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@bp.route('/api/courses', methods=['GET'])
def get_courses():
    courses = list(db.courses.find({}, {"_id": 0}))
    return jsonify(courses), 200

@bp.route('/api/courses', methods=['POST'])
def add_course():
    data = request.json
    db.courses.insert_one(data)
    return jsonify({"message": "Course added"}), 201

@bp.route('/api/timetable/generate', methods=['POST'])
def generate_timetable():
    data = request.json
    courses = list(db.courses.find({}, {"_id": 0}))
    rooms = data.get("rooms", ["Room A", "Room B", "Room C"])
    days = data.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    slots = data.get("slots", ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4"])
    
    scheduler = GeneticScheduler(courses, rooms, days, slots)
    best_schedule, fitness = scheduler.evolve()
    
    # Save schedule to database
    db.timetables.insert_one({
        "schedule": best_schedule,
        "fitness_score": fitness,
        "generated_at": "now"
    })
    
    return jsonify({
        "schedule": best_schedule,
        "fitness_score": fitness
    }), 200

@bp.route('/api/timetable/latest', methods=['GET'])
def get_latest_timetable():
    timetable = db.timetables.find_one(sort=[("_id", -1)], projection={"_id": 0})
    return jsonify(timetable or {"message": "No timetable found"}), 200