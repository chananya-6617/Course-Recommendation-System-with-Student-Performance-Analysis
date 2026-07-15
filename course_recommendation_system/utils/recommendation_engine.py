import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

class RecommendationEngine:
    def __init__(self, students, courses, enrollments):
        self.students = students
        self.courses = courses
        self.enrollments = enrollments
        self.course_features = self._extract_course_features()
    
    def _extract_course_features(self):
        """Extract features from courses for similarity calculation"""
        features = []
        course_names = []
        
        for course_id, course in self.courses.items():
            # Combine course attributes into a feature string
            feature_str = f"{course.name} {course.department} {course.difficulty}"
            features.append(feature_str)
            course_names.append(course_id)
        
        # Convert to TF-IDF vectors
        vectorizer = TfidfVectorizer()
        feature_matrix = vectorizer.fit_transform(features)
        
        return {'matrix': feature_matrix, 'names': course_names, 'vectorizer': vectorizer}
    
    def recommend_by_similarity(self, course_id, top_n=3):
        """Recommend courses similar to a given course"""
        if course_id not in self.courses:
            return []
        
        idx = self.course_features['names'].index(course_id)
        similarity_scores = cosine_similarity(
            self.course_features['matrix'][idx:idx+1], 
            self.course_features['matrix']
        ).flatten()
        
        # Get top N similar courses (excluding the course itself)
        similar_indices = similarity_scores.argsort()[::-1][1:top_n+1]
        
        recommendations = []
        for i in similar_indices:
            course = self.courses[self.course_features['names'][i]]
            recommendations.append({
                'course': course,
                'similarity_score': similarity_scores[i]
            })
        
        return recommendations
    
    def recommend_for_student(self, student_id, top_n=5):
        """Generate personalized course recommendations for a student"""
        if student_id not in self.students:
            return []
        
        student = self.students[student_id]
        taken_courses = {e.course_id for e in student.enrolled_courses}
        
        # Get courses not taken yet
        available_courses = [c for c in self.courses.values() if c.course_id not in taken_courses]
        
        # Score each available course
        scored_courses = []
        for course in available_courses:
            score = self._calculate_course_score(student, course)
            scored_courses.append((course, score))
        
        # Sort by score and return top N
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for course, score in scored_courses[:top_n]:
            recommendations.append({
                'course': course,
                'score': score,
                'reason': self._get_recommendation_reason(student, course),
                'predicted_success': self.predict_success_rate(student_id, course.course_id)
            })
        
        return recommendations
    
    def _calculate_course_score(self, student, course):
        """Calculate recommendation score for a course (10.0 GPA scale)"""
        score = 0
        
        # Department match (30% weight)
        if course.department == student.department:
            score += 30
        
        # Interest match (25% weight)
        interest_match = sum(1 for interest in student.interests 
                            if interest.lower() in course.name.lower())
        score += min(25, interest_match * 8)
        
        # Difficulty based on GPA (20% weight) - Updated for 10.0 scale
        if student.gpa >= 9.0:  # Excellent students (9.0+)
            if course.difficulty == "Advanced":
                score += 20
            elif course.difficulty == "Intermediate":
                score += 15
        elif student.gpa >= 7.5:  # Good students (7.5-8.9)
            if course.difficulty == "Intermediate":
                score += 20
            elif course.difficulty == "Beginner":
                score += 15
        else:  # Students needing improvement (below 7.5)
            if course.difficulty == "Beginner":
                score += 20
        
        # Popularity (15% weight)
        score += (course.popularity / 100) * 15
        
        # Prerequisites check (10% weight)
        taken_courses = [e.course_id for e in student.enrolled_courses]
        if student.can_take_course(course, taken_courses):
            score += 10
        
        return score
    
    def _get_recommendation_reason(self, student, course):
        """Generate explanation for recommendation"""
        reasons = []
        
        if course.department == student.department:
            reasons.append(f"Matches your {student.department} major")
        
        interest_match = [i for i in student.interests if i.lower() in course.name.lower()]
        if interest_match:
            reasons.append(f"Aligns with your interest in {', '.join(interest_match)}")
        
        if student.gpa >= 9.0 and course.difficulty == "Advanced":
            reasons.append("Advanced course suitable for your strong academic performance")
        elif student.gpa < 7.5 and course.difficulty == "Beginner":
            reasons.append("Beginner-friendly course matching your current level")
        elif course.difficulty == "Intermediate":
            reasons.append("Intermediate level course for steady progress")
        
        return " | ".join(reasons)
    
    def analyze_performance_trends(self, student_id):
        """Analyze student performance trends"""
        if student_id not in self.students:
            return None
        
        student = self.students[student_id]
        performance_data = []
        
        for enrollment in student.enrolled_courses:
            if enrollment.exam_score:
                performance_data.append({
                    'course_id': enrollment.course_id,
                    'course_name': self.courses[enrollment.course_id].name,
                    'score': enrollment.exam_score,
                    'grade': enrollment.grade,
                    'semester': enrollment.semester,
                    'year': enrollment.year
                })
        
        if performance_data:
            df = pd.DataFrame(performance_data)
            avg_score = df['score'].mean()
            trending = "Improving" if len(df) > 1 and df['score'].iloc[-1] > df['score'].iloc[0] else "Stable or Declining"
            
            return {
                'average_score': avg_score,
                'trend': trending,
                'best_course': df.loc[df['score'].idxmax(), 'course_name'],
                'worst_course': df.loc[df['score'].idxmin(), 'course_name'],
                'performance_history': performance_data
            }
        
        return None
    
    def predict_success_rate(self, student_id, course_id):
        """Predict student success rate in a course"""
        if student_id not in self.students or course_id not in self.courses:
            return None
        
        student = self.students[student_id]
        course = self.courses[course_id]
        
        # Previous performance factor
        student_avg = np.mean([e.exam_score for e in student.enrolled_courses 
                              if e.exam_score]) if student.enrolled_courses else 70
        
        # Course difficulty factor
        difficulty_factor = {
            "Beginner": 1.2,
            "Intermediate": 1.0,
            "Advanced": 0.8
        }.get(course.difficulty, 1.0)
        
        # Department familiarity factor
        dept_factor = 1.1 if course.department == student.department else 0.9
        
        # Interest factor
        interest_factor = 1.0
        for interest in student.interests:
            if interest.lower() in course.name.lower():
                interest_factor = 1.15
                break
        
        # Prerequisite factor
        prereq_factor = 1.0
        if course.prerequisites != "None":
            prereq_list = course.prerequisites.split(',')
            taken_courses = [e.course_id for e in student.enrolled_courses]
            completed_prereqs = sum(1 for p in prereq_list if p.strip() in taken_courses)
            prereq_factor = completed_prereqs / len(prereq_list) if prereq_list else 1.0
        
        # Calculate predicted score
        predicted_score = (student_avg * 0.4 + 70 * 0.2) * difficulty_factor * dept_factor * interest_factor * prereq_factor
        predicted_score = min(100, max(0, predicted_score))
        
        # Determine success level
        if predicted_score >= 85:
            success_level = "High"
        elif predicted_score >= 70:
            success_level = "Medium"
        else:
            success_level = "Low"
        
        return {
            'predicted_score': predicted_score,
            'success_level': success_level,
            'factors': {
                'student_avg': student_avg,
                'difficulty_factor': difficulty_factor,
                'department_factor': dept_factor,
                'interest_factor': interest_factor,
                'prerequisite_completion': prereq_factor
            }
        }
    
    def recommend_for_student_with_tests(self, student_id, test_manager, top_n=5):
        """Generate recommendations considering test progression"""
        if student_id not in self.students:
            return [], []
        
        student = self.students[student_id]
        taken_courses = {e.course_id for e in student.enrolled_courses}
        
        # Get available courses (passed prerequisites)
        available_courses, locked_courses = test_manager.get_available_courses(
            student_id, 
            list(self.courses.values()), 
            taken_courses
        )
        
        # Score available courses
        scored_courses = []
        for course in available_courses:
            score = self._calculate_course_score(student, course)
            # Bonus for courses where prerequisites test is passed
            if test_manager.has_passed_course(student_id, course.course_id):
                score += 15
            scored_courses.append((course, score))
        
        scored_courses.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for course, score in scored_courses[:top_n]:
            recommendations.append({
                'course': course,
                'score': score,
                'reason': self._get_recommendation_reason(student, course),
                'predicted_success': self.predict_success_rate(student_id, course.course_id),
                'test_required': True,
                'passing_score': 60
            })
        
        return recommendations, locked_courses