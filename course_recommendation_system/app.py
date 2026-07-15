from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from utils.data_loader import DataLoader
from utils.recommendation_engine import RecommendationEngine
from utils.prolog_integration import PrologIntegration
from utils.test_manager import TestManager
import pandas as pd
import os
import csv
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-in-production'

# ============ SECURITY DECORATORS ============

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session and 'role' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_owns_profile(f):
    """Decorator to check if student is accessing their own profile"""
    @wraps(f)
    def decorated_function(student_id, *args, **kwargs):
        if 'student_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        
        if session.get('role') == 'admin':
            return f(student_id, *args, **kwargs)
        
        if session['student_id'] != student_id:
            flash('Access denied! You can only view your own profile.', 'error')
            return redirect(url_for('student_profile', student_id=session['student_id']))
        
        return f(student_id, *args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ============ END OF SECURITY DECORATORS ============

# Initialize the system
print("Loading course recommendation system...")
loader = DataLoader()
loader.load_all_data()
recommender = RecommendationEngine(loader.students, loader.courses, loader.enrollments)
prolog = PrologIntegration()
test_manager = TestManager()
print("System ready!")

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', 
                         students=loader.students.values(),
                         courses=loader.courses.values())

@app.route('/student/<student_id>')
@login_required
@student_owns_profile
def student_profile(student_id):
    """View student profile and recommendations"""
    if student_id not in loader.students:
        return "Student not found", 404
    
    student = loader.students[student_id]
    
    # Get last test result from session
    last_test_result = session.pop('last_test_result', None)
    
    # Load completed courses
    completed_courses = {}
    completed_file = os.path.join(loader.data_path, 'student_completed_courses.csv')
    if os.path.exists(completed_file):
        with open(completed_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 5 and row[0] == student_id:
                    completed_courses[row[1]] = {
                        'completed_date': row[2],
                        'test_taken': row[3] == 'Yes',
                        'test_passed': row[4] == 'Yes'
                    }
    
    # Get recommendations from Prolog
    prolog_recs = prolog.recommend_courses_prolog(student_id, top_n=5)
    
    # Convert Prolog course IDs to course objects
    prolog_recommendations = []
    for course_id in prolog_recs:
        if course_id in loader.courses:
            course = loader.courses[course_id]
            score = 75
            prolog_recommendations.append({
                'course': course,
                'score': score,
                'reason': 'Recommended by Prolog AI rules based on your profile',
                'predicted_success': recommender.predict_success_rate(student_id, course_id)
            })
    
    # Get regular Python recommendations
    python_recs = recommender.recommend_for_student(student_id, top_n=5)
    
    # Combine both
    all_recommendations = prolog_recommendations + python_recs
    
    # Get performance analysis
    performance = recommender.analyze_performance_trends(student_id)
    
    # Get Prolog performance level
    prolog_level = prolog.get_performance_level_prolog(student_id)
    
    # Get taken courses with completion status
    taken_courses = []
    for enrollment in student.enrolled_courses:
        course = loader.courses[enrollment.course_id]
        completion = completed_courses.get(enrollment.course_id, {})
        taken_courses.append({
            'name': course.name,
            'course_id': course.course_id,
            'grade': enrollment.grade,
            'score': enrollment.exam_score,
            'credits': course.credits,
            'completed': course.course_id in completed_courses,
            'test_taken': completion.get('test_taken', False),
            'test_passed': completion.get('test_passed', False)
        })
    
    return render_template('student.html',
                         student=student,
                         recommendations=all_recommendations[:5],
                         performance=performance,
                         taken_courses=taken_courses,
                         prolog_level=prolog_level,
                         last_test_result=last_test_result)

@app.route('/course/<course_id>')
def course_details(course_id):
    """View course details and similar courses"""
    if course_id not in loader.courses:
        return "Course not found", 404
    
    course = loader.courses[course_id]
    
    # Get similar courses
    similar = recommender.recommend_by_similarity(course_id, top_n=4)
    
    # Get students enrolled in this course
    enrolled_students = []
    for enrollment in loader.enrollments.values():
        if enrollment.course_id == course_id:
            student = loader.students[enrollment.student_id]
            enrolled_students.append({
                'name': student.name,
                'grade': enrollment.grade,
                'score': enrollment.exam_score
            })
    
    # Check if current student is enrolled (if logged in)
    is_enrolled = False
    if 'student_id' in session:
        student_id = session['student_id']
        if student_id in loader.students:
            for enrollment in loader.students[student_id].enrolled_courses:
                if enrollment.course_id == course_id:
                    is_enrolled = True
                    break
    
    return render_template('course.html',
                         course=course,
                         similar_courses=similar,
                         enrolled_students=enrolled_students,
                         is_enrolled=is_enrolled)

@app.route('/complete_course/<course_id>', methods=['POST'])
@login_required
def complete_course(course_id):
    """Mark a course as completed by student"""
    student_id = session['student_id']
    course = loader.courses.get(course_id)
    
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('index'))
    
    completed_file = os.path.join(loader.data_path, 'student_completed_courses.csv')
    already_completed = False
    
    if os.path.exists(completed_file):
        with open(completed_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2 and row[0] == student_id and row[1] == course_id:
                    already_completed = True
                    break
    
    if already_completed:
        flash(f'You have already completed {course.name}!', 'info')
    else:
        file_exists = os.path.exists(completed_file)
        with open(completed_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['student_id', 'course_id', 'completed_date', 'test_taken', 'test_passed'])
            writer.writerow([student_id, course_id, datetime.now().strftime('%Y-%m-%d'), 'No', 'No'])
        
        flash(f'✅ Congratulations! You have completed {course.name}! You can now take the test.', 'success')
    
    return redirect(url_for('course_details', course_id=course_id))

@app.route('/take_test/<course_id>', methods=['GET', 'POST'])
@login_required
def take_test(course_id):
    """Take a test for a course"""
    student_id = session['student_id']
    course = loader.courses.get(course_id)
    
    if not course:
        return "Course not found", 404
    
    if request.method == 'POST':
        # Calculate score based on answers
        total_questions = len(course.questions)
        correct_count = 0
        
        for question in course.questions:
            answer_key = f'q{question["question_id"]}'
            user_answer = request.form.get(answer_key)
            
            if user_answer and user_answer == question['correct_answer']:
                correct_count += 1
        
        score = (correct_count / total_questions) * 100
        passed = score >= 60
        
        # Save result to completed courses file
        completed_file = os.path.join(loader.data_path, 'student_completed_courses.csv')
        rows = []
        
        if os.path.exists(completed_file):
            with open(completed_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2 and not (row[0] == student_id and row[1] == course_id):
                        rows.append(row)
        
        rows.append([student_id, course_id, datetime.now().strftime('%Y-%m-%d'), 'Yes', 'Yes' if passed else 'No'])
        
        with open(completed_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['student_id', 'course_id', 'completed_date', 'test_taken', 'test_passed'])
            writer.writerows(rows)
        
        # Store results in session to display on profile
        session['last_test_result'] = {
            'course_name': course.name,
            'score': score,
            'correct': correct_count,
            'total': total_questions,
            'passed': passed
        }
        
        if passed:
            flash(f'🎉 Congratulations! You passed the {course.name} test with {score:.1f}%! ({correct_count}/{total_questions} correct)', 'success')
        else:
            flash(f'❌ You scored {score:.1f}% ({correct_count}/{total_questions} correct). Need 60% to pass. Please review the course and try again.', 'error')
        
        return redirect(url_for('student_profile', student_id=student_id))
    
    return render_template('take_test.html', 
                         course=course,
                         total_questions=len(course.questions),
                         passing_score=60)

@app.route('/recommend', methods=['POST'])
def recommend_course():
    """API endpoint to get recommendations for a student"""
    data = request.json
    student_id = data.get('student_id')
    
    if student_id not in loader.students:
        return jsonify({'error': 'Student not found'}), 404
    
    recommendations = recommender.recommend_for_student(student_id, top_n=5)
    
    results = []
    for rec in recommendations:
        results.append({
            'course_id': rec['course'].course_id,
            'course_name': rec['course'].name,
            'department': rec['course'].department,
            'credits': rec['course'].credits,
            'difficulty': rec['course'].difficulty,
            'score': rec['score'],
            'reason': rec['reason'],
            'predicted_success': recommender.predict_success_rate(student_id, rec['course'].course_id)
        })
    
    return jsonify(results)

@app.route('/api/students')
def list_students():
    """API endpoint to list all students"""
    students_list = []
    for student_id, student in loader.students.items():
        students_list.append({
            'id': student_id,
            'name': student.name,
            'department': student.department,
            'gpa': student.gpa,
            'performance_level': student.get_performance_level()
        })
    return jsonify(students_list)

@app.route('/api/courses')
def list_courses():
    """API endpoint to list all courses"""
    courses_list = []
    for course_id, course in loader.courses.items():
        courses_list.append({
            'id': course_id,
            'name': course.name,
            'department': course.department,
            'credits': course.credits,
            'difficulty': course.difficulty,
            'popularity': course.popularity
        })
    return jsonify(courses_list)

@app.route('/admin')
@admin_required
def admin_panel():
    """Admin dashboard"""
    return render_template('admin.html', 
                         students=loader.students.values(),
                         courses=loader.courses.values())

@app.route('/admin/add_course', methods=['GET', 'POST'])
@admin_required
def add_course():
    """Add a new course"""
    if request.method == 'POST':
        try:
            course_id = request.form['course_id']
            name = request.form['name']
            department = request.form['department']
            credits = request.form['credits']
            prerequisites = request.form['prerequisites']
            difficulty = request.form['difficulty']
            popularity = request.form['popularity']
            
            from models.course import Course
            new_course = Course(course_id, name, department, credits, prerequisites, difficulty, popularity)
            loader.courses[course_id] = new_course
            
            csv_path = os.path.join(loader.data_path, 'courses.csv')
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([course_id, name, department, credits, prerequisites, difficulty, popularity])
            
            flash(f'Course {name} added successfully!', 'success')
            return redirect(url_for('admin_panel'))
            
        except Exception as e:
            flash(f'Error adding course: {str(e)}', 'error')
            return redirect(url_for('add_course'))
    
    return render_template('add_course.html')

@app.route('/admin/edit_course/<course_id>', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    """Edit an existing course"""
    if course_id not in loader.courses:
        flash('Course not found!', 'error')
        return redirect(url_for('admin_panel'))
    
    course = loader.courses[course_id]
    
    if request.method == 'POST':
        try:
            course.name = request.form['name']
            course.department = request.form['department']
            course.credits = int(request.form['credits'])
            course.prerequisites = request.form['prerequisites']
            course.difficulty = request.form['difficulty']
            course.popularity = int(request.form['popularity'])
            
            csv_path = os.path.join(loader.data_path, 'courses.csv')
            rows = []
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                rows.append(header)
                for row in reader:
                    if row[0] == course_id:
                        rows.append([course_id, course.name, course.department, course.credits, 
                                   course.prerequisites, course.difficulty, course.popularity])
                    else:
                        rows.append(row)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            
            flash(f'Course {course.name} updated successfully!', 'success')
            return redirect(url_for('admin_panel'))
            
        except Exception as e:
            flash(f'Error updating course: {str(e)}', 'error')
    
    return render_template('edit_course.html', course=course)

@app.route('/admin/delete_course/<course_id>')
@admin_required
def delete_course(course_id):
    """Delete a course"""
    if course_id in loader.courses:
        course_name = loader.courses[course_id].name
        del loader.courses[course_id]
        
        csv_path = os.path.join(loader.data_path, 'courses.csv')
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows.append(header)
            for row in reader:
                if row[0] != course_id:
                    rows.append(row)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        
        flash(f'Course {course_name} deleted successfully!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new student"""
    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            name = request.form['name']
            department = request.form['department']
            gpa = float(request.form['gpa'])
            completed_credits = int(request.form['completed_credits'])
            interests = request.form['interests']
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('register'))
            
            if len(password) < 4:
                flash('Password must be at least 4 characters long!', 'error')
                return redirect(url_for('register'))
            
            if student_id in loader.students:
                flash('Student ID already exists!', 'error')
                return redirect(url_for('register'))
            
            from models.student import Student
            new_student = Student(student_id, name, department, gpa, completed_credits, interests, password)
            loader.students[student_id] = new_student
            
            csv_path = os.path.join(loader.data_path, 'students.csv')
            file_exists = os.path.exists(csv_path)
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['student_id', 'name', 'department', 'gpa', 'completed_credits', 'interests', 'password'])
                writer.writerow([student_id, name, department, gpa, completed_credits, interests, password])
            
            flash(f'Student {name} registered successfully! You can now login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Error registering student: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login for existing students with password"""
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form.get('password', '')
        
        if student_id in loader.students:
            student = loader.students[student_id]
            
            if student.check_password(password):
                session['student_id'] = student_id
                session['student_name'] = student.name
                session['role'] = 'student'
                session['logged_in'] = True
                flash(f'Welcome back, {student.name}!', 'success')
                return redirect(url_for('student_profile', student_id=student_id))
            else:
                flash('Incorrect password! Please try again.', 'error')
                return redirect(url_for('login'))
        else:
            flash('Student ID not found. Please register first.', 'error')
            return redirect(url_for('register'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout student"""
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'admin123':
            session['admin_id'] = 'ADMIN001'
            session['role'] = 'admin'
            session['username'] = username
            session['logged_in'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid admin credentials!', 'error')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/all_students')
@login_required
def all_students():
    """View all students - Only for Admin"""
    if session.get('role') != 'admin':
        flash('Access denied! Only administrators can view all students.', 'error')
        return redirect(url_for('index'))
    
    return render_template('all_students.html', 
                         students=loader.students.values())

@app.route('/enroll_course', methods=['POST'])
@login_required
def enroll_course():
    """Enroll student in a course"""
    student_id = session['student_id']
    course_id = request.form['course_id']
    
    # Check if already enrolled
    for enrollment in loader.students[student_id].enrolled_courses:
        if enrollment.course_id == course_id:
            flash('You are already enrolled in this course!', 'error')
            return redirect(url_for('student_profile', student_id=student_id))
    
    from models.enrollment import Enrollment
    
    enrollment_id = f"E{len(loader.enrollments) + 1:03d}"
    enrollment = Enrollment(
        enrollment_id,
        student_id,
        course_id,
        'Spring',
        2024
    )
    
    loader.enrollments[enrollment_id] = enrollment
    loader.students[student_id].enrolled_courses.append(enrollment)
    
    csv_path = os.path.join(loader.data_path, 'enrollments.csv')
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([enrollment_id, student_id, course_id, 'Spring', 2024])
    
    flash(f'Successfully enrolled in {loader.courses[course_id].name}!', 'success')
    return redirect(url_for('student_profile', student_id=student_id))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)