# PLI Weekly Digest - Quick Start Guide

## What You Just Built

A complete automated weekly digest system that:
- Parses PDF syllabi using AI
- Sends email digests every Sunday at 8am
- Sends daily reminders at 6pm
- Tracks assignments, readings, and custom items
- Manages multiple subscribers

## Get Started in 5 Minutes

### Step 1: Run Setup Script

```bash
cd ~/pli-weekly-digest
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Initialize the database
- Create your `.env` file

### Step 2: Get Your API Keys

You need two API keys:

#### Anthropic API Key (for syllabus parsing)
1. Go to https://console.anthropic.com
2. Sign up / Login
3. Go to API Keys
4. Create a new key
5. Copy it

#### SendGrid API Key (for sending emails)
1. Go to https://sendgrid.com
2. Sign up for free account (100 emails/day free)
3. Go to Settings → API Keys
4. Create a new key with "Mail Send" permissions
5. Copy it
6. Verify your sender email (Settings → Sender Authentication)

### Step 3: Configure Environment

Edit `~/pli-weekly-digest/.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
SENDGRID_API_KEY=SG.your-key-here
FROM_EMAIL=your-verified-email@example.com
SECRET_KEY=any-random-string-here
DATABASE_URL=sqlite:///pli_digest.db
```

### Step 4: Run the App

```bash
cd ~/pli-weekly-digest
source venv/bin/activate
python app.py
```

Visit: http://localhost:5000

### Step 5: Upload Your Syllabus

1. Click "Upload Syllabus"
2. Upload: `/Users/ceceepenney/Downloads/Education 263B Course Syllabus_Spring 2026 [FINAL].pdf`
3. Wait ~30 seconds for AI to parse it
4. All 13 sessions, assignments, and readings will be imported!

### Step 6: Add Yourself as Subscriber

1. Click "Subscribers"
2. Add your email
3. You're now subscribed!

### Step 7: Test It

Click "Send Test Digest Now" on the dashboard to see what the email looks like.

## What's Included

### Files Created:
```
~/pli-weekly-digest/
├── app.py                  # Main Flask web app
├── models.py               # Database models
├── syllabus_parser.py      # AI syllabus parser
├── digest_generator.py     # Email digest generator
├── requirements.txt        # Python dependencies
├── setup.sh               # Setup script
├── README.md              # Full documentation
├── .env.example           # Environment template
├── Procfile              # For cloud deployment
├── runtime.txt           # Python version
└── templates/            # HTML templates
    ├── base.html
    ├── index.html
    ├── upload_syllabus.html
    ├── custom_items.html
    ├── subscribers.html
    ├── history.html
    └── course.html
```

## Features You Can Use Right Now

### 1. Dashboard
- See all upcoming items for the next 7 days
- Mark items as complete
- Quick access to all features

### 2. Upload Syllabus
- Upload any PDF syllabus
- AI automatically extracts:
  - Course info
  - Session dates and topics
  - Assignment due dates
  - Reading assignments

### 3. Custom Items
- Add reminders like "Venmo $20 by Friday"
- Categories: reminder, event, payment, other
- Optional: link to a specific course

### 4. Subscribers
- Add yourself
- Add classmates
- Everyone gets the same digest

### 5. Weekly Digest (Automated)
- Sent every **Sunday at 8:00am Pacific Time**
- Beautiful HTML email with:
  - Class sessions this week
  - Assignments due
  - Readings due
  - Custom reminders

### 6. Daily Reminder (Automated)
- Sent every day at **6:00pm Pacific Time**
- Lists items due tomorrow
- Quick reminder so nothing sneaks up on you

### 7. History
- View all past digests
- See what was sent and when
- Useful if you delete an email

## Deploy to Cloud (Optional)

When you're ready to deploy so it runs automatically:

### Option 1: Railway (Easiest)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway add --database postgres
railway up
```

Add your environment variables in Railway dashboard, and you're live!

### Option 2: Render

1. Push code to GitHub
2. Connect Render to your repo
3. Add environment variables
4. Deploy!

## Troubleshooting

### "Module not found" error?
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Emails not sending?
- Check SendGrid API key is correct
- Verify your FROM_EMAIL in SendGrid dashboard
- Check you haven't exceeded free tier (100/day)

### Syllabus parsing failed?
- Make sure PDF is text-based (not scanned image)
- Check Anthropic API key is correct
- Try a simpler test PDF first

### Database error?
```bash
python models.py  # Re-initialize database
```

## Next Steps

1. **Test everything locally first** before deploying
2. **Add all your classmates** as subscribers
3. **Upload multiple syllabi** if you have them
4. **Add custom items** for things not in syllabi
5. **Deploy to cloud** when ready for automation

## Support

- Check README.md for full documentation
- All code is commented and readable
- Modify anything you want - it's yours!

---

Enjoy your automated weekly digest! 🎓

No more forgetting assignments or missing deadlines!
