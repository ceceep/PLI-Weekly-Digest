"""
Add ALL missing readings to EDUC 263B from the full syllabus
"""
from datetime import datetime
from models import Course, Reading, get_session, init_db

# Initialize database
init_db()

db = get_session()

try:
    # Get EDUC 263B
    course = db.query(Course).filter(Course.code == "EDUC 263B").first()
    if not course:
        print("❌ EDUC 263B not found!")
        db.close()
        exit(1)

    print(f"Found course: {course.name}")
    print(f"Current readings: {len(course.readings)}")

    # ALL readings from the full 263B syllabus
    new_readings = [
        # Session 1 - Jan 10 (AM)
        ("The class syllabus", "", "", "2026-01-10", "READ: The class syllabus - calendar important due dates"),
        ("Special education and the law: Sources of Law", "Osborne, A. G., Russo, C. J., Lavoie, R. D., & Eckes, S.", "pp. 2-4", "2026-01-10", "Pages 2-4 only, Sources of Law section"),
        ("Introduction and Hallmark Critical Race Theory Themes", "Delgado, R., Stefancic, J., & Harris, A. P.", "", "2026-01-10", "In Critical race theory: An introduction. New York: New York University Press. (in reader)"),
        ("Improving Student Achievement Through the Creation of Relationships", "Dome, D.", "", "2026-01-10", "Oakland, CA: Dora Dome Law"),
        ("The Insurgent Origins of Critical Race Theory (Podcast)", "Crenshaw, K.", "", "2026-01-10", "Intersectionality Matters podcast, 1 hr 12 min"),

        # Session 2 - Jan 10 (PM)
        ("New Jim Crow, Chapter 1", "Alexander, M.", "", "2026-01-10", ""),
        ("Mandate for Leadership: The Mission", "The Heritage Foundation", "pp. 319-320", "2026-01-10", "2025 Presidential Transition Project"),
        ("Mandate for Leadership: New Policy Priorities", "The Heritage Foundation", "pp. 441-351", "2026-01-10", "Close read section"),
        ("The Historical Context of Oppression (Lecture)", "", "", "2026-01-10", "VIDEO LECTURE"),

        # Session 3 - Jan 26
        ("California Education Code, Sections 48900-48927", "", "", "2026-01-26", "Student Discipline Code of Conduct"),
        ("Student Discipline Resource Binder, Chapters 1-4", "Dome, D.", "", "2026-01-26", "A Comprehensive Guide for K-12 Schools"),
        ("A Quick Guide to IRAC", "", "", "2026-01-26", ""),
        ("School Discipline Overview and suspensions (Lecture 1)", "", "", "2026-01-26", "VIDEO LECTURE"),
        ("Expulsions (Lecture 2)", "", "", "2026-01-26", "VIDEO LECTURE"),

        # Session 4 - Feb 2
        ("New Jim Crow, Chapter 3", "Alexander, M.", "pp. 95-106", "2026-02-02", ""),
        ("Do We Have A Bias Problem?", "Benson, T. A., & Fiarman, S. E.", "", "2026-02-02", "In Unconscious bias in schools"),
        ("Guilty as charged? Principals' perspectives on disciplinary practices", "DeMatthews, D. E., Carey, R. L., Olivarez, A., & Moussavi Saeedi, K.", "", "2026-02-02", "Educational Administration Quarterly, 53(4), 519-555"),
        ("Lost Opportunities: Executive Summary", "Losen, D and Martinez, P.", "pp. 2-10", "2026-02-02", "How Disparate School Discipline Continues"),
        ("Sidelining bias: A Situationist approach", "Okonofua, J. A., Harris, L. T., & Walton, G. M.", "", "2026-02-02", "Current Directions in Psychological Science"),
        ("Disciplinary Investigations, Searches, and Seizures (Lecture 1)", "", "", "2026-02-02", "VIDEO LECTURE"),
        ("Unconscious Bias: How It Happens (Lecture 2)", "", "", "2026-02-02", "VIDEO LECTURE"),
        ("Implicit Bias: What to Do About It (Lecture 3)", "", "", "2026-02-02", "VIDEO LECTURE"),

        # Session 5 - Feb 9
        ("Special education and the law, Chapter 6", "Osborne, A. G., Russo, C. J., Lavoie, R. D., & Eckes, S.", "", "2026-02-09", ""),
        ("Federal Register, 34 CFR Part 300, Sections 300.530-300.537", "", "", "2026-02-09", "Special Education Discipline"),
        ("Student Discipline Book, Chapters 5-6", "Dome, D.", "", "2026-02-09", ""),
        ("Discipline of Students with Disabilities (Lecture)", "", "", "2026-02-09", "VIDEO LECTURE"),

        # Session 6 - Feb 17
        ("California Education Code, Sections 48900-48918.6", "", "", "2026-02-17", ""),
        ("Student Discipline Resource Binder, Chapters 2 & 4", "Dome, D.", "", "2026-02-17", ""),
        ("Expulsion Hearings and the Role of the Administrative Panel (Lecture 1)", "", "", "2026-02-17", "VIDEO LECTURE"),
        ("Manifestation Determination (Lecture 2 - Rewatch)", "", "", "2026-02-17", "VIDEO LECTURE"),
        ("California Education Code Section 48915.5", "", "", "2026-02-17", ""),
        ("The Bill Troublesome Expulsion Packet", "", "pp. 15-33", "2026-02-17", "Witness statements and police reports"),

        # Session 7 - Feb 23
        ("DIS/Ability Critical Race Studies (DisCrit)", "Annamma, S. A., Connor, D., & Ferri, B.", "", "2026-02-23", "Race Ethnicity and Education, 16(1), 1-31"),
        ("Special education and the law, pp. 6-16 and chapters 3-5", "Osborne, A. G., Russo, C. J., Lavoie, R. D., & Eckes, S.", "", "2026-02-23", ""),
        ("34 CFR 300.8 Eligibility Criteria", "", "", "2026-02-23", ""),
        ("California Education Code, Sections 56300-56347, 56441.11, 56500-56525", "", "", "2026-02-23", ""),
        ("Title V CCR 3030", "", "", "2026-02-23", ""),
        ("Special Education Overview & IEP Process (Lecture)", "", "", "2026-02-23", "VIDEO LECTURE"),

        # Session 8 - Mar 9
        ("Special education and the law, Chapter 9", "Osborne, A. G., Russo, C. J., Lavoie, R. D., & Eckes, S.", "", "2026-03-09", ""),
        ("Section 504 of Rehabilitation Act sections 104.1-104.4 and 104.31-104.39", "", "", "2026-03-09", ""),
        ("IEPs vs 504s (Lecture 1)", "", "", "2026-03-09", "VIDEO LECTURE"),
        ("504 Plans (Lecture 2)", "", "", "2026-03-09", "VIDEO LECTURE"),

        # Session 10 - Mar 23
        ("Understanding Othering and Belonging (Video)", "", "", "2026-03-23", "VIDEO - 23 min"),
        ("The Future of Healing: Shifting from Trauma Informed Care to Healing Centered Engagement", "Ginwright, S.", "", "2026-03-23", ""),
        ("Bullying: Definition & Terms, Laws, and Intervention (Lecture)", "", "", "2026-03-23", "VIDEO LECTURE"),
        ("Restorative justice conferencing, chapters 1-4", "Wachtel, T., O'Connell, T., & Wachtel, B.", "", "2026-03-23", "Real justice & the conferencing handbook"),
        ("Restorative Welcome & Re-entry Circle (Video)", "Restorative Justice for Oakland Youth", "", "2026-03-23", "VIDEO - 14 min"),

        # Session 11 - Apr 6
        ("Federal Harassment Law (reader)", "", "", "2026-04-06", ""),
        ("USDOE Dear Colleague Letter: Harassment and Bullying", "", "", "2026-04-06", ""),
        ("Uniform Complaint Procedures - AR 1312.3", "", "", "2026-04-06", ""),
        ("Reinstating common sense school discipline policies", "The White House", "", "2026-04-06", "Presidential Action, April 23, 2025"),
    ]

    # Check which ones already exist
    existing_titles = {r.title for r in course.readings}
    added_count = 0

    print("\nChecking for duplicates and adding new readings...")
    for title, authors, pages, due_date_str, citation in new_readings:
        if title not in existing_titles:
            reading = Reading(
                course_id=course.id,
                title=title,
                authors=authors,
                pages=pages,
                due_date=datetime.strptime(due_date_str, '%Y-%m-%d').date(),
                citation=citation
            )
            db.add(reading)
            added_count += 1
            print(f"  ✓ Added: {title}")
        else:
            print(f"  ⊘ Skipped (exists): {title}")

    db.commit()

    # Get updated count
    updated_course = db.query(Course).filter(Course.code == "EDUC 263B").first()
    print(f"\n✅ Successfully added {added_count} new readings!")
    print(f"Total readings now: {len(updated_course.readings)}")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
