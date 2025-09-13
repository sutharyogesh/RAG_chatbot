"""
Helper Utilities
"""

from flask import render_template
from flask_mail import Message
from datetime import datetime, timedelta
import re

def send_email(to, subject, template, **kwargs):
    """Send email using Flask-Mail"""
    from flask import current_app
    from flask_mail import mail
    
    msg = Message(
        subject=subject,
        recipients=[to],
        html=render_template(template, **kwargs),
        sender=current_app.config.get('MAIL_USERNAME')
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def format_datetime(dt, format='%Y-%m-%d %H:%M:%S'):
    """Format datetime object"""
    if dt is None:
        return ''
    return dt.strftime(format)

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        if minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"

def format_file_size(bytes_size):
    """Format file size in bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

def truncate_text(text, length=100, suffix='...'):
    """Truncate text to specified length"""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix

def get_time_ago(dt):
    """Get human readable time ago string"""
    if dt is None:
        return 'Never'
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def get_mood_emoji(mood_score):
    """Get emoji for mood score"""
    if mood_score >= 9:
        return "😄"
    elif mood_score >= 7:
        return "😊"
    elif mood_score >= 5:
        return "😐"
    elif mood_score >= 3:
        return "😔"
    else:
        return "😢"

def get_stress_level_color(level):
    """Get color for stress level"""
    if level <= 3:
        return "success"  # Green
    elif level <= 6:
        return "warning"  # Yellow
    else:
        return "danger"   # Red

def get_severity_color(severity):
    """Get color for severity level"""
    color_map = {
        'minimal': 'success',
        'mild': 'info',
        'moderate': 'warning',
        'severe': 'danger',
        'moderately_severe': 'danger'
    }
    return color_map.get(severity, 'secondary')

def format_phone_number(phone):
    """Format phone number for display"""
    if not phone:
        return ''
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Format as (XXX) XXX-XXXX for US numbers
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone

def generate_random_string(length=8):
    """Generate random string of specified length"""
    import string
    import random
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def is_valid_url(url):
    """Check if URL is valid"""
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(pattern.match(url))

def clean_html(html_text):
    """Remove HTML tags from text"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_text)

def extract_mentions(text):
    """Extract @mentions from text"""
    pattern = r'@(\w+)'
    return re.findall(pattern, text)

def extract_hashtags(text):
    """Extract #hashtags from text"""
    pattern = r'#(\w+)'
    return re.findall(pattern, text)