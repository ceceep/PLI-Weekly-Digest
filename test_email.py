"""
Test script to verify SendGrid email setup
"""
import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

def test_sendgrid():
    """Test SendGrid connection and send a test email"""

    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL')

    print(f"Testing SendGrid with:")
    print(f"  API Key: {api_key[:10]}..." if api_key else "  API Key: NOT SET")
    print(f"  From Email: {from_email}")
    print()

    if not api_key:
        print("❌ ERROR: SENDGRID_API_KEY not set in .env file")
        return

    if not from_email:
        print("❌ ERROR: FROM_EMAIL not set in .env file")
        return

    # Check API key format
    if not api_key.startswith('SG.'):
        print("⚠️  WARNING: SendGrid API keys should start with 'SG.'")

    if len(api_key) < 50:
        print(f"⚠️  WARNING: Your API key seems too short ({len(api_key)} chars)")
        print("    SendGrid API keys are typically 69+ characters long")
        print()

    # Try to send test email
    try:
        sg = SendGridAPIClient(api_key)

        message = Mail(
            from_email=from_email,
            to_emails=from_email,  # Send to yourself
            subject='PLI Digest - Test Email',
            html_content='<strong>Success!</strong> Your SendGrid is configured correctly. 🎉'
        )

        print("📧 Attempting to send test email...")
        response = sg.send(message)

        print(f"✅ Email sent successfully!")
        print(f"   Status Code: {response.status_code}")
        print(f"   To: {from_email}")
        print()
        print("Check your inbox (including spam folder)!")

        if response.status_code == 202:
            print()
            print("Note: Status 202 means 'Accepted' - the email is queued for delivery.")
            print("It should arrive within a few minutes.")

    except Exception as e:
        print(f"❌ ERROR sending email:")
        print(f"   {str(e)}")
        print()

        error_str = str(e).lower()

        if 'unauthorized' in error_str or '401' in error_str:
            print("💡 This usually means:")
            print("   1. Your API key is invalid or incomplete")
            print("   2. Your API key doesn't have 'Mail Send' permissions")
            print()
            print("To fix:")
            print("   1. Go to https://sendgrid.com")
            print("   2. Log in and go to Settings → API Keys")
            print("   3. Create a new API key with 'Mail Send' permissions")
            print("   4. Copy the FULL key (starts with SG., about 69 chars)")
            print("   5. Update SENDGRID_API_KEY in your .env file")

        elif 'forbidden' in error_str or '403' in error_str:
            print("💡 This usually means:")
            print("   1. Your sender email is not verified in SendGrid")
            print("   2. Your account needs verification")
            print()
            print("To fix:")
            print("   1. Go to https://sendgrid.com")
            print("   2. Go to Settings → Sender Authentication")
            print("   3. Click 'Verify a Single Sender'")
            print("   4. Add cecee.penney@gmail.com")
            print("   5. Check your email for verification link")
            print("   6. Click the link to verify")

if __name__ == "__main__":
    test_sendgrid()
