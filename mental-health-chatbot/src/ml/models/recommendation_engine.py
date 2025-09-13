"""
Recommendation Engine - Generates personalized mental health recommendations
"""

import os
import json
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np

class RecommendationEngine:
    """Generates personalized mental health recommendations"""
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.recommendations_db = self._load_recommendations_database()
        self.user_preferences = {}
        self.recommendation_history = {}
    
    def generate_recommendations(self, 
                               user_profile: Dict[str, Any],
                               current_context: Dict[str, Any],
                               assessment_results: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate personalized recommendations based on user profile and context"""
        
        # Extract key information
        mental_health_status = user_profile.get('mental_health_status', 'healthy')
        mood_score = user_profile.get('mood_score', 5)
        stress_level = user_profile.get('stress_level', 5)
        preferences = user_profile.get('preferences', {})
        
        # Current context
        current_mood = current_context.get('current_mood', 'neutral')
        time_of_day = current_context.get('time_of_day', 'morning')
        available_time = current_context.get('available_time', 30)  # minutes
        
        # Generate recommendations based on different criteria
        recommendations = []
        
        # 1. Mood-based recommendations
        mood_recs = self._get_mood_based_recommendations(current_mood, mood_score)
        recommendations.extend(mood_recs)
        
        # 2. Stress-based recommendations
        stress_recs = self._get_stress_based_recommendations(stress_level, available_time)
        recommendations.extend(stress_recs)
        
        # 3. Mental health status recommendations
        status_recs = self._get_status_based_recommendations(mental_health_status, assessment_results)
        recommendations.extend(status_recs)
        
        # 4. Time-based recommendations
        time_recs = self._get_time_based_recommendations(time_of_day, available_time)
        recommendations.extend(time_recs)
        
        # 5. Activity-based recommendations
        activity_recs = self._get_activity_based_recommendations(user_profile, available_time)
        recommendations.extend(activity_recs)
        
        # 6. Professional help recommendations
        if self._should_recommend_professional_help(mental_health_status, assessment_results):
            prof_recs = self._get_professional_help_recommendations(mental_health_status)
            recommendations.extend(prof_recs)
        
        # Filter and prioritize recommendations
        filtered_recs = self._filter_recommendations(recommendations, preferences, available_time)
        prioritized_recs = self._prioritize_recommendations(filtered_recs, user_profile, current_context)
        
        # Limit to top recommendations
        return prioritized_recs[:5]
    
    def get_emergency_recommendations(self) -> List[Dict[str, Any]]:
        """Get emergency/crisis recommendations"""
        return [
            {
                'type': 'crisis_support',
                'title': 'Crisis Support Resources',
                'description': 'Immediate help is available 24/7',
                'content': 'National Suicide Prevention Lifeline: 988\nCrisis Text Line: Text HOME to 741741\nEmergency Services: 911',
                'priority': 1,
                'duration': 'Immediate',
                'is_emergency': True
            },
            {
                'type': 'professional_help',
                'title': 'Emergency Mental Health Services',
                'description': 'Connect with emergency mental health professionals',
                'content': 'Contact your local emergency room or mental health crisis center immediately',
                'priority': 1,
                'duration': 'Immediate',
                'is_emergency': True
            },
            {
                'type': 'support_system',
                'title': 'Reach Out to Support System',
                'description': 'Contact trusted friends, family, or support groups',
                'content': 'Call or text someone you trust. You don\'t have to go through this alone.',
                'priority': 2,
                'duration': '5-10 minutes',
                'is_emergency': True
            }
        ]
    
    def get_daily_recommendations(self, user_id: str, date: str = None) -> List[Dict[str, Any]]:
        """Get daily recommendations for a specific user and date"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get user's recent mood and activity data
        user_data = self._get_user_data(user_id, date)
        
        # Generate daily recommendations
        recommendations = []
        
        # Morning routine recommendations
        if datetime.now().hour < 12:
            morning_recs = self._get_morning_recommendations(user_data)
            recommendations.extend(morning_recs)
        
        # Afternoon recommendations
        elif datetime.now().hour < 18:
            afternoon_recs = self._get_afternoon_recommendations(user_data)
            recommendations.extend(afternoon_recs)
        
        # Evening recommendations
        else:
            evening_recs = self._get_evening_recommendations(user_data)
            recommendations.extend(evening_recs)
        
        return recommendations[:3]  # Limit to 3 daily recommendations
    
    def get_weekly_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get weekly recommendations for goal setting and planning"""
        user_data = self._get_user_data(user_id)
        
        recommendations = [
            {
                'type': 'weekly_planning',
                'title': 'Weekly Mental Health Check-in',
                'description': 'Review your week and plan for the next one',
                'content': 'Take 15 minutes to reflect on your week. What went well? What challenges did you face? Plan one self-care activity for next week.',
                'priority': 3,
                'duration': '15 minutes',
                'frequency': 'weekly'
            },
            {
                'type': 'goal_setting',
                'title': 'Set Weekly Mental Health Goals',
                'description': 'Create achievable goals for your mental wellness',
                'content': 'Set 2-3 small, achievable goals for this week. Examples: practice mindfulness 3 times, exercise twice, or reach out to a friend.',
                'priority': 3,
                'duration': '10 minutes',
                'frequency': 'weekly'
            }
        ]
        
        # Add personalized recommendations based on user data
        if user_data.get('stress_level', 0) > 6:
            recommendations.append({
                'type': 'stress_management',
                'title': 'Weekly Stress Management Plan',
                'description': 'Create a plan to manage stress this week',
                'content': 'Identify your main stress sources and plan specific coping strategies. Schedule regular breaks and relaxation time.',
                'priority': 2,
                'duration': '20 minutes',
                'frequency': 'weekly'
            })
        
        return recommendations
    
    def _get_mood_based_recommendations(self, current_mood: str, mood_score: int) -> List[Dict[str, Any]]:
        """Get recommendations based on current mood"""
        recommendations = []
        
        if mood_score <= 3:  # Low mood
            recommendations.extend([
                {
                    'type': 'mood_boost',
                    'title': 'Mood-Boosting Activities',
                    'description': 'Engage in activities that can help improve your mood',
                    'content': 'Try listening to uplifting music, going for a walk in nature, or doing something creative like drawing or writing.',
                    'priority': 2,
                    'duration': '15-30 minutes'
                },
                {
                    'type': 'social_connection',
                    'title': 'Connect with Others',
                    'description': 'Reach out to friends, family, or support groups',
                    'content': 'Call or text someone you care about. Social connection can significantly improve mood.',
                    'priority': 2,
                    'duration': '10-20 minutes'
                }
            ])
        elif mood_score >= 8:  # High mood
            recommendations.extend([
                {
                    'type': 'mood_maintenance',
                    'title': 'Maintain Positive Mood',
                    'description': 'Keep up the good work and maintain your positive mood',
                    'content': 'Continue doing what\'s working for you. Consider journaling about what\'s contributing to your good mood.',
                    'priority': 3,
                    'duration': '10 minutes'
                }
            ])
        
        return recommendations
    
    def _get_stress_based_recommendations(self, stress_level: int, available_time: int) -> List[Dict[str, Any]]:
        """Get recommendations based on stress level"""
        recommendations = []
        
        if stress_level >= 7:  # High stress
            if available_time >= 30:
                recommendations.append({
                    'type': 'stress_relief',
                    'title': 'Deep Relaxation Session',
                    'description': 'Take time for a comprehensive stress relief session',
                    'content': 'Try progressive muscle relaxation, guided meditation, or a calming bath. Focus on deep breathing.',
                    'priority': 1,
                    'duration': '30 minutes'
                })
            else:
                recommendations.append({
                    'type': 'quick_stress_relief',
                    'title': 'Quick Stress Relief',
                    'description': 'Fast techniques to reduce stress in the moment',
                    'content': 'Try the 4-7-8 breathing technique: Inhale for 4 counts, hold for 7, exhale for 8. Repeat 3 times.',
                    'priority': 1,
                    'duration': '5 minutes'
                })
        elif stress_level >= 5:  # Moderate stress
            recommendations.append({
                'type': 'stress_management',
                'title': 'Stress Management Techniques',
                'description': 'Practice techniques to manage moderate stress',
                'content': 'Try mindfulness meditation, gentle stretching, or a short walk. Focus on being present in the moment.',
                'priority': 2,
                'duration': '15 minutes'
            })
        
        return recommendations
    
    def _get_status_based_recommendations(self, mental_health_status: str, assessment_results: Optional[Dict]) -> List[Dict[str, Any]]:
        """Get recommendations based on mental health status"""
        recommendations = []
        
        if 'depression' in mental_health_status:
            severity = assessment_results.get('severity_level', 'mild') if assessment_results else 'mild'
            
            if severity in ['moderate', 'severe']:
                recommendations.append({
                    'type': 'professional_help',
                    'title': 'Professional Support for Depression',
                    'description': 'Consider seeking professional help for depression',
                    'content': 'Depression is treatable. Consider reaching out to a therapist or counselor who specializes in depression treatment.',
                    'priority': 1,
                    'duration': 'Ongoing',
                    'requires_professional': True
                })
            
            recommendations.append({
                'type': 'depression_management',
                'title': 'Depression Management Strategies',
                'description': 'Evidence-based strategies for managing depression',
                'content': 'Try behavioral activation: engage in activities you used to enjoy, even if you don\'t feel like it. Start small.',
                'priority': 2,
                'duration': '20-30 minutes'
            })
        
        elif 'anxiety' in mental_health_status:
            recommendations.append({
                'type': 'anxiety_management',
                'title': 'Anxiety Management Techniques',
                'description': 'Proven techniques for managing anxiety',
                'content': 'Practice grounding techniques: Name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste.',
                'priority': 2,
                'duration': '10-15 minutes'
            })
        
        return recommendations
    
    def _get_time_based_recommendations(self, time_of_day: str, available_time: int) -> List[Dict[str, Any]]:
        """Get recommendations based on time of day"""
        recommendations = []
        
        if time_of_day == 'morning':
            recommendations.append({
                'type': 'morning_routine',
                'title': 'Morning Mental Health Routine',
                'description': 'Start your day with positive mental health practices',
                'content': 'Try gratitude journaling, gentle stretching, or a short meditation to set a positive tone for your day.',
                'priority': 3,
                'duration': '10-15 minutes'
            })
        elif time_of_day == 'evening':
            recommendations.append({
                'type': 'evening_wind_down',
                'title': 'Evening Wind-Down Routine',
                'description': 'Prepare your mind and body for restful sleep',
                'content': 'Create a calming bedtime routine: dim lights, avoid screens, try gentle breathing exercises or light reading.',
                'priority': 3,
                'duration': '20-30 minutes'
            })
        
        return recommendations
    
    def _get_activity_based_recommendations(self, user_profile: Dict, available_time: int) -> List[Dict[str, Any]]:
        """Get recommendations based on user activity preferences"""
        recommendations = []
        
        preferences = user_profile.get('preferences', {})
        activity_level = preferences.get('activity_level', 'moderate')
        
        if activity_level == 'low' and available_time >= 20:
            recommendations.append({
                'type': 'gentle_activity',
                'title': 'Gentle Physical Activity',
                'description': 'Low-impact activities for mental wellness',
                'content': 'Try gentle yoga, tai chi, or a leisurely walk. Physical activity releases endorphins that improve mood.',
                'priority': 3,
                'duration': '20-30 minutes'
            })
        elif activity_level == 'high' and available_time >= 30:
            recommendations.append({
                'type': 'energetic_activity',
                'title': 'Energetic Physical Activity',
                'description': 'Higher intensity activities for stress relief',
                'content': 'Try running, dancing, or a workout session. High-intensity exercise can be very effective for stress relief.',
                'priority': 3,
                'duration': '30-45 minutes'
            })
        
        return recommendations
    
    def _should_recommend_professional_help(self, mental_health_status: str, assessment_results: Optional[Dict]) -> bool:
        """Determine if professional help should be recommended"""
        if assessment_results:
            severity = assessment_results.get('severity_level', 'mild')
            if severity in ['moderate', 'severe']:
                return True
        
        high_risk_statuses = ['severe_depression', 'severe_anxiety', 'bipolar']
        return mental_health_status in high_risk_statuses
    
    def _get_professional_help_recommendations(self, mental_health_status: str) -> List[Dict[str, Any]]:
        """Get professional help recommendations"""
        return [
            {
                'type': 'professional_help',
                'title': 'Mental Health Professional',
                'description': 'Connect with a qualified mental health professional',
                'content': 'Consider reaching out to a therapist, psychologist, or psychiatrist. They can provide specialized treatment and support.',
                'priority': 1,
                'duration': 'Ongoing',
                'requires_professional': True
            },
            {
                'type': 'support_group',
                'title': 'Support Group',
                'description': 'Join a support group for shared experiences',
                'content': 'Support groups can provide understanding, shared experiences, and practical advice from others facing similar challenges.',
                'priority': 2,
                'duration': '1-2 hours weekly'
            }
        ]
    
    def _filter_recommendations(self, recommendations: List[Dict], preferences: Dict, available_time: int) -> List[Dict[str, Any]]:
        """Filter recommendations based on user preferences and constraints"""
        filtered = []
        
        for rec in recommendations:
            # Check time constraints
            if rec.get('duration') and 'minutes' in str(rec['duration']):
                try:
                    duration = int(rec['duration'].split()[0])
                    if duration > available_time:
                        continue
                except:
                    pass
            
            # Check user preferences
            rec_type = rec.get('type', '')
            if rec_type in ['physical_activity'] and not preferences.get('likes_exercise', True):
                continue
            
            if rec_type in ['meditation'] and not preferences.get('likes_meditation', True):
                continue
            
            filtered.append(rec)
        
        return filtered
    
    def _prioritize_recommendations(self, recommendations: List[Dict], user_profile: Dict, current_context: Dict) -> List[Dict[str, Any]]:
        """Prioritize recommendations based on user needs and context"""
        # Sort by priority (1 = highest, 3 = lowest)
        recommendations.sort(key=lambda x: x.get('priority', 3))
        
        # Add personalization score
        for rec in recommendations:
            rec['personalization_score'] = self._calculate_personalization_score(rec, user_profile, current_context)
        
        # Sort by personalization score within priority groups
        recommendations.sort(key=lambda x: (x.get('priority', 3), -x.get('personalization_score', 0)))
        
        return recommendations
    
    def _calculate_personalization_score(self, recommendation: Dict, user_profile: Dict, current_context: Dict) -> float:
        """Calculate how well a recommendation matches user preferences and context"""
        score = 0.0
        
        # Base score
        score += 0.5
        
        # Match with user preferences
        preferences = user_profile.get('preferences', {})
        rec_type = recommendation.get('type', '')
        
        if rec_type == 'physical_activity' and preferences.get('likes_exercise', False):
            score += 0.3
        
        if rec_type == 'meditation' and preferences.get('likes_meditation', False):
            score += 0.3
        
        if rec_type == 'social_connection' and preferences.get('likes_social', False):
            score += 0.3
        
        # Match with current context
        current_mood = current_context.get('current_mood', 'neutral')
        if 'mood' in rec_type and current_mood in recommendation.get('content', '').lower():
            score += 0.2
        
        # Match with mental health status
        mental_health_status = user_profile.get('mental_health_status', 'healthy')
        if mental_health_status in recommendation.get('content', '').lower():
            score += 0.2
        
        return min(score, 1.0)
    
    def _load_recommendations_database(self) -> Dict[str, Any]:
        """Load recommendations database"""
        # This would typically load from a file or database
        # For now, return a basic structure
        return {
            'activities': {
                'physical': ['walking', 'yoga', 'running', 'dancing', 'swimming'],
                'mental': ['meditation', 'journaling', 'reading', 'puzzles', 'art'],
                'social': ['calling_friend', 'joining_group', 'volunteering', 'coffee_meetup']
            },
            'techniques': {
                'breathing': ['4-7-8', 'box_breathing', 'diaphragmatic'],
                'mindfulness': ['body_scan', 'mindful_walking', 'loving_kindness'],
                'coping': ['progressive_muscle_relaxation', 'grounding', 'reframing']
            }
        }
    
    def _get_user_data(self, user_id: str, date: str = None) -> Dict[str, Any]:
        """Get user data for recommendations"""
        # This would typically query the database
        # For now, return sample data
        return {
            'mood_score': 6,
            'stress_level': 5,
            'sleep_hours': 7.5,
            'energy_level': 6,
            'activities_completed': [],
            'preferences': {
                'likes_exercise': True,
                'likes_meditation': False,
                'likes_social': True
            }
        }
    
    def _get_morning_recommendations(self, user_data: Dict) -> List[Dict[str, Any]]:
        """Get morning-specific recommendations"""
        return [
            {
                'type': 'morning_mindfulness',
                'title': 'Morning Mindfulness',
                'description': 'Start your day with intention and awareness',
                'content': 'Take 5 minutes to sit quietly and set an intention for your day. What do you want to focus on?',
                'priority': 3,
                'duration': '5 minutes'
            }
        ]
    
    def _get_afternoon_recommendations(self, user_data: Dict) -> List[Dict[str, Any]]:
        """Get afternoon-specific recommendations"""
        return [
            {
                'type': 'afternoon_break',
                'title': 'Afternoon Mental Break',
                'description': 'Take a break to recharge your mental energy',
                'content': 'Step away from work and take a 10-minute walk or do some gentle stretching.',
                'priority': 3,
                'duration': '10 minutes'
            }
        ]
    
    def _get_evening_recommendations(self, user_data: Dict) -> List[Dict[str, Any]]:
        """Get evening-specific recommendations"""
        return [
            {
                'type': 'evening_reflection',
                'title': 'Evening Reflection',
                'description': 'Reflect on your day and prepare for rest',
                'content': 'Write down three things that went well today and one thing you\'re grateful for.',
                'priority': 3,
                'duration': '10 minutes'
            }
        ]