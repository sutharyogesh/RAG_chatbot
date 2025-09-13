"""
Web Module - Flask web application
"""

from .app import create_app
from .config import Config

__all__ = ['create_app', 'Config']