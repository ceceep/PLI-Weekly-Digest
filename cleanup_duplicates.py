"""
Delete duplicate courses from the database
"""
from models import Course, get_session

db = get_session()

# Courses to delete (the duplicates with less data)
courses_to_delete = [2, 4, 6]  # IDs of duplicate courses

print("=" * 60)
print("DELETING DUPLICATE COURSES")
print("=" * 60)

for course_id in courses_to_delete:
    course = db.query(Course).get(course_id)
    if course:
        print(f"\n✓ Deleting: ID {course.id} - {course.code}: {course.name}")
        print(f"  Sessions: {len(course.sessions)}")
        print(f"  Assignments: {len(course.assignments)}")
        print(f"  Readings: {len(course.readings)}")

        # Delete the course (cascade will delete all related items)
        db.delete(course)
    else:
        print(f"\n⚠️  Course ID {course_id} not found")

# Commit the deletions
db.commit()

print("\n" + "=" * 60)
print("CLEANUP COMPLETE!")
print("=" * 60)

# Show remaining courses
remaining_courses = db.query(Course).all()
print(f"\nRemaining courses: {len(remaining_courses)}")
for course in remaining_courses:
    print(f"  - {course.code}: {course.name}")

db.close()
