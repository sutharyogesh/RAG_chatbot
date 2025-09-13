"""
Database Configuration and Connection
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate = Migrate(app, db)
    return db

def get_db_uri():
    """Get database URI from environment variables"""
    return os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///mental_health_chatbot.db'