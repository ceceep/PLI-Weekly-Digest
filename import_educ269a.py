"""
Script to import EDUC 269A syllabus data
"""
from datetime import datetime
from models import Course, Session, Assignment, Reading, get_session, init_db

# Initialize database
init_db()

db = get_session()

try:
    # Create course
    course = Course(
        name="Leadership Seminar: Leading for Equity",
        code="EDUC 269A",
        instructor="Dr. Lanette Jimerson"
    )
    db.add(course)
    db.flush()

    print(f"Created course: {course.name}")

    # Create sessions
    sessions_data = [
        (1, "Session 1", "2026-01-12", "1:00-4:00pm", "Zoom", "Introduction & Leading with Equity in Mind"),
        (2, "Session 2", "2026-01-26", "1:00-4:00pm", "Zoom", ""),
        (3, "Session 3", "2026-02-09", "1:00-4:00pm", "Zoom", ""),
        (4, "Session 4", "2026-02-23", "1:00-4:00pm", "Zoom", ""),
        (5, "Session 5", "2026-03-02", "1:00-4:00pm", "Zoom", ""),
        (6, "Session 6", "2026-03-09", "1:00-4:00pm", "Zoom", ""),
        (7, "Session 7", "2026-03-16", "1:00-4:00pm", "Zoom", ""),
        (8, "Session 8", "2026-03-23", "1:00-4:00pm", "Zoom", ""),
        (9, "Session 9", "2026-04-06", "1:00-4:00pm", "Zoom", ""),
        (10, "Session 10", "2026-04-13", "1:00-4:00pm", "Zoom", ""),
        (11, "Session 11", "2026-04-20", "1:00-4:00pm", "Zoom", ""),
        (12, "Session 12", "2026-04-27", "1:00-4:00pm", "Zoom", ""),
        (13, "Session 13", "2026-05-04", "1:00-4:00pm", "Zoom", ""),
        (14, "Session 14", "2026-05-11", "1:00-4:00pm", "Zoom", ""),
        (15, "Session 15", "2026-05-18", "1:00-4:00pm", "Zoom", "Course Wrap-Up")
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
        ("CII #1: Standards-based Goals", "First CII assignment", "2026-01-26"),
        ("CII #2: Assessing Leadership Learning", "Second CII assignment", "2026-02-16"),
        ("CII #3: Applying Leadership Learning", "Third CII assignment", "2026-03-16"),
        ("CII #4: Reflecting on Leadership Learning", "Fourth CII assignment", "2026-04-13"),
        ("CII #5: Collaborating with Community", "Fifth CII assignment", "2026-05-11"),
        ("CalAPA Cycle 2, Step 1", "Submit focus statement, video recording, and prompts 1–3 to your assessor", "2026-02-07"),
        ("CalAPA Cycle 2, Step 2", "Submit prompts 4–9 to your assessor", "2026-03-28"),
        ("CalAPA Cycle 2, Step 3", "Submit feedback report and prompts 10–12 to your assessor", "2026-05-16"),
        ("Mock Orals Exam", "Practice oral examination", "2026-04-27"),
        ("Orals Exam", "Final oral examination", "2026-05-18")
    ]

    for title, desc, due_date_str in assignments_data:
        assignment = Assignment(
            course_id=course.id,
            title=title,
            description=desc,
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date()
        )
        db.add(assignment)

    print(f"Created {len(assignments_data)} assignments")

    # Create readings (from the syllabus)
    readings_data = [
        ("The Equity-Centered Trauma-Informed Education Handbook", "Alex Shevrin Venet", "pp. 1-50", "2026-01-12", ""),
        ("Culturally Responsive Teaching and The Brain", "Zaretta Hammond", "Chapters 1-3", "2026-01-26", ""),
        ("Leading for Equity", "Dr. Lanette Jimerson", "Selected chapters", "2026-02-09", "")
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
    print("\n✅ Successfully imported EDUC 269A syllabus!")
    print(f"Course ID: {course.id}")

except Exception as e:
    db.rollback()
    print(f"❌ Error importing data: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
