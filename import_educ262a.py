"""
Script to import EDUC 262A: Urban School Leadership and Management
"""
from datetime import datetime
from models import Course, Session, Reading, get_session, init_db

# Initialize database
init_db()

db = get_session()

try:
    # Check if course already exists
    existing = db.query(Course).filter(Course.code == "EDUC 262A").first()
    if existing:
        print("EDUC 262A already exists in database!")
        print(f"Course: {existing.name}")
        print(f"Instructor: {existing.instructor}")
        print(f"Sessions: {len(existing.sessions)}")
        print(f"Readings: {len(existing.readings)}")
        db.close()
        exit(0)

    # Create course
    course = Course(
        name="Urban School Leadership and Management",
        code="EDUC 262A",
        instructor="Britton & Patel"
    )
    db.add(course)
    db.flush()

    # Create sessions (14 total from calendar)
    sessions_data = [
        (1, "Session 1", "2026-01-14", "6-9pm", "In person, BWW", "Britton"),
        (2, "Session 2", "2026-01-20", "6-9pm", "Online", "Patel"),
        (3, "Session 3", "2026-01-21", "6-9pm", "In person, BWW", "Britton"),
        (4, "Session 4", "2026-02-04", "6-9pm", "In person, BWW", "Britton"),
        (5, "Session 5", "2026-02-07", "6-9pm", "In person, BWW", "Patel (Part 1)"),
        (6, "Session 6", "2026-02-07", "6-9pm", "In person, BWW", "Patel (Part 2)"),
        (7, "Session 7", "2026-02-18", "6-9pm", "In person, BWW", "Britton"),
        (8, "Session 8", "2026-03-11", "6-9pm", "In person, BWW", "Britton"),
        (9, "Session 9", "2026-03-18", "6-9pm", "In person, BWW", "Britton"),
        (10, "Session 10", "2026-03-30", "6-9pm", "In person, BWW", "Britton"),
        (11, "Session 11", "2026-04-08", "6-9pm", "In person, BWW", "Britton"),
        (12, "Session 12", "2026-04-15", "6-9pm", "In person, BWW", "Britton"),
        (13, "Session 13", "2026-04-22", "6-9pm", "In person, BWW", "Patel"),
        (14, "Session 14 - PLI Spring Assessment Center", "2026-05-02", "TBD", "In person, BWW", "Britton, Jimerson, Patel, WWZ")
    ]

    print(f"\nImporting {len(sessions_data)} sessions...")
    for session_num, title, date_str, time, location, desc in sessions_data:
        session_obj = Session(
            course_id=course.id,
            session_number=session_num,
            title=title,
            date=datetime.strptime(date_str, '%Y-%m-%d').date(),
            time=time,
            location=location,
            description=desc
        )
        db.add(session_obj)
        print(f"  Session {session_num}: {date_str} - {desc}")

    # Create readings (5 readings)
    readings_data = [
        ("Founding the American school system", "Labaree, David F.", "pp. 42-79", "2026-01-14", "In Someone has to fail: The zero-sum game of public schooling. Cambridge: Harvard University Press."),
        ("Does the Negro need separate schools?", "Du Bois, W. B.", "pp. 328-335", "2026-01-14", "Journal of Negro Education (1935)"),
        ("Teaching to Change, Chapter 2", "Oakes, Lipton, Anderson, Stillman", "", "2026-01-20", ""),
        ("From the Achievement Gap to Education Debt", "Ladson-Billings", "", "2026-01-21", ""),
        ("Generalizing Across Borders: Policy & Limits of Educational Science", "Luke, A.", "", "2026-01-21", "")
    ]

    print(f"\nImporting {len(readings_data)} readings...")
    for title, authors, pages, due_date_str, citation in readings_data:
        reading = Reading(
            course_id=course.id,
            title=title,
            authors=authors,
            pages=pages,
            due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date(),
            citation=citation
        )
        db.add(reading)
        print(f"  {due_date_str}: {title} by {authors}")

    db.commit()
    print("\n✅ Successfully imported EDUC 262A with 14 sessions and 5 readings!")

except Exception as e:
    db.rollback()
    print(f"❌ Error importing EDUC 262A: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
