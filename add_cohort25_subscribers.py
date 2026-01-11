"""
Add PLI Cohort 25 subscribers to the database
"""
from datetime import datetime
from models import Subscriber, get_session, init_db

# Initialize database
init_db()

db = get_session()

try:
    # List of email addresses to add
    emails = [
        "daechelle_m@berkeley.edu",
        "k_yoshiispiegelman@berkeley.edu",
        "rosandoval@berkeley.edu",
        "snapoliellocheveres@berkeley.edu",
        "youngsarah00@berkeley.edu",
        "jrwoo10102414@berkeley.edu",
        "juamolin@berkeley.edu",
        "evabeleche@berkeley.edu",
        "yschang@berkeley.edu",
        "leangelo.acuna@berkeley.edu",
        "lenagarcia@berkeley.edu",
        "luz_salazar-Jed@berkeley.edu"
    ]

    print(f"Adding {len(emails)} subscribers...")

    # Check which ones already exist
    existing_emails = {s.email.lower() for s in db.query(Subscriber).all()}
    added_count = 0
    skipped_count = 0

    for email in emails:
        if email.lower() not in existing_emails:
            subscriber = Subscriber(email=email, subscribed_at=datetime.utcnow())
            db.add(subscriber)
            added_count += 1
            print(f"  ✓ Added: {email}")
        else:
            skipped_count += 1
            print(f"  ⊘ Skipped (exists): {email}")

    db.commit()
    db.close()

    print(f"\n✅ Successfully added {added_count} new subscribers!")
    if skipped_count > 0:
        print(f"   ({skipped_count} already existed)")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
