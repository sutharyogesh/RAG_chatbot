"""
Validation Utilities
"""

import re
from typing import bool

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    
    # Check for uppercase, lowercase, number, and special character
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_number = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    return has_upper and has_lower and has_number and has_special

def validate_username(username: str) -> bool:
    """Validate username format"""
    if len(username) < 3 or len(username) > 20:
        return False
    
    # Only allow letters, numbers, and underscores
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15

def validate_age(age: int) -> bool:
    """Validate age range"""
    return 13 <= age <= 120

def validate_mood_score(score: int) -> bool:
    """Validate mood score range"""
    return 1 <= score <= 10

def validate_stress_level(level: int) -> bool:
    """Validate stress level range"""
    return 1 <= level <= 10

def validate_energy_level(level: int) -> bool:
    """Validate energy level range"""
    return 1 <= level <= 10

def validate_sleep_hours(hours: float) -> bool:
    """Validate sleep hours range"""
    return 0 <= hours <= 24