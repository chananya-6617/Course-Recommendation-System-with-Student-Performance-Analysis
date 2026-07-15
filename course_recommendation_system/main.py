import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import DataLoader
from utils.recommendation_engine import RecommendationEngine

class CourseRecommendationSystem:
    def __init__(self):
        self.data_loader = DataLoader()
        self.recommendation_engine = None
    
    def initialize(self):
        """Initialize the system by loading data"""
        print("=" * 60)
        print("COURSE RECOMMENDATION SYSTEM")
        print("=" * 60)
        print("\nLoading data...")
        self.data_loader.load_all_data()
        self.recommendation_engine = RecommendationEngine(
            self.data_loader.students,
            self.data_loader.courses,
            self.data_loader.enrollments
        )
        print("System initialized successfully!\n")
    
    def display_student_info(self, student_id):
        """Display student information"""
        if student_id not in self.data_loader.students:
            print(f"Student {student_id} not found!")
            return False
        
        student = self.data_loader.students[student_id]
        print(f"\n--- Student Information ---")
        print(f"Name: {student.name}")
        print(f"ID: {student.student_id}")
        print(f"Department: {student.department}")
        print(f"GPA: {student.gpa} ({student.get_performance_level()})")
        print(f"Completed Credits: {student.completed_credits}")
        print(f"Interests: {', '.join(student.interests)}")
        
        # Display enrolled courses
        if student.enrolled_courses:
            print(f"\nEnrolled Courses:")
            for enrollment in student.enrolled_courses:
                course = self.data_loader.courses[enrollment.course_id]
                print(f"  - {course.name}: Grade {enrollment.grade} (Score: {enrollment.exam_score})")
        
        return True
    
    def show_recommendations(self, student_id):
        """Show course recommendations for a student"""
        print(f"\n--- Course Recommendations ---")
        recommendations = self.recommendation_engine.recommend_for_student(student_id, top_n=5)
        
        if not recommendations:
            print("No recommendations available.")
            return
        
        for i, rec in enumerate(recommendations, 1):
            course = rec['course']
            print(f"\n{i}. {course.name} (ID: {course.course_id})")
            print(f"   Department: {course.department}")
            print(f"   Credits: {course.credits} | Difficulty: {course.difficulty}")
            print(f"   Popularity Score: {course.popularity}/100")
            print(f"   Recommendation Score: {rec['score']:.1f}/100")
            print(f"   Reason: {rec['reason']}")
            
            # Show success prediction
            success_pred = self.recommendation_engine.predict_success_rate(student_id, course.course_id)
            if success_pred:
                print(f"   Predicted Success: {success_pred['success_level']} "
                      f"(Expected Score: {success_pred['predicted_score']:.1f}/100)")
    
    def show_performance_analysis(self, student_id):
        """Show performance analysis for a student"""
        print(f"\n--- Performance Analysis ---")
        analysis = self.recommendation_engine.analyze_performance_trends(student_id)
        
        if analysis:
            print(f"Average Exam Score: {analysis['average_score']:.1f}/100")
            print(f"Performance Trend: {analysis['trend']}")
            print(f"Best Performing Course: {analysis['best_course']}")
            print(f"Course Needing Improvement: {analysis['worst_course']}")
            
            print(f"\nPerformance History:")
            for perf in analysis['performance_history']:
                print(f"  {perf['semester']} {perf['year']}: {perf['course_name']} - "
                      f"Score: {perf['score']}/100 (Grade: {perf['grade']})")
        else:
            print("No performance data available.")
    
    def show_course_similarity(self, course_id):
        """Show courses similar to a given course"""
        if course_id not in self.data_loader.courses:
            print(f"Course {course_id} not found!")
            return
        
        course = self.data_loader.courses[course_id]
        print(f"\n--- Courses Similar to {course.name} ---")
        similar_courses = self.recommendation_engine.recommend_by_similarity(course_id, top_n=3)
        
        if similar_courses:
            for i, rec in enumerate(similar_courses, 1):
                similar_course = rec['course']
                print(f"\n{i}. {similar_course.name} (ID: {similar_course.course_id})")
                print(f"   Similarity Score: {rec['similarity_score']:.2f}")
                print(f"   Department: {similar_course.department}")
                print(f"   Difficulty: {similar_course.difficulty}")
        else:
            print("No similar courses found.")
    
    def run_menu(self):
        """Run the main menu interface"""
        while True:
            print("\n" + "=" * 60)
            print("MAIN MENU")
            print("=" * 60)
            print("1. View Student Information")
            print("2. Get Course Recommendations")
            print("3. View Performance Analysis")
            print("4. Find Similar Courses")
            print("5. List All Students")
            print("6. List All Courses")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                student_id = input("Enter Student ID: ").strip()
                self.display_student_info(student_id)
            
            elif choice == '2':
                student_id = input("Enter Student ID: ").strip()
                if self.display_student_info(student_id):
                    self.show_recommendations(student_id)
            
            elif choice == '3':
                student_id = input("Enter Student ID: ").strip()
                if self.display_student_info(student_id):
                    self.show_performance_analysis(student_id)
            
            elif choice == '4':
                course_id = input("Enter Course ID: ").strip()
                self.show_course_similarity(course_id)
            
            elif choice == '5':
                print("\n--- All Students ---")
                for student_id, student in self.data_loader.students.items():
                    print(f"{student_id}: {student.name} - {student.department} (GPA: {student.gpa})")
            
            elif choice == '6':
                print("\n--- All Courses ---")
                for course_id, course in self.data_loader.courses.items():
                    print(f"{course_id}: {course.name} - {course.department} "
                          f"({course.difficulty}, {course.credits} credits)")
            
            elif choice == '7':
                print("\nThank you for using the Course Recommendation System!")
                break
            
            else:
                print("Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")

def main():
    """Main function to run the system"""
    system = CourseRecommendationSystem()
    system.initialize()
    system.run_menu()

if __name__ == "__main__":
    main()
    