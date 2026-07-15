class Student:
    def __init__(self, student_id, name, department, gpa, completed_credits, interests, password=None):
        self.student_id = student_id
        self.name = name
        self.department = department
        self.gpa = float(gpa)
        self.completed_credits = int(completed_credits)
        self.interests = interests.split(',')
        self.password = password
        self.enrolled_courses = []
        self.performance_history = []
    
    def check_password(self, password):
        """Verify student password"""
        return self.password == password
    
    def get_performance_level(self):
        """Determine performance level based on GPA (10.0 scale)"""
        if self.gpa >= 9.0:
            return "Excellent"
        elif self.gpa >= 7.5:
            return "Good"
        elif self.gpa >= 6.0:
            return "Average"
        else:
            return "Needs Improvement"
    
    def can_take_course(self, course, prerequisites_completed):
        """Check if student meets prerequisites"""
        if course.prerequisites is None or course.prerequisites == "None" or course.prerequisites == "":
            return True
        
        prereq_str = str(course.prerequisites)
        prereq_list = prereq_str.split(',')
        return all(prereq.strip() in prerequisites_completed for prereq in prereq_list)
    
    def __str__(self):
        return f"{self.name} ({self.student_id}) - GPA: {self.gpa}, Dept: {self.department}"