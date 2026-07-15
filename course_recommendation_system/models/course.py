class Course:
    def __init__(self, course_id, name, department, credits, prerequisites, difficulty, popularity, youtube_link=None):
        self.course_id = course_id
        self.name = name
        self.department = department
        self.credits = int(credits)
        self.prerequisites = prerequisites
        self.difficulty = difficulty
        self.popularity = int(popularity)
        self.youtube_link = youtube_link
        
        # Test and progression attributes
        self.test_questions = 10
        self.passing_score = 60
        self.retake_allowed = 3
        self.questions = []  # Will store questions for this course
        
        self.avg_grade = None
        self.completion_rate = None
    
    def load_questions(self, questions_data):
        """Load questions for this course"""
        self.questions = [q for q in questions_data if q['course_id'] == self.course_id]
        self.test_questions = len(self.questions)
    
    def get_youtube_embed_url(self):
        """Convert YouTube URL to embed URL"""
        if not self.youtube_link:
            return None
        
        if 'youtu.be/' in self.youtube_link:
            video_id = self.youtube_link.split('youtu.be/')[1].split('?')[0]
        elif 'watch?v=' in self.youtube_link:
            video_id = self.youtube_link.split('watch?v=')[1].split('&')[0]
        elif 'embed/' in self.youtube_link:
            video_id = self.youtube_link.split('embed/')[1].split('?')[0]
        else:
            return self.youtube_link
        
        return f"https://www.youtube.com/embed/{video_id}"
    
    def get_test_info(self):
        """Get test information"""
        return {
            'questions': self.test_questions,
            'passing_score': self.passing_score,
            'retake_allowed': self.retake_allowed
        }
    
    def calculate_course_metrics(self, performances):
        """Calculate course performance metrics"""
        if performances:
            grades = [p['exam_score'] for p in performances]
            self.avg_grade = sum(grades) / len(grades)
            self.completion_rate = len([p for p in performances if p['grade'] != 'F']) / len(performances) * 100
    
    def __str__(self):
        return f"{self.name} ({self.course_id}) - Credits: {self.credits}, Difficulty: {self.difficulty}"