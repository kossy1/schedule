from flask import Blueprint, request, jsonify
from datetime import datetime
from .database import db
from .auth import token_required
from .scheduler import GeneticScheduler
import re

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============================================================
# AUTHENTICATION
# ============================================================

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

@admin_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(payload):
    """Get system statistics."""
    stats = {
        'departments': db.departments.count_documents({}),
        'lecturers': db.lecturers.count_documents({}),
        'students': db.students.count_documents({}),
        'courses': db.courses.count_documents({}),
        'halls': db.halls.count_documents({}),
        'exams': db.exams.count_documents({}),
        'timetables': db.timetables.count_documents({}),
        'users': db.users.count_documents({})
    }
    return jsonify(stats), 200

# ============================================================
# DEPARTMENTS CRUD
# ============================================================

@admin_bp.route('/departments', methods=['GET'])
@token_required
def get_departments(payload):
    """Get all departments."""
    departments = list(db.departments.find({}, {'_id': 0}))
    return jsonify(departments), 200

@admin_bp.route('/departments', methods=['POST'])
@token_required
def add_department(payload):
    """Add a new department."""
    data = request.json
    required = ['id', 'name', 'code']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    if db.departments.find_one({'id': data['id']}):
        return jsonify({'error': f'Department {data["id"]} already exists'}), 400
    
    db.departments.insert_one({
        'id': data['id'],
        'name': data['name'],
        'code': data['code'].upper(),
        'head': data.get('head', ''),
        'created_at': datetime.utcnow().isoformat()
    })
    return jsonify({'message': 'Department added successfully'}), 201

@admin_bp.route('/departments/<dept_id>', methods=['PUT'])
@token_required
def update_department(payload, dept_id):
    """Update a department."""
    data = request.json
    result = db.departments.update_one(
        {'id': dept_id}, 
        {'$set': {
            'name': data.get('name'),
            'code': data.get('code', '').upper(),
            'head': data.get('head', ''),
            'updated_at': datetime.utcnow().isoformat()
        }}
    )
    
    if result.matched_count == 0:
        return jsonify({'error': 'Department not found'}), 404
    
    return jsonify({'message': 'Department updated successfully'}), 200

@admin_bp.route('/departments/<dept_id>', methods=['DELETE'])
@token_required
def delete_department(payload, dept_id):
    """Delete a department."""
    result = db.departments.delete_one({'id': dept_id})
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Department not found'}), 404
    
    return jsonify({'message': 'Department deleted successfully'}), 200

# ============================================================
# LECTURERS CRUD
# ============================================================

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
    required = ['id', 'name', 'surname', 'department', 'email']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    if db.lecturers.find_one({'id': data['id']}):
        return jsonify({'error': f'Lecturer {data["id"]} already exists'}), 400
    
    db.lecturers.insert_one({
        'id': data['id'],
        'name': data['name'],
        'surname': data['surname'],
        'department': data['department'],
        'email': data['email'],
        'phone': data.get('phone', ''),
        'created_at': datetime.utcnow().isoformat()
    })
    return jsonify({'message': 'Lecturer added successfully'}), 201

@admin_bp.route('/lecturers/<lecturer_id>', methods=['PUT'])
@token_required
def update_lecturer(payload, lecturer_id):
    """Update a lecturer."""
    data = request.json
    result = db.lecturers.update_one(
        {'id': lecturer_id},
        {'$set': {
            'name': data.get('name'),
            'surname': data.get('surname'),
            'department': data.get('department'),
            'email': data.get('email'),
            'phone': data.get('phone', ''),
            'updated_at': datetime.utcnow().isoformat()
        }}
    )
    
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

# ============================================================
# STUDENTS CRUD (Updated with Matric Number)
# ============================================================

@admin_bp.route('/students', methods=['GET'])
@token_required
def get_students(payload):
    """Get all students."""
    students = list(db.students.find({}, {'_id': 0}))
    return jsonify(students), 200

@admin_bp.route('/students', methods=['POST'])
@token_required
def add_student(payload):
    """Add a new student with matric number."""
    data = request.json
    required = ['matric', 'name', 'surname', 'department', 'level']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    # Validate matric number format
    matric = data['matric'].strip().upper()
    if not re.match(r'^HND\/[A-Z]{3}\/\d{4}\/\d{3}$', matric):
        return jsonify({'error': 'Invalid matric number format. Use: HND/DEPT/YEAR/XXX (e.g., HND/CSC/2024/001)'}), 400
    
    # Check if student exists
    if db.students.find_one({'matric': matric}):
        return jsonify({'error': f'Student with matric {matric} already exists'}), 400
    
    db.students.insert_one({
        'matric': matric,
        'name': data['name'],
        'surname': data['surname'],
        'department': data['department'],
        'level': data['level'],
        'email': data.get('email', ''),
        'phone': data.get('phone', ''),
        'created_at': datetime.utcnow().isoformat()
    })
    return jsonify({'message': 'Student added successfully'}), 201

@admin_bp.route('/students/<matric>', methods=['PUT'])
@token_required
def update_student(payload, matric):
    """Update a student by matric number."""
    data = request.json
    matric = matric.upper()
    
    # Validate matric format if provided
    if 'matric' in data:
        new_matric = data['matric'].strip().upper()
        if not re.match(r'^HND\/[A-Z]{3}\/\d{4}\/\d{3}$', new_matric):
            return jsonify({'error': 'Invalid matric number format'}), 400
        # Check if new matric already exists
        if new_matric != matric and db.students.find_one({'matric': new_matric}):
            return jsonify({'error': f'Student with matric {new_matric} already exists'}), 400
    
    update_data = {
        'name': data.get('name'),
        'surname': data.get('surname'),
        'department': data.get('department'),
        'level': data.get('level'),
        'email': data.get('email', ''),
        'phone': data.get('phone', ''),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # If matric is being updated
    if 'matric' in data and data['matric'].strip().upper() != matric:
        update_data['matric'] = data['matric'].strip().upper()
    
    result = db.students.update_one(
        {'matric': matric},
        {'$set': update_data}
    )
    
    if result.matched_count == 0:
        return jsonify({'error': 'Student not found'}), 404
    
    return jsonify({'message': 'Student updated successfully'}), 200

@admin_bp.route('/students/<matric>', methods=['DELETE'])
@token_required
def delete_student(payload, matric):
    """Delete a student by matric number."""
    result = db.students.delete_one({'matric': matric.upper()})
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Student not found'}), 404
    
    return jsonify({'message': 'Student deleted successfully'}), 200

# ============================================================
# STUDENT LOGIN (Matric + Surname)
# ============================================================

@admin_bp.route('/timetable/student/login', methods=['POST'])
def student_login():
    """Student login with matric number and surname."""
    data = request.json
    matric = data.get('matric', '').strip().upper()
    surname = data.get('surname', '').strip().title()
    
    if not matric or not surname:
        return jsonify({'error': 'Matric number and surname required'}), 400
    
    # Validate matric format
    if not re.match(r'^HND\/[A-Z]{3}\/\d{4}\/\d{3}$', matric):
        return jsonify({'error': 'Invalid matric number format'}), 400
    
    # Find student by matric number
    student = db.students.find_one(
        {'matric': matric}, 
        {'_id': 0}
    )
    
    if not student:
        return jsonify({'error': 'Student not found. Please check your matric number.'}), 404
    
    # Verify surname (case-insensitive)
    if student.get('surname', '').upper() != surname.upper():
        return jsonify({'error': 'Invalid surname. Please check and try again.'}), 401
    
    return jsonify({
        'student': student,
        'message': 'Login successful'
    }), 200

# ============================================================
# STUDENT TIMETABLE VIEW
# ============================================================

@admin_bp.route('/timetable/student/<matric>', methods=['GET'])
def get_student_timetable(matric):
    """Get timetable for a specific student by matric number."""
    # Find student
    student = db.students.find_one({'matric': matric.upper()}, {'_id': 0})
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Get latest timetable
    timetable = db.timetables.find_one(sort=[('_id', -1)], projection={'_id': 0})
    
    if not timetable:
        return jsonify({'error': 'No timetable found'}), 404
    
    # For demo, return all schedule
    # In production, filter by student's enrolled courses
    return jsonify({
        'student': student,
        'schedule': timetable.get('schedule', []),
        'fitness_score': timetable.get('fitness_score', 0),
        'generated_at': timetable.get('generated_at')
    }), 200

# ============================================================
# LECTURER LOGIN (Staff ID + Surname)
# ============================================================

@admin_bp.route('/timetable/lecturer/login', methods=['POST'])
def lecturer_login():
    """Lecturer login with staff ID and surname."""
    data = request.json
    staff_id = data.get('staff_id', '').strip().upper()
    surname = data.get('surname', '').strip().title()
    
    if not staff_id or not surname:
        return jsonify({'error': 'Staff ID and surname required'}), 400
    
    # Find lecturer by staff ID
    lecturer = db.lecturers.find_one(
        {'id': staff_id}, 
        {'_id': 0}
    )
    
    if not lecturer:
        return jsonify({'error': 'Lecturer not found. Please check your staff ID.'}), 404
    
    # Verify surname (case-insensitive)
    if lecturer.get('surname', '').upper() != surname.upper():
        return jsonify({'error': 'Invalid surname. Please check and try again.'}), 401
    
    return jsonify({
        'lecturer': lecturer,
        'message': 'Login successful'
    }), 200

# ============================================================
# LECTURER TIMETABLE VIEW
# ============================================================

@admin_bp.route('/timetable/lecturer/<staff_id>', methods=['GET'])
def get_lecturer_timetable(staff_id):
    """Get timetable for a specific lecturer by staff ID."""
    # Find lecturer
    lecturer = db.lecturers.find_one({'id': staff_id.upper()}, {'_id': 0})
    if not lecturer:
        return jsonify({'error': 'Lecturer not found'}), 404
    
    # Get latest timetable
    timetable = db.timetables.find_one(sort=[('_id', -1)], projection={'_id': 0})
    
    if not timetable:
        return jsonify({'error': 'No timetable found'}), 404
    
    # Filter schedule for this lecturer
    lecturer_name = lecturer.get('name', '')
    filtered_schedule = []
    
    for item in timetable.get('schedule', []):
        if item.get('lecturer') == lecturer_name:
            filtered_schedule.append(item)
    
    return jsonify({
        'lecturer': lecturer,
        'schedule': filtered_schedule,
        'fitness_score': timetable.get('fitness_score', 0),
        'generated_at': timetable.get('generated_at')
    }), 200

# ============================================================
# COURSES CRUD
# ============================================================

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
    required = ['code', 'name', 'department', 'lecturer', 'credits', 'semester']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    if db.courses.find_one({'code': data['code']}):
        return jsonify({'error': f'Course {data["code"]} already exists'}), 400
    
    # Get department code
    dept = db.departments.find_one({'id': data['department']})
    dept_code = dept['code'] if dept else data['department'][:3].upper()
    
    db.courses.insert_one({
        'code': data['code'],
        'name': data['name'],
        'department': data['department'],
        'department_code': dept_code,
        'lecturer': data['lecturer'],
        'credits': data['credits'],
        'semester': data['semester'],
        'created_at': datetime.utcnow().isoformat()
    })
    return jsonify({'message': 'Course added successfully'}), 201

@admin_bp.route('/courses/<course_code>', methods=['PUT'])
@token_required
def update_course(payload, course_code):
    """Update a course."""
    data = request.json
    result = db.courses.update_one(
        {'code': course_code},
        {'$set': {
            'name': data.get('name'),
            'department': data.get('department'),
            'lecturer': data.get('lecturer'),
            'credits': data.get('credits'),
            'semester': data.get('semester'),
            'updated_at': datetime.utcnow().isoformat()
        }}
    )
    
    if result.matched_count == 0:
        return jsonify({'error': 'Course not found'}), 404
    
    return jsonify({'message': 'Course updated successfully'}), 200

@admin_bp.route('/courses/<course_code>', methods=['DELETE'])
@token_required
def delete_course(payload, course_code):
    """Delete a course."""
    result = db.courses.delete_one({'code': course_code})
    
    if result.deleted_count == 0:
        return jsonify({'error': 'Course not found'}), 404
    
    return jsonify({'message': 'Course deleted successfully'}), 200

# ============================================================
# HALLS CRUD
# ============================================================

@admin_bp.route('/halls', methods=['GET'])
@token_required
def get_halls(payload):
    """Get all halls."""
    halls = list(db.halls.find({}, {'_id': 0}))
    return jsonify(halls), 200

@admin_bp.route('/halls', methods=['POST'])
@token_required
def add_hall(payload):
    """Add a new hall."""
    data = request.json
    required = ['id', 'name', 'capacity', 'type']
    
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400
    
    if db.halls.find_one({'id': data['id']}):
        return jsonify({'error': f'Hall {data["id"]} already exists'}), 400
    
    db.halls.insert_one({
        'id': data['id'],
        'name': data['name'],
        'capacity': data['capacity'],
        'type': data['type'],
        'location': data.get('location', ''),
        'created_at': datetime.utcnow().isoformat()
    })
    return jsonify({'message': 'Hall added successfully'}), 201

@admin_bp.route('/halls/<hall_id>', methods=['PUT'])
@token_required
def update_hall(payload, hall_id):
    """Update a hall."""
    data = request.json
    result = db.halls.update_one(
        {'id': hall_id},
        {'$set': {
            'name': data.get('name'),
            'capacity': data.get('capacity'),
            'type': data.get('type'),
            'location': data.get('location', ''),
            'updated_at': datetime.utcnow().isoformat()
        }}
    )
    
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

# ============================================================
# EXAMS CRUD
# ============================================================

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
    required = ['id', 'course', 'date', 'time', 'hall']
    
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
    
    db.exams.insert_one({
        'id': data['id'],
        'course': data['course'],
        'date': data['date'],
        'time': data['time'],
        'hall': data['hall'],
        'duration': data.get('duration', '2 hours'),
        'created_at': datetime.utcnow().isoformat()
    })
    return jsonify({'message': 'Exam added successfully'}), 201

@admin_bp.route('/exams/<exam_id>', methods=['PUT'])
@token_required
def update_exam(payload, exam_id):
    """Update an exam."""
    data = request.json
    result = db.exams.update_one(
        {'id': exam_id},
        {'$set': {
            'course': data.get('course'),
            'date': data.get('date'),
            'time': data.get('time'),
            'hall': data.get('hall'),
            'duration': data.get('duration', '2 hours'),
            'updated_at': datetime.utcnow().isoformat()
        }}
    )
    
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
    """Generate exam schedule automatically."""
    courses = list(db.courses.find({}, {'_id': 0}))
    halls = list(db.halls.find({}, {'_id': 0}))
    
    if not courses or not halls:
        return jsonify({'error': 'Need courses and halls to generate exam schedule'}), 400
    
    # Clear existing exams
    db.exams.delete_many({})
    
    # Generate exam schedule
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    times = ['9-11', '11-1', '2-4']
    
    exam_slots = []
    idx = 0
    for course in courses:
        day = days[idx % len(days)]
        time = times[idx % len(times)]
        hall = halls[idx % len(halls)]
        
        exam_slots.append({
            'id': f'EXAM{idx+1:03d}',
            'course': course['code'],
            'date': day,
            'time': time,
            'hall': hall['id'],
            'duration': '2 hours'
        })
        idx += 1
    
    # Insert all exams
    if exam_slots:
        db.exams.insert_many(exam_slots)
    
    return jsonify({
        'message': f'Generated {len(exam_slots)} exam slots',
        'exams': exam_slots
    }), 200

# ============================================================
# CLASS TIMETABLE
# ============================================================

@admin_bp.route('/timetable/latest', methods=['GET'])
@token_required
def get_latest_timetable(payload):
    """Get the latest generated timetable."""
    timetable = db.timetables.find_one(
        sort=[('_id', -1)], 
        projection={'_id': 0}
    )
    
    if not timetable:
        return jsonify({'error': 'No timetable found'}), 404
    
    return jsonify(timetable), 200

@admin_bp.route('/timetable/generate', methods=['POST'])
@token_required
def generate_timetable(payload):
    """Generate class timetable using genetic algorithm."""
    data = request.json
    courses = list(db.courses.find({}, {'_id': 0}))
    halls = list(db.halls.find({}, {'_id': 0}))
    
    if not courses or not halls:
        return jsonify({'error': 'Need courses and halls to generate timetable'}), 400
    
    room_names = [h['name'] for h in halls]
    days = data.get('days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
    slots = data.get('slots', ['8-9', '9-10', '10-11', '11-12', '12-1', '2-3', '3-4', '4-5'])
    
    # Convert courses to format expected by scheduler
    course_data = []
    for c in courses:
        course_data.append({
            'id': c['code'],
            'name': c['name'],
            'lecturer': c.get('lecturer', 'Unknown'),
            'semester': c.get('semester', 1)
        })
    
    scheduler = GeneticScheduler(course_data, room_names, days, slots)
    best_schedule, fitness = scheduler.evolve()
    
    # Save timetable
    timetable_data = {
        'schedule': best_schedule,
        'fitness_score': fitness,
        'generated_at': datetime.utcnow().isoformat(),
        'generated_by': payload.get('username', 'admin')
    }
    db.timetables.insert_one(timetable_data)
    
    return jsonify({
        'message': 'Timetable generated successfully',
        'schedule': best_schedule,
        'fitness_score': fitness,
        'generated_at': timetable_data['generated_at']
    }), 200

@admin_bp.route('/timetable', methods=['DELETE'])
@token_required
def delete_timetable(payload):
    """Delete all timetables."""
    result = db.timetables.delete_many({})
    return jsonify({
        'message': f'Deleted {result.deleted_count} timetables'
    }), 200

# ============================================================
# PUBLIC TIMETABLE VIEW (No Auth Required)
# ============================================================

@admin_bp.route('/timetable/public', methods=['GET'])
def get_public_timetable():
    """Get the latest timetable (public access)."""
    timetable = db.timetables.find_one(sort=[('_id', -1)], projection={'_id': 0})
    
    if not timetable:
        return jsonify({'error': 'No timetable found'}), 404
    
    return jsonify({
        'schedule': timetable.get('schedule', []),
        'fitness_score': timetable.get('fitness_score', 0),
        'generated_at': timetable.get('generated_at')
    }), 200

# ============================================================
# STUDENT ENROLLMENT (Assign Courses to Student)
# ============================================================

@admin_bp.route('/students/<matric>/enroll', methods=['POST'])
@token_required
def enroll_student(payload, matric):
    """Enroll a student in courses."""
    data = request.json
    courses = data.get('courses', [])
    
    if not courses:
        return jsonify({'error': 'No courses provided'}), 400
    
    result = db.students.update_one(
        {'matric': matric.upper()},
        {'$set': {
            'courses': courses,
            'updated_at': datetime.utcnow().isoformat()
        }}
    )
    
    if result.matched_count == 0:
        return jsonify({'error': 'Student not found'}), 404
    
    return jsonify({
        'message': f'Student enrolled in {len(courses)} courses',
        'courses': courses
    }), 200

@admin_bp.route('/students/<matric>/courses', methods=['GET'])
def get_student_courses(matric):
    """Get courses enrolled by a student."""
    student = db.students.find_one({'matric': matric.upper()}, {'_id': 0})
    
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    return jsonify({
        'matric': student['matric'],
        'name': student['name'],
        'courses': student.get('courses', [])
    }), 200