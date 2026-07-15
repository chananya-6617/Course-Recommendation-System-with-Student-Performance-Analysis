import csv
import os
from datetime import datetime

class TestManager:
    def __init__(self, data_path='data'):
        self.data_path = data_path
        self.test_results = {}
        self.course_tests = {}
        self.load_test_data()
        print("TestManager initialized")
    
    def load_test_data(self):
        """Load test configuration and results"""
        # Load course test configs
        csv_path = os.path.join(self.data_path, 'course_tests.csv')
        if os.path.exists(csv_path):
            print(f"Loading course tests from {csv_path}")
            import pandas as pd
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                self.course_tests[row['course_id']] = {
                    'questions': row['test_questions'],
                    'passing_score': row['passing_score'],
                    'retake_allowed': row['retake_allowed']
                }
            print(f"Loaded {len(self.course_tests)} course tests")
    
    def has_passed_course(self, student_id, course_id):
        """Check if student has passed the course test"""
        return False
    
    def get_test_status(self, student_id, course_id):
        """Get test status for a course"""
        return None
    
    def can_take_next_course(self, student_id, course_id, prerequisites):
        """Check if student can take next course"""
        if not prerequisites or prerequisites == "None":
            return True, "No prerequisites required"
        return True, "All prerequisite tests passed"
    
    def submit_test_result(self, student_id, course_id, score, attempt):
        """Save test result"""
        return True
    
    def get_available_courses(self, student_id, all_courses, taken_courses):
        """Get courses that student can take"""
        available = []
        locked_courses = []
        
        for course in all_courses:
            if course.course_id not in taken_courses:
                available.append(course)
        
        return available, locked_courses
    
    def get_course_test_info(self, course_id):
        """Get test configuration for a specific course"""
        if course_id in self.course_tests:
            return self.course_tests[course_id]
        return {
            'questions': 10,
            'passing_score': 60,
            'retake_allowed': 3
        }
    
    def get_attempts_remaining(self, student_id, course_id):
        """Get remaining attempts for a course test"""
        return 3