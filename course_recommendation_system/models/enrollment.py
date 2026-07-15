class Enrollment:
    def __init__(self, enrollment_id, student_id, course_id, semester, year, 
                 grade=None, attendance=None, assignments_completed=None, exam_score=None):
        self.enrollment_id = enrollment_id
        self.student_id = student_id
        self.course_id = course_id
        self.semester = semester
        self.year = int(year)
        self.grade = grade
        self.attendance = float(attendance) if attendance else None
        self.assignments_completed = float(assignments_completed) if assignments_completed else None
        self.exam_score = float(exam_score) if exam_score else None
    
    def calculate_final_grade(self):
        """Calculate final grade based on performance"""
        if self.attendance and self.assignments_completed and self.exam_score:
            # Weighted score: 10% attendance, 30% assignments, 60% exam
            total_score = (self.attendance * 0.1) + (self.assignments_completed * 0.3) + (self.exam_score * 0.6)
            
            if total_score >= 90:
                return 'A'
            elif total_score >= 80:
                return 'B'
            elif total_score >= 70:
                return 'C'
            elif total_score >= 60:
                return 'D'
            else:
                return 'F'
        return self.grade
    
    def __str__(self):
        return f"Enrollment {self.enrollment_id}: Student {self.student_id} in {self.course_id}"