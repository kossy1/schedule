from flask import Blueprint, request, jsonify
from datetime import datetime
from .database import db
from .auth import token_required, hash_password
from .scheduler import GeneticScheduler

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ==================== AUTHENTICATION ====================

@admin_bp.route('/login', methods=['POST'])
def login():
    """Admin login endpoint."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = db.users.find_one({'username': username})
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    from .auth import verify_password, generate_token
    if not verify_password(password, user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = generate_token(str(user['_id']), user['username'])
    return jsonify({
        'token': token,
        'user': {
            'username': user['username'],
            'role': user.get('role', 'admin')
        }
    }), 200

@admin_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(payload):
    """Verify token validity."""
    return jsonify({'valid': True, 'user': payload}), 200

# ==================== COURSE MANAGEMENT ====================

@admin_bp.route('/courses', methods=['GET'])
@token_required
def get_courses(payload):
    """Get all courses."""
    courses = list(db.courses.find({}, {'_id': 0}))
    return jsonify(courses), 200

@admin_bp.route('/courses', methods=['POST'])
@token_required
def add_course(payload):
    """Add a new course."""
    data = request.json
    required = ['id', 'name', 'lecturer', 'semester']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    # Check if course exists
    if db.courses.find_one({'id': data['id']}):
        return jsonify({'error': f'Course {data["id"]} already exists'}), 400
    
    db.courses.insert_one(data)
    return jsonify({'message': 'Course added successfully', 'course': data}), 201

@admin_bp.route('/courses/<course_id>', methods=['PUT'])
@token_required
def update_course(payload, course_id):
    """Update a course."""
    data = request.json
    result = db.courses.update_one({'id': course_id}, {'$set': data})
    
    if result.matched_count == 0:
        return jsonify({'error': 'Course not found'}), 404
    
    return jsonify({'message': 'Course updated successfully'}), 200

@admin_bp.route('/courses/<course_id>', methods=['DELETE'])
@token_required
def delete_course(payload, course_id):
    """Delete a course."""
    result = db.courses.delete_one({'id': course_id})
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Course not found'}), 404
    
    return jsonify({'message': 'Course deleted successfully'}), 200

# ==================== LECTURER MANAGEMENT ====================

@admin_bp.route('/lecturers', methods=['GET'])
@token_required
def get_lecturers(payload):
    """Get all lecturers."""
    lecturers = list(db.lecturers.find({}, {'_id': 0}))
    return jsonify(lecturers), 200

@admin_bp.route('/lecturers', methods=['POST'])
@token_required
def add_lecturer(payload):
    """Add a new lecturer."""
    data = request.json
    required = ['id', 'name', 'department', 'email']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    if db.lecturers.find_one({'id': data['id']}):
        return jsonify({'error': f'Lecturer {data["id"]} already exists'}), 400
    
    db.lecturers.insert_one(data)
    return jsonify({'message': 'Lecturer added successfully', 'lecturer': data}), 201

@admin_bp.route('/lecturers/<lecturer_id>', methods=['PUT'])
@token_required
def update_lecturer(payload, lecturer_id):
    """Update a lecturer."""
    data = request.json
    result = db.lecturers.update_one({'id': lecturer_id}, {'$set': data})
    
    if result.matched_count == 0:
        return jsonify({'error': 'Lecturer not found'}), 404
    
    return jsonify({'message': 'Lecturer updated successfully'}), 200

@admin_bp.route('/lecturers/<lecturer_id>', methods=['DELETE'])
@token_required
def delete_lecturer(payload, lecturer_id):
    """Delete a lecturer."""
    result = db.lecturers.delete_one({'id': lecturer_id})
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Lecturer not found'}), 404
    
    return jsonify({'message': 'Lecturer deleted successfully'}), 200

# ==================== HALL MANAGEMENT ====================

@admin_bp.route('/halls', methods=['GET'])
@token_required
def get_halls(payload):
    """Get all halls/rooms."""
    halls = list(db.halls.find({}, {'_id': 0}))
    return jsonify(halls), 200

@admin_bp.route('/halls', methods=['POST'])
@token_required
def add_hall(payload):
    """Add a new hall/room."""
    data = request.json
    required = ['id', 'name', 'capacity', 'type']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    if db.halls.find_one({'id': data['id']}):
        return jsonify({'error': f'Hall {data["id"]} already exists'}), 400
    
    db.halls.insert_one(data)
    return jsonify({'message': 'Hall added successfully', 'hall': data}), 201

@admin_bp.route('/halls/<hall_id>', methods=['PUT'])
@token_required
def update_hall(payload, hall_id):
    """Update a hall."""
    data = request.json
    result = db.halls.update_one({'id': hall_id}, {'$set': data})
    
    if result.matched_count == 0:
        return jsonify({'error': 'Hall not found'}), 404
    
    return jsonify({'message': 'Hall updated successfully'}), 200

@admin_bp.route('/halls/<hall_id>', methods=['DELETE'])
@token_required
def delete_hall(payload, hall_id):
    """Delete a hall."""
    result = db.halls.delete_one({'id': hall_id})
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Hall not found'}), 404
    
    return jsonify({'message': 'Hall deleted successfully'}), 200

# ==================== EXAM SCHEDULING ====================

@admin_bp.route('/exams', methods=['GET'])
@token_required
def get_exams(payload):
    """Get all exams."""
    exams = list(db.exams.find({}, {'_id': 0}))
    return jsonify(exams), 200

@admin_bp.route('/exams', methods=['POST'])
@token_required
def add_exam(payload):
    """Add a new exam."""
    data = request.json
    required = ['id', 'course', 'date', 'time', 'hall', 'duration']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    # Check for conflicts
    existing = db.exams.find_one({
        'date': data['date'],
        'time': data['time'],
        'hall': data['hall']
    })
    if existing:
        return jsonify({'error': 'Hall already booked for this time slot'}), 400
    
    db.exams.insert_one(data)
    return jsonify({'message': 'Exam added successfully', 'exam': data}), 201

@admin_bp.route('/exams/<exam_id>', methods=['PUT'])
@token_required
def update_exam(payload, exam_id):
    """Update an exam."""
    data = request.json
    result = db.exams.update_one({'id': exam_id}, {'$set': data})
    
    if result.matched_count == 0:
        return jsonify({'error': 'Exam not found'}), 404
    
    return jsonify({'message': 'Exam updated successfully'}), 200

@admin_bp.route('/exams/<exam_id>', methods=['DELETE'])
@token_required
def delete_exam(payload, exam_id):
    """Delete an exam."""
    result = db.exams.delete_one({'id': exam_id})
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Exam not found'}), 404
    
    return jsonify({'message': 'Exam deleted successfully'}), 200

@admin_bp.route('/exams/generate', methods=['POST'])
@token_required
def generate_exam_schedule(payload):
    """Generate exam schedule using algorithm."""
    data = request.json
    courses = list(db.courses.find({}, {'_id': 0}))
    halls = list(db.halls.find({}, {'_id': 0}))
    
    if not courses or not halls:
        return jsonify({'error': 'Need courses and halls to generate exam schedule'}), 400
    
    # Simple algorithm: assign exams to available slots
    exam_slots = []
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    times = ['9-11', '11-1', '2-4']
    
    for idx, course in enumerate(courses):
        day = days[idx % len(days)]
        time = times[idx % len(times)]
        hall = halls[idx % len(halls)]
        
        exam_slots.append({
            'id': f'EXAM{idx+1:03d}',
            'course': course['id'],
            'course_name': course['name'],
            'date': day,
            'time': time,
            'hall': hall['id'],
            'hall_name': hall['name'],
            'duration': '2 hours'
        })
    
    return jsonify({
        'message': 'Exam schedule generated',
        'exams': exam_slots
    }), 200

# ==================== TIMETABLE MANAGEMENT ====================

@admin_bp.route('/timetable/generate', methods=['POST'])
@token_required
def generate_timetable(payload):
    """Generate class timetable."""
    data = request.json
    courses = list(db.courses.find({}, {'_id': 0}))
    halls = list(db.halls.find({}, {'_id': 0}))
    
    if not courses or not halls:
        return jsonify({'error': 'Need courses and halls to generate timetable'}), 400
    
    room_names = [h['name'] for h in halls]
    days = data.get('days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    slots = data.get('slots', ['8-9', '9-10', '10-11', '11-12', '12-1', '2-3', '3-4', '4-5'])
    
    scheduler = GeneticScheduler(courses, room_names, days, slots)
    best_schedule, fitness = scheduler.evolve()
    
    # Save timetable
    db.timetables.insert_one({
        'schedule': best_schedule,
        'fitness_score': fitness,
        'generated_at': datetime.utcnow().isoformat(),
        'generated_by': payload.get('username', 'admin')
    })
    
    return jsonify({
        'message': 'Timetable generated successfully',
        'schedule': best_schedule,
        'fitness_score': fitness
    }), 200

@admin_bp.route('/timetable/latest', methods=['GET'])
@token_required
def get_latest_timetable(payload):
    """Get latest timetable."""
    timetable = db.timetables.find_one(sort=[('_id', -1)], projection={'_id': 0})
    
    if not timetable:
        return jsonify({'message': 'No timetable found'}), 404
    
    return jsonify(timetable), 200

@admin_bp.route('/timetable', methods=['DELETE'])
@token_required
def delete_timetable(payload):
    """Delete all timetables."""
    result = db.timetables.delete_many({})
    return jsonify({
        'message': f'Deleted {result.deleted_count} timetables'
    }), 200

# ==================== STATISTICS ====================

@admin_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(payload):
    """Get system statistics."""
    stats = {
        'courses': db.courses.count_documents({}),
        'lecturers': db.lecturers.count_documents({}),
        'halls': db.halls.count_documents({}),
        'exams': db.exams.count_documents({}),
        'timetables': db.timetables.count_documents({}),
        'users': db.users.count_documents({})
    }
    return jsonify(stats), 200