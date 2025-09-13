"""
Conversation Context Module - Manages conversation state and context
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque

class ConversationContext:
    """Manages conversation context and state"""
    
    def __init__(self, max_history: int = 20):
        """Initialize conversation context"""
        self.max_history = max_history
        self.context = {
            'session_id': None,
            'user_id': None,
            'conversation_history': deque(maxlen=max_history),
            'current_topic': None,
            'mood_trend': 'neutral',
            'sentiment_history': [],
            'intent_history': [],
            'user_preferences': {},
            'assessment_in_progress': None,
            'recommendations_given': [],
            'crisis_detected': False,
            'escalation_needed': False,
            'last_activity': None,
            'session_start': None,
            'context_metadata': {}
        }
    
    def initialize_session(self, session_id: str, user_id: Optional[str] = None):
        """Initialize a new conversation session"""
        self.context['session_id'] = session_id
        self.context['user_id'] = user_id
        self.context['session_start'] = datetime.now()
        self.context['last_activity'] = datetime.now()
        self.context['conversation_history'].clear()
        self.context['sentiment_history'].clear()
        self.context['intent_history'].clear()
        self.context['recommendations_given'].clear()
        self.context['crisis_detected'] = False
        self.context['escalation_needed'] = False
    
    def add_message(self, sender: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history"""
        message = {
            'sender': sender,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.context['conversation_history'].append(message)
        self.context['last_activity'] = datetime.now()
    
    def update_sentiment(self, sentiment_data: Dict[str, Any]):
        """Update sentiment analysis data"""
        sentiment_entry = {
            'timestamp': datetime.now().isoformat(),
            'polarity': sentiment_data.get('polarity', 0),
            'sentiment_label': sentiment_data.get('sentiment_label', 'neutral'),
            'confidence': sentiment_data.get('confidence', 0),
            'emotions': sentiment_data.get('emotions', {}),
            'risk_level': sentiment_data.get('risk_level', 'low')
        }
        
        self.context['sentiment_history'].append(sentiment_entry)
        
        # Update mood trend
        self._update_mood_trend()
        
        # Check for crisis
        if sentiment_data.get('risk_level') == 'high':
            self.context['crisis_detected'] = True
            self.context['escalation_needed'] = True
    
    def update_intent(self, intent_data: Dict[str, Any]):
        """Update intent detection data"""
        intent_entry = {
            'timestamp': datetime.now().isoformat(),
            'primary_intent': intent_data.get('primary_intent', 'general_question'),
            'confidence': intent_data.get('confidence', 0),
            'urgency_level': intent_data.get('urgency_level', 'low'),
            'all_intents': intent_data.get('all_intents', {})
        }
        
        self.context['intent_history'].append(intent_entry)
        
        # Update current topic
        self._update_current_topic(intent_data.get('primary_intent'))
        
        # Check for escalation needs
        if intent_data.get('urgency_level') == 'high' and intent_data.get('confidence', 0) > 0.7:
            self.context['escalation_needed'] = True
    
    def start_assessment(self, assessment_type: str, questions: List[Dict[str, Any]]):
        """Start a mental health assessment"""
        self.context['assessment_in_progress'] = {
            'type': assessment_type,
            'questions': questions,
            'responses': {},
            'current_question': 0,
            'started_at': datetime.now().isoformat()
        }
    
    def add_assessment_response(self, question_id: str, response: Any):
        """Add response to current assessment"""
        if self.context['assessment_in_progress']:
            self.context['assessment_in_progress']['responses'][question_id] = response
    
    def complete_assessment(self) -> Optional[Dict[str, Any]]:
        """Complete current assessment and return results"""
        if not self.context['assessment_in_progress']:
            return None
        
        assessment = self.context['assessment_in_progress']
        self.context['assessment_in_progress'] = None
        
        return {
            'type': assessment['type'],
            'responses': assessment['responses'],
            'completed_at': datetime.now().isoformat(),
            'duration': (datetime.now() - datetime.fromisoformat(assessment['started_at'])).total_seconds()
        }
    
    def add_recommendation(self, recommendation: Dict[str, Any]):
        """Add a recommendation to the context"""
        recommendation_entry = {
            'timestamp': datetime.now().isoformat(),
            'recommendation': recommendation,
            'accepted': False,
            'completed': False
        }
        
        self.context['recommendations_given'].append(recommendation_entry)
    
    def mark_recommendation_accepted(self, recommendation_index: int):
        """Mark a recommendation as accepted"""
        if 0 <= recommendation_index < len(self.context['recommendations_given']):
            self.context['recommendations_given'][recommendation_index]['accepted'] = True
    
    def mark_recommendation_completed(self, recommendation_index: int):
        """Mark a recommendation as completed"""
        if 0 <= recommendation_index < len(self.context['recommendations_given']):
            self.context['recommendations_given'][recommendation_index]['completed'] = True
    
    def update_user_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.context['user_preferences'].update(preferences)
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current conversation context"""
        recent_messages = list(self.context['conversation_history'])[-5:]
        recent_sentiments = self.context['sentiment_history'][-5:]
        recent_intents = self.context['intent_history'][-5:]
        
        # Calculate average sentiment
        avg_sentiment = 0
        if recent_sentiments:
            avg_sentiment = sum(s['polarity'] for s in recent_sentiments) / len(recent_sentiments)
        
        # Get most common recent intent
        most_common_intent = 'general_question'
        if recent_intents:
            intent_counts = {}
            for intent in recent_intents:
                primary = intent['primary_intent']
                intent_counts[primary] = intent_counts.get(primary, 0) + 1
            most_common_intent = max(intent_counts, key=intent_counts.get)
        
        return {
            'session_id': self.context['session_id'],
            'user_id': self.context['user_id'],
            'session_duration': self._get_session_duration(),
            'message_count': len(self.context['conversation_history']),
            'current_topic': self.context['current_topic'],
            'mood_trend': self.context['mood_trend'],
            'avg_sentiment': avg_sentiment,
            'most_common_intent': most_common_intent,
            'crisis_detected': self.context['crisis_detected'],
            'escalation_needed': self.context['escalation_needed'],
            'assessment_in_progress': self.context['assessment_in_progress'] is not None,
            'recommendations_count': len(self.context['recommendations_given']),
            'recent_messages': recent_messages,
            'user_preferences': self.context['user_preferences']
        }
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history"""
        history = list(self.context['conversation_history'])
        if limit:
            return history[-limit:]
        return history
    
    def get_sentiment_trend(self) -> Dict[str, Any]:
        """Get sentiment trend analysis"""
        sentiments = self.context['sentiment_history']
        if not sentiments:
            return {'trend': 'stable', 'direction': 'neutral', 'volatility': 0}
        
        polarities = [s['polarity'] for s in sentiments]
        
        # Calculate trend direction
        if len(polarities) >= 2:
            recent_avg = sum(polarities[-3:]) / min(3, len(polarities))
            earlier_avg = sum(polarities[:-3]) / max(1, len(polarities) - 3) if len(polarities) > 3 else recent_avg
            
            if recent_avg > earlier_avg + 0.1:
                direction = 'improving'
            elif recent_avg < earlier_avg - 0.1:
                direction = 'declining'
            else:
                direction = 'stable'
        else:
            direction = 'stable'
        
        # Calculate volatility
        if len(polarities) > 1:
            volatility = sum(abs(polarities[i] - polarities[i-1]) for i in range(1, len(polarities))) / (len(polarities) - 1)
        else:
            volatility = 0
        
        return {
            'trend': 'improving' if direction == 'improving' else 'declining' if direction == 'declining' else 'stable',
            'direction': direction,
            'volatility': volatility,
            'recent_sentiment': polarities[-1] if polarities else 0,
            'sentiment_count': len(sentiments)
        }
    
    def should_continue_conversation(self) -> bool:
        """Determine if conversation should continue"""
        # Don't continue if crisis detected and escalation needed
        if self.context['crisis_detected'] and self.context['escalation_needed']:
            return False
        
        # Don't continue if session is too long (over 2 hours)
        if self._get_session_duration() > 7200:  # 2 hours in seconds
            return False
        
        # Don't continue if no activity for 30 minutes
        if self.context['last_activity']:
            time_since_activity = (datetime.now() - self.context['last_activity']).total_seconds()
            if time_since_activity > 1800:  # 30 minutes
                return False
        
        return True
    
    def get_context_for_gpt(self) -> str:
        """Get formatted context for GPT API"""
        context_parts = []
        
        # Session info
        context_parts.append(f"Session ID: {self.context['session_id']}")
        if self.context['user_id']:
            context_parts.append(f"User ID: {self.context['user_id']}")
        
        # Current topic and mood
        if self.context['current_topic']:
            context_parts.append(f"Current topic: {self.context['current_topic']}")
        
        context_parts.append(f"Mood trend: {self.context['mood_trend']}")
        
        # Recent conversation
        recent_messages = list(self.context['conversation_history'])[-3:]
        if recent_messages:
            context_parts.append("Recent conversation:")
            for msg in recent_messages:
                context_parts.append(f"- {msg['sender']}: {msg['content']}")
        
        # Assessment in progress
        if self.context['assessment_in_progress']:
            assessment = self.context['assessment_in_progress']
            context_parts.append(f"Assessment in progress: {assessment['type']} (question {assessment['current_question'] + 1}/{len(assessment['questions'])})")
        
        # Crisis status
        if self.context['crisis_detected']:
            context_parts.append("⚠️ CRISIS DETECTED - Handle with extreme care and provide crisis resources")
        
        if self.context['escalation_needed']:
            context_parts.append("⚠️ ESCALATION NEEDED - Consider referring to human support")
        
        return "\n".join(context_parts)
    
    def _update_mood_trend(self):
        """Update mood trend based on sentiment history"""
        sentiments = self.context['sentiment_history']
        if len(sentiments) < 2:
            return
        
        recent_sentiments = sentiments[-5:]  # Last 5 sentiments
        avg_recent = sum(s['polarity'] for s in recent_sentiments) / len(recent_sentiments)
        
        if avg_recent > 0.1:
            self.context['mood_trend'] = 'positive'
        elif avg_recent < -0.1:
            self.context['mood_trend'] = 'negative'
        else:
            self.context['mood_trend'] = 'neutral'
    
    def _update_current_topic(self, intent: str):
        """Update current conversation topic based on intent"""
        topic_mapping = {
            'depression': 'depression',
            'anxiety': 'anxiety',
            'relationship_issues': 'relationships',
            'work_stress': 'work',
            'sleep_issues': 'sleep',
            'coping_strategies': 'coping',
            'professional_help': 'professional_help',
            'assessment_request': 'assessment',
            'mood_tracking': 'mood_tracking'
        }
        
        if intent in topic_mapping:
            self.context['current_topic'] = topic_mapping[intent]
    
    def _get_session_duration(self) -> float:
        """Get session duration in seconds"""
        if not self.context['session_start']:
            return 0
        
        return (datetime.now() - self.context['session_start']).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for storage"""
        # Convert deque to list for JSON serialization
        context_copy = self.context.copy()
        context_copy['conversation_history'] = list(context_copy['conversation_history'])
        
        return context_copy
    
    def from_dict(self, context_dict: Dict[str, Any]):
        """Load context from dictionary"""
        self.context.update(context_dict)
        
        # Convert list back to deque
        if 'conversation_history' in context_dict:
            self.context['conversation_history'] = deque(
                context_dict['conversation_history'], 
                maxlen=self.max_history
            )
        
        # Convert ISO strings back to datetime objects
        if 'session_start' in context_dict and context_dict['session_start']:
            self.context['session_start'] = datetime.fromisoformat(context_dict['session_start'])
        
        if 'last_activity' in context_dict and context_dict['last_activity']:
            self.context['last_activity'] = datetime.fromisoformat(context_dict['last_activity'])