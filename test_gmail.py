"""
Test Gmail SMTP setup
"""
import os
from dotenv import load_dotenv
from gmail_digest_generator import GmailDigestGenerator

load_dotenv()

def test_gmail():
    """Test Gmail connection"""

    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')

    print("Testing Gmail SMTP setup...")
    print(f"Gmail User: {gmail_user}")
    print(f"App Password: {'*' * len(gmail_password) if gmail_password else 'NOT SET'}")
    print()

    if not gmail_user or not gmail_password:
        print("❌ ERROR: Gmail credentials not set in .env file")
        return

    if gmail_password == 'your-gmail-app-password-here':
        print("❌ ERROR: Please replace 'your-gmail-app-password-here' with your actual Gmail App Password")
        return

    # Try to send test email
    try:
        generator = GmailDigestGenerator()

        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #003262;">🎉 Success!</h1>
            <p>Your PLI Weekly Digest email system is working perfectly!</p>
            <p>You can now:</p>
            <ul>
                <li>Upload syllabi and parse them with AI</li>
                <li>Manually add assignments and readings</li>
                <li>Receive weekly digests every Sunday at 8am</li>
                <li>Get daily reminders for items due tomorrow</li>
            </ul>
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                Sent from PLI Weekly Digest
            </p>
        </body>
        </html>
        """

        print("📧 Sending test email to cecee.penney@gmail.com...")
        success = generator.send_email(
            gmail_user,
            "PLI Digest - Test Email ✅",
            html_content
        )

        if success:
            print()
            print("✅ SUCCESS! Email sent!")
            print()
            print("Check your inbox at cecee.penney@gmail.com")
            print("(It should arrive within a few seconds)")
            print()
            print("If you don't see it:")
            print("  1. Check your Spam/Junk folder")
            print("  2. Check your Promotions tab (if using Gmail)")
        else:
            print()
            print("❌ Failed to send email. Check the error message above.")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("Common issues:")
        print("  1. Make sure 2-Step Verification is enabled on your Google account")
        print("  2. Make sure you're using an App Password (not your regular Gmail password)")
        print("  3. Make sure you copied the app password correctly (no spaces)")

if __name__ == "__main__":
    test_gmail()
