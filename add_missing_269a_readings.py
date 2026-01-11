"""
Add missing readings to EDUC 269A
"""
from datetime import datetime
from models import Course, Reading, get_session, init_db

# Initialize database
init_db()

db = get_session()

try:
    # Get EDUC 269A
    course = db.query(Course).filter(Course.code == "EDUC 269A").first()
    if not course:
        print("❌ EDUC 269A not found!")
        db.close()
        exit(1)

    print(f"Found course: {course.name}")
    print(f"Current readings: {len(course.readings)}")

    # Missing readings to add
    new_readings = [
        # Session 1 - Jan 12
        ("CII and Orals Guide", "", "", "2026-01-12", "Read CII and Orals Guide. Start the readings by first asking yourself what you already know about the topic of Change Theory"),
        ("CalAPA Cycle 2 Overview Slides", "", "", "2026-01-12", "📽 Review CalAPA Cycle 2 Overview Slides found in the CalAPA Support Course on bCourses (VIDEO)"),

        # Session 3 - Jan 28
        ("Change Agents, Chapter 1: Are you a Change Agent?", "Cohen, J.", "pp. 11-34", "2026-01-28", ""),
        ("Woven in Deeply: Identity and leadership of urban school principals", "Theoharis, G.", "", "2026-01-28", "Education and Urban Society, 41 (1), 3-25"),
        ("CalAPA Assessment Guide Steps 2 & 3", "", "", "2026-01-28", "CalAPA Assessment Guide and Submission Templates Steps 2 & 3 (Pre-Class Assignment)"),
        ("CalAPA Cycle 2 Step 2 & 3 Videos", "", "", "2026-01-28", "📽 CalAPA Cycle 2 Step 2 & 3 Videos (Pre-Class Assignment, Watch and Take Notes) (VIDEO)"),
        ("CII Model Paper I", "", "", "2026-01-28", "CII Model Paper I (example)"),
        ("CII Model Paper II", "", "", "2026-01-28", "CII Model Paper II (example)"),

        # Session 4 - Feb 11
        ("Change Agents, Chapter 2: Assembling Your Crew?", "Cohen, J.", "pp. 35-55", "2026-02-11", ""),
        ("Change Agents, Chapter 3: Finding Bright Spots and Building Momentum", "Cohen, J.", "pp. 57-81", "2026-02-11", ""),
        ("The New Meaning of Educational Change, Chapter 5: Planning, Doing and Coping with Change", "Fullan, M.", "pp. 82-93", "2026-02-11", ""),

        # Session 5 - Feb 21
        ("Change Agents, Chapter 4: Focus, Follow, Through, See: The Art and Science of Implementation", "Cohen, J.", "pp. 83-106", "2026-02-21", ""),
        ("CalAPA Assessment Guide Step 4", "", "", "2026-02-21", "CalAPA Assessment Guide and Submission Templates Step 4 (Pre-Class Assignment)"),

        # Session 6 - Feb 25
        ("Students' own literature review", "", "", "2026-02-25", "Review your own literature review"),
        ("Change Agents, Chapter 5: Who Said Change Was Gonna Be Easy?", "Cohen, J.", "pp. 107-124", "2026-02-25", ""),

        # Session 7 - Mar 4
        ("Changing the Discourse in Schools and Discourse I & II 'T' Chart", "Eubanks, E., Parish, R., Smith, D.", "", "2026-03-04", ""),
        ("Change Agents, Chapter 7: School Transformation Requires Personal Transformation", "Cohen, J.", "pp. 141-158", "2026-03-04", ""),

        # Session 8/9 - Mar 21
        ("Leadership on the line: Staying alive through the dangers of leading", "Heifetz, R. & Linsky, M.", "pp. 31-74", "2026-03-21", "continuation from Summer 272B"),
        ("The New Meaning of Educational Change, Chapters 6 & 7", "Fullan, M.", "pp. 97-137", "2026-03-21", "Part II: Educational Change at the Local Level"),
        ("CalAPA Cycle 2 Step 4 Videos", "", "", "2026-03-21", "📽 CalAPA Cycle 2 Step 4 Videos (Pre-Class Assignment, Watch and Take Notes) (VIDEO)"),

        # Session 10 - Mar 25
        ("The New Meaning of Educational Change, Chapters 8 & 9", "Fullan, M.", "pp. 138-176", "2026-03-25", "Part II: Educational Change at the Local Level"),
        ("CII Model Paper IV: Integrated Social-Emotional Learning to Interrupt Disproportionality in Discipline", "Founds, Jennifer K.", "", "2026-03-25", ""),

        # Session 11 - Mar 31
        ("Change Agents, Chapter 11: Thriving Schools, Thriving Communities", "Cohen, J.", "pp. 223-243", "2026-03-31", ""),
        ("CII Model Paper III: Building the Instructional Leadership Team Capacity", "Tran, Jonathan", "", "2026-03-31", ""),
        ("CII Model Paper IV: Coherence in Elementary School Math Teaching and Learning", "Riggs, Kelly", "", "2026-03-31", ""),
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
    updated_course = db.query(Course).filter(Course.code == "EDUC 269A").first()
    print(f"\n✅ Successfully added {added_count} new readings!")
    print(f"Total readings now: {len(updated_course.readings)}")

except Exception as e:
    db.rollback()
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
