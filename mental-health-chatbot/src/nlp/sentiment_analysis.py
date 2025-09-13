"""
Sentiment Analysis Module - Analyzes emotional tone and sentiment
"""

import os
import re
from typing import Dict, List, Any, Tuple
from textblob import TextBlob
import spacy
from transformers import pipeline
import torch

class SentimentAnalyzer:
    """Advanced sentiment analysis for mental health conversations"""
    
    def __init__(self):
        """Initialize sentiment analyzer"""
        self.nlp = None
        self.sentiment_pipeline = None
        self.emotion_pipeline = None
        
        # Initialize spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
        
        # Initialize HuggingFace pipelines
        try:
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True
            )
            self.emotion_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
        except Exception as e:
            print(f"Warning: Could not load HuggingFace models: {e}")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Comprehensive sentiment analysis"""
        # Basic TextBlob analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Convert polarity to sentiment label
        if polarity > 0.1:
            sentiment_label = 'positive'
        elif polarity < -0.1:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'
        
        # Advanced analysis with HuggingFace models
        advanced_sentiment = self._analyze_advanced_sentiment(text)
        emotions = self._analyze_emotions(text)
        mental_health_indicators = self._analyze_mental_health_indicators(text)
        
        return {
            'text': text,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment_label': sentiment_label,
            'confidence': abs(polarity),
            'advanced_sentiment': advanced_sentiment,
            'emotions': emotions,
            'mental_health_indicators': mental_health_indicators,
            'risk_level': self._assess_risk_level(text, polarity, emotions, mental_health_indicators)
        }
    
    def analyze_conversation_sentiment(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze sentiment trends across a conversation"""
        if not messages:
            return {'overall_sentiment': 'neutral', 'trend': 'stable', 'risk_level': 'low'}
        
        sentiments = []
        emotions_over_time = []
        
        for message in messages:
            if message.get('sender') == 'user':
                sentiment = self.analyze_sentiment(message.get('content', ''))
                sentiments.append(sentiment)
                emotions_over_time.append(sentiment.get('emotions', {}))
        
        if not sentiments:
            return {'overall_sentiment': 'neutral', 'trend': 'stable', 'risk_level': 'low'}
        
        # Calculate overall sentiment
        avg_polarity = sum(s['polarity'] for s in sentiments) / len(sentiments)
        avg_subjectivity = sum(s['subjectivity'] for s in sentiments) / len(sentiments)
        
        # Determine trend
        if len(sentiments) >= 3:
            recent_polarity = sum(s['polarity'] for s in sentiments[-3:]) / 3
            earlier_polarity = sum(s['polarity'] for s in sentiments[:-3]) / len(sentiments[:-3]) if len(sentiments) > 3 else recent_polarity
            trend = 'improving' if recent_polarity > earlier_polarity + 0.1 else 'declining' if recent_polarity < earlier_polarity - 0.1 else 'stable'
        else:
            trend = 'stable'
        
        # Calculate risk level
        risk_levels = [s['risk_level'] for s in sentiments]
        high_risk_count = sum(1 for level in risk_levels if level == 'high')
        medium_risk_count = sum(1 for level in risk_levels if level == 'medium')
        
        if high_risk_count > 0:
            overall_risk = 'high'
        elif medium_risk_count > len(risk_levels) / 2:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        return {
            'overall_sentiment': 'positive' if avg_polarity > 0.1 else 'negative' if avg_polarity < -0.1 else 'neutral',
            'avg_polarity': avg_polarity,
            'avg_subjectivity': avg_subjectivity,
            'trend': trend,
            'risk_level': overall_risk,
            'message_count': len(sentiments),
            'emotions_timeline': emotions_over_time
        }
    
    def detect_mental_health_keywords(self, text: str) -> Dict[str, Any]:
        """Detect mental health related keywords and phrases"""
        # Mental health keywords by category
        depression_keywords = [
            'depressed', 'depression', 'sad', 'hopeless', 'worthless', 'empty',
            'guilty', 'shame', 'suicidal', 'death', 'die', 'kill myself'
        ]
        
        anxiety_keywords = [
            'anxious', 'anxiety', 'worried', 'worry', 'panic', 'nervous',
            'stressed', 'stress', 'overwhelmed', 'fear', 'afraid', 'scared'
        ]
        
        bipolar_keywords = [
            'manic', 'mania', 'high', 'euphoric', 'energetic', 'irritable',
            'mood swings', 'bipolar', 'cycling'
        ]
        
        ptsd_keywords = [
            'trauma', 'flashback', 'nightmare', 'triggered', 'ptsd', 'post traumatic',
            'memories', 'avoiding', 'hypervigilant'
        ]
        
        eating_disorder_keywords = [
            'anorexia', 'bulimia', 'binge', 'purge', 'body image', 'weight',
            'eating disorder', 'food', 'diet', 'starving'
        ]
        
        substance_abuse_keywords = [
            'alcohol', 'drugs', 'addiction', 'substance', 'drinking', 'smoking',
            'overdose', 'withdrawal', 'rehab'
        ]
        
        categories = {
            'depression': depression_keywords,
            'anxiety': anxiety_keywords,
            'bipolar': bipolar_keywords,
            'ptsd': ptsd_keywords,
            'eating_disorder': eating_disorder_keywords,
            'substance_abuse': substance_abuse_keywords
        }
        
        text_lower = text.lower()
        detected_categories = {}
        
        for category, keywords in categories.items():
            found_keywords = [kw for kw in keywords if kw in text_lower]
            if found_keywords:
                detected_categories[category] = {
                    'keywords': found_keywords,
                    'count': len(found_keywords),
                    'confidence': min(len(found_keywords) / len(keywords), 1.0)
                }
        
        return {
            'detected_categories': detected_categories,
            'total_keywords': sum(len(cat['keywords']) for cat in detected_categories.values()),
            'has_mental_health_content': len(detected_categories) > 0
        }
    
    def _analyze_advanced_sentiment(self, text: str) -> Dict[str, Any]:
        """Advanced sentiment analysis using HuggingFace models"""
        if not self.sentiment_pipeline:
            return {'label': 'neutral', 'score': 0.5}
        
        try:
            results = self.sentiment_pipeline(text)
            if results and len(results) > 0:
                # Get the highest scoring sentiment
                best_result = max(results[0], key=lambda x: x['score'])
                return {
                    'label': best_result['label'],
                    'score': best_result['score'],
                    'all_scores': results[0]
                }
        except Exception as e:
            print(f"Error in advanced sentiment analysis: {e}")
        
        return {'label': 'neutral', 'score': 0.5}
    
    def _analyze_emotions(self, text: str) -> Dict[str, Any]:
        """Analyze emotions in text"""
        if not self.emotion_pipeline:
            return {'primary_emotion': 'neutral', 'confidence': 0.5}
        
        try:
            results = self.emotion_pipeline(text)
            if results and len(results) > 0:
                # Get the highest scoring emotion
                best_result = max(results[0], key=lambda x: x['score'])
                return {
                    'primary_emotion': best_result['label'],
                    'confidence': best_result['score'],
                    'all_emotions': results[0]
                }
        except Exception as e:
            print(f"Error in emotion analysis: {e}")
        
        return {'primary_emotion': 'neutral', 'confidence': 0.5}
    
    def _analyze_mental_health_indicators(self, text: str) -> Dict[str, Any]:
        """Analyze specific mental health indicators"""
        indicators = {
            'crisis_indicators': 0,
            'support_seeking': 0,
            'coping_mechanisms': 0,
            'social_indicators': 0,
            'physical_symptoms': 0
        }
        
        text_lower = text.lower()
        
        # Crisis indicators
        crisis_phrases = [
            'kill myself', 'end it all', 'not worth living', 'better off dead',
            'hurt myself', 'suicide', 'overdose', 'jump off', 'hang myself'
        ]
        indicators['crisis_indicators'] = sum(1 for phrase in crisis_phrases if phrase in text_lower)
        
        # Support seeking
        support_phrases = [
            'need help', 'can\'t cope', 'don\'t know what to do', 'feeling lost',
            'need support', 'reaching out', 'cry for help'
        ]
        indicators['support_seeking'] = sum(1 for phrase in support_phrases if phrase in text_lower)
        
        # Coping mechanisms
        coping_phrases = [
            'meditation', 'breathing', 'exercise', 'therapy', 'counseling',
            'talking to someone', 'journaling', 'mindfulness'
        ]
        indicators['coping_mechanisms'] = sum(1 for phrase in coping_phrases if phrase in text_lower)
        
        # Social indicators
        social_phrases = [
            'lonely', 'isolated', 'alone', 'no friends', 'social anxiety',
            'avoiding people', 'withdrawn'
        ]
        indicators['social_indicators'] = sum(1 for phrase in social_phrases if phrase in text_lower)
        
        # Physical symptoms
        physical_phrases = [
            'headache', 'stomach ache', 'tired', 'exhausted', 'sleep problems',
            'appetite', 'weight loss', 'weight gain', 'pain'
        ]
        indicators['physical_symptoms'] = sum(1 for phrase in physical_phrases if phrase in text_lower)
        
        return indicators
    
    def _assess_risk_level(self, text: str, polarity: float, emotions: Dict, indicators: Dict) -> str:
        """Assess overall risk level based on multiple factors"""
        risk_score = 0
        
        # Crisis indicators (highest weight)
        if indicators['crisis_indicators'] > 0:
            risk_score += 50
        
        # Support seeking (medium weight)
        if indicators['support_seeking'] > 0:
            risk_score += 20
        
        # Negative sentiment
        if polarity < -0.3:
            risk_score += 15
        elif polarity < -0.1:
            risk_score += 10
        
        # Negative emotions
        if emotions.get('primary_emotion') in ['sadness', 'anger', 'fear']:
            risk_score += 10
        
        # Social isolation
        if indicators['social_indicators'] > 2:
            risk_score += 15
        
        # Physical symptoms
        if indicators['physical_symptoms'] > 2:
            risk_score += 10
        
        # Determine risk level
        if risk_score >= 50:
            return 'high'
        elif risk_score >= 25:
            return 'medium'
        else:
            return 'low'
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text using spaCy"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            phrases = []
            
            # Extract noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) > 1:  # Multi-word phrases
                    phrases.append(chunk.text)
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT']:
                    phrases.append(ent.text)
            
            return list(set(phrases))  # Remove duplicates
        except Exception as e:
            print(f"Error extracting key phrases: {e}")
            return []
    
    def get_sentiment_summary(self, text: str) -> str:
        """Get a human-readable sentiment summary"""
        analysis = self.analyze_sentiment(text)
        
        sentiment = analysis['sentiment_label']
        confidence = analysis['confidence']
        emotions = analysis['emotions']
        risk = analysis['risk_level']
        
        summary_parts = []
        
        # Basic sentiment
        if confidence > 0.7:
            summary_parts.append(f"The text shows {sentiment} sentiment (high confidence)")
        else:
            summary_parts.append(f"The text shows {sentiment} sentiment (moderate confidence)")
        
        # Emotions
        if emotions.get('confidence', 0) > 0.6:
            summary_parts.append(f"Primary emotion detected: {emotions['primary_emotion']}")
        
        # Risk level
        if risk == 'high':
            summary_parts.append("⚠️ HIGH RISK: Immediate attention may be needed")
        elif risk == 'medium':
            summary_parts.append("⚠️ MEDIUM RISK: Monitoring recommended")
        
        return ". ".join(summary_parts)