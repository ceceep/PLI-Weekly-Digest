"""
Email digest generator for PLI Weekly Digest
"""
import os
from datetime import datetime, timedelta
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from models import Session, Assignment, Reading, CustomItem, Subscriber, DigestHistory, get_session
import json


class DigestGenerator:
    def __init__(self):
        self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = os.getenv('FROM_EMAIL')

    def get_week_items(self, start_date, end_date):
        """Get all items for a given week"""
        db = get_session()

        try:
            sessions = db.query(Session).filter(
                Session.date >= start_date,
                Session.date <= end_date
            ).order_by(Session.date).all()

            assignments = db.query(Assignment).filter(
                Assignment.due_date >= start_date,
                Assignment.due_date <= end_date,
                Assignment.completed == False
            ).order_by(Assignment.due_date).all()

            readings = db.query(Reading).filter(
                Reading.due_date >= start_date,
                Reading.due_date <= end_date,
                Reading.completed == False
            ).order_by(Reading.due_date).all()

            custom_items = db.query(CustomItem).filter(
                CustomItem.due_date >= start_date,
                CustomItem.due_date <= end_date,
                CustomItem.completed == False
            ).order_by(CustomItem.due_date).all()

            return {
                'sessions': sessions,
                'assignments': assignments,
                'readings': readings,
                'custom_items': custom_items
            }
        finally:
            db.close()

    def generate_weekly_html(self, items):
        """Generate HTML for weekly digest"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #003262;
            border-bottom: 3px solid #FDB515;
            padding-bottom: 10px;
        }
        h2 {
            color: #003262;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 20px;
        }
        .item {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #FDB515;
            border-radius: 4px;
        }
        .date {
            font-weight: bold;
            color: #003262;
        }
        .title {
            font-size: 18px;
            margin: 5px 0;
        }
        .description {
            color: #666;
            font-size: 14px;
            margin-top: 8px;
        }
        .location, .pages, .authors {
            color: #666;
            font-size: 14px;
            font-style: italic;
        }
        .reminder {
            background: #fff3cd;
            border-left-color: #ffc107;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #666;
            text-align: center;
        }
        .empty {
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>🎓 Happy Sunday! Here's what's coming up this week...</h1>
"""

        # Class Sessions
        html += "<h2>📅 Class Sessions</h2>"
        if items['sessions']:
            for session in items['sessions']:
                html += f"""
    <div class="item">
        <div class="date">{session.date.strftime('%A, %B %d, %Y')}</div>
        <div class="title">Session {session.session_number}: {session.title}</div>
        <div class="location">{session.location} • {session.time}</div>
        {f'<div class="description">{session.description}</div>' if session.description else ''}
    </div>
"""
        else:
            html += '<div class="empty">No class sessions this week</div>'

        # Assignments
        html += "<h2>📝 Assignments Due</h2>"
        if items['assignments']:
            for assignment in items['assignments']:
                html += f"""
    <div class="item">
        <div class="date">Due: {assignment.due_date.strftime('%A, %B %d, %Y')}</div>
        <div class="title">{assignment.title}</div>
        {f'<div class="description">{assignment.description}</div>' if assignment.description else ''}
        {f'<div class="description">Points: {assignment.points}</div>' if assignment.points else ''}
    </div>
"""
        else:
            html += '<div class="empty">No assignments due this week</div>'

        # Readings
        html += "<h2>📚 Readings</h2>"
        if items['readings']:
            for reading in items['readings']:
                html += f"""
    <div class="item">
        <div class="date">Due: {reading.due_date.strftime('%A, %B %d, %Y')}</div>
        <div class="title">{reading.title}</div>
        {f'<div class="authors">{reading.authors}</div>' if reading.authors else ''}
        {f'<div class="pages">{reading.pages}</div>' if reading.pages else ''}
        {f'<div class="description"><a href="{reading.url}">Link to reading</a></div>' if reading.url else ''}
    </div>
"""
        else:
            html += '<div class="empty">No readings due this week</div>'

        # Reminders & Custom Items
        html += "<h2>📌 Things to Keep in Mind</h2>"
        if items['custom_items']:
            for item in items['custom_items']:
                html += f"""
    <div class="item reminder">
        <div class="date">Due: {item.due_date.strftime('%A, %B %d, %Y')}</div>
        <div class="title">{item.title}</div>
        {f'<div class="description">{item.description}</div>' if item.description else ''}
        <div class="description">Category: {item.category}</div>
    </div>
"""
        else:
            html += '<div class="empty">No special reminders this week</div>'

        # Footer
        html += """
    <div class="footer">
        <p>This digest was automatically generated by PLI Weekly Digest</p>
        <p>Have a great week! 🌟</p>
    </div>
</body>
</html>
"""
        return html

    def send_weekly_digest(self):
        """Send weekly digest email"""
        # Get this week's items (Sunday to Saturday)
        today = datetime.now().date()
        start_of_week = today
        end_of_week = today + timedelta(days=6)

        items = self.get_week_items(start_of_week, end_of_week)

        # Generate HTML
        html_content = self.generate_weekly_html(items)

        # Get active subscribers
        db = get_session()
        subscribers = db.query(Subscriber).filter(Subscriber.active == True).all()

        if not subscribers:
            print("No active subscribers found")
            db.close()
            return

        # Send to each subscriber
        recipient_emails = [sub.email for sub in subscribers]

        for email in recipient_emails:
            message = Mail(
                from_email=self.from_email,
                to_emails=email,
                subject=f"PLI Weekly Digest - Week of {start_of_week.strftime('%B %d, %Y')}",
                html_content=html_content
            )

            try:
                response = self.sg.send(message)
                print(f"Email sent to {email}: Status {response.status_code}")
            except Exception as e:
                print(f"Error sending to {email}: {e}")

        # Save to history
        history = DigestHistory(
            sent_at=datetime.now(),
            digest_type='weekly',
            content=html_content,
            recipients=json.dumps(recipient_emails)
        )
        db.add(history)
        db.commit()
        db.close()

        print(f"Weekly digest sent to {len(recipient_emails)} subscribers")

    def send_daily_reminder(self):
        """Send daily reminder for items due tomorrow"""
        db = get_session()
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        # Get items due tomorrow
        assignments = db.query(Assignment).filter(
            Assignment.due_date == tomorrow,
            Assignment.completed == False
        ).all()

        readings = db.query(Reading).filter(
            Reading.due_date == tomorrow,
            Reading.completed == False
        ).all()

        custom_items = db.query(CustomItem).filter(
            CustomItem.due_date == tomorrow,
            CustomItem.completed == False
        ).all()

        if not (assignments or readings or custom_items):
            print("Nothing due tomorrow")
            db.close()
            return

        # Generate simple HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            padding: 20px;
            max-width: 600px;
            margin: 0 auto;
        }}
        h1 {{ color: #d9534f; }}
        .item {{
            background: #fff3cd;
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
        }}
    </style>
</head>
<body>
    <h1>⏰ Reminder: Items Due Tomorrow ({tomorrow.strftime('%A, %B %d')})</h1>
"""

        if assignments:
            html += "<h2>Assignments:</h2>"
            for a in assignments:
                html += f'<div class="item">{a.title}</div>'

        if readings:
            html += "<h2>Readings:</h2>"
            for r in readings:
                html += f'<div class="item">{r.title}</div>'

        if custom_items:
            html += "<h2>Reminders:</h2>"
            for c in custom_items:
                html += f'<div class="item">{c.title}</div>'

        html += "</body></html>"

        # Send to subscribers
        subscribers = db.query(Subscriber).filter(Subscriber.active == True).all()
        recipient_emails = [sub.email for sub in subscribers]

        for email in recipient_emails:
            message = Mail(
                from_email=self.from_email,
                to_emails=email,
                subject=f"⏰ Reminder: Items Due Tomorrow",
                html_content=html
            )

            try:
                self.sg.send(message)
                print(f"Daily reminder sent to {email}")
            except Exception as e:
                print(f"Error sending reminder to {email}: {e}")

        # Save to history
        history = DigestHistory(
            sent_at=datetime.now(),
            digest_type='daily',
            content=html,
            recipients=json.dumps(recipient_emails)
        )
        db.add(history)
        db.commit()
        db.close()


if __name__ == "__main__":
    # Test digest generation
    generator = DigestGenerator()

    # Test weekly digest
    print("Generating weekly digest...")
    generator.send_weekly_digest()
