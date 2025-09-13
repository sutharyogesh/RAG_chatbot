"""
Flask Application Factory
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from src.web.config import config
from src.db.database import db

# Initialize extensions
login_manager = LoginManager()
jwt = JWTManager()
migrate = Migrate()
cors = CORS()
mail = Mail()

def create_app(config_name=None):
    """Create and configure Flask application"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    mail.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from src.db.models import User
        return User.query.get(int(user_id))
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': 'Authorization token is required'}, 401
    
    # Register blueprints
    from src.web.routes.auth import auth_bp
    from src.web.routes.chat import chat_bp
    from src.web.routes.dashboard import dashboard_bp
    from src.web.routes.admin import admin_bp
    from src.web.routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Main routes
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')
    
    @app.route('/about')
    def about():
        from flask import render_template
        return render_template('about.html')
    
    @app.route('/contact')
    def contact():
        from flask import render_template
        return render_template('contact.html')
    
    @app.route('/features')
    def features():
        from flask import render_template
        return render_template('features.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_app_info():
        return {
            'app_name': app.config['APP_NAME'],
            'app_version': app.config['APP_VERSION']
        }
    
    # Before request handlers
    @app.before_request
    def before_request():
        from flask import g, request
        from datetime import datetime
        
        g.request_start_time = datetime.now()
        
        # Log request (in production, use proper logging)
        if app.config['DEBUG']:
            print(f"Request: {request.method} {request.path}")
    
    # After request handlers
    @app.after_request
    def after_request(response):
        from flask import g, request
        from datetime import datetime
        
        if hasattr(g, 'request_start_time'):
            duration = (datetime.now() - g.request_start_time).total_seconds()
            if app.config['DEBUG']:
                print(f"Request completed in {duration:.3f}s")
        
        return response
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'app_name': app.config['APP_NAME'],
            'version': app.config['APP_VERSION'],
            'timestamp': datetime.now().isoformat()
        }
    
    return app