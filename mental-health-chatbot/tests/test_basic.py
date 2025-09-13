"""
Basic tests for Mental Health ChatBot
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from src.nlp.gpt_handler import GPTHandler
        from src.nlp.sentiment_analysis import SentimentAnalyzer
        from src.nlp.intent_detection import IntentDetector
        from src.ml.models.mental_health_classifier import MentalHealthClassifier
        from src.ml.models.recommendation_engine import RecommendationEngine
        from src.db.models import User, ChatSession, Message
        from src.web.app import create_app
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

def test_app_creation():
    """Test Flask app creation"""
    from src.web.app import create_app
    app = create_app('testing')
    assert app is not None
    assert app.config['TESTING'] is True

def test_sentiment_analyzer():
    """Test sentiment analysis functionality"""
    from src.nlp.sentiment_analysis import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze_sentiment("I feel great today!")
    
    assert 'sentiment_label' in result
    assert 'polarity' in result
    assert 'confidence' in result

def test_intent_detection():
    """Test intent detection functionality"""
    from src.nlp.intent_detection import IntentDetector
    
    detector = IntentDetector()
    result = detector.detect_intent("I'm feeling depressed")
    
    assert 'primary_intent' in result
    assert 'confidence' in result
    assert 'urgency_level' in result

def test_recommendation_engine():
    """Test recommendation engine functionality"""
    from src.ml.models.recommendation_engine import RecommendationEngine
    
    engine = RecommendationEngine()
    user_profile = {
        'mental_health_status': 'healthy',
        'mood_score': 7,
        'stress_level': 5
    }
    current_context = {
        'current_mood': 'neutral',
        'time_of_day': 'morning',
        'available_time': 30
    }
    
    recommendations = engine.generate_recommendations(user_profile, current_context)
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0

def test_mental_health_classifier():
    """Test mental health classifier functionality"""
    from src.ml.models.mental_health_classifier import MentalHealthClassifier
    
    classifier = MentalHealthClassifier()
    text_features = ["I feel good", "happy", "positive"]
    numerical_features = {
        'mood_score': 8,
        'stress_level': 3,
        'sleep_hours': 8,
        'energy_level': 7,
        'social_activity': 6,
        'physical_activity': 5
    }
    
    result = classifier.predict_mental_health_status(text_features, numerical_features)
    
    assert 'predicted_class' in result
    assert 'confidence' in result
    assert 'risk_level' in result

def test_phq9_scoring():
    """Test PHQ-9 scoring functionality"""
    from src.ml.models.mental_health_classifier import MentalHealthClassifier
    
    classifier = MentalHealthClassifier()
    phq9_scores = [0, 1, 2, 1, 0, 1, 2, 1, 0]  # Total: 8 (mild depression)
    
    result = classifier.predict_depression_severity(phq9_scores)
    
    assert result['total_score'] == 8
    assert result['severity'] == 'mild'
    assert result['risk_level'] == 'low'

def test_gad7_scoring():
    """Test GAD-7 scoring functionality"""
    from src.ml.models.mental_health_classifier import MentalHealthClassifier
    
    classifier = MentalHealthClassifier()
    gad7_scores = [1, 2, 1, 2, 1, 1, 2]  # Total: 10 (moderate anxiety)
    
    result = classifier.predict_anxiety_severity(gad7_scores)
    
    assert result['total_score'] == 10
    assert result['severity'] == 'moderate'
    assert result['risk_level'] == 'medium'

if __name__ == '__main__':
    pytest.main([__file__])