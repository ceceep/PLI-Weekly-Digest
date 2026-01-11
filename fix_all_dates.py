"""
Fix all 2025 dates by converting them to 2026
"""
from datetime import datetime, timedelta
from models import Session, Assignment, Reading, Course, CustomItem, get_session, init_db
from sqlalchemy import extract

init_db()
db = get_session()

print("="*60)
print("FIXING ALL 2025 DATES TO 2026")
print("="*60)

# Fix Sessions
sessions_2025 = db.query(Session).filter(extract('year', Session.date) == 2025).all()
print(f"\nFound {len(sessions_2025)} sessions with 2025 dates")
for session in sessions_2025:
    old_date = session.date
    # Add one year
    session.date = datetime(2026, old_date.month, old_date.day).date()
    print(f"  Fixed: {old_date} → {session.date} | {session.title}")

# Fix Assignments
assignments_2025 = db.query(Assignment).filter(extract('year', Assignment.due_date) == 2025).all()
print(f"\nFound {len(assignments_2025)} assignments with 2025 dates")
for assignment in assignments_2025:
    old_date = assignment.due_date
    assignment.due_date = datetime(2026, old_date.month, old_date.day).date()
    print(f"  Fixed: {old_date} → {assignment.due_date} | {assignment.title}")

# Fix Readings
readings_2025 = db.query(Reading).filter(extract('year', Reading.due_date) == 2025).all()
print(f"\nFound {len(readings_2025)} readings with 2025 dates")
for reading in readings_2025:
    old_date = reading.due_date
    reading.due_date = datetime(2026, old_date.month, old_date.day).date()
    print(f"  Fixed: {old_date} → {reading.due_date} | {reading.title}")

# Fix Custom Items (already did this but double-check)
custom_2025 = db.query(CustomItem).filter(extract('year', CustomItem.due_date) == 2025).all()
print(f"\nFound {len(custom_2025)} custom items with 2025 dates")
for item in custom_2025:
    old_date = item.due_date
    item.due_date = datetime(2026, old_date.month, old_date.day).date()
    print(f"  Fixed: {old_date} → {item.due_date} | {item.title}")

db.commit()
db.close()

print("\n" + "="*60)
print("✅ ALL DATES FIXED TO 2026!")
print("="*60)
