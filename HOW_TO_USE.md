# PLI Weekly Digest - How to Use

## 🎉 Congratulations! Your app is ready!

Your PLI Weekly Digest is running locally on your laptop and will send automated emails.

## 🚀 Starting the App

Every time you want to use the app, run these commands in Terminal:

```bash
cd ~/pli-weekly-digest
source venv/bin/activate
python app.py
```

Then open: **http://localhost:5000** in your browser

(Or if port 5000 is in use: `python -c "from app import app; app.run(debug=True, host='0.0.0.0', port=5001)"` and visit http://localhost:5001)

## 📧 What Happens Automatically

As long as the app is running on your laptop:

- **Every Sunday at 8:00am Pacific Time**: Weekly digest email sent to all subscribers
- **Every day at 6:00pm Pacific Time**: Daily reminder for items due tomorrow

**IMPORTANT**: Your laptop must be:
- Powered on
- Connected to the internet
- Running the app

## 🎯 Features You Can Use

### 1. Dashboard (Home)
- View all upcoming items for the next 7 days
- See stats (courses, sessions, assignments, subscribers)
- Quick actions: Send test digest, Preview digest

### 2. Upload Syllabus
- Upload any PDF syllabus
- AI automatically extracts:
  - Course information
  - Session dates and topics
  - Assignment due dates
  - Reading assignments
- Takes ~30 seconds to parse

**Try it now**: Upload your Education 263B syllabus!
```
/Users/ceceepenney/Downloads/Education 263B Course Syllabus_Spring 2026 [FINAL].pdf
```

### 3. Manual Entry
- Quickly add items without uploading a PDF
- Three types:
  - **Assignments**: Title, description, due date, points
  - **Readings**: Title, authors, pages, citation, URL, due date
  - **Sessions**: Session number, title, date, time, location
- Optional: Link to a specific course

### 4. Custom Items
- Add reminders for things not in syllabi
- Examples:
  - "Venmo $20 for group lunch by Friday"
  - "Submit travel reimbursement by Tuesday"
  - "Office hours with Professor Smith"
- Categories: reminder, event, payment, other

### 5. Subscribers
- Add yourself and classmates
- Everyone gets the same digest emails
- Can activate/deactivate subscribers
- Currently subscribed: **cecee.penney@gmail.com**

### 6. History
- View all past digests
- See what was sent and when
- Useful if you delete an email

### 7. Preview
- See what the weekly digest will look like
- Opens in new tab
- Doesn't send email, just shows preview

## 💡 Pro Tips

### Keep Your Laptop Running
For automated emails to work, your laptop needs to be on. Options:
1. **Keep it running 24/7** (plug it in!)
2. **Wake it up each morning** before 8am on Sundays
3. **Deploy to cloud later** when you're ready

### Test Everything First
Before relying on automated emails:
1. Add a few test items using Manual Entry
2. Click "Send Test Digest Now" on dashboard
3. Check your Gmail to see the email
4. Make sure it looks good!

### Add Classmates
Once you're confident it works:
1. Go to "Subscribers"
2. Add your classmates' emails
3. They'll all get the digest emails automatically

### Mark Items Complete
- Click "Mark Complete" on any assignment/reading
- Completed items won't appear in future digests
- Helps keep your inbox clean!

### Multiple Courses
- Upload multiple syllabi
- Each course tracked separately
- All items appear in one unified digest

## 🔧 Troubleshooting

### Can't access the app?
Make sure you've run:
```bash
cd ~/pli-weekly-digest
source venv/bin/activate
python app.py
```

### Emails not sending?
- Check that the app is running
- Verify your Gmail app password is correct in `.env`
- Test with "Send Test Digest Now" button

### Syllabus parsing failed?
- Make sure PDF is text-based (not a scanned image)
- Try a different PDF to test
- Use "Manual Entry" as a backup

### Database error?
```bash
cd ~/pli-weekly-digest
source venv/bin/activate
python models.py
```

## 📁 Important Files

- `~/pli-weekly-digest/` - Main folder
- `.env` - Your API keys and settings (NEVER share this!)
- `pli_digest.db` - Your database (all your data)
- `app.py` - The main application
- `QUICKSTART.md` - Quick reference guide
- `README.md` - Full documentation

## 🚀 Future: Deploy to Cloud

When you're ready to have it run 24/7 without your laptop:
1. Push code to GitHub
2. Connect to Railway or Render
3. Add environment variables
4. Deploy!

See `README.md` for full deployment instructions.

## 💬 Need Help?

All the code is in `~/pli-weekly-digest/` and is well-commented. Feel free to modify anything!

---

**Enjoy your automated weekly digest! 🎓**

No more forgetting assignments or missing deadlines!
