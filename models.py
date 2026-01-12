"""
Database models for PLI Weekly Digest
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
import os

Base = declarative_base()


class User(Base):
    """User accounts with role-based access"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    name = Column(String(200))
    role = Column(String(20), default='user')  # 'admin' or 'user'
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password is correct"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'


class Course(Base):
    """Represents a course/class"""
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50))  # e.g., "EDUC 263B"
    instructor = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    readings = relationship("Reading", back_populates="course", cascade="all, delete-orphan")
    custom_items = relationship("CustomItem", back_populates="course", cascade="all, delete-orphan")


class Session(Base):
    """Represents a class session"""
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    session_number = Column(Integer)
    title = Column(String(500))
    date = Column(Date, nullable=False)
    time = Column(String(50))  # e.g., "6-9pm"
    location = Column(String(200))  # e.g., "In person, room 1102" or "Virtual"
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="sessions")


class Assignment(Base):
    """Represents an assignment"""
    __tablename__ = 'assignments'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    due_date = Column(Date, nullable=False)
    points = Column(Integer)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="assignments")


class Reading(Base):
    """Represents a reading assignment"""
    __tablename__ = 'readings'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(500), nullable=False)
    authors = Column(String(500))
    citation = Column(Text)
    pages = Column(String(100))  # e.g., "pp. 1-35"
    due_date = Column(Date, nullable=False)
    url = Column(String(1000))  # Optional link
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="readings")


class CustomItem(Base):
    """Represents a custom item (e.g., 'Venmo $20 by Friday')"""
    __tablename__ = 'custom_items'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=True)  # Can be course-specific or general
    title = Column(String(500), nullable=False)
    description = Column(Text)
    due_date = Column(Date, nullable=False)
    category = Column(String(50))  # 'reminder', 'event', 'payment', 'other'
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="custom_items")


class Subscriber(Base):
    """Email subscribers for the digest"""
    __tablename__ = 'subscribers'

    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, unique=True)
    name = Column(String(200))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DigestHistory(Base):
    """Records of sent digests"""
    __tablename__ = 'digest_history'

    id = Column(Integer, primary_key=True)
    sent_at = Column(DateTime, nullable=False)
    digest_type = Column(String(50))  # 'weekly' or 'daily'
    content = Column(Text)  # HTML content that was sent
    recipients = Column(Text)  # JSON list of email addresses
    created_at = Column(DateTime, default=datetime.utcnow)


# Database setup
def get_engine():
    """Get database engine"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///pli_digest.db')

    # Fix for Render PostgreSQL URLs (they use postgres:// but SQLAlchemy needs postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    return create_engine(database_url)


def get_session():
    """Get database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Initialize database (create all tables)"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()
