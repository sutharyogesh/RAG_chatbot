#!/usr/bin/env python3
"""
Mental Health ChatBot - Main Application Entry Point
"""

import os
from flask import Flask
from flask_migrate import Migrate
from src.web.app import create_app
from src.db.database import db

def main():
    """Main application entry point"""
    app = create_app()
    
    # Initialize database migrations
    migrate = Migrate(app, db)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Mental Health ChatBot on port {port}")
    print(f"🌐 Environment: {'Development' if debug else 'Production'}")
    print(f"🔗 Access the application at: http://localhost:{port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()