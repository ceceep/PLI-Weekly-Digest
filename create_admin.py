"""
Script to create an admin user account
Run this after updating to the new authentication system
"""
from models import User, get_session, init_db
import getpass
import sys

def create_admin_user():
    """Create an admin user account"""
    print("=" * 50)
    print("CREATE ADMIN USER")
    print("=" * 50)

    # Initialize database (creates tables if they don't exist)
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized")

    db = get_session()

    # Get admin details
    print("\nEnter admin account details:")
    email = input("Email: ").strip()

    # Check if user already exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"\n⚠️  User with email {email} already exists!")
        overwrite = input("Do you want to update this user? (yes/no): ").strip().lower()
        if overwrite != 'yes':
            print("Cancelled.")
            db.close()
            sys.exit(0)

        user = existing
        print(f"Updating existing user: {user.name}")
    else:
        user = User(email=email)
        print(f"Creating new user with email: {email}")

    name = input("Full Name: ").strip()
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm Password: ")

    if password != password_confirm:
        print("\n❌ Passwords don't match!")
        db.close()
        sys.exit(1)

    if len(password) < 8:
        print("\n❌ Password must be at least 8 characters!")
        db.close()
        sys.exit(1)

    # Set user details
    user.name = name
    user.role = 'admin'
    user.active = True
    user.set_password(password)

    if not existing:
        db.add(user)

    db.commit()

    print("\n" + "=" * 50)
    print("✅ Admin user created successfully!")
    print("=" * 50)
    print(f"Email: {user.email}")
    print(f"Name: {user.name}")
    print(f"Role: {user.role}")
    print("\nYou can now log in with these credentials at /login")

    db.close()

if __name__ == "__main__":
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
