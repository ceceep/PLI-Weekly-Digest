"""
Script to import EDUC 460A syllabus data
"""
from datetime import datetime
from models import Course, Session, Assignment, Reading, get_session, init_db

# Initialize database
init_db()

db = get_session()

try:
    # Create course
    course = Course(
        name="Practicum in School Site Management",
        code="EDUC 460A",
        instructor="Dr. nives wetzel de cediel"
    )
    db.add(course)
    db.flush()

    print(f"Created course: {course.name}")

    # Create sessions
    sessions_data = [
        (1, "Spring Overview, PLI Mid Year Coach/Coachee Reflection Questions, Planning for Summer Internships", "2025-01-24", "9am-noon", "In person, BWW 1203", "Spring Overview, PLI Mid Year Coach/Coachee Reflection Questions, Planning for Summer Internships, Check-In w/ Spring Home Group, Portfolios Ongoing reflection"),
        (2, "Mock Interview Prep and Practice", "2025-02-21", "1-4pm", "In person, BWW 1203", "Mock Interview Prep and Practice, What is a Mock Interview? How do you present as a leader? Resume tuning, More Metaphors, Internships, Summer Internship Resources & Guidelines"),
        (3, "Mock Interviews", "2025-03-07", "1-4pm (Mock Interviews 9am-noon)", "In person, BWW 1203", "Students will participate in Mock Interviews for the first half of the day. Class in the afternoon following Mock Interviews. Debrief & Reflection, Metaphors"),
        (4, "Leadership Experiences, Metaphor & Rubric Task", "2025-04-04", "1-4pm", "In person, BWW 1203", "C25 Leadership Experiences, Metaphor & Rubric Task (in-class-due April 4, by 5pm)"),
        (5, "Spring Portfolio", "2025-04-27", "6-9pm", "Online (zoom)", "Spring Portfolio, Sneak Peak at Summer 2026")
    ]

    for session_num, title, date_str, time, location, desc in sessions_data:
        session = Session(
            course_id=course.id,
            session_number=session_num,
            title=title,
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            time=time,
            location=location,
            description=desc
        )
        db.add(session)

    print(f"Created {len(sessions_data)} sessions")

    # Create assignments
    assignments_data = [
        ("Complete the Fall Reflective Narrative: Leadership Competency Development", "Review your Fall Portfolio Feedback, the CTC CAPE CACE document and the PLI Leadership Connection Rubric to inform your reflection", "2025-02-07", 25),
        ("Revised Fall Portfolio", "Incorporate feedback received from home group and instructors to make revisions to fall portfolio", "2025-02-06", 10),
        ("Final Resume & Cover Letter", "Create final draft of resume and cover letter for Mock Interviews using provided resources and group feedback", "2025-02-27", 25),
        ("Spring Portfolio", "Add leadership experiences for Spring Semester which reflect both breadth and depth of experience, including approved spring logs and revised Fall Portfolio", "2025-05-08", 50)
    ]

    for title, desc, due_date_str, points in assignments_data:
        assignment = Assignment(
            course_id=course.id,
            title=title,
            description=desc,
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date(),
            points=points
        )
        db.add(assignment)

    print(f"Created {len(assignments_data)} assignments")

    # Create readings
    readings_data = [
        ("Metaphor as a tool in educational leadership classrooms", "Singh, K.", "", "2025-04-04", "")
    ]

    for title, authors, pages, due_date_str, url in readings_data:
        reading = Reading(
            course_id=course.id,
            title=title,
            authors=authors,
            pages=pages,
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date(),
            url=url
        )
        db.add(reading)

    print(f"Created {len(readings_data)} readings")

    # Commit all changes
    db.commit()
    print("\n✅ Successfully imported EDUC 460A syllabus!")
    print(f"Course ID: {course.id}")

except Exception as e:
    db.rollback()
    print(f"❌ Error importing data: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
