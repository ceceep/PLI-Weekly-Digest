"""
Flask web application for PLI Weekly Digest
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from functools import wraps
from models import (
    Course, Session, Assignment, Reading, CustomItem, Subscriber, DigestHistory,
    get_session as get_db_session, init_db
)
from syllabus_parser import SyllabusParser
from gmail_digest_generator import GmailDigestGenerator
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Admin password
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '19PLI89!')

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Initialize database
init_db()

# Initialize scheduler for automated emails
scheduler = BackgroundScheduler()
digest_generator = GmailDigestGenerator()

# Schedule weekly digest (Sundays at 8am Pacific Time)
pacific = pytz.timezone('America/Los_Angeles')
scheduler.add_job(
    func=digest_generator.send_weekly_digest,
    trigger=CronTrigger(day_of_week='sun', hour=8, minute=0, timezone=pacific),
    id='weekly_digest',
    name='Send weekly digest',
    replace_existing=True
)

# Schedule daily reminder (Every day at 6pm Pacific Time)
scheduler.add_job(
    func=digest_generator.send_daily_reminder,
    trigger=CronTrigger(hour=18, minute=0, timezone=pacific),
    id='daily_reminder',
    name='Send daily reminder',
    replace_existing=True
)

scheduler.start()


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            next_url = request.args.get('next') or url_for('index')
            flash('Successfully logged in!', 'success')
            return redirect(next_url)
        else:
            flash('Incorrect password', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.pop('authenticated', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


@app.route('/')
def index():
    """Home page with dashboard"""
    db = get_db_session()

    # Get upcoming items (next 7 days)
    today = datetime.now().date()
    week_from_now = today + timedelta(days=7)

    upcoming_sessions = db.query(Session).filter(
        Session.date >= today,
        Session.date <= week_from_now
    ).order_by(Session.date).all()

    upcoming_assignments = db.query(Assignment).filter(
        Assignment.due_date >= today,
        Assignment.due_date <= week_from_now,
        Assignment.completed == False
    ).order_by(Assignment.due_date).all()

    upcoming_readings = db.query(Reading).filter(
        Reading.due_date >= today,
        Reading.due_date <= week_from_now,
        Reading.completed == False
    ).order_by(Reading.due_date).all()

    upcoming_custom = db.query(CustomItem).filter(
        CustomItem.due_date >= today,
        CustomItem.due_date <= week_from_now,
        CustomItem.completed == False
    ).order_by(CustomItem.due_date).all()

    courses = db.query(Course).all()
    subscriber_count = db.query(Subscriber).filter(Subscriber.active == True).count()

    db.close()

    return render_template('index.html',
                         sessions=upcoming_sessions,
                         assignments=upcoming_assignments,
                         readings=upcoming_readings,
                         custom_items=upcoming_custom,
                         courses=courses,
                         subscriber_count=subscriber_count)


@app.route('/upload_syllabus', methods=['GET', 'POST'])
@require_auth
def upload_syllabus():
    """Upload and parse a syllabus"""
    if request.method == 'POST':
        if 'syllabus' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)

        file = request.files['syllabus']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.pdf'):
            # Save temporarily
            temp_path = f"/tmp/{file.filename}"
            file.save(temp_path)

            try:
                # Parse syllabus
                parser = SyllabusParser()
                data = parser.parse_syllabus(temp_path)
                course_id = parser.import_to_database(data)

                flash(f'Successfully imported syllabus: {data["course"]["name"]}', 'success')
                return redirect(url_for('view_course', course_id=course_id))

            except Exception as e:
                flash(f'Error parsing syllabus: {str(e)}', 'error')
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        else:
            flash('Please upload a PDF file', 'error')

    return render_template('upload_syllabus.html')


@app.route('/manual_entry', methods=['GET', 'POST'])
@require_auth
def manual_entry():
    """Manually add assignments and readings"""
    db = get_db_session()

    if request.method == 'POST':
        entry_type = request.form['entry_type']
        course_id = request.form.get('course_id')

        if entry_type == 'assignment':
            assignment = Assignment(
                course_id=course_id if course_id else None,
                title=request.form['title'],
                description=request.form.get('description', ''),
                due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d').date(),
                points=request.form.get('points')
            )
            db.add(assignment)
            db.commit()
            flash('Assignment added successfully', 'success')

        elif entry_type == 'reading':
            reading = Reading(
                course_id=course_id if course_id else None,
                title=request.form['title'],
                authors=request.form.get('authors', ''),
                citation=request.form.get('citation', ''),
                pages=request.form.get('pages', ''),
                due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d').date(),
                url=request.form.get('url', '')
            )
            db.add(reading)
            db.commit()
            flash('Reading added successfully', 'success')

        elif entry_type == 'session':
            session = Session(
                course_id=course_id if course_id else None,
                session_number=request.form.get('session_number'),
                title=request.form['title'],
                date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
                time=request.form.get('time', ''),
                location=request.form.get('location', ''),
                description=request.form.get('description', '')
            )
            db.add(session)
            db.commit()
            flash('Session added successfully', 'success')

        db.close()
        return redirect(url_for('manual_entry'))

    courses = db.query(Course).all()
    db.close()

    return render_template('manual_entry.html', courses=courses)


@app.route('/course/<int:course_id>')
def view_course(course_id):
    """View course details"""
    db = get_db_session()
    course = db.query(Course).get(course_id)

    if not course:
        flash('Course not found', 'error')
        db.close()
        return redirect(url_for('index'))

    sessions = db.query(Session).filter(Session.course_id == course_id).order_by(Session.date).all()
    assignments = db.query(Assignment).filter(Assignment.course_id == course_id).order_by(Assignment.due_date).all()
    readings = db.query(Reading).filter(Reading.course_id == course_id).order_by(Reading.due_date).all()

    db.close()

    return render_template('course.html',
                         course=course,
                         sessions=sessions,
                         assignments=assignments,
                         readings=readings)


@app.route('/custom_items', methods=['GET', 'POST'])
def custom_items():
    """Manage custom items (reminders, events, etc.)"""
    db = get_db_session()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        category = request.form['category']
        course_id = request.form.get('course_id')

        item = CustomItem(
            course_id=course_id if course_id else None,
            title=title,
            description=description,
            due_date=due_date,
            category=category
        )
        db.add(item)
        db.commit()

        flash('Custom item added successfully', 'success')
        return redirect(url_for('custom_items'))

    items = db.query(CustomItem).order_by(CustomItem.due_date).all()
    courses = db.query(Course).all()

    db.close()

    return render_template('custom_items.html', items=items, courses=courses)


@app.route('/toggle_complete/<item_type>/<int:item_id>')
def toggle_complete(item_type, item_id):
    """Toggle completion status of an item"""
    db = get_db_session()

    model_map = {
        'assignment': Assignment,
        'reading': Reading,
        'custom': CustomItem
    }

    if item_type not in model_map:
        flash('Invalid item type', 'error')
        return redirect(url_for('index'))

    item = db.query(model_map[item_type]).get(item_id)

    if item:
        item.completed = not item.completed
        item.completed_at = datetime.now() if item.completed else None
        db.commit()
        flash('Item updated', 'success')
    else:
        flash('Item not found', 'error')

    db.close()
    return redirect(request.referrer or url_for('index'))


@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    """Public subscription page for classmates"""
    db = get_db_session()

    if request.method == 'POST':
        email = request.form['email']
        name = request.form.get('name', '')

        # Check if already exists
        existing = db.query(Subscriber).filter(Subscriber.email == email).first()

        if existing:
            if existing.active:
                flash('You are already subscribed! Check your email for digests every Sunday at 8am.', 'warning')
            else:
                existing.active = True
                db.commit()
                flash('Welcome back! Your subscription has been reactivated.', 'success')
        else:
            subscriber = Subscriber(email=email, name=name)
            db.add(subscriber)
            db.commit()
            flash('Success! You are now subscribed. Check your email for the weekly digest every Sunday at 8am PT.', 'success')

        db.close()
        return redirect(url_for('subscribe'))

    db.close()
    return render_template('subscribe.html')


@app.route('/subscribers', methods=['GET', 'POST'])
@require_auth
def subscribers():
    """Manage email subscribers"""
    db = get_db_session()

    if request.method == 'POST':
        email = request.form['email']
        name = request.form.get('name', '')

        # Check if already exists
        existing = db.query(Subscriber).filter(Subscriber.email == email).first()

        if existing:
            flash('Email already subscribed', 'warning')
        else:
            subscriber = Subscriber(email=email, name=name)
            db.add(subscriber)
            db.commit()
            flash('Subscriber added successfully', 'success')

        return redirect(url_for('subscribers'))

    subs = db.query(Subscriber).order_by(Subscriber.created_at.desc()).all()
    db.close()

    return render_template('subscribers.html', subscribers=subs)


@app.route('/toggle_subscriber/<int:sub_id>')
def toggle_subscriber(sub_id):
    """Toggle subscriber active status"""
    db = get_db_session()
    subscriber = db.query(Subscriber).get(sub_id)

    if subscriber:
        subscriber.active = not subscriber.active
        db.commit()
        flash('Subscriber updated', 'success')
    else:
        flash('Subscriber not found', 'error')

    db.close()
    return redirect(url_for('subscribers'))


@app.route('/history')
def history():
    """View past digest emails"""
    db = get_db_session()
    digests = db.query(DigestHistory).order_by(DigestHistory.sent_at.desc()).limit(50).all()
    db.close()

    return render_template('history.html', digests=digests)


@app.route('/preview_digest')
def preview_digest():
    """Preview what the weekly digest will look like"""
    generator = GmailDigestGenerator()

    today = datetime.now().date()
    end_of_week = today + timedelta(days=6)

    items = generator.get_week_items(today, end_of_week)
    html_content = generator.generate_weekly_html(items)

    return html_content


@app.route('/calendar')
def calendar():
    """Year-at-a-glance calendar view"""
    db = get_db_session()

    # Get all items for the entire academic year
    today = datetime.now().date()

    # Get sessions, assignments, readings, custom items
    sessions = db.query(Session).order_by(Session.date).all()
    assignments = db.query(Assignment).order_by(Assignment.due_date).all()
    readings = db.query(Reading).order_by(Reading.due_date).all()
    custom_items = db.query(CustomItem).order_by(CustomItem.due_date).all()
    courses = db.query(Course).all()

    db.close()

    return render_template('calendar.html',
                         sessions=sessions,
                         assignments=assignments,
                         readings=readings,
                         custom_items=custom_items,
                         courses=courses,
                         today=today)


@app.route('/send_test_digest')
def send_test_digest():
    """Manually trigger sending the weekly digest (for testing)"""
    try:
        generator = GmailDigestGenerator()
        generator.send_weekly_digest()
        flash('Weekly digest sent successfully', 'success')
    except Exception as e:
        flash(f'Error sending digest: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/import_educ269a')
@require_auth
def import_educ269a():
    """Import EDUC 269A syllabus data"""
    try:
        # Import the data
        from datetime import datetime

        db = get_db_session()

        # Check if course already exists
        existing = db.query(Course).filter(Course.code == "EDUC 269A").first()
        if existing:
            flash('EDUC 269A already imported!', 'warning')
            db.close()
            return redirect(url_for('index'))

        # Create course
        course = Course(
            name="Leadership Seminar: Leading for Equity",
            code="EDUC 269A",
            instructor="Dr. Lanette Jimerson"
        )
        db.add(course)
        db.flush()

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

        # Create readings
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

        db.commit()
        db.close()

        flash('Successfully imported EDUC 269A with 15 sessions, 10 assignments, and 3 readings!', 'success')
    except Exception as e:
        flash(f'Error importing EDUC 269A: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/import_educ460a')
@require_auth
def import_educ460a():
    """Import EDUC 460A syllabus data"""
    try:
        from datetime import datetime

        db = get_db_session()

        # Check if course already exists
        existing = db.query(Course).filter(Course.code == "EDUC 460A").first()
        if existing:
            flash('EDUC 460A already imported!', 'warning')
            db.close()
            return redirect(url_for('index'))

        # Create course
        course = Course(
            name="Practicum in School Site Management",
            code="EDUC 460A",
            instructor="Dr. nives wetzel de cediel"
        )
        db.add(course)
        db.flush()

        # Create sessions
        sessions_data = [
            (1, "Spring Overview, PLI Mid Year Coach/Coachee Reflection Questions, Planning for Summer Internships", "2025-01-24", "9am-noon", "In person, BWW 1203", "Spring Overview, PLI Mid Year Coach/Coachee Reflection Questions, Planning for Summer Internships, Check-In w/ Spring Home Group, Portfolios Ongoing reflection"),
            (2, "Mock Interview Prep and Practice", "2025-02-21", "1-4pm", "In person, BWW 1203", "Mock Interview Prep and Practice, What is a Mock Interview? How do you present as a leader? Resume tuning, More Metaphors, Internships, Summer Internship Resources & Guidelines"),
            (3, "Mock Interviews", "2025-03-07", "1-4pm (Mock Interviews 9am-noon)", "In person, BWW 1203", "Students will participate in Mock Interviews for the first half of the day. Class in the afternoon following Mock Interviews. Debrief & Reflection, Metaphors"),
            (4, "Leadership Experiences, Metaphor & Rubric Task", "2025-04-04", "1-4pm", "In person, BWW 1203", "C25 Leadership Experiences, Metaphor & Rubric Task (in-class-due April 4, by 5pm)"),
            (5, "Spring Portfolio", "2025-04-27", "6-9pm", "Online (zoom)", "Spring Portfolio, Sneak Peak at Summer 2026")
        ]

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

        db.commit()
        db.close()

        flash('Successfully imported EDUC 460A with 5 sessions, 4 assignments, and 1 reading!', 'success')
    except Exception as e:
        flash(f'Error importing EDUC 460A: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/import_educ263b')
@require_auth
def import_educ263b():
    """Import EDUC 263B syllabus data"""
    try:
        from datetime import datetime

        db = get_db_session()

        # Check if course already exists
        existing = db.query(Course).filter(Course.code == "EDUC 263B").first()
        if existing:
            flash('EDUC 263B already imported!', 'warning')
            db.close()
            return redirect(url_for('index'))

        # Create course
        course = Course(
            name="Legal and Policy Issues in Urban Education",
            code="EDUC 263B",
            instructor="Shannon Woo Williams-Zou"
        )
        db.add(course)
        db.flush()

        # Create sessions
        sessions_data = [
            (1, "Introduction to the Course and Critical Race Theory", "2026-01-10", "9-12", "In person, room 1102", "Begin to build our learning community, establish a general understanding of CRT"),
            (2, "Inequity by Design: Race & the American Public Education System", "2026-01-10", "1-4", "In Person, room 1102", "Explore CRT's application to Education and identify institutional practices"),
            (3, "Intro to Student Discipline", "2026-01-26", "6-9", "In person, room 1102", "Increase understanding of school discipline laws"),
            (4, "Investigations & Implicit Bias in Student Discipline", "2026-02-02", "6-9", "Virtual", "Learn how to conduct a student disciplinary investigation"),
            (5, "Discipline of Students with Disabilities", "2026-02-09", "6-9", "Virtual", "Increased understanding of special education discipline laws"),
            (6, "Student Removals: Manifestation Determination & Expulsion Hearings", "2026-02-17", "6-9", "Virtual", "Learn how to prepare an expulsion packet"),
            (7, "Intro to Dis/ability Critical Race Studies (DisCrit) & Special Education Law", "2026-02-23", "6-9", "In person, room 1102", "Consider the implications that Dis/Crit has for our work"),
            (8, "Intro to the IEP Process and Section 504 of the Rehabilitation Act", "2026-03-09", "6-9", "Virtual", "Learn the components of a compliant IEP"),
            (9, "IEP Process and Section 504, Part 2: Role Plays", "2026-03-16", "6-9", "In person, room 1102", "Practical application through role plays"),
            (10, "Proactively Building Strong Communities: Restorative Practices & Anti-Bullying", "2026-03-23", "6-9", "Virtual", "Learn the basic principles and structures of restorative practices"),
            (11, "Harassment and Anti-discrimination", "2026-04-06", "6-9", "In person, room 1102", "Increase understanding of federal harassment and anti-discrimination laws"),
            (12, "Mock manifestation determination and expulsion hearing", "2026-04-13", "6-9", "In person, room 1102", "In-class performance task with mandatory attendance"),
            (13, "Mock Re-entry Circle & Course Closing Circle", "2026-04-20", "6-9", "In person, room 1102", "In-class performance task with mandatory attendance")
        ]

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

        # Create assignments
        assignments_data = [
            ("Discipline Hypo #1", "Apply discipline laws to hypothetical situation using IRAC format", "2026-02-02", 100),
            ("Implicit Bias Reflection #1", "Reflection on implicit bias in disciplinary situations", "2026-02-09", 100),
            ("Discipline Hypo #2", "Apply discipline laws to hypothetical situation", "2026-02-17", 100),
            ("Complex Discipline Hypo: Implicit Bias Reflection component", "Bias reflection component of the complex discipline hypo analysis", "2026-02-23", 100),
            ("Complex Discipline Hypo: Final Group Analysis paper", "Culminating group project analyzing complex disciplinary scenario", "2026-03-16", 200),
            ("Complex Discipline Hypo: Mock Expulsion & Manifestation Determination Hearings", "Documents and preparation for mock hearings", "2026-04-06", 300),
            ("Complex Discipline Hypo: Mock Re-entry Circle", "Participation in mock restorative re-entry circle", "2026-04-13", 100),
            ("End of semester reflection", "Final reflection on course learning", "2026-04-18", 100)
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

        # Create readings
        readings_data = [
            ("Special education and the law: A guide for practitioners", "Osborne, A. G., Russo, C. J., Lavoie, R. D., & Eckes, S.", "pp. 2-4", "2026-01-10", ""),
            ("Introduction and Hallmark Critical Race Theory Themes", "Delgado, R., Stefancic, J., & Harris, A. P.", "", "2026-01-10", ""),
            ("Improving Student Achievement Through the Creation of Relationships", "Dome, D.", "", "2026-01-10", ""),
            ("California Education Code", "", "Sections 48900 – 48927", "2026-01-26", ""),
            ("Student Discipline Resource Binder", "Dome, D.", "Chapters 1-4", "2026-01-26", "")
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

        db.commit()
        db.close()

        flash('Successfully imported EDUC 263B with 13 sessions, 8 assignments, and 5 readings!', 'success')
    except Exception as e:
        flash(f'Error importing EDUC 263B: {str(e)}', 'error')

    return redirect(url_for('index'))


if __name__ == '__main__':
    # Get port from environment variable (for cloud deployment) or default to 5000
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
