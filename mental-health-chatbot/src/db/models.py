"""
Database Models for Mental Health ChatBot
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from src.db.database import db
import json

class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    preferred_language = db.Column(db.String(10), default='en')
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    mood_entries = db.relationship('MoodEntry', backref='user', lazy=True, cascade='all, delete-orphan')
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'preferred_language': self.preferred_language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class ChatSession(db.Model):
    """Chat session model for conversation tracking"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for anonymous sessions
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    context_data = db.Column(db.Text, nullable=True)  # JSON string for conversation context
    mood_detected = db.Column(db.String(50), nullable=True)
    sentiment_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    messages = db.relationship('Message', backref='chat_session', lazy=True, cascade='all, delete-orphan')
    
    def get_context(self):
        """Get conversation context as dictionary"""
        if self.context_data:
            return json.loads(self.context_data)
        return {}
    
    def set_context(self, context_dict):
        """Set conversation context from dictionary"""
        self.context_data = json.dumps(context_dict)

class Message(db.Model):
    """Message model for storing chat messages"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user' or 'bot'
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # 'text', 'assessment', 'recommendation'
    metadata = db.Column(db.Text, nullable=True)  # JSON string for additional data
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def get_metadata(self):
        """Get message metadata as dictionary"""
        if self.metadata:
            return json.loads(self.metadata)
        return {}
    
    def set_metadata(self, metadata_dict):
        """Set message metadata from dictionary"""
        self.metadata = json.dumps(metadata_dict)

class MoodEntry(db.Model):
    """Mood tracking entries"""
    __tablename__ = 'mood_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    mood_label = db.Column(db.String(50), nullable=False)  # 'happy', 'sad', 'anxious', etc.
    activities = db.Column(db.Text, nullable=True)  # JSON string of activities
    notes = db.Column(db.Text, nullable=True)
    energy_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    sleep_hours = db.Column(db.Float, nullable=True)
    stress_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def get_activities(self):
        """Get activities as list"""
        if self.activities:
            return json.loads(self.activities)
        return []
    
    def set_activities(self, activities_list):
        """Set activities from list"""
        self.activities = json.dumps(activities_list)

class Assessment(db.Model):
    """Mental health assessment results"""
    __tablename__ = 'assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assessment_type = db.Column(db.String(50), nullable=False)  # 'PHQ-9', 'GAD-7', 'custom'
    responses = db.Column(db.Text, nullable=False)  # JSON string of responses
    total_score = db.Column(db.Integer, nullable=False)
    severity_level = db.Column(db.String(50), nullable=False)  # 'minimal', 'mild', 'moderate', 'severe'
    recommendations = db.Column(db.Text, nullable=True)  # JSON string of recommendations
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def get_responses(self):
        """Get assessment responses as dictionary"""
        if self.responses:
            return json.loads(self.responses)
        return {}
    
    def set_responses(self, responses_dict):
        """Set assessment responses from dictionary"""
        self.responses = json.dumps(responses_dict)
    
    def get_recommendations(self):
        """Get recommendations as list"""
        if self.recommendations:
            return json.loads(self.recommendations)
        return []
    
    def set_recommendations(self, recommendations_list):
        """Set recommendations from list"""
        self.recommendations = json.dumps(recommendations_list)

class Recommendation(db.Model):
    """Personalized recommendations for users"""
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recommendation_type = db.Column(db.String(50), nullable=False)  # 'exercise', 'meditation', 'resource', 'activity'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=True)  # Detailed content or instructions
    priority = db.Column(db.Integer, default=1)  # 1-5 priority scale
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def mark_completed(self, feedback=None):
        """Mark recommendation as completed"""
        self.is_completed = True
        self.completed_at = datetime.now(timezone.utc)
        if feedback:
            self.feedback = feedback

class Notification(db.Model):
    """User notifications and reminders"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'reminder', 'assessment', 'recommendation', 'general'
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    read_at = db.Column(db.DateTime, nullable=True)
    
    def mark_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.now(timezone.utc)

class ContactMessage(db.Model):
    """Contact form messages"""
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    replied_at = db.Column(db.DateTime, nullable=True)
    reply_message = db.Column(db.Text, nullable=True)

class UserAchievement(db.Model):
    """User achievements and gamification"""
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_type = db.Column(db.String(50), nullable=False)  # 'streak', 'badge', 'milestone'
    achievement_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    points = db.Column(db.Integer, default=0)
    metadata = db.Column(db.Text, nullable=True)  # JSON string for additional data
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def get_metadata(self):
        """Get achievement metadata as dictionary"""
        if self.metadata:
            return json.loads(self.metadata)
        return {}
    
    def set_metadata(self, metadata_dict):
        """Set achievement metadata from dictionary"""
        self.metadata = json.dumps(metadata_dict)