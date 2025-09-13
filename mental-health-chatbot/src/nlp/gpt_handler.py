"""
GPT Handler - OpenAI GPT API integration for empathetic conversations
"""

import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from datetime import datetime

class GPTHandler:
    """Handles GPT API interactions for mental health conversations"""
    
    def __init__(self):
        """Initialize GPT handler"""
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4')
        self.max_tokens = int(os.environ.get('OPENAI_MAX_TOKENS', '1000'))
        self.temperature = float(os.environ.get('OPENAI_TEMPERATURE', '0.7'))
        
        # System prompts for different conversation contexts
        self.system_prompts = {
            'general': """You are an empathetic mental health support chatbot. Your role is to:
1. Provide emotional support and validation
2. Listen actively and respond with empathy
3. Offer practical coping strategies when appropriate
4. Encourage professional help when needed
5. Maintain a warm, non-judgmental tone
6. Ask thoughtful follow-up questions
7. Never provide medical diagnoses or replace professional therapy

Remember: You are here to support, not to diagnose or treat.""",
            
            'crisis': """You are a mental health crisis support chatbot. Your role is to:
1. Take any mention of self-harm or suicide seriously
2. Provide immediate emotional support
3. Encourage contacting crisis hotlines or emergency services
4. Stay calm and supportive
5. Never minimize the person's feelings
6. Provide crisis resources immediately

CRISIS RESOURCES:
- National Suicide Prevention Lifeline: 988
- Crisis Text Line: Text HOME to 741741
- Emergency Services: 911""",
            
            'assessment': """You are conducting a mental health assessment. Your role is to:
1. Ask assessment questions in a supportive manner
2. Validate the person's responses
3. Explain the purpose of each question
4. Maintain a non-judgmental approach
5. Provide reassurance about confidentiality
6. Guide through the assessment process smoothly""",
            
            'recommendations': """You are providing personalized mental health recommendations. Your role is to:
1. Suggest evidence-based coping strategies
2. Recommend appropriate activities and exercises
3. Provide resources and tools
4. Consider the person's current mental state
5. Offer practical, actionable advice
6. Encourage gradual progress"""
        }
    
    def generate_response(self, 
                         user_message: str,
                         conversation_history: List[Dict[str, str]] = None,
                         context: Dict[str, Any] = None,
                         conversation_type: str = 'general') -> Dict[str, Any]:
        """Generate empathetic response using GPT"""
        try:
            # Prepare system prompt
            system_prompt = self.system_prompts.get(conversation_type, self.system_prompts['general'])
            
            # Add context information to system prompt
            if context:
                context_info = self._format_context(context)
                system_prompt += f"\n\nCurrent context: {context_info}"
            
            # Prepare messages
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-10:]:  # Keep last 10 messages for context
                    messages.append({
                        "role": "user" if msg.get('sender') == 'user' else "assistant",
                        "content": msg.get('content', '')
                    })
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            bot_response = response.choices[0].message.content.strip()
            
            # Analyze response for safety and appropriateness
            safety_check = self._safety_check(bot_response)
            
            return {
                'response': bot_response,
                'conversation_type': conversation_type,
                'safety_check': safety_check,
                'tokens_used': response.usage.total_tokens if response.usage else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'response': "I apologize, but I'm having trouble processing your message right now. Please try again in a moment.",
                'error': str(e),
                'conversation_type': conversation_type,
                'timestamp': datetime.now().isoformat()
            }
    
    def detect_crisis_keywords(self, message: str) -> Dict[str, Any]:
        """Detect crisis keywords in user message"""
        crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'not worth living',
            'hurt myself', 'self harm', 'cut myself', 'overdose',
            'jump off', 'hang myself', 'die', 'death', 'dead'
        ]
        
        message_lower = message.lower()
        detected_keywords = [keyword for keyword in crisis_keywords if keyword in message_lower]
        
        return {
            'is_crisis': len(detected_keywords) > 0,
            'keywords': detected_keywords,
            'severity': 'high' if len(detected_keywords) > 2 else 'medium' if detected_keywords else 'low'
        }
    
    def generate_assessment_questions(self, assessment_type: str) -> List[Dict[str, Any]]:
        """Generate assessment questions based on type"""
        if assessment_type == 'PHQ-9':
            return self._get_phq9_questions()
        elif assessment_type == 'GAD-7':
            return self._get_gad7_questions()
        elif assessment_type == 'custom':
            return self._get_custom_questions()
        else:
            return []
    
    def analyze_assessment_responses(self, 
                                   assessment_type: str, 
                                   responses: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze assessment responses and provide scoring"""
        if assessment_type == 'PHQ-9':
            return self._analyze_phq9(responses)
        elif assessment_type == 'GAD-7':
            return self._analyze_gad7(responses)
        else:
            return self._analyze_custom(responses)
    
    def generate_recommendations(self, 
                               user_profile: Dict[str, Any],
                               current_mood: str,
                               assessment_results: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate personalized recommendations"""
        try:
            # Prepare recommendation prompt
            prompt = f"""
            Based on the following user profile and current state, generate 3-5 personalized mental health recommendations:
            
            User Profile: {json.dumps(user_profile, indent=2)}
            Current Mood: {current_mood}
            Assessment Results: {json.dumps(assessment_results or {}, indent=2)}
            
            For each recommendation, provide:
            1. Type (exercise, meditation, activity, resource, professional_help)
            2. Title
            3. Description
            4. Instructions
            5. Priority (1-5)
            6. Expected duration
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.5
            )
            
            recommendations_text = response.choices[0].message.content.strip()
            return self._parse_recommendations(recommendations_text)
            
        except Exception as e:
            return [{
                'type': 'general',
                'title': 'General Support',
                'description': 'Consider reaching out to a mental health professional for personalized support.',
                'instructions': 'Contact a therapist or counselor for professional guidance.',
                'priority': 3,
                'duration': 'Ongoing'
            }]
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for GPT"""
        context_parts = []
        
        if context.get('mood'):
            context_parts.append(f"Current mood: {context['mood']}")
        
        if context.get('stress_level'):
            context_parts.append(f"Stress level: {context['stress_level']}/10")
        
        if context.get('recent_activities'):
            context_parts.append(f"Recent activities: {', '.join(context['recent_activities'])}")
        
        if context.get('assessment_results'):
            context_parts.append(f"Assessment results: {context['assessment_results']}")
        
        return "; ".join(context_parts)
    
    def _safety_check(self, response: str) -> Dict[str, Any]:
        """Check response for safety and appropriateness"""
        # Basic safety checks
        inappropriate_keywords = ['kill yourself', 'hurt yourself', 'end it all']
        response_lower = response.lower()
        
        has_inappropriate = any(keyword in response_lower for keyword in inappropriate_keywords)
        
        return {
            'is_safe': not has_inappropriate,
            'has_inappropriate_content': has_inappropriate,
            'confidence': 0.9 if not has_inappropriate else 0.1
        }
    
    def _get_phq9_questions(self) -> List[Dict[str, Any]]:
        """Get PHQ-9 depression assessment questions"""
        return [
            {
                'id': 'phq9_1',
                'question': 'Little interest or pleasure in doing things',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'phq9_2',
                'question': 'Feeling down, depressed, or hopeless',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'phq9_3',
                'question': 'Trouble falling or staying asleep, or sleeping too much',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'phq9_4',
                'question': 'Feeling tired or having little energy',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'phq9_5',
                'question': 'Poor appetite or overeating',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'phq9_6',
                'question': 'Feeling bad about yourself - or that you are a failure or have let yourself or your family down',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'phq9_7',
                'question': 'Trouble concentrating on things, such as reading the newspaper or watching television',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'phq9_8',
                'question': 'Moving or speaking so slowly that other people could have noticed, or the opposite - being so fidgety or restless that you have been moving around a lot more than usual',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'phq9_9',
                'question': 'Thoughts that you would be better off dead, or of hurting yourself',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            }
        ]
    
    def _get_gad7_questions(self) -> List[Dict[str, Any]]:
        """Get GAD-7 anxiety assessment questions"""
        return [
            {
                'id': 'gad7_1',
                'question': 'Feeling nervous, anxious, or on edge',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'gad7_2',
                'question': 'Not being able to stop or control worrying',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'gad7_3',
                'question': 'Worrying too much about different things',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'gad7_4',
                'question': 'Trouble relaxing',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'gad7_5',
                'question': 'Being so restless that it is hard to sit still',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'gad7_6',
                'question': 'Becoming easily annoyed or irritable',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            },
            {
                'id': 'gad7_7',
                'question': 'Feeling afraid, as if something awful might happen',
                'options': [
                    {'value': 0, 'text': 'Not at all'},
                    {'value': 1, 'text': 'Several days'},
                    {'value': 2, 'text': 'More than half the days'},
                    {'value': 3, 'text': 'Nearly every day'}
                ]
            }
        ]
    
    def _get_custom_questions(self) -> List[Dict[str, Any]]:
        """Get custom assessment questions"""
        return [
            {
                'id': 'custom_1',
                'question': 'How would you rate your overall mood today?',
                'options': [
                    {'value': 1, 'text': 'Very poor'},
                    {'value': 2, 'text': 'Poor'},
                    {'value': 3, 'text': 'Fair'},
                    {'value': 4, 'text': 'Good'},
                    {'value': 5, 'text': 'Excellent'}
                ]
            },
            {
                'id': 'custom_2',
                'question': 'How well did you sleep last night?',
                'options': [
                    {'value': 1, 'text': 'Very poorly'},
                    {'value': 2, 'text': 'Poorly'},
                    {'value': 3, 'text': 'Fairly well'},
                    {'value': 4, 'text': 'Well'},
                    {'value': 5, 'text': 'Very well'}
                ]
            },
            {
                'id': 'custom_3',
                'question': 'How would you rate your stress level today?',
                'options': [
                    {'value': 1, 'text': 'Very low'},
                    {'value': 2, 'text': 'Low'},
                    {'value': 3, 'text': 'Moderate'},
                    {'value': 4, 'text': 'High'},
                    {'value': 5, 'text': 'Very high'}
                ]
            }
        ]
    
    def _analyze_phq9(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze PHQ-9 responses"""
        total_score = sum(responses.values())
        
        if total_score <= 4:
            severity = 'minimal'
        elif total_score <= 9:
            severity = 'mild'
        elif total_score <= 14:
            severity = 'moderate'
        elif total_score <= 19:
            severity = 'moderately severe'
        else:
            severity = 'severe'
        
        return {
            'total_score': total_score,
            'severity_level': severity,
            'max_score': 27,
            'interpretation': f'PHQ-9 score of {total_score} indicates {severity} depression'
        }
    
    def _analyze_gad7(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze GAD-7 responses"""
        total_score = sum(responses.values())
        
        if total_score <= 4:
            severity = 'minimal'
        elif total_score <= 9:
            severity = 'mild'
        elif total_score <= 14:
            severity = 'moderate'
        else:
            severity = 'severe'
        
        return {
            'total_score': total_score,
            'severity_level': severity,
            'max_score': 21,
            'interpretation': f'GAD-7 score of {total_score} indicates {severity} anxiety'
        }
    
    def _analyze_custom(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze custom assessment responses"""
        total_score = sum(responses.values())
        max_possible = len(responses) * 5  # Assuming 5-point scale
        
        if total_score <= max_possible * 0.2:
            severity = 'very_low'
        elif total_score <= max_possible * 0.4:
            severity = 'low'
        elif total_score <= max_possible * 0.6:
            severity = 'moderate'
        elif total_score <= max_possible * 0.8:
            severity = 'high'
        else:
            severity = 'very_high'
        
        return {
            'total_score': total_score,
            'severity_level': severity,
            'max_score': max_possible,
            'interpretation': f'Custom assessment score of {total_score} indicates {severity} level'
        }
    
    def _parse_recommendations(self, recommendations_text: str) -> List[Dict[str, Any]]:
        """Parse GPT-generated recommendations into structured format"""
        recommendations = []
        lines = recommendations_text.split('\n')
        
        current_rec = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_rec:
                    recommendations.append(current_rec)
                    current_rec = {}
                continue
            
            if line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.') or line.startswith('5.'):
                if current_rec:
                    recommendations.append(current_rec)
                current_rec = {'title': line[3:].strip()}
            elif line.startswith('Type:'):
                current_rec['type'] = line.split(':', 1)[1].strip()
            elif line.startswith('Description:'):
                current_rec['description'] = line.split(':', 1)[1].strip()
            elif line.startswith('Instructions:'):
                current_rec['instructions'] = line.split(':', 1)[1].strip()
            elif line.startswith('Priority:'):
                current_rec['priority'] = int(line.split(':', 1)[1].strip())
            elif line.startswith('Duration:'):
                current_rec['duration'] = line.split(':', 1)[1].strip()
        
        if current_rec:
            recommendations.append(current_rec)
        
        # Add default values for missing fields
        for rec in recommendations:
            rec.setdefault('type', 'general')
            rec.setdefault('priority', 3)
            rec.setdefault('duration', '15-30 minutes')
            rec.setdefault('instructions', rec.get('description', ''))
        
        return recommendations