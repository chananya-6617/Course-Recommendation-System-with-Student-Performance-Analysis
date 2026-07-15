import pandas as pd
import os
import math
from models.student import Student
from models.course import Course
from models.enrollment import Enrollment

class DataLoader:
    def __init__(self, data_path='data'):
        self.data_path = data_path
        self.students = {}
        self.courses = {}
        self.enrollments = {}
        self.performance_data = {}
    
    def load_all_data(self):
        """Load all data from CSV files"""
        self.load_students()
        self.load_courses()
        self.load_enrollments()
        self.load_performance()
        self.load_course_questions()
        self.link_data()
        
        print(f"Loaded {len(self.students)} students")
        print(f"Loaded {len(self.courses)} courses")
        print(f"Loaded {len(self.enrollments)} enrollments")
    
    def load_students(self):
        """Load student data"""
        try:
            df = pd.read_csv(os.path.join(self.data_path, 'students.csv'))
            for _, row in df.iterrows():
                # Get password if column exists
                password = None
                if 'password' in df.columns:
                    password = row['password'] if not pd.isna(row['password']) else None
                
                student = Student(
                    row['student_id'],
                    row['name'],
                    row['department'],
                    row['gpa'],
                    row['completed_credits'],
                    row['interests'],
                    password
                )
                self.students[row['student_id']] = student
            print(f"✓ Loaded {len(self.students)} students")
        except Exception as e:
            print(f"Error loading students: {e}")
    
    def load_courses(self):
        """Load course data"""
        try:
            df = pd.read_csv(os.path.join(self.data_path, 'courses.csv'))
            for _, row in df.iterrows():
                # Handle NaN values in prerequisites
                prerequisites = row['prerequisites']
                
                # Check if it's NaN (float) or None
                if isinstance(prerequisites, float):
                    if math.isnan(prerequisites):
                        prerequisites = "None"
                elif prerequisites is None:
                    prerequisites = "None"
                elif str(prerequisites).strip() == '':
                    prerequisites = "None"
                
                # Get YouTube link (handle if column doesn't exist)
                youtube_link = None
                if 'youtube_link' in df.columns:
                    link = row['youtube_link']
                    if not pd.isna(link) and str(link).strip() != '':
                        youtube_link = str(link)
                
                course = Course(
                    row['course_id'],
                    row['name'],
                    row['department'],
                    row['credits'],
                    prerequisites,
                    row['difficulty'],
                    row['popularity'],
                    youtube_link
                )
                self.courses[row['course_id']] = course
            print(f"✓ Loaded {len(self.courses)} courses")
        except Exception as e:
            print(f"Error loading courses: {e}")
    
    def load_enrollments(self):
        """Load enrollment data"""
        try:
            df = pd.read_csv(os.path.join(self.data_path, 'enrollments.csv'))
            for _, row in df.iterrows():
                enrollment = Enrollment(
                    row['enrollment_id'],
                    row['student_id'],
                    row['course_id'],
                    row['semester'],
                    row['year']
                )
                self.enrollments[row['enrollment_id']] = enrollment
            print(f"✓ Loaded {len(self.enrollments)} enrollments")
        except Exception as e:
            print(f"Error loading enrollments: {e}")
    
    def load_performance(self):
        """Load performance data"""
        try:
            df = pd.read_csv(os.path.join(self.data_path, 'performance.csv'))
            for _, row in df.iterrows():
                self.performance_data[row['enrollment_id']] = {
                    'grade': row['grade'],
                    'attendance': row['attendance'],
                    'assignments_completed': row['assignments_completed'],
                    'exam_score': row['exam_score']
                }
            print(f"✓ Loaded {len(self.performance_data)} performance records")
        except Exception as e:
            print(f"Error loading performance: {e}")
    
    def load_course_questions(self):
        """Load questions for each course from CSV"""
        questions_path = os.path.join(self.data_path, 'course_questions.csv')
        if os.path.exists(questions_path):
            try:
                df = pd.read_csv(questions_path)
                questions_by_course = {}
                
                for _, row in df.iterrows():
                    course_id = row['course_id']
                    if course_id not in questions_by_course:
                        questions_by_course[course_id] = []
                    
                    questions_by_course[course_id].append({
                        'question_id': int(row['question_id']),
                        'question_text': row['question_text'],
                        'option_a': row['option_a'],
                        'option_b': row['option_b'],
                        'option_c': row['option_c'],
                        'option_d': row['option_d'],
                        'correct_answer': row['correct_answer']
                    })
                
                # Assign questions to courses
                for course_id, questions in questions_by_course.items():
                    if course_id in self.courses:
                        self.courses[course_id].questions = questions
                        self.courses[course_id].test_questions = len(questions)
                
                print(f"✅ Loaded questions for {len(questions_by_course)} courses")
            except Exception as e:
                print(f"Error loading questions: {e}")
        else:
            print("⚠️ No course questions file found")
    
    def link_data(self):
        """Link enrollments with performance data"""
        for enrollment_id, enrollment in self.enrollments.items():
            if enrollment_id in self.performance_data:
                perf = self.performance_data[enrollment_id]
                enrollment.grade = perf['grade']
                enrollment.attendance = perf['attendance']
                enrollment.assignments_completed = perf['assignments_completed']
                enrollment.exam_score = perf['exam_score']
                
                # Link to student
                if enrollment.student_id in self.students:
                    self.students[enrollment.student_id].enrolled_courses.append(enrollment)
                    self.students[enrollment.student_id].performance_history.append(perf)
    
    def get_student_courses(self, student_id):
        """Get all courses taken by a student"""
        return [e for e in self.enrollments.values() if e.student_id == student_id]
    
    def get_course_students(self, course_id):
        """Get all students enrolled in a course"""
        return [e for e in self.enrollments.values() if e.course_id == course_id]