"""
Script to import PLI Calendar program-wide events
"""
from datetime import datetime
from models import CustomItem, get_session, init_db
import json

# Initialize database
init_db()

db = get_session()

events_data = [
    {"title": "Cal APA Scores released", "date": "2025-12-29", "description": "December Cal APA Scores released", "category": "Program Event"},
    {"title": "PLI Spring Orientation Session", "date": "2026-01-07", "description": "Zoom 5-7pm, Meeting ID: 3726372789", "category": "Program Event"},
    {"title": "UCB Spring Semester Begins", "date": "2026-01-13", "description": "University of California Berkeley Spring Semester starts", "category": "Program Event"},
    {"title": "Cal APA Deadline", "date": "2026-01-15", "description": "Cal APA submission deadline", "category": "Deadline"},
    {"title": "MLK Day", "date": "2026-01-19", "description": "Martin Luther King Jr. Day holiday", "category": "Holiday"},
    {"title": "Required PLI CalAPA Work Session", "date": "2026-01-31", "description": "9-12pm (for anyone still working on Cycle 1 and/or 3)", "category": "Program Event"},
    {"title": "January Cal APA Scores released", "date": "2026-02-05", "description": "January Cal APA Scores released today", "category": "Program Event"},
    {"title": "PRESIDENT'S DAY Holiday", "date": "2026-02-16", "description": "President's Day holiday", "category": "Holiday"},
    {"title": "Cal APA Deadline", "date": "2026-02-19", "description": "Cal APA submission deadline", "category": "Deadline"},
    {"title": "INTERVIEW CLINIC", "date": "2026-02-28", "description": "Optional, but registration required", "category": "Program Event"},
    {"title": "MOCK INTERVIEWS", "date": "2026-03-07", "description": "Mock interview sessions", "category": "Program Event"},
    {"title": "Cal APA Deadline / February Cal APA Scores released", "date": "2026-03-12", "description": "Cal APA deadline and February scores released today", "category": "Deadline"},
    {"title": "UCB Spring Recess", "date": "2026-03-23", "description": "University of California Berkeley Spring Recess", "category": "Program Event"},
    {"title": "Cesar Chavez Day", "date": "2026-03-27", "description": "Cesar Chavez Day holiday", "category": "Holiday"},
    {"title": "March Cal APA Scores released", "date": "2026-04-02", "description": "March Cal APA Scores released today", "category": "Program Event"},
    {"title": "Cal APA Deadline", "date": "2026-04-04", "description": "Cal APA submission deadline", "category": "Deadline"},
    {"title": "AERA Conference", "date": "2026-04-23", "description": "AERA conference (April 23-25)", "category": "Program Event"},
    {"title": "April Cal APA Scores released", "date": "2026-04-30", "description": "April Cal APA Scores released today", "category": "Program Event"},
    {"title": "PLI SPRING ASSESSMENT CENTER", "date": "2026-05-02", "description": "Spring assessment center", "category": "Program Event"},
    {"title": "ORALS EXAMS", "date": "2026-05-05", "description": "Oral examinations", "category": "Program Event"},
    {"title": "ORALS EXAMS", "date": "2026-05-07", "description": "Oral examinations", "category": "Program Event"},
    {"title": "LEAD ASSESSMENT CENTER", "date": "2026-05-09", "description": "Leadership assessment center", "category": "Program Event"},
    {"title": "Cal APA Deadline", "date": "2026-05-14", "description": "Cal APA deadline, scores released 6/4", "category": "Deadline"},
    {"title": "Spring semester ends", "date": "2026-05-15", "description": "Spring semester concludes", "category": "Program Event"}
]

try:
    count = 0
    for event in events_data:
        # Check if already exists (by title and date)
        existing = db.query(CustomItem).filter(
            CustomItem.title == event['title'],
            CustomItem.due_date == datetime.strptime(event['date'], '%Y-%m-%d').date()
        ).first()

        if not existing:
            item = CustomItem(
                title=event['title'],
                description=event['description'],
                due_date=datetime.strptime(event['date'], '%Y-%m-%d').date(),
                category=event['category']
            )
            db.add(item)
            count += 1

    db.commit()
    print(f"\n✅ Successfully imported {count} PLI calendar events!")
    print(f"Total events in calendar: {len(events_data)}")

except Exception as e:
    db.rollback()
    print(f"❌ Error importing calendar: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
