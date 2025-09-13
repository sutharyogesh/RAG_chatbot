"""
Database Module - Handles all database operations
"""

from .database import db
from .models import *

__all__ = ['db', 'User', 'ChatSession', 'Message', 'MoodEntry', 'Assessment', 'Recommendation', 'Notification']