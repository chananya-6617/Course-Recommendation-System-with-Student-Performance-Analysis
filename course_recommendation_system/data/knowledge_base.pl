% ============================================
% COURSE RECOMMENDATION SYSTEM - PROLOG KNOWLEDGE BASE
% ============================================

% Student facts: student(ID, Name, Department, GPA, Interests)
student('S001', 'Alice Johnson', 'Computer Science', 9.5, ['AI', 'Python', 'Data Science']).
student('S002', 'Bob Smith', 'Computer Science', 8.0, ['Web Dev', 'Java', 'Database']).
student('S003', 'Carol Davis', 'Mathematics', 9.8, ['Statistics', 'Python', 'AI']).
student('S004', 'David Brown', 'Electrical Engineering', 8.5, ['Robotics', 'C++', 'Embedded']).
student('S005', 'Emma Wilson', 'Computer Science', 7.2, ['Web Dev', 'JavaScript', 'UI/UX']).
student('S006', 'Frank Miller', 'Data Science', 9.2, ['Machine Learning', 'Python', 'Statistics']).
student('S007', 'RIYA', 'Computer Science', 7.0, ['AI', 'Web development']).
student('S008', 'Sarayu', 'Electrical Engineering', 6.5, ['AI']).
student('S009', 'Sriansh', 'Computer Science', 8.0, ['AI', 'Web development']).
student('S010', 'John', 'Computer Science', 9.0, ['Python']).

% Course facts: course(ID, Name, Department, Credits, Difficulty, Popularity)
course('C001', 'Introduction to Programming', 'Computer Science', 3, 'Beginner', 95).
course('C002', 'Data Structures', 'Computer Science', 4, 'Intermediate', 88).
course('C003', 'Machine Learning', 'Computer Science', 4, 'Advanced', 92).
course('C004', 'Web Development', 'Computer Science', 3, 'Intermediate', 85).
course('C005', 'Database Systems', 'Computer Science', 3, 'Intermediate', 82).
course('C006', 'Linear Algebra', 'Mathematics', 4, 'Intermediate', 75).
course('C007', 'Statistics', 'Mathematics', 3, 'Intermediate', 78).
course('C008', 'Digital Circuits', 'Electrical Engineering', 4, 'Beginner', 70).
course('C009', 'Robotics', 'Electrical Engineering', 4, 'Advanced', 80).
course('C010', 'Artificial Intelligence', 'Computer Science', 4, 'Advanced', 90).

% Prerequisite facts: prerequisite(Course, Prerequisite)
prerequisite('C002', 'C001').
prerequisite('C003', 'C002').
prerequisite('C003', 'MAT101').
prerequisite('C004', 'C001').
prerequisite('C005', 'C002').
prerequisite('C007', 'MAT101').
prerequisite('C009', 'C008').
prerequisite('C009', 'PHY101').
prerequisite('C010', 'C003').
prerequisite('C010', 'MAT101').

% Enrollment facts: enrolled(StudentID, CourseID)
enrolled('S001', 'C001').
enrolled('S001', 'C002').
enrolled('S001', 'C003').
enrolled('S002', 'C001').
enrolled('S002', 'C004').
enrolled('S002', 'C005').
enrolled('S003', 'C006').
enrolled('S003', 'C007').
enrolled('S003', 'C003').
enrolled('S004', 'C008').
enrolled('S004', 'C009').
enrolled('S005', 'C001').
enrolled('S005', 'C004').
enrolled('S006', 'C006').
enrolled('S006', 'C007').
enrolled('S006', 'C003').

% ============ PROLOG RULES ============

% Rule 1: Check if student has completed prerequisites
completed_prerequisites(StudentID, CourseID) :-
    \+ prerequisite(CourseID, _), !.
completed_prerequisites(StudentID, CourseID) :-
    findall(Prereq, prerequisite(CourseID, Prereq), Prereqs),
    all_completed(StudentID, Prereqs).

all_completed(_, []).
all_completed(StudentID, [Prereq|Rest]) :-
    enrolled(StudentID, Prereq),
    all_completed(StudentID, Rest).

% Rule 2: Recommend courses by department match
recommend_by_department(StudentID, CourseID) :-
    student(StudentID, _, Dept, _, _),
    course(CourseID, _, Dept, _, _, _),
    \+ enrolled(StudentID, CourseID).

% Rule 3: Recommend courses by interest match
recommend_by_interest(StudentID, CourseID) :-
    student(StudentID, _, _, _, Interests),
    course(CourseID, Name, _, _, _, _),
    member(Interest, Interests),
    sub_string(lower(Name), _, _, _, lower(Interest)),
    \+ enrolled(StudentID, CourseID).

% Rule 4: Recommend courses by GPA level
recommend_by_gpa(StudentID, CourseID) :-
    student(StudentID, _, _, GPA, _),
    course(CourseID, _, _, _, Difficulty, _),
    ((GPA >= 9.0, Difficulty = 'Advanced');
     (GPA >= 7.5, Difficulty = 'Intermediate');
     (GPA < 7.5, Difficulty = 'Beginner')),
    \+ enrolled(StudentID, CourseID).

% Rule 5: Overall recommendation
recommend_course(StudentID, CourseID) :-
    recommend_by_department(StudentID, CourseID),
    completed_prerequisites(StudentID, CourseID).

recommend_course(StudentID, CourseID) :-
    recommend_by_interest(StudentID, CourseID),
    completed_prerequisites(StudentID, CourseID).

recommend_course(StudentID, CourseID) :-
    recommend_by_gpa(StudentID, CourseID),
    completed_prerequisites(StudentID, CourseID).

% Rule 6: Get top N recommendations
top_recommendations(StudentID, TopN, Recommendations) :-
    findall(CourseID, recommend_course(StudentID, CourseID), AllRecs),
    sort(AllRecs, UniqueRecs),
    length(UniqueRecs, Len),
    TopN2 is min(TopN, Len),
    length(Recommendations, TopN2),
    append(Recommendations, _, UniqueRecs).

% Rule 7: Get student performance level
performance_level(StudentID, Level) :-
    student(StudentID, _, _, GPA, _),
    (GPA >= 9.0 -> Level = 'Excellent';
     GPA >= 7.5 -> Level = 'Good';
     GPA >= 6.0 -> Level = 'Average';
     Level = 'Needs Improvement').