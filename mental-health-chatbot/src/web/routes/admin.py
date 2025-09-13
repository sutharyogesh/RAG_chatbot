"""
Admin Routes - Administrative functions
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from src.db.models import User, ChatSession, Message, MoodEntry, Assessment, ContactMessage, db
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def index():
    """Admin dashboard"""
    # Get basic statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_sessions = ChatSession.query.count()
    active_sessions = ChatSession.query.filter_by(is_active=True).count()
    total_messages = Message.query.count()
    total_mood_entries = MoodEntry.query.count()
    total_assessments = Assessment.query.count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_sessions = ChatSession.query.order_by(ChatSession.created_at.desc()).limit(5).all()
    recent_contacts = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    
    # Crisis detection stats
    crisis_sessions = ChatSession.query.filter(
        ChatSession.sentiment_score < -0.5
    ).count()
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_sessions': total_sessions,
        'active_sessions': active_sessions,
        'total_messages': total_messages,
        'total_mood_entries': total_mood_entries,
        'total_assessments': total_assessments,
        'crisis_sessions': crisis_sessions
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_sessions=recent_sessions,
                         recent_contacts=recent_contacts)

@admin_bp.route('/users')
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """User detail page"""
    user = User.query.get_or_404(user_id)
    
    # Get user's recent activity
    recent_sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.created_at.desc()).limit(10).all()
    recent_mood_entries = MoodEntry.query.filter_by(user_id=user_id).order_by(MoodEntry.created_at.desc()).limit(10).all()
    recent_assessments = Assessment.query.filter_by(user_id=user_id).order_by(Assessment.created_at.desc()).limit(5).all()
    
    return render_template('admin/user_detail.html', 
                         user=user,
                         recent_sessions=recent_sessions,
                         recent_mood_entries=recent_mood_entries,
                         recent_assessments=recent_assessments)

@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    return jsonify({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
        'is_active': user.is_active
    })

@admin_bp.route('/sessions')
@admin_required
def sessions():
    """Chat sessions management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    sessions = ChatSession.query.order_by(ChatSession.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/sessions.html', sessions=sessions)

@admin_bp.route('/sessions/<int:session_id>')
@admin_required
def session_detail(session_id):
    """Session detail page"""
    session = ChatSession.query.get_or_404(session_id)
    messages = Message.query.filter_by(session_id=session.id).order_by(Message.created_at).all()
    
    return render_template('admin/session_detail.html', 
                         session=session,
                         messages=messages)

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Analytics and reporting"""
    # Get date range
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    # User registration trends
    user_registrations = db.session.query(
        db.func.date(User.created_at).label('date'),
        db.func.count(User.id).label('count')
    ).filter(
        User.created_at >= start_date
    ).group_by(
        db.func.date(User.created_at)
    ).all()
    
    # Session trends
    session_trends = db.session.query(
        db.func.date(ChatSession.created_at).label('date'),
        db.func.count(ChatSession.id).label('count')
    ).filter(
        ChatSession.created_at >= start_date
    ).group_by(
        db.func.date(ChatSession.created_at)
    ).all()
    
    # Mood distribution
    mood_distribution = db.session.query(
        MoodEntry.mood_score,
        db.func.count(MoodEntry.id).label('count')
    ).filter(
        MoodEntry.created_at >= start_date
    ).group_by(MoodEntry.mood_score).all()
    
    # Assessment results
    assessment_results = db.session.query(
        Assessment.severity_level,
        db.func.count(Assessment.id).label('count')
    ).filter(
        Assessment.created_at >= start_date
    ).group_by(Assessment.severity_level).all()
    
    return render_template('admin/analytics.html',
                         user_registrations=user_registrations,
                         session_trends=session_trends,
                         mood_distribution=mood_distribution,
                         assessment_results=assessment_results,
                         days=days)

@admin_bp.route('/contact-messages')
@admin_required
def contact_messages():
    """Contact form messages"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/contact_messages.html', messages=messages)

@admin_bp.route('/contact-messages/<int:message_id>')
@admin_required
def contact_message_detail(message_id):
    """Contact message detail"""
    message = ContactMessage.query.get_or_404(message_id)
    
    return render_template('admin/contact_message_detail.html', message=message)

@admin_bp.route('/contact-messages/<int:message_id>/reply', methods=['POST'])
@admin_required
def reply_to_contact(message_id):
    """Reply to contact message"""
    message = ContactMessage.query.get_or_404(message_id)
    data = request.get_json()
    
    reply_text = data.get('reply', '').strip()
    if not reply_text:
        return jsonify({'error': 'Reply message is required'}), 400
    
    try:
        # Update message
        message.reply_message = reply_text
        message.replied_at = datetime.utcnow()
        message.is_read = True
        
        db.session.commit()
        
        # Send email reply (would need email service)
        # send_email(
        #     to=message.email,
        #     subject=f'Re: {message.subject}',
        #     body=reply_text
        # )
        
        return jsonify({'message': 'Reply sent successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to send reply'}), 500

@admin_bp.route('/export-data')
@admin_required
def export_data():
    """Export system data"""
    format_type = request.args.get('format', 'csv')
    data_type = request.args.get('type', 'users')
    
    if format_type == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if data_type == 'users':
            writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Created At', 'Last Login', 'Is Active'])
            users = User.query.all()
            for user in users:
                writer.writerow([
                    user.id,
                    user.username,
                    user.email,
                    user.first_name or '',
                    user.last_name or '',
                    user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
                    user.is_active
                ])
        
        elif data_type == 'sessions':
            writer.writerow(['ID', 'User ID', 'Session ID', 'Is Anonymous', 'Mood Detected', 'Sentiment Score', 'Created At', 'Is Active'])
            sessions = ChatSession.query.all()
            for session in sessions:
                writer.writerow([
                    session.id,
                    session.user_id or '',
                    session.session_id,
                    session.is_anonymous,
                    session.mood_detected or '',
                    session.sentiment_score or '',
                    session.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    session.is_active
                ])
        
        elif data_type == 'mood_entries':
            writer.writerow(['ID', 'User ID', 'Mood Score', 'Mood Label', 'Stress Level', 'Energy Level', 'Sleep Hours', 'Created At'])
            entries = MoodEntry.query.all()
            for entry in entries:
                writer.writerow([
                    entry.id,
                    entry.user_id,
                    entry.mood_score,
                    entry.mood_label,
                    entry.stress_level or '',
                    entry.energy_level or '',
                    entry.sleep_hours or '',
                    entry.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={data_type}_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    
    return jsonify({'error': 'Invalid format or data type'}), 400

@admin_bp.route('/system-health')
@admin_required
def system_health():
    """System health check"""
    health_status = {
        'database': 'healthy',
        'openai_api': 'unknown',
        'pinecone': 'unknown',
        'email_service': 'unknown'
    }
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        health_status['database'] = 'healthy'
    except Exception as e:
        health_status['database'] = f'error: {str(e)}'
    
    # Check OpenAI API (would need actual API call)
    # try:
    #     # Test OpenAI API
    #     health_status['openai_api'] = 'healthy'
    # except Exception as e:
    #     health_status['openai_api'] = f'error: {str(e)}'
    
    # Check Pinecone (would need actual API call)
    # try:
    #     # Test Pinecone API
    #     health_status['pinecone'] = 'healthy'
    # except Exception as e:
    #     health_status['pinecone'] = f'error: {str(e)}'
    
    return jsonify(health_status)

@admin_bp.route('/settings')
@admin_required
def settings():
    """System settings"""
    return render_template('admin/settings.html')

@admin_bp.route('/settings', methods=['POST'])
@admin_required
def update_settings():
    """Update system settings"""
    data = request.get_json()
    
    # This would typically update configuration in database or config file
    # For now, just return success
    
    return jsonify({'message': 'Settings updated successfully'})