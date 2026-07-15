class Test:
    def __init__(self, student_id, course_id, attempt=1):
        self.student_id = student_id
        self.course_id = course_id
        self.attempt = attempt
        self.score = None
        self.passed = False
        self.date_taken = None
        self.answers = {}
    
    def calculate_score(self, user_answers, total_questions):
        """Calculate test score based on answers"""
        correct = 0
        for q_id, answer in user_answers.items():
            if self.check_answer(q_id, answer):
                correct += 1
        self.score = (correct / total_questions) * 100
        self.passed = self.score >= 60
        return self.score
    
    def check_answer(self, question_id, answer):
        """Check if answer is correct (simplified - you can expand)"""
        return len(str(answer)) > 0
    
    def can_retake(self, max_attempts=3):
        """Check if student can retake the test"""
        return self.attempt < max_attempts
    
    def __str__(self):
        status = "PASSED" if self.passed else "FAILED"
        return f"Test for {self.course_id} - Attempt {self.attempt}: {self.score}% ({status})"