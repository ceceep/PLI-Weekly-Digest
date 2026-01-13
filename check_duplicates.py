"""
Check for duplicate courses and sessions in the database
"""
from models import Course, Session, Assignment, Reading, CustomItem, get_session

db = get_session()

# Get all courses
print("=" * 60)
print("COURSES IN DATABASE:")
print("=" * 60)
courses = db.query(Course).all()
for course in courses:
    print(f"\nID: {course.id}")
    print(f"Code: {course.code}")
    print(f"Name: {course.name}")
    print(f"Instructor: {course.instructor}")
    print(f"Created: {course.created_at}")

    # Count items
    session_count = len(course.sessions)
    assignment_count = len(course.assignments)
    reading_count = len(course.readings)

    print(f"  → Sessions: {session_count}")
    print(f"  → Assignments: {assignment_count}")
    print(f"  → Readings: {reading_count}")

print("\n" + "=" * 60)
print(f"TOTAL COURSES: {len(courses)}")
print("=" * 60)

# Check for duplicate course codes
print("\n" + "=" * 60)
print("CHECKING FOR DUPLICATES:")
print("=" * 60)

course_codes = {}
for course in courses:
    if course.code in course_codes:
        course_codes[course.code].append(course)
    else:
        course_codes[course.code] = [course]

for code, course_list in course_codes.items():
    if len(course_list) > 1:
        print(f"\n⚠️  DUPLICATE FOUND: {code}")
        for course in course_list:
            print(f"   - ID {course.id}: {course.name} (created {course.created_at})")

db.close()
