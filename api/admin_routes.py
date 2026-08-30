from flask import Blueprint, request, jsonify
from datetime import datetime
from .database import db
from .auth import token_required
import re
import random
import traceback

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============================================================
# CONSTANTS
# ============================================================

VALID_LEVELS = ['ND1', 'ND2', 'HND1', 'HND2']

# ============================================================
# AUTHENTICATION
# ============================================================

@admin_bp.route('/login', methods=['POST'])
def login():
    """Admin login endpoint."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
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
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(payload):
    """Verify token validity."""
    return jsonify({'valid': True, 'user': payload}), 200

# ============================================================
# TOKEN REFRESH
# ============================================================

@admin_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token(payload):
    """Refresh the JWT token."""
    try:
        from .auth import generate_token
        user_id = payload.get('user_id')
        username = payload.get('username')
        
        if not user_id or not username:
            return jsonify({'error': 'Invalid token payload'}), 400
        
        new_token = generate_token(user_id, username)
        return jsonify({
            'token': new_token,
            'message': 'Token refreshed successfully'
        }), 200
    except Exception as e:
        print(f"❌ Token refresh error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# TEST ENDPOINT
# ============================================================

@admin_bp.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify API is working."""
    try:
        return jsonify({
            'status': 'ok',
            'message': 'API is working',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# STATS
# ============================================================

@admin_bp.route('/stats', methods=['GET'])
@token_required
def get_stats(payload):
    """Get system statistics."""
    try:
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
        print(f"📊 Stats: {stats}")
        return jsonify(stats), 200
    except Exception as e:
        print(f"❌ Stats error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================================
# DEPARTMENTS CRUD
# ============================================================

@admin_bp.route('/departments', methods=['GET'])
@token_required
def get_departments(payload):
    """Get all departments."""
    try:
        departments = list(db.departments.find({}, {'_id': 0}))
        return jsonify(departments), 200
    except Exception as e:
        print(f"❌ Get departments error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments', methods=['POST'])
@token_required
def add_department(payload):
    """Add a new department."""
    try:
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
    except Exception as e:
        print(f"❌ Add department error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments/<dept_id>', methods=['PUT'])
@token_required
def update_department(payload, dept_id):
    """Update a department."""
    try:
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
    except Exception as e:
        print(f"❌ Update department error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments/<dept_id>', methods=['DELETE'])
@token_required
def delete_department(payload, dept_id):
    """Delete a department."""
    try:
        result = db.departments.delete_one({'id': dept_id})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Department not found'}), 404
        
        return jsonify({'message': 'Department deleted successfully'}), 200
    except Exception as e:
        print(f"❌ Delete department error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# LECTURERS CRUD
# ============================================================

@admin_bp.route('/lecturers', methods=['GET'])
@token_required
def get_lecturers(payload):
    """Get all lecturers."""
    try:
        lecturers = list(db.lecturers.find({}, {'_id': 0}))
        return jsonify(lecturers), 200
    except Exception as e:
        print(f"❌ Get lecturers error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/lecturers', methods=['POST'])
@token_required
def add_lecturer(payload):
    """Add a new lecturer."""
    try:
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
    except Exception as e:
        print(f"❌ Add lecturer error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/lecturers/<lecturer_id>', methods=['PUT'])
@token_required
def update_lecturer(payload, lecturer_id):
    """Update a lecturer."""
    try:
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
    except Exception as e:
        print(f"❌ Update lecturer error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/lecturers/<lecturer_id>', methods=['DELETE'])
@token_required
def delete_lecturer(payload, lecturer_id):
    """Delete a lecturer."""
    try:
        result = db.lecturers.delete_one({'id': lecturer_id})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Lecturer not found'}), 404
        
        return jsonify({'message': 'Lecturer deleted successfully'}), 200
    except Exception as e:
        print(f"❌ Delete lecturer error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# STUDENTS CRUD
# ============================================================

@admin_bp.route('/students', methods=['GET'])
@token_required
def get_students(payload):
    """Get all students."""
    try:
        students = list(db.students.find({}, {'_id': 0}))
        return jsonify(students), 200
    except Exception as e:
        print(f"❌ Get students error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/students', methods=['POST'])
@token_required
def add_student(payload):
    """Add a new student with matric number (numbers only) and polytechnic level."""
    try:
        data = request.json
        required = ['matric', 'name', 'surname', 'department', 'level']
        
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        # Validate matric number - numbers only
        matric = data['matric'].strip()
        if not matric.isdigit():
            return jsonify({'error': 'Matric number must contain only numbers (no letters or special characters)'}), 400
        
        # Validate level - must be ND1, ND2, HND1, or HND2
        if data['level'] not in VALID_LEVELS:
            return jsonify({'error': f'Invalid level. Must be one of: {", ".join(VALID_LEVELS)}'}), 400
        
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
    except Exception as e:
        print(f"❌ Add student error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/students/<matric>', methods=['PUT'])
@token_required
def update_student(payload, matric):
    """Update a student by matric number."""
    try:
        data = request.json
        matric = matric.strip()
        
        # Validate matric format if provided
        if 'matric' in data:
            new_matric = data['matric'].strip()
            if not new_matric.isdigit():
                return jsonify({'error': 'Matric number must contain only numbers'}), 400
            # Check if new matric already exists
            if new_matric != matric and db.students.find_one({'matric': new_matric}):
                return jsonify({'error': f'Student with matric {new_matric} already exists'}), 400
        
        # Validate level if provided
        if 'level' in data and data['level'] not in VALID_LEVELS:
            return jsonify({'error': f'Invalid level. Must be one of: {", ".join(VALID_LEVELS)}'}), 400
        
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
        if 'matric' in data and data['matric'].strip() != matric:
            update_data['matric'] = data['matric'].strip()
        
        result = db.students.update_one(
            {'matric': matric},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify({'message': 'Student updated successfully'}), 200
    except Exception as e:
        print(f"❌ Update student error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/students/<matric>', methods=['DELETE'])
@token_required
def delete_student(payload, matric):
    """Delete a student by matric number."""
    try:
        result = db.students.delete_one({'matric': matric.strip()})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify({'message': 'Student deleted successfully'}), 200
    except Exception as e:
        print(f"❌ Delete student error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# STUDENT LOGIN
# ============================================================

@admin_bp.route('/timetable/student/login', methods=['POST'])
def student_login():
    """Student login with matric number (numbers only) and surname."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        matric = data.get('matric', '').strip()
        surname = data.get('surname', '').strip().title()
        
        if not matric or not surname:
            return jsonify({'error': 'Matric number and surname are required'}), 400
        
        # Validate matric - numbers only
        if not matric.isdigit():
            return jsonify({'error': 'Matric number must contain only numbers (no letters or special characters)'}), 400
        
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
        
    except Exception as e:
        print(f"❌ Student login error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# STUDENT TIMETABLE VIEW
# ============================================================

@admin_bp.route('/timetable/student/<matric>', methods=['GET'])
def get_student_timetable(matric):
    """Get timetable for a specific student by matric number."""
    try:
        matric = matric.strip()
        
        # Validate matric - numbers only
        if not matric.isdigit():
            return jsonify({'error': 'Matric number must contain only numbers'}), 400
        
        # Find student
        student = db.students.find_one({'matric': matric}, {'_id': 0})
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Get latest timetable
        timetable = db.timetables.find_one(sort=[('_id', -1)], projection={'_id': 0})
        
        if not timetable:
            return jsonify({'error': 'No timetable found'}), 404
        
        return jsonify({
            'student': student,
            'schedule': timetable.get('schedule', []),
            'fitness_score': timetable.get('fitness_score', 0),
            'semester': timetable.get('semester', 1),
            'generated_at': timetable.get('generated_at')
        }), 200
        
    except Exception as e:
        print(f"❌ Student timetable error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# LECTURER LOGIN
# ============================================================

@admin_bp.route('/timetable/lecturer/login', methods=['POST'])
def lecturer_login():
    """Lecturer login with staff ID and surname."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        staff_id = data.get('staff_id', '').strip().upper()
        surname = data.get('surname', '').strip().title()
        
        if not staff_id or not surname:
            return jsonify({'error': 'Staff ID and surname required'}), 400
        
        # Validate staff ID format
        if not re.match(r'^LEC-\d{3}$', staff_id):
            return jsonify({'error': 'Invalid staff ID format. Use: LEC-001, LEC-002, etc.'}), 400
        
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
        
    except Exception as e:
        print(f"❌ Lecturer login error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# LECTURER TIMETABLE VIEW
# ============================================================

@admin_bp.route('/timetable/lecturer/<staff_id>', methods=['GET'])
def get_lecturer_timetable(staff_id):
    """Get timetable for a specific lecturer by staff ID."""
    try:
        staff_id = staff_id.strip().upper()
        
        # Find lecturer
        lecturer = db.lecturers.find_one({'id': staff_id}, {'_id': 0})
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
            'semester': timetable.get('semester', 1),
            'generated_at': timetable.get('generated_at')
        }), 200
        
    except Exception as e:
        print(f"❌ Lecturer timetable error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# COURSES CRUD - FIXED SYNTAX ERROR
# ============================================================

@admin_bp.route('/courses', methods=['GET'])
@token_required
def get_courses(payload):
    """Get all courses."""
    try:
        courses = list(db.courses.find({}, {'_id': 0}))
        return jsonify(courses), 200
    except Exception as e:
        print(f"❌ Get courses error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/courses', methods=['POST'])
@token_required
def add_course(payload):
    """Add a new course with manual code entry."""
    try:
        data = request.json
        required = ['code', 'name', 'department', 'level', 'lecturer', 'credits', 'semester']
        
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing required fields: {required}'}), 400
        
        # Validate level
        if data['level'] not in VALID_LEVELS:
            return jsonify({'error': f'Invalid level. Must be one of: {", ".join(VALID_LEVELS)}'}), 400
        
        # Check if course exists
        if db.courses.find_one({'code': data['code']}):
            return jsonify({'error': f'Course {data["code"]} already exists'}), 400
        
        db.courses.insert_one({
            'code': data['code'],
            'name': data['name'],
            'department': data['department'],
            'level': data['level'],
            'lecturer': data['lecturer'],
            'credits': data['credits'],
            'semester': data['semester'],
            'created_at': datetime.utcnow().isoformat()
        })
        return jsonify({'message': 'Course added successfully'}), 201
    except Exception as e:
        print(f"❌ Add course error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/courses/<course_code>', methods=['PUT'])
@token_required
def update_course(payload, course_code):
    """Update a course - allows changing the course code."""
    try:
        data = request.json
        
        # Validate level if provided
        if 'level' in data and data['level'] not in VALID_LEVELS:
            return jsonify({'error': f'Invalid level. Must be one of: {", ".join(VALID_LEVELS)}'}), 400
        
        # If course code is being changed, check if the new code already exists
        if 'code' in data and data['code'] != course_code:
            if db.courses.find_one({'code': data['code']}):
                return jsonify({'error': f'Course {data["code"]} already exists'}), 400
        
        update_data = {
            'code': data.get('code', course_code),
            'name': data.get('name'),
            'department': data.get('department'),
            'level': data.get('level'),
            'lecturer': data.get('lecturer'),
            'credits': data.get('credits'),
            'semester': data.get('semester'),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = db.courses.update_one(
            {'code': course_code},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify({'message': 'Course updated successfully'}), 200
    except Exception as e:
        print(f"❌ Update course error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/courses/<course_code>', methods=['DELETE'])
@token_required
def delete_course(payload, course_code):
    """Delete a course."""
    try:
        result = db.courses.delete_one({'code': course_code})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify({'message': 'Course deleted successfully'}), 200
    except Exception as e:
        print(f"❌ Delete course error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# HALLS CRUD
# ============================================================

@admin_bp.route('/halls', methods=['GET'])
@token_required
def get_halls(payload):
    """Get all halls."""
    try:
        halls = list(db.halls.find({}, {'_id': 0}))
        return jsonify(halls), 200
    except Exception as e:
        print(f"❌ Get halls error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/halls', methods=['POST'])
@token_required
def add_hall(payload):
    """Add a new hall."""
    try:
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
    except Exception as e:
        print(f"❌ Add hall error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/halls/<hall_id>', methods=['PUT'])
@token_required
def update_hall(payload, hall_id):
    """Update a hall."""
    try:
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
    except Exception as e:
        print(f"❌ Update hall error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/halls/<hall_id>', methods=['DELETE'])
@token_required
def delete_hall(payload, hall_id):
    """Delete a hall."""
    try:
        result = db.halls.delete_one({'id': hall_id})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Hall not found'}), 404
        
        return jsonify({'message': 'Hall deleted successfully'}), 200
    except Exception as e:
        print(f"❌ Delete hall error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# EXAMS CRUD
# ============================================================

@admin_bp.route('/exams', methods=['GET'])
@token_required
def get_exams(payload):
    """Get all exams."""
    try:
        exams = list(db.exams.find({}, {'_id': 0}))
        return jsonify(exams), 200
    except Exception as e:
        print(f"❌ Get exams error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/exams', methods=['POST'])
@token_required
def add_exam(payload):
    """Add a new exam."""
    try:
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
    except Exception as e:
        print(f"❌ Add exam error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/exams/<exam_id>', methods=['PUT'])
@token_required
def update_exam(payload, exam_id):
    """Update an exam."""
    try:
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
    except Exception as e:
        print(f"❌ Update exam error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/exams/<exam_id>', methods=['DELETE'])
@token_required
def delete_exam(payload, exam_id):
    """Delete an exam."""
    try:
        result = db.exams.delete_one({'id': exam_id})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Exam not found'}), 404
        
        return jsonify({'message': 'Exam deleted successfully'}), 200
    except Exception as e:
        print(f"❌ Delete exam error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/exams/generate', methods=['POST'])
@token_required
def generate_exam_schedule(payload):
    """Generate exam schedule automatically."""
    try:
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
                'course': course.get('code', course.get('id', f'COURSE{idx+1}')),
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
    except Exception as e:
        print(f"❌ Generate exams error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# CLASS TIMETABLE WITH LEVEL
# ============================================================

@admin_bp.route('/timetable/latest', methods=['GET'])
@token_required
def get_latest_timetable(payload):
    """Get the latest generated timetable."""
    try:
        timetable = db.timetables.find_one(
            sort=[('_id', -1)], 
            projection={'_id': 0}
        )
        
        if not timetable:
            return jsonify({'error': 'No timetable found'}), 404
        
        return jsonify(timetable), 200
    except Exception as e:
        print(f"❌ Get latest timetable error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/timetable/by-semester/<semester>', methods=['GET'])
@token_required
def get_timetable_by_semester(payload, semester):
    """Get timetable by semester."""
    try:
        semester = int(semester)
        timetable = db.timetables.find_one(
            {'semester': semester},
            sort=[('_id', -1)], 
            projection={'_id': 0}
        )
        
        if not timetable:
            return jsonify({'error': f'No timetable found for Semester {semester}'}), 404
        
        return jsonify(timetable), 200
    except Exception as e:
        print(f"❌ Get timetable by semester error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/timetable/generate', methods=['POST'])
@token_required
def generate_timetable(payload):
    """Generate class timetable for a specific semester with 2-hour slots and level."""
    try:
        data = request.json or {}
        
        # Get semester from request
        semester = data.get('semester', 1)
        if semester not in [1, 2]:
            return jsonify({'error': 'Invalid semester. Must be 1 or 2'}), 400
        
        # Get courses for the specified semester
        courses = list(db.courses.find({'semester': semester}, {'_id': 0}))
        halls = list(db.halls.find({}, {'_id': 0}))
        
        print(f"📚 Found {len(courses)} courses for Semester {semester}, {len(halls)} halls")
        
        if not courses:
            return jsonify({'error': f'No courses found for Semester {semester}. Please add courses first.'}), 400
        
        if not halls:
            return jsonify({'error': 'No halls found. Please add halls first.'}), 400
        
        # Prepare rooms
        room_names = [h['name'] for h in halls]
        days = data.get('days', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
        
        # 2-HOUR TIME SLOTS
        slots = data.get('slots', [
            '8:00 - 10:00',
            '10:00 - 12:00',
            '12:00 - 2:00',
            '2:00 - 4:00',
            '4:00 - 6:00'
        ])
        
        # Convert courses to format expected by scheduler
        course_data = []
        for idx, c in enumerate(courses):
            try:
                # Safe way to get course ID
                course_id = c.get('code') or c.get('id') or f"COURSE_{idx+1}"
                
                # Get course name
                course_name = c.get('name', f'Course {course_id}')
                
                # Get lecturer name
                lecturer_name = c.get('lecturer', 'Unknown')
                
                # If lecturer is an ID, get the name
                if lecturer_name and not lecturer_name.startswith('Dr.') and not lecturer_name.startswith('Prof.'):
                    lecturer = db.lecturers.find_one({'id': lecturer_name})
                    if lecturer:
                        lecturer_name = lecturer.get('name', lecturer_name)
                
                course_data.append({
                    'id': course_id,
                    'name': course_name,
                    'lecturer': lecturer_name,
                    'department': c.get('department', ''),
                    'level': c.get('level', 'ND1'),
                    'semester': semester,
                    'duration': 2
                })
            except Exception as e:
                print(f"⚠️ Error processing course {idx}: {e}")
                course_data.append({
                    'id': f"COURSE_{idx+1}",
                    'name': f"Course {idx+1}",
                    'lecturer': 'Unknown',
                    'department': '',
                    'level': 'ND1',
                    'semester': semester,
                    'duration': 2
                })
        
        print(f"🔄 Processing {len(course_data)} courses for Semester {semester} with 2-hour slots...")
        if course_data:
            print(f"📋 First course: {course_data[0]}")
        
        # Generate timetable with 2-hour slots
        best_schedule = generate_simple_timetable(course_data, room_names, days, slots)
        fitness = calculate_fitness(best_schedule)
        
        print(f"✅ Schedule generated with fitness score: {fitness}")
        print(f"📊 Generated {len(best_schedule)} sessions (2 hours each) for Semester {semester}")
        
        # Save timetable with semester
        timetable_data = {
            'schedule': best_schedule,
            'fitness_score': fitness,
            'semester': semester,
            'generated_at': datetime.utcnow().isoformat(),
            'generated_by': payload.get('username', 'admin'),
            'total_courses': len(course_data),
            'total_sessions': len(best_schedule),
            'slot_duration': '2 hours'
        }
        db.timetables.insert_one(timetable_data)
        
        return jsonify({
            'message': f'Timetable generated successfully for Semester {semester} (2-hour sessions)',
            'schedule': best_schedule,
            'fitness_score': fitness,
            'semester': semester,
            'generated_at': timetable_data['generated_at'],
            'total_sessions': len(best_schedule),
            'slot_duration': '2 hours'
        }), 200
        
    except Exception as e:
        print(f"❌ Error generating timetable: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate timetable: {str(e)}'}), 500

def generate_simple_timetable(courses, rooms, days, slots):
    """Simple timetable generation with 2-hour slots and level."""
    schedule = []
    for i, course in enumerate(courses):
        day_idx = i % len(days)
        slot_idx = (i // len(days)) % len(slots)
        room_idx = (i + slot_idx) % len(rooms)
        
        schedule.append({
            "course": course.get("id", f"COURSE_{i+1}"),
            "course_name": course.get("name", f"Course {i+1}"),
            "lecturer": course.get("lecturer", "Unknown"),
            "department": course.get("department", ""),
            "level": course.get("level", "ND1"),
            "semester": course.get("semester", 1),
            "day": days[day_idx],
            "time": slots[slot_idx],
            "venue": rooms[room_idx],
            "duration": "2 hours"
        })
    return schedule

def calculate_fitness(schedule):
    """Calculate fitness score for a schedule."""
    penalties = 0
    lecturer_schedule = {}
    room_schedule = {}
    
    for entry in schedule:
        lecturer_key = (entry.get("lecturer", ""), entry.get("day", ""), entry.get("time", ""))
        room_key = (entry.get("venue", ""), entry.get("day", ""), entry.get("time", ""))
        
        if lecturer_key in lecturer_schedule:
            penalties += 10
        lecturer_schedule[lecturer_key] = True
        
        if room_key in room_schedule:
            penalties += 10
        room_schedule[room_key] = True
    
    return max(0, 100 - penalties)

@admin_bp.route('/timetable', methods=['DELETE'])
@token_required
def delete_timetable(payload):
    """Delete all timetables."""
    try:
        result = db.timetables.delete_many({})
        return jsonify({
            'message': f'Deleted {result.deleted_count} timetables'
        }), 200
    except Exception as e:
        print(f"❌ Delete timetable error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# PUBLIC TIMETABLE VIEW
# ============================================================

@admin_bp.route('/timetable/public', methods=['GET'])
def get_public_timetable():
    """Get the latest timetable (public access)."""
    try:
        timetable = db.timetables.find_one(sort=[('_id', -1)], projection={'_id': 0})
        
        if not timetable:
            return jsonify({'error': 'No timetable found'}), 404
        
        return jsonify({
            'schedule': timetable.get('schedule', []),
            'fitness_score': timetable.get('fitness_score', 0),
            'semester': timetable.get('semester', 1),
            'generated_at': timetable.get('generated_at')
        }), 200
    except Exception as e:
        print(f"❌ Public timetable error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# STUDENT ENROLLMENT
# ============================================================

@admin_bp.route('/students/<matric>/enroll', methods=['POST'])
@token_required
def enroll_student(payload, matric):
    """Enroll a student in courses."""
    try:
        data = request.json
        courses = data.get('courses', [])
        
        if not courses:
            return jsonify({'error': 'No courses provided'}), 400
        
        result = db.students.update_one(
            {'matric': matric.strip()},
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
    except Exception as e:
        print(f"❌ Enroll student error: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/students/<matric>/courses', methods=['GET'])
def get_student_courses(matric):
    """Get courses enrolled by a student."""
    try:
        student = db.students.find_one({'matric': matric.strip()}, {'_id': 0})
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        return jsonify({
            'matric': student['matric'],
            'name': student['name'],
            'courses': student.get('courses', [])
        }), 200
    except Exception as e:
        print(f"❌ Get student courses error: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================
# DEBUG ENDPOINT
# ============================================================

@admin_bp.route('/debug/courses', methods=['GET'])
@token_required
def debug_courses(payload):
    """Debug endpoint to check course data structure."""
    try:
        courses = list(db.courses.find({}, {'_id': 0}))
        if courses:
            return jsonify({
                'count': len(courses),
                'sample': courses[0] if courses else None,
                'all_fields': list(courses[0].keys()) if courses else []
            }), 200
        else:
            return jsonify({
                'count': 0,
                'message': 'No courses found'
            }), 200
    except Exception as e:
        print(f"❌ Debug courses error: {e}")
        return jsonify({'error': str(e)}), 500