"""
Authentication Routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from src.db.models import User, db
from src.web.utils.validators import validate_email, validate_password, validate_username
from src.web.utils.auth_utils import generate_confirmation_token, confirm_token
from src.web.utils.helpers import send_email
from datetime import datetime, timedelta
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not username or not password:
            error_msg = 'Username and password are required'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                error_msg = 'Account is deactivated. Please contact support.'
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('login.html')
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Login user
            login_user(user, remember=remember)
            
            if request.is_json:
                # Generate JWT tokens for API access
                access_token = create_access_token(identity=user.id)
                refresh_token = create_refresh_token(identity=user.id)
                
                return jsonify({
                    'message': 'Login successful',
                    'user': user.to_dict(),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                })
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        else:
            error_msg = 'Invalid username or password'
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            flash(error_msg, 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        
        # Validation
        errors = []
        
        if not username:
            errors.append('Username is required')
        elif not validate_username(username):
            errors.append('Username must be 3-20 characters and contain only letters, numbers, and underscores')
        elif User.query.filter_by(username=username).first():
            errors.append('Username already exists')
        
        if not email:
            errors.append('Email is required')
        elif not validate_email(email):
            errors.append('Invalid email format')
        elif User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if not password:
            errors.append('Password is required')
        elif not validate_password(password):
            errors.append('Password must be at least 8 characters with uppercase, lowercase, number, and special character')
        elif password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            if request.is_json:
                return jsonify({'errors': errors}), 400
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Create user
        try:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                preferred_language='en'
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Send welcome email (optional)
            try:
                send_email(
                    to=user.email,
                    subject='Welcome to Mental Health ChatBot',
                    template='emails/welcome.html',
                    user=user
                )
            except Exception as e:
                print(f"Error sending welcome email: {e}")
            
            if request.is_json:
                return jsonify({
                    'message': 'Registration successful',
                    'user': user.to_dict()
                }), 201
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = 'Registration failed. Please try again.'
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            flash(error_msg, 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.get_json()
    
    try:
        # Update allowed fields
        if 'first_name' in data:
            current_user.first_name = data['first_name'].strip()
        
        if 'last_name' in data:
            current_user.last_name = data['last_name'].strip()
        
        if 'email' in data:
            email = data['email'].strip().lower()
            if validate_email(email) and email != current_user.email:
                if User.query.filter_by(email=email).first():
                    return jsonify({'error': 'Email already exists'}), 400
                current_user.email = email
        
        if 'preferred_language' in data:
            current_user.preferred_language = data['preferred_language']
        
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    data = request.get_json()
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validation
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    if not current_user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    if not validate_password(new_password):
        return jsonify({'error': 'New password must be at least 8 characters with uppercase, lowercase, number, and special character'}), 400
    
    if new_password != confirm_password:
        return jsonify({'error': 'New passwords do not match'}), 400
    
    try:
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change password'}), 500

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password request"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email', '').strip().lower()
        
        if not email or not validate_email(email):
            error_msg = 'Valid email is required'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate reset token
            token = generate_confirmation_token(user.email)
            
            # Send reset email
            try:
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                send_email(
                    to=user.email,
                    subject='Password Reset Request',
                    template='emails/reset_password.html',
                    user=user,
                    reset_url=reset_url
                )
            except Exception as e:
                print(f"Error sending reset email: {e}")
        
        # Always return success message for security
        success_msg = 'If an account with that email exists, a password reset link has been sent.'
        if request.is_json:
            return jsonify({'message': success_msg})
        flash(success_msg, 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    try:
        email = confirm_token(token)
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid or expired token', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        if request.method == 'POST':
            data = request.get_json() if request.is_json else request.form
            password = data.get('password', '')
            confirm_password = data.get('confirm_password', '')
            
            if not password or not confirm_password:
                error_msg = 'Password and confirmation are required'
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('reset_password.html', token=token)
            
            if not validate_password(password):
                error_msg = 'Password must be at least 8 characters with uppercase, lowercase, number, and special character'
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('reset_password.html', token=token)
            
            if password != confirm_password:
                error_msg = 'Passwords do not match'
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                flash(error_msg, 'error')
                return render_template('reset_password.html', token=token)
            
            # Update password
            user.set_password(password)
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            success_msg = 'Password reset successful. Please log in with your new password.'
            if request.is_json:
                return jsonify({'message': success_msg})
            flash(success_msg, 'success')
            return redirect(url_for('auth.login'))
        
        return render_template('reset_password.html', token=token)
        
    except Exception as e:
        flash('Invalid or expired token', 'error')
        return redirect(url_for('auth.forgot_password'))

@auth_bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh JWT token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 401
    
    new_access_token = create_access_token(identity=current_user_id)
    return jsonify({
        'access_token': new_access_token,
        'user': user.to_dict()
    })

@auth_bp.route('/api/verify')
@jwt_required()
def verify_token():
    """Verify JWT token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'Invalid token'}), 401
    
    return jsonify({
        'valid': True,
        'user': user.to_dict()
    })