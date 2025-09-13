"""
Web Routes Package
"""

from .auth import auth_bp
from .chat import chat_bp
from .dashboard import dashboard_bp
from .admin import admin_bp
from .api import api_bp

__all__ = ['auth_bp', 'chat_bp', 'dashboard_bp', 'admin_bp', 'api_bp']