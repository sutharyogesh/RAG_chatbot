"""
API Routes - REST API endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.db.models import User, ChatSession, Message, MoodEntry, Assessment, Recommendation, db
from src.nlp.gpt_handler import GPTHandler
from src.nlp.sentiment_analysis import SentimentAnalyzer
from src.nlp.intent_detection import IntentDetector
from src.ml.models.recommendation_engine import RecommendationEngine
from datetime import datetime, timedelta
import json

api_bp = Blueprint('api', __name__)

# Initialize components
gpt_handler = GPTHandler()
sentiment_analyzer = SentimentAnalyzer()
intent_detector = IntentDetector()
recommendation_engine = RecommendationEngine()

@api_bp.route('/health')
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API login endpoint"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Find user
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if user and user.check_password(password) and user.is_active:
        from flask_jwt_extended import create_access_token, create_refresh_token
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    """API registration endpoint"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    # Validation
    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
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
        
        from flask_jwt_extended import create_access_token, create_refresh_token
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@api_bp.route('/chat/session', methods=['POST'])
@jwt_required()
def create_chat_session():
    """Create a new chat session"""
    data = request.get_json()
    user_id = get_jwt_identity()
    is_anonymous = data.get('anonymous', False)
    
    import uuid
    session_id = str(uuid.uuid4())
    
    chat_session = ChatSession(
        session_id=session_id,
        user_id=user_id if not is_anonymous else None,
        is_anonymous=is_anonymous
    )
    
    db.session.add(chat_session)
    db.session.commit()
    
    return jsonify({
        'session_id': session_id,
        'message': 'Chat session created'
    })

@api_bp.route('/chat/session/<session_id>/message', methods=['POST'])
@jwt_required()
def send_chat_message(session_id):
    """Send a message to the chatbot"""
    data = request.get_json()
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Get chat session
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if not chat_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Check permissions
    user_id = get_jwt_identity()
    if not chat_session.is_anonymous and chat_session.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Save user message
        user_message = Message(
            session_id=chat_session.id,
            sender='user',
            content=message_text,
            message_type='text'
        )
        db.session.add(user_message)
        
        # Analyze message
        sentiment_result = sentiment_analyzer.analyze_sentiment(message_text)
        intent_result = intent_detector.detect_intent(message_text)
        
        # Generate GPT response
        gpt_response = gpt_handler.generate_response(
            user_message=message_text,
            conversation_type=intent_result.get('primary_intent', 'general')
        )
        
        bot_response_text = gpt_response['response']
        
        # Save bot response
        bot_message = Message(
            session_id=chat_session.id,
            sender='bot',
            content=bot_response_text,
            message_type='text',
            metadata=json.dumps({
                'sentiment': sentiment_result,
                'intent': intent_result,
                'gpt_metadata': gpt_response
            })
        )
        db.session.add(bot_message)
        
        # Update chat session
        chat_session.mood_detected = sentiment_result.get('sentiment_label')
        chat_session.sentiment_score = sentiment_result.get('polarity')
        
        db.session.commit()
        
        return jsonify({
            'message': bot_response_text,
            'sentiment': sentiment_result,
            'intent': intent_result
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to process message'}), 500

@api_bp.route('/mood/entry', methods=['POST'])
@jwt_required()
def add_mood_entry():
    """Add a mood entry"""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    try:
        mood_entry = MoodEntry(
            user_id=user_id,
            mood_score=data.get('mood_score'),
            mood_label=data.get('mood_label', ''),
            activities=data.get('activities', []),
            notes=data.get('notes', ''),
            energy_level=data.get('energy_level'),
            sleep_hours=data.get('sleep_hours'),
            stress_level=data.get('stress_level')
        )
        
        mood_entry.set_activities(data.get('activities', []))
        
        db.session.add(mood_entry)
        db.session.commit()
        
        return jsonify({
            'message': 'Mood entry added successfully',
            'entry_id': mood_entry.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add mood entry'}), 500

@api_bp.route('/mood/entries')
@jwt_required()
def get_mood_entries():
    """Get mood entries"""
    user_id = get_jwt_identity()
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    entries = MoodEntry.query.filter(
        MoodEntry.user_id == user_id,
        MoodEntry.created_at >= start_date
    ).order_by(MoodEntry.created_at.desc()).all()
    
    entries_data = []
    for entry in entries:
        entries_data.append({
            'id': entry.id,
            'mood_score': entry.mood_score,
            'mood_label': entry.mood_label,
            'activities': entry.get_activities(),
            'notes': entry.notes,
            'energy_level': entry.energy_level,
            'sleep_hours': entry.sleep_hours,
            'stress_level': entry.stress_level,
            'created_at': entry.created_at.isoformat()
        })
    
    return jsonify({
        'entries': entries_data,
        'total_count': len(entries_data)
    })

@api_bp.route('/assessment', methods=['POST'])
@jwt_required()
def submit_assessment():
    """Submit assessment responses"""
    data = request.get_json()
    user_id = get_jwt_identity()
    
    assessment_type = data.get('type')
    responses = data.get('responses', {})
    
    if not assessment_type or not responses:
        return jsonify({'error': 'Assessment type and responses are required'}), 400
    
    try:
        # Analyze responses
        results = gpt_handler.analyze_assessment_responses(assessment_type, responses)
        
        # Save assessment
        assessment = Assessment(
            user_id=user_id,
            assessment_type=assessment_type,
            responses=responses,
            total_score=results.get('total_score', 0),
            severity_level=results.get('severity_level', 'minimal')
        )
        assessment.set_responses(responses)
        assessment.set_recommendations(results.get('recommendations', []))
        
        db.session.add(assessment)
        db.session.commit()
        
        return jsonify({
            'message': 'Assessment submitted successfully',
            'results': results,
            'assessment_id': assessment.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to submit assessment'}), 500

@api_bp.route('/recommendations')
@jwt_required()
def get_recommendations():
    """Get personalized recommendations"""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    
    user_profile = data.get('user_profile', {})
    current_context = data.get('current_context', {})
    assessment_results = data.get('assessment_results')
    
    # Get user's recent mood data
    recent_mood = MoodEntry.query.filter_by(user_id=user_id).order_by(MoodEntry.created_at.desc()).first()
    if recent_mood:
        user_profile.setdefault('mood_score', recent_mood.mood_score)
        user_profile.setdefault('stress_level', recent_mood.stress_level or 5)
    
    recommendations = recommendation_engine.generate_recommendations(
        user_profile=user_profile,
        current_context=current_context,
        assessment_results=assessment_results
    )
    
    return jsonify({
        'recommendations': recommendations
    })

@api_bp.route('/sentiment/analyze', methods=['POST'])
def analyze_sentiment():
    """Analyze text sentiment"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    try:
        result = sentiment_analyzer.analyze_sentiment(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'Failed to analyze sentiment'}), 500

@api_bp.route('/intent/detect', methods=['POST'])
def detect_intent():
    """Detect text intent"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    try:
        result = intent_detector.detect_intent(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'Failed to detect intent'}), 500

@api_bp.route('/contact', methods=['POST'])
def submit_contact():
    """Submit contact form"""
    data = request.get_json()
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    
    if not all([name, email, subject, message]):
        return jsonify({'error': 'All fields are required'}), 400
    
    try:
        contact_message = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        
        db.session.add(contact_message)
        db.session.commit()
        
        return jsonify({'message': 'Contact message submitted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to submit contact message'}), 500

@api_bp.route('/export/data')
@jwt_required()
def export_user_data():
    """Export user data"""
    user_id = get_jwt_identity()
    format_type = request.args.get('format', 'json')
    
    if format_type == 'json':
        # Get user data
        user = User.query.get(user_id)
        mood_entries = MoodEntry.query.filter_by(user_id=user_id).all()
        assessments = Assessment.query.filter_by(user_id=user_id).all()
        recommendations = Recommendation.query.filter_by(user_id=user_id).all()
        
        export_data = {
            'user': user.to_dict(),
            'mood_entries': [],
            'assessments': [],
            'recommendations': []
        }
        
        for entry in mood_entries:
            export_data['mood_entries'].append({
                'mood_score': entry.mood_score,
                'mood_label': entry.mood_label,
                'activities': entry.get_activities(),
                'notes': entry.notes,
                'energy_level': entry.energy_level,
                'sleep_hours': entry.sleep_hours,
                'stress_level': entry.stress_level,
                'created_at': entry.created_at.isoformat()
            })
        
        for assessment in assessments:
            export_data['assessments'].append({
                'type': assessment.assessment_type,
                'total_score': assessment.total_score,
                'severity_level': assessment.severity_level,
                'responses': assessment.get_responses(),
                'created_at': assessment.created_at.isoformat()
            })
        
        for rec in recommendations:
            export_data['recommendations'].append({
                'type': rec.recommendation_type,
                'title': rec.title,
                'description': rec.description,
                'priority': rec.priority,
                'is_completed': rec.is_completed,
                'created_at': rec.created_at.isoformat()
            })
        
        return jsonify(export_data)
    
    return jsonify({'error': 'Invalid format'}), 400