"""
Flask web application for PLI Weekly Digest
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from functools import wraps
from models import (
    Course, Session, Assignment, Reading, CustomItem, Subscriber, DigestHistory, User,
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

# Authentication decorators
def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require user to be logged in as admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login', next=request.url))

        db = get_db_session()
        user = db.query(User).get(session['user_id'])
        db.close()

        if not user or not user.is_admin():
            flash('You must be an admin to access this page', 'error')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function


# Backwards compatibility alias
require_auth = admin_required

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


@app.route('/setup_admin', methods=['GET', 'POST'])
def setup_admin():
    """One-time setup route to create initial admin user"""
    # Security: Require setup token from environment variable
    setup_token = os.getenv('SETUP_TOKEN', 'pli-setup-2026')
    provided_token = request.args.get('token') or request.form.get('token')

    if provided_token != setup_token:
        return "Invalid setup token", 403

    db = get_db_session()

    # Check if any admin users already exist
    existing_admin = db.query(User).filter_by(role='admin').first()
    if existing_admin:
        db.close()
        return """
        <html><body style='font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;'>
        <h2>⚠️ Setup Already Complete</h2>
        <p>An admin user already exists. Please log in at <a href='/login'>/login</a></p>
        </body></html>
        """, 400

    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')

        # Create admin user
        user = User(
            email=email,
            name=name,
            role='admin'
        )
        user.set_password(password)

        db.add(user)
        db.commit()
        db.close()

        return f"""
        <html><body style='font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;'>
        <h2>✅ Admin User Created!</h2>
        <p>Admin user <strong>{email}</strong> has been created successfully.</p>
        <p><a href='/login' style='display: inline-block; padding: 10px 20px; background: #003262; color: white; text-decoration: none; border-radius: 4px;'>Go to Login</a></p>
        </body></html>
        """

    db.close()

    # Show setup form
    return f"""
    <html>
    <head>
        <title>Admin Setup - PLI Weekly Digest</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 500px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .card {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #003262;
                margin-top: 0;
            }}
            .form-group {{
                margin-bottom: 15px;
            }}
            label {{
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #003262;
            }}
            input {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                box-sizing: border-box;
            }}
            button {{
                width: 100%;
                padding: 12px;
                background: #003262;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                margin-top: 10px;
            }}
            button:hover {{
                background: #002147;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🔧 Admin Setup</h1>
            <p>Create the initial admin user for PLI Weekly Digest</p>
            <form method="POST">
                <input type="hidden" name="token" value="{provided_token}">
                <div class="form-group">
                    <label for="email">Email *</label>
                    <input type="email" id="email" name="email" required value="cecee_penney@berkeley.edu">
                </div>
                <div class="form-group">
                    <label for="name">Full Name *</label>
                    <input type="text" id="name" name="name" required value="Cecee Penney">
                </div>
                <div class="form-group">
                    <label for="password">Password *</label>
                    <input type="password" id="password" name="password" required minlength="8">
                </div>
                <button type="submit">Create Admin User</button>
            </form>
        </div>
    </body>
    </html>
    """


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        db = get_db_session()
        user = db.query(User).filter(User.email == email).first()

        if user and user.active and user.check_password(password):
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()

            # Set session
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_role'] = user.role
            session['user_name'] = user.name

            db.close()

            next_url = request.args.get('next') or url_for('index')
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_url)
        else:
            db.close()
            flash('Invalid email or password', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
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

    # Get current user info
    current_user = None
    if session.get('user_id'):
        current_user = db.query(User).get(session['user_id'])

    db.close()

    return render_template('index.html',
                         sessions=upcoming_sessions,
                         assignments=upcoming_assignments,
                         readings=upcoming_readings,
                         custom_items=upcoming_custom,
                         courses=courses,
                         subscriber_count=subscriber_count,
                         current_user=current_user)


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
@require_auth
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

    # Get current user info
    current_user = None
    if session.get('user_id'):
        current_user = db.query(User).get(session['user_id'])

    db.close()

    return render_template('calendar.html',
                         sessions=sessions,
                         assignments=assignments,
                         readings=readings,
                         custom_items=custom_items,
                         courses=courses,
                         today=today,
                         current_user=current_user)


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
            (1, "Spring Overview, PLI Mid Year Coach/Coachee Reflection Questions, Planning for Summer Internships", "2026-01-24", "9am-noon", "In person, BWW 1203", "Spring Overview, PLI Mid Year Coach/Coachee Reflection Questions, Planning for Summer Internships, Check-In w/ Spring Home Group, Portfolios Ongoing reflection"),
            (2, "Mock Interview Prep and Practice", "2026-02-21", "1-4pm", "In person, BWW 1203", "Mock Interview Prep and Practice, What is a Mock Interview? How do you present as a leader? Resume tuning, More Metaphors, Internships, Summer Internship Resources & Guidelines"),
            (3, "Mock Interviews", "2026-03-07", "1-4pm (Mock Interviews 9am-noon)", "In person, BWW 1203", "Students will participate in Mock Interviews for the first half of the day. Class in the afternoon following Mock Interviews. Debrief & Reflection, Metaphors"),
            (4, "Leadership Experiences, Metaphor & Rubric Task", "2026-04-04", "1-4pm", "In person, BWW 1203", "C25 Leadership Experiences, Metaphor & Rubric Task (in-class-due April 4, by 5pm)"),
            (5, "Spring Portfolio", "2026-04-27", "6-9pm", "Online (zoom)", "Spring Portfolio, Sneak Peak at Summer 2026")
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
            ("Complete the Fall Reflective Narrative: Leadership Competency Development", "Review your Fall Portfolio Feedback, the CTC CAPE CACE document and the PLI Leadership Connection Rubric to inform your reflection", "2026-02-07", 25),
            ("Revised Fall Portfolio", "Incorporate feedback received from home group and instructors to make revisions to fall portfolio", "2026-02-06", 10),
            ("Final Resume & Cover Letter", "Create final draft of resume and cover letter for Mock Interviews using provided resources and group feedback", "2026-02-27", 25),
            ("Spring Portfolio", "Add leadership experiences for Spring Semester which reflect both breadth and depth of experience, including approved spring logs and revised Fall Portfolio", "2026-05-08", 50)
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
            ("Metaphor as a tool in educational leadership classrooms", "Singh, K.", "", "2026-04-04", "")
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


@app.route('/import_educ262a')
@require_auth
def import_educ262a():
    """Import EDUC 262A syllabus data"""
    try:
        from datetime import datetime

        db = get_db_session()

        # Check if course already exists
        existing = db.query(Course).filter(Course.code == "EDUC 262A").first()
        if existing:
            flash('EDUC 262A already imported!', 'warning')
            db.close()
            return redirect(url_for('index'))

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

        # Create readings (4 readings from your info)
        readings_data = [
            ("Founding the American school system", "Labaree, David F.", "pp. 42-79", "2026-01-14", "In Someone has to fail: The zero-sum game of public schooling. Cambridge: Harvard University Press."),
            ("Does the Negro need separate schools?", "Du Bois, W. B.", "pp. 328-335", "2026-01-14", "Journal of Negro Education (1935)"),
            ("Teaching to Change, Chapter 2", "Oakes, Lipton, Anderson, Stillman", "", "2026-01-20", ""),
            ("From the Achievement Gap to Education Debt", "Ladson-Billings", "", "2026-01-21", ""),
            ("Generalizing Across Borders: Policy & Limits of Educational Science", "Luke, A.", "", "2026-01-21", "")
        ]

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

        db.commit()
        db.close()

        flash('Successfully imported EDUC 262A with 14 sessions and 5 readings!', 'success')
    except Exception as e:
        flash(f'Error importing EDUC 262A: {str(e)}', 'error')

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


@app.route('/cleanup_2025_dates')
@require_auth
def cleanup_2025_dates():
    """Remove any custom items with 2025 dates"""
    try:
        from datetime import datetime

        db = get_db_session()

        # Delete all items with dates before 2026
        deleted = db.query(CustomItem).filter(
            CustomItem.due_date < datetime(2026, 1, 1).date()
        ).delete()

        db.commit()
        db.close()

        flash(f'Successfully deleted {deleted} item(s) with 2025 dates!', 'success')
    except Exception as e:
        flash(f'Error cleaning up dates: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/fix_all_2025_dates')
@require_auth
def fix_all_2025_dates():
    """Convert all 2025 dates to 2026 across all models"""
    try:
        from datetime import datetime
        from sqlalchemy import extract

        db = get_db_session()

        fixed_counts = {
            'sessions': 0,
            'assignments': 0,
            'readings': 0,
            'custom_items': 0
        }

        # Fix Sessions
        sessions_2025 = db.query(Session).filter(extract('year', Session.date) == 2025).all()
        for session in sessions_2025:
            old_date = session.date
            session.date = datetime(2026, old_date.month, old_date.day).date()
            fixed_counts['sessions'] += 1

        # Fix Assignments
        assignments_2025 = db.query(Assignment).filter(extract('year', Assignment.due_date) == 2025).all()
        for assignment in assignments_2025:
            old_date = assignment.due_date
            assignment.due_date = datetime(2026, old_date.month, old_date.day).date()
            fixed_counts['assignments'] += 1

        # Fix Readings
        readings_2025 = db.query(Reading).filter(extract('year', Reading.due_date) == 2025).all()
        for reading in readings_2025:
            old_date = reading.due_date
            reading.due_date = datetime(2026, old_date.month, old_date.day).date()
            fixed_counts['readings'] += 1

        # Fix Custom Items
        custom_2025 = db.query(CustomItem).filter(extract('year', CustomItem.due_date) == 2025).all()
        for item in custom_2025:
            old_date = item.due_date
            item.due_date = datetime(2026, old_date.month, old_date.day).date()
            fixed_counts['custom_items'] += 1

        db.commit()
        db.close()

        total = sum(fixed_counts.values())
        message = f'Successfully converted {total} dates from 2025 to 2026! '
        message += f'(Sessions: {fixed_counts["sessions"]}, Assignments: {fixed_counts["assignments"]}, '
        message += f'Readings: {fixed_counts["readings"]}, Custom Items: {fixed_counts["custom_items"]})'

        flash(message, 'success')
    except Exception as e:
        flash(f'Error fixing dates: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/import_pli_calendar')
@require_auth
def import_pli_calendar():
    """Import PLI program-wide calendar events"""
    try:
        from datetime import datetime

        db = get_db_session()

        events_data = [
            # Removed 2025-12-29 date - only 2026 dates
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
        db.close()

        flash(f'Successfully imported {count} PLI calendar events!', 'success')
    except Exception as e:
        flash(f'Error importing calendar: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/add_missing_269a_readings')
@require_auth
def add_missing_269a_readings():
    """Add missing readings to EDUC 269A"""
    try:
        db = get_db_session()

        # Get EDUC 269A
        course = db.query(Course).filter(Course.code == "EDUC 269A").first()
        if not course:
            flash('EDUC 269A not found!', 'error')
            return redirect(url_for('index'))

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

        db.commit()
        db.close()

        flash(f'Successfully added {added_count} new readings to EDUC 269A!', 'success')
    except Exception as e:
        flash(f'Error adding readings: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/add_missing_263b_readings')
@require_auth
def add_missing_263b_readings():
    """Add ALL missing readings to EDUC 263B from the full syllabus"""
    try:
        db = get_db_session()

        # Get EDUC 263B
        course = db.query(Course).filter(Course.code == "EDUC 263B").first()
        if not course:
            flash('EDUC 263B not found!', 'error')
            return redirect(url_for('index'))

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

        db.commit()
        db.close()

        flash(f'Successfully added {added_count} new readings to EDUC 263B!', 'success')
    except Exception as e:
        flash(f'Error adding readings: {str(e)}', 'error')

    return redirect(url_for('index'))


@app.route('/users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    """Manage user accounts (admin only)"""
    db = get_db_session()

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        name = request.form.get('name', '')
        role = request.form['role']

        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            flash('User with this email already exists', 'warning')
        else:
            user = User(email=email, name=name, role=role)
            user.set_password(password)
            db.add(user)
            db.commit()
            flash(f'User {name} created successfully!', 'success')

        return redirect(url_for('manage_users'))

    users = db.query(User).order_by(User.created_at.desc()).all()
    db.close()

    return render_template('users.html', users=users)


@app.route('/toggle_user/<int:user_id>')
@admin_required
def toggle_user(user_id):
    """Toggle user active status"""
    db = get_db_session()
    user = db.query(User).get(user_id)

    if user:
        # Don't allow deactivating yourself
        if user.id == session.get('user_id'):
            flash('You cannot deactivate your own account', 'warning')
        else:
            user.active = not user.active
            db.commit()
            flash(f'User {user.name} {"activated" if user.active else "deactivated"}', 'success')
    else:
        flash('User not found', 'error')

    db.close()
    return redirect(url_for('manage_users'))


@app.route('/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Delete a user"""
    db = get_db_session()
    user = db.query(User).get(user_id)

    if user:
        # Don't allow deleting yourself
        if user.id == session.get('user_id'):
            flash('You cannot delete your own account', 'warning')
        else:
            name = user.name
            db.delete(user)
            db.commit()
            flash(f'User {name} deleted successfully', 'success')
    else:
        flash('User not found', 'error')

    db.close()
    return redirect(url_for('manage_users'))


@app.route('/edit_session/<int:session_id>', methods=['GET', 'POST'])
@admin_required
def edit_session(session_id):
    """Edit a class session"""
    db = get_db_session()
    session_obj = db.query(Session).get(session_id)

    if not session_obj:
        flash('Session not found', 'error')
        db.close()
        return redirect(url_for('calendar'))

    if request.method == 'POST':
        session_obj.title = request.form['title']
        session_obj.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        session_obj.time = request.form.get('time', '')
        session_obj.location = request.form.get('location', '')
        session_obj.description = request.form.get('description', '')
        db.commit()
        flash('Session updated successfully', 'success')
        db.close()
        return redirect(url_for('calendar'))

    # Access related objects before closing the database
    courses = db.query(Course).all()
    # Trigger loading of the course relationship
    _ = session_obj.course
    db.close()
    return render_template('edit_session.html', session=session_obj, courses=courses)


@app.route('/edit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
@admin_required
def edit_assignment(assignment_id):
    """Edit an assignment"""
    db = get_db_session()
    assignment = db.query(Assignment).get(assignment_id)

    if not assignment:
        flash('Assignment not found', 'error')
        db.close()
        return redirect(url_for('calendar'))

    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.description = request.form.get('description', '')
        assignment.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        assignment.points = request.form.get('points')
        db.commit()
        flash('Assignment updated successfully', 'success')
        db.close()
        return redirect(url_for('calendar'))

    # Access related objects before closing the database
    courses = db.query(Course).all()
    # Trigger loading of the course relationship
    _ = assignment.course
    db.close()
    return render_template('edit_assignment.html', assignment=assignment, courses=courses)


@app.route('/edit_reading/<int:reading_id>', methods=['GET', 'POST'])
@admin_required
def edit_reading(reading_id):
    """Edit a reading"""
    db = get_db_session()
    reading = db.query(Reading).get(reading_id)

    if not reading:
        flash('Reading not found', 'error')
        db.close()
        return redirect(url_for('calendar'))

    if request.method == 'POST':
        reading.title = request.form['title']
        reading.authors = request.form.get('authors', '')
        reading.pages = request.form.get('pages', '')
        reading.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        reading.citation = request.form.get('citation', '')
        reading.url = request.form.get('url', '')
        db.commit()
        flash('Reading updated successfully', 'success')
        db.close()
        return redirect(url_for('calendar'))

    # Access related objects before closing the database
    courses = db.query(Course).all()
    # Trigger loading of the course relationship
    _ = reading.course
    db.close()
    return render_template('edit_reading.html', reading=reading, courses=courses)


@app.route('/edit_custom/<int:item_id>', methods=['GET', 'POST'])
@admin_required
def edit_custom_item(item_id):
    """Edit a custom item"""
    db = get_db_session()
    item = db.query(CustomItem).get(item_id)

    if not item:
        flash('Item not found', 'error')
        db.close()
        return redirect(url_for('calendar'))

    if request.method == 'POST':
        item.title = request.form['title']
        item.description = request.form.get('description', '')
        item.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
        item.category = request.form['category']
        db.commit()
        flash('Custom item updated successfully', 'success')
        db.close()
        return redirect(url_for('calendar'))

    # Access related objects before closing the database
    courses = db.query(Course).all()
    # Trigger loading of the course relationship
    _ = item.course
    db.close()
    return render_template('edit_custom_item.html', item=item, courses=courses)


@app.route('/delete_session/<int:session_id>')
@admin_required
def delete_session(session_id):
    """Delete a session"""
    db = get_db_session()
    session_obj = db.query(Session).get(session_id)

    if session_obj:
        title = session_obj.title
        db.delete(session_obj)
        db.commit()
        flash(f'Session "{title}" deleted successfully', 'success')
    else:
        flash('Session not found', 'error')

    db.close()
    return redirect(url_for('calendar'))


@app.route('/delete_assignment/<int:assignment_id>')
@admin_required
def delete_assignment(assignment_id):
    """Delete an assignment"""
    db = get_db_session()
    assignment = db.query(Assignment).get(assignment_id)

    if assignment:
        title = assignment.title
        db.delete(assignment)
        db.commit()
        flash(f'Assignment "{title}" deleted successfully', 'success')
    else:
        flash('Assignment not found', 'error')

    db.close()
    return redirect(url_for('calendar'))


@app.route('/delete_reading/<int:reading_id>')
@admin_required
def delete_reading(reading_id):
    """Delete a reading"""
    db = get_db_session()
    reading = db.query(Reading).get(reading_id)

    if reading:
        title = reading.title
        db.delete(reading)
        db.commit()
        flash(f'Reading "{title}" deleted successfully', 'success')
    else:
        flash('Reading not found', 'error')

    db.close()
    return redirect(url_for('calendar'))


@app.route('/delete_custom/<int:item_id>')
@admin_required
def delete_custom_item(item_id):
    """Delete a custom item"""
    db = get_db_session()
    item = db.query(CustomItem).get(item_id)

    if item:
        title = item.title
        db.delete(item)
        db.commit()
        flash(f'Item "{title}" deleted successfully', 'success')
    else:
        flash('Item not found', 'error')

    db.close()
    return redirect(url_for('calendar'))


@app.route('/add_cohort25_subscribers')
@require_auth
def add_cohort25_subscribers():
    """Add PLI Cohort 25 subscribers"""
    try:
        db = get_db_session()

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

        # Check which ones already exist
        existing_emails = {s.email.lower() for s in db.query(Subscriber).all()}
        added_count = 0

        for email in emails:
            if email.lower() not in existing_emails:
                subscriber = Subscriber(email=email, subscribed_at=datetime.utcnow())
                db.add(subscriber)
                added_count += 1

        db.commit()
        db.close()

        flash(f'Successfully added {added_count} new subscribers! (Total: {len(emails)})', 'success')
    except Exception as e:
        flash(f'Error adding subscribers: {str(e)}', 'error')

    return redirect(url_for('index'))


if __name__ == '__main__':
    # Get port from environment variable (for cloud deployment) or default to 5000
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
