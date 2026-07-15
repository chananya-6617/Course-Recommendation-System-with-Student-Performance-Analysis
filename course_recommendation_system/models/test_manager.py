import pandas as pd
import os
import csv
from datetime import datetime
from models.test import Test

class TestManager:
    def __init__(self, data_path='data'):
        self.data_path = data_path
        self.test_results = {}
        self.course_tests = {}
        self.load_test_data()
    
    def load_test_data(self):
        """Load test configuration and results"""
        # Load course test configs
        csv_path = os.path.join(self.data_path, 'course_tests.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                self.course_tests[row['course_id']] = {
                    'questions': row['test_questions'],
                    'passing_score': row['passing_score'],
                    'retake_allowed': row['retake_allowed']
                }
        
        # Load student test results
        results_path = os.path.join(self.data_path, 'student_test_results.csv')
        if os.path.exists(results_path):
            df = pd.read_csv(results_path)
            for _, row in df.iterrows():
                key = f"{row['student_id']}_{row['course_id']}"
                if key not in self.test_results:
                    self.test_results[key] = []
                self.test_results[key].append({
                    'attempt': row['attempt'],
                    'score': row['score'],
                    'passed': row['passed'] == 'Yes',
                    'date_taken': row['date_taken']
                })
    
    def has_passed_course(self, student_id, course_id):
        """Check if student has passed the course test"""
        key = f"{student_id}_{course_id}"
        if key in self.test_results:
            for result in self.test_results[key]:
                if result['passed']:
                    return True
        return False
    
    def get_test_status(self, student_id, course_id):
        """Get test status for a course"""
        key = f"{student_id}_{course_id}"
        if key in self.test_results and self.test_results[key]:
            latest = self.test_results[key][-1]
            return {
                'attempt': latest['attempt'],
                'score': latest['score'],
                'passed': latest['passed'],
                'date_taken': latest['date_taken']
            }
        return None
    
    def can_take_next_course(self, student_id, course_id, prerequisites):
        """Check if student can take next course (must pass prerequisite tests)"""
        if not prerequisites or prerequisites == "None":
            return True, "No prerequisites required"
        
        prereq_list = [p.strip() for p in prerequisites.split(',')]
        for prereq in prereq_list:
            if not self.has_passed_course(student_id, prereq):
                return False, f"You must pass {prereq} test before taking this course"
        
        return True, "All prerequisite tests passed"
    
    def submit_test_result(self, student_id, course_id, score, attempt):
        """Save test result"""
        key = f"{student_id}_{course_id}"
        passed = score >= 60
        
        result = {
            'attempt': attempt,
            'score': score,
            'passed': passed,
            'date_taken': datetime.now().strftime('%Y-%m-%d')
        }
        
        if key not in self.test_results:
            self.test_results[key] = []
        self.test_results[key].append(result)
        
        # Save to CSV
        csv_path = os.path.join(self.data_path, 'student_test_results.csv')
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['student_id', 'course_id', 'attempt', 'score', 'passed', 'date_taken'])
            writer.writerow([student_id, course_id, attempt, score, 'Yes' if passed else 'No', result['date_taken']])
        
        return passed
    
    def get_available_courses(self, student_id, all_courses, taken_courses):
        """Get courses that student can take (based on passed prerequisites)"""
        available = []
        locked_courses = []
        
        for course in all_courses:
            if course.course_id in taken_courses:
                continue
            
            can_take, reason = self.can_take_next_course(
                student_id, 
                course.course_id, 
                course.prerequisites
            )
            
            if can_take:
                available.append(course)
            else:
                locked_courses.append({'course': course, 'reason': reason})
        
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
        key = f"{student_id}_{course_id}"
        test_info = self.get_course_test_info(course_id)
        max_attempts = test_info['retake_allowed']
        
        if key not in self.test_results:
            return max_attempts
        
        attempts_used = len(self.test_results[key])
        return max(0, max_attempts - attempts_used)