"""
Chat Routes - Handles chatbot interactions
"""

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.db.models import ChatSession, Message, db
from src.nlp.gpt_handler import GPTHandler
from src.nlp.sentiment_analysis import SentimentAnalyzer
from src.nlp.intent_detection import IntentDetector
from src.nlp.conversation_context import ConversationContext
from src.ml.models.recommendation_engine import RecommendationEngine
from datetime import datetime
import uuid
import json

chat_bp = Blueprint('chat', __name__)

# Initialize NLP components
gpt_handler = GPTHandler()
sentiment_analyzer = SentimentAnalyzer()
intent_detector = IntentDetector()
recommendation_engine = RecommendationEngine()

# Store conversation contexts in memory (in production, use Redis)
conversation_contexts = {}

@chat_bp.route('/')
@login_required
def index():
    """Main chat interface"""
    return render_template('chat.html')

@chat_bp.route('/anonymous')
def anonymous_chat():
    """Anonymous chat interface"""
    return render_template('chat.html', anonymous=True)

@chat_bp.route('/api/session/start', methods=['POST'])
def start_session():
    """Start a new chat session"""
    data = request.get_json()
    is_anonymous = data.get('anonymous', False)
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Create chat session
    chat_session = ChatSession(
        session_id=session_id,
        user_id=current_user.id if current_user.is_authenticated and not is_anonymous else None,
        is_anonymous=is_anonymous
    )
    
    db.session.add(chat_session)
    db.session.commit()
    
    # Initialize conversation context
    context = ConversationContext()
    context.initialize_session(
        session_id=session_id,
        user_id=current_user.id if current_user.is_authenticated and not is_anonymous else None
    )
    conversation_contexts[session_id] = context
    
    return jsonify({
        'session_id': session_id,
        'message': 'Chat session started'
    })

@chat_bp.route('/api/session/<session_id>/message', methods=['POST'])
def send_message(session_id):
    """Send a message to the chatbot"""
    data = request.get_json()
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Get chat session
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if not chat_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Get conversation context
    context = conversation_contexts.get(session_id)
    if not context:
        context = ConversationContext()
        context.initialize_session(session_id, chat_session.user_id)
        conversation_contexts[session_id] = context
    
    try:
        # Save user message
        user_message = Message(
            session_id=chat_session.id,
            sender='user',
            content=message_text,
            message_type='text'
        )
        db.session.add(user_message)
        
        # Add to conversation context
        context.add_message('user', message_text)
        
        # Analyze message
        sentiment_result = sentiment_analyzer.analyze_sentiment(message_text)
        intent_result = intent_detector.detect_intent(message_text)
        
        # Update context with analysis
        context.update_sentiment(sentiment_result)
        context.update_intent(intent_result)
        
        # Check for crisis keywords
        crisis_check = gpt_handler.detect_crisis_keywords(message_text)
        
        # Determine conversation type
        conversation_type = 'crisis' if crisis_check['is_crisis'] else intent_result.get('primary_intent', 'general')
        
        # Generate GPT response
        conversation_history = context.get_conversation_history(limit=10)
        context_summary = context.get_context_for_gpt()
        
        gpt_response = gpt_handler.generate_response(
            user_message=message_text,
            conversation_history=conversation_history,
            context={'context_summary': context_summary},
            conversation_type=conversation_type
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
                'crisis_check': crisis_check,
                'gpt_metadata': gpt_response
            })
        )
        db.session.add(bot_message)
        
        # Add bot response to context
        context.add_message('bot', bot_response_text)
        
        # Update chat session
        chat_session.context_data = json.dumps(context.to_dict())
        chat_session.mood_detected = sentiment_result.get('sentiment_label')
        chat_session.sentiment_score = sentiment_result.get('polarity')
        
        db.session.commit()
        
        # Generate recommendations if appropriate
        recommendations = []
        if intent_result.get('primary_intent') == 'recommendation_request' or sentiment_result.get('risk_level') == 'medium':
            user_profile = {
                'mental_health_status': 'healthy',  # This would come from user data
                'mood_score': int((sentiment_result.get('polarity', 0) + 1) * 5),  # Convert -1,1 to 1,10
                'stress_level': 5,  # This would come from user data
                'preferences': {}
            }
            
            current_context = {
                'current_mood': sentiment_result.get('sentiment_label', 'neutral'),
                'time_of_day': datetime.now().strftime('%H:%M'),
                'available_time': 30
            }
            
            recommendations = recommendation_engine.generate_recommendations(
                user_profile=user_profile,
                current_context=current_context
            )
        
        # Check if escalation is needed
        escalation_needed = (
            crisis_check['is_crisis'] or 
            intent_result.get('urgency_level') == 'high' or
            sentiment_result.get('risk_level') == 'high'
        )
        
        response_data = {
            'message': bot_response_text,
            'sentiment': sentiment_result,
            'intent': intent_result,
            'crisis_detected': crisis_check['is_crisis'],
            'escalation_needed': escalation_needed,
            'recommendations': recommendations[:3],  # Limit to 3 recommendations
            'conversation_context': context.get_context_summary()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        print(f"Error processing message: {e}")
        return jsonify({
            'error': 'Failed to process message',
            'message': 'I apologize, but I encountered an error. Please try again.'
        }), 500

@chat_bp.route('/api/session/<session_id>/history')
def get_chat_history(session_id):
    """Get chat history for a session"""
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if not chat_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Check permissions
    if not chat_session.is_anonymous and current_user.is_authenticated:
        if chat_session.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    elif not chat_session.is_anonymous and not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    messages = Message.query.filter_by(session_id=chat_session.id).order_by(Message.created_at).all()
    
    history = []
    for msg in messages:
        history.append({
            'id': msg.id,
            'sender': msg.sender,
            'content': msg.content,
            'message_type': msg.message_type,
            'timestamp': msg.created_at.isoformat(),
            'metadata': msg.get_metadata()
        })
    
    return jsonify({
        'session_id': session_id,
        'messages': history,
        'total_messages': len(history)
    })

@chat_bp.route('/api/session/<session_id>/context')
def get_conversation_context(session_id):
    """Get conversation context for a session"""
    context = conversation_contexts.get(session_id)
    if not context:
        return jsonify({'error': 'Context not found'}), 404
    
    return jsonify(context.get_context_summary())

@chat_bp.route('/api/session/<session_id>/recommendations', methods=['POST'])
def get_recommendations(session_id):
    """Get personalized recommendations for a session"""
    data = request.get_json()
    
    # Get user profile data
    user_profile = data.get('user_profile', {})
    current_context = data.get('current_context', {})
    assessment_results = data.get('assessment_results')
    
    # Generate recommendations
    recommendations = recommendation_engine.generate_recommendations(
        user_profile=user_profile,
        current_context=current_context,
        assessment_results=assessment_results
    )
    
    return jsonify({
        'recommendations': recommendations,
        'session_id': session_id
    })

@chat_bp.route('/api/session/<session_id>/assessment/start', methods=['POST'])
def start_assessment(session_id):
    """Start a mental health assessment"""
    data = request.get_json()
    assessment_type = data.get('type', 'PHQ-9')
    
    # Get conversation context
    context = conversation_contexts.get(session_id)
    if not context:
        return jsonify({'error': 'Session context not found'}), 404
    
    # Generate assessment questions
    questions = gpt_handler.generate_assessment_questions(assessment_type)
    
    # Start assessment in context
    context.start_assessment(assessment_type, questions)
    
    return jsonify({
        'assessment_type': assessment_type,
        'questions': questions,
        'total_questions': len(questions)
    })

@chat_bp.route('/api/session/<session_id>/assessment/response', methods=['POST'])
def submit_assessment_response(session_id):
    """Submit assessment response"""
    data = request.get_json()
    question_id = data.get('question_id')
    response = data.get('response')
    
    # Get conversation context
    context = conversation_contexts.get(session_id)
    if not context:
        return jsonify({'error': 'Session context not found'}), 404
    
    # Add response to context
    context.add_assessment_response(question_id, response)
    
    return jsonify({'message': 'Response recorded'})

@chat_bp.route('/api/session/<session_id>/assessment/complete', methods=['POST'])
def complete_assessment(session_id):
    """Complete assessment and get results"""
    # Get conversation context
    context = conversation_contexts.get(session_id)
    if not context:
        return jsonify({'error': 'Session context not found'}), 404
    
    # Complete assessment
    assessment_data = context.complete_assessment()
    if not assessment_data:
        return jsonify({'error': 'No assessment in progress'}), 400
    
    # Analyze responses
    assessment_type = assessment_data['type']
    responses = assessment_data['responses']
    
    results = gpt_handler.analyze_assessment_responses(assessment_type, responses)
    
    # Save assessment to database
    if current_user.is_authenticated:
        from src.db.models import Assessment
        assessment = Assessment(
            user_id=current_user.id,
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
        'assessment_type': assessment_type,
        'results': results,
        'completed_at': assessment_data['completed_at']
    })

@chat_bp.route('/api/session/<session_id>/export', methods=['GET'])
def export_chat_history(session_id):
    """Export chat history as CSV or PDF"""
    format_type = request.args.get('format', 'csv')
    
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if not chat_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Check permissions
    if not chat_session.is_anonymous and current_user.is_authenticated:
        if chat_session.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    elif not chat_session.is_anonymous and not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    messages = Message.query.filter_by(session_id=chat_session.id).order_by(Message.created_at).all()
    
    if format_type == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Timestamp', 'Sender', 'Message', 'Type'])
        
        # Write messages
        for msg in messages:
            writer.writerow([
                msg.created_at.isoformat(),
                msg.sender,
                msg.content,
                msg.message_type
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=chat_history_{session_id}.csv'}
        )
    
    elif format_type == 'pdf':
        # PDF export would require additional libraries like reportlab
        return jsonify({'error': 'PDF export not implemented yet'}), 501
    
    else:
        return jsonify({'error': 'Invalid format'}), 400

@chat_bp.route('/api/session/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """End a chat session"""
    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
    if not chat_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Check permissions
    if not chat_session.is_anonymous and current_user.is_authenticated:
        if chat_session.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    elif not chat_session.is_anonymous and not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Mark session as inactive
    chat_session.is_active = False
    db.session.commit()
    
    # Remove from memory
    if session_id in conversation_contexts:
        del conversation_contexts[session_id]
    
    return jsonify({'message': 'Session ended successfully'})