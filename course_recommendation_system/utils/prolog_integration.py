from pyswip import Prolog
import os

class PrologIntegration:
    def __init__(self):
        self.prolog = Prolog()
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load the Prolog knowledge base"""
        kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'knowledge_base.pl')
        self.prolog.consult(kb_path)
        print("✓ Prolog knowledge base loaded")
    
    def recommend_courses_prolog(self, student_id, top_n=5):
        """Get recommendations using Prolog rules"""
        try:
            query = f"top_recommendations('{student_id}', {top_n}, Recommendations)"
            results = list(self.prolog.query(query))
            
            if results:
                recommendations = results[0]['Recommendations']
                return [str(r) for r in recommendations]
            return []
        except Exception as e:
            print(f"Prolog query error: {e}")
            return []
    
    def check_prerequisites_prolog(self, student_id, course_id):
        """Check if student has completed prerequisites using Prolog"""
        try:
            query = f"completed_prerequisites('{student_id}', '{course_id}')"
            result = list(self.prolog.query(query))
            return len(result) > 0
        except:
            return False
    
    def get_performance_level_prolog(self, student_id):
        """Get student performance level using Prolog"""
        try:
            query = f"performance_level('{student_id}', Level)"
            result = list(self.prolog.query(query))
            if result:
                return result[0]['Level']
            return "Unknown"
        except:
            return "Unknown"
    
    def get_similar_courses_prolog(self, course_id):
        """Get similar courses using Prolog"""
        try:
            query = f"similar_course('{course_id}', SimilarID)"
            results = list(self.prolog.query(query))
            return [str(r['SimilarID']) for r in results]
        except:
            return []
    
    def eligible_for_advanced_prolog(self, student_id):
        """Check if student is eligible for advanced courses"""
        try:
            query = f"eligible_for_advanced('{student_id}')"
            result = list(self.prolog.query(query))
            return len(result) > 0
        except:
            return False