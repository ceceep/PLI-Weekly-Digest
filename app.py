"""
Flask web application for PLI Weekly Digest
"""
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
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


if __name__ == '__main__':
    # Get port from environment variable (for cloud deployment) or default to 5000
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
