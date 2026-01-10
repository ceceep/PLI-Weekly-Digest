# PLI Weekly Digest

An automated weekly digest system for tracking course syllabi, assignments, readings, and custom reminders with email notifications.

## Features

- 📄 **AI-Powered Syllabus Parsing**: Upload PDF syllabi and automatically extract sessions, assignments, and readings
- 📧 **Weekly Email Digests**: Automatic emails every Sunday at 8am PT with the week's schedule
- ⏰ **Daily Reminders**: Daily emails at 6pm PT for items due tomorrow
- ✅ **Completion Tracking**: Mark assignments and readings as complete
- 📌 **Custom Items**: Add custom reminders like "Venmo $20 for lunch by Friday"
- 👥 **Multiple Subscribers**: Share digests with classmates
- 📜 **Digest History**: View past emails

## Setup Instructions

### 1. Install Dependencies

```bash
cd ~/pli-weekly-digest
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy the example environment file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env` and add:

- **ANTHROPIC_API_KEY**: Your Anthropic API key (for syllabus parsing)
- **SENDGRID_API_KEY**: Your SendGrid API key (for sending emails)
- **FROM_EMAIL**: Your verified sender email in SendGrid
- **SECRET_KEY**: A random secret key for Flask sessions

### 3. Initialize Database

```bash
python models.py
```

### 4. Run Locally

```bash
python app.py
```

Visit http://localhost:5000

### 5. Upload Your First Syllabus

1. Go to "Upload Syllabus" in the navigation
2. Upload your Education 263B syllabus PDF
3. Wait for AI to parse it (takes ~30 seconds)
4. All items will be imported automatically!

### 6. Add Yourself as a Subscriber

1. Go to "Subscribers"
2. Add your email address
3. You'll now receive weekly digests and daily reminders

## Deployment to Cloud (Railway)

### Option A: Deploy to Railway (Recommended)

1. Create account at https://railway.app
2. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

3. Login and deploy:
   ```bash
   railway login
   railway init
   railway add --database postgres
   railway up
   ```

4. Add environment variables in Railway dashboard
5. Your app will be live at a Railway URL!

### Option B: Deploy to Render

1. Create account at https://render.com
2. Connect your GitHub repo
3. Create new Web Service
4. Add environment variables
5. Deploy!

## Usage

### Weekly Digest
- Automatically sent every **Sunday at 8:00am Pacific Time**
- Includes all items for the upcoming week

### Daily Reminder
- Automatically sent every day at **6:00pm Pacific Time**
- Includes items due tomorrow

### Manual Test
- Click "Send Test Digest Now" on the dashboard to test immediately

### Add Custom Items
- Use "Custom Items" to add things like:
  - "Venmo $20 for conference lunch by Friday"
  - "Review slides before Thursday's presentation"
  - "RSVP for faculty event by Monday"

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite (local) / PostgreSQL (production)
- **AI**: Anthropic Claude for syllabus parsing
- **Email**: SendGrid
- **Scheduling**: APScheduler
- **Deployment**: Railway / Render

## Troubleshooting

### Emails not sending?
- Check your SendGrid API key is valid
- Verify your FROM_EMAIL is verified in SendGrid
- Check logs for error messages

### Syllabus parsing failed?
- Ensure PDF is text-based (not scanned images)
- Check Anthropic API key is valid
- Try a simpler PDF first to test

### App won't start?
- Run `python models.py` to initialize database
- Check all environment variables are set
- Verify Python version is 3.8+

## Future Enhancements

- [ ] Multiple course support
- [ ] Calendar integration (iCal export)
- [ ] Mobile notifications
- [ ] Slack/Discord integration
- [ ] Assignment grade tracking

## License

MIT License - feel free to use and modify for your own courses!

---

Built with ❤️ for PLI students at UC Berkeley
