# Authentication & User Management Setup

## Overview

The PLI Weekly Digest now includes a comprehensive authentication system with role-based access control. Users can log in with email and password, and admins have special privileges to manage content and users.

## Features

### User Roles
- **Admin**: Full access to create, edit, and delete all content, manage users
- **User**: Can view calendar and content (future: personalized features)

### Admin Capabilities
- Create and manage user accounts
- Edit and delete calendar items (sessions, assignments, readings, custom items)
- Manage email subscribers
- Upload syllabi and import course data
- Send test digests

### User Capabilities
- View calendar and upcoming items
- Access course information
- Subscribe to email digest (public route)

## Initial Setup

### Step 1: Update Database Schema

The database will automatically create the new `users` table when you run the application for the first time after this update.

```bash
python app.py
```

### Step 2: Create Your First Admin User

Run the admin creation script:

```bash
python create_admin.py
```

You'll be prompted to enter:
- Email address
- Full name
- Password (minimum 8 characters)
- Password confirmation

Example:
```
==================================================
CREATE ADMIN USER
==================================================

Initializing database...
✓ Database initialized

Enter admin account details:
Email: admin@berkeley.edu
Full Name: Admin User
Password: ********
Confirm Password: ********

==================================================
✅ Admin user created successfully!
==================================================
Email: admin@berkeley.edu
Name: Admin User
Role: admin

You can now log in with these credentials at /login
```

### Step 3: Log In

1. Navigate to `/login` in your browser
2. Enter your email and password
3. You'll be redirected to the dashboard

## Routes & Permissions

### Public Routes (No Login Required)
- `/` - Home dashboard
- `/login` - Login page
- `/subscribe` - Email subscription form
- `/calendar` - Calendar view (view-only)
- `/course/<id>` - Course details
- `/history` - Digest history
- `/preview_digest` - Preview digest

### Admin-Only Routes
- `/users` - User management
- `/upload_syllabus` - Upload and parse syllabi
- `/manual_entry` - Manually add items
- `/custom_items` - Manage custom items
- `/subscribers` - Manage email subscribers
- `/edit_session/<id>` - Edit a class session
- `/edit_assignment/<id>` - Edit an assignment
- `/edit_reading/<id>` - Edit a reading
- `/edit_custom/<id>` - Edit a custom item
- `/delete_session/<id>` - Delete a session
- `/delete_assignment/<id>` - Delete an assignment
- `/delete_reading/<id>` - Delete a reading
- `/delete_custom/<id>` - Delete a custom item
- All import routes (`/import_educ269a`, etc.)

## User Management

### Creating New Users (Admin Only)

1. Log in as an admin
2. Navigate to `/users`
3. Fill out the "Add New User" form:
   - Email
   - Password
   - Full Name
   - Role (admin or user)
4. Click "Add User"

### Managing Existing Users

From `/users`, admins can:
- **Toggle Active Status**: Enable/disable user accounts (green/red indicator)
- **Delete Users**: Permanently remove user accounts
- **View User Info**: Email, name, role, last login, creation date

**Important**: You cannot deactivate or delete your own admin account.

## Calendar Item Editing

### Editing Items

When logged in as an admin, calendar items will show "Edit" and "Delete" buttons:

1. **Sessions**: `/edit_session/<id>`
   - Update title, date, time, location, description

2. **Assignments**: `/edit_assignment/<id>`
   - Update title, description, due date, points

3. **Readings**: `/edit_reading/<id>`
   - Update title, authors, pages, due date, citation, URL

4. **Custom Items**: `/edit_custom/<id>`
   - Update title, description, due date, category

### Deleting Items

Click the "Delete" button next to any calendar item. You'll be redirected back to the calendar with a success message.

## Security Features

### Password Hashing
- Passwords are hashed using Werkzeug's security utilities
- Plain-text passwords are never stored in the database
- Uses PBKDF2 with SHA-256

### Session Management
- Secure session-based authentication
- Session data includes: user_id, email, role, name
- Sessions clear on logout

### Permission Checks
- `@login_required` decorator: Requires any logged-in user
- `@admin_required` decorator: Requires admin role
- Redirects to login page if not authenticated
- Shows error message if insufficient permissions

## Migration from Old System

### Before (Single Password)
- One `ADMIN_PASSWORD` in .env
- Simple session flag: `session['authenticated']`
- All admins shared one password

### After (User Accounts)
- Individual user accounts with email/password
- Role-based access control (admin/user)
- Track last login and user creation dates
- Can create multiple admin accounts

### Backwards Compatibility
- Old `require_auth` decorator is aliased to `admin_required`
- Existing protected routes remain protected
- No changes needed to existing route decorators

## Troubleshooting

### "Invalid email or password"
- Check that you're using the correct email address
- Passwords are case-sensitive
- Make sure your account is active (admin can check in `/users`)

### "You must be an admin to access this page"
- Your account doesn't have admin privileges
- Contact an admin to update your role

### "Please log in to access this page"
- Your session has expired
- Navigate to `/login` to log in again

### Can't Log In After Update
1. Make sure you've run `python create_admin.py` to create your first admin user
2. Check that the database was initialized properly
3. Look for error messages in the console

## Development Notes

### Database Models

**User Model** (`models.py`):
```python
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    name = Column(String(200))
    role = Column(String(20), default='user')  # 'admin' or 'user'
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
```

### Authentication Decorators

**login_required**: Any authenticated user
```python
@app.route('/my_route')
@login_required
def my_route():
    # Only accessible to logged-in users
    pass
```

**admin_required**: Admins only
```python
@app.route('/admin_route')
@admin_required
def admin_route():
    # Only accessible to admins
    pass
```

### Accessing Current User in Templates

The `current_user` object is passed to templates:
```python
# In route
current_user = db.query(User).get(session['user_id']) if session.get('user_id') else None
return render_template('template.html', current_user=current_user)
```

```html
<!-- In template -->
{% if current_user and current_user.is_admin() %}
    <a href="/edit_item/{{ item.id }}">Edit</a>
{% endif %}
```

## Future Enhancements

- [ ] Password reset functionality
- [ ] Email verification
- [ ] User profile editing
- [ ] Activity logging/audit trail
- [ ] Two-factor authentication
- [ ] API tokens for programmatic access
- [ ] Role customization (custom permission sets)

## Support

If you encounter issues or have questions:
1. Check this documentation
2. Review the console output for error messages
3. Check the `/users` page to verify your account status
4. Contact the system administrator
