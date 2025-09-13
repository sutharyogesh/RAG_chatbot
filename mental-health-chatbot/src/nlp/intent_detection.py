"""
Intent Detection Module - Identifies user intentions and conversation goals
"""

import re
from typing import Dict, List, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib
import os

class IntentDetector:
    """Detects user intentions in mental health conversations"""
    
    def __init__(self):
        """Initialize intent detector"""
        self.intent_patterns = {
            'greeting': [
                r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
                r'\b(how are you|how do you do)\b',
                r'\b(nice to meet you|pleased to meet you)\b'
            ],
            'farewell': [
                r'\b(bye|goodbye|see you|take care|farewell)\b',
                r'\b(thanks|thank you|thank you very much)\b',
                r'\b(that\'s all|that\'s it|nothing else)\b'
            ],
            'crisis': [
                r'\b(kill myself|suicide|end it all|not worth living)\b',
                r'\b(hurt myself|self harm|cut myself|overdose)\b',
                r'\b(jump off|hang myself|die|death|dead)\b',
                r'\b(better off dead|want to die|end my life)\b'
            ],
            'depression': [
                r'\b(depressed|depression|sad|hopeless|worthless)\b',
                r'\b(empty|guilty|shame|down|low)\b',
                r'\b(can\'t get out of bed|no energy|tired)\b',
                r'\b(lost interest|no pleasure|nothing matters)\b'
            ],
            'anxiety': [
                r'\b(anxious|anxiety|worried|worry|panic)\b',
                r'\b(nervous|stressed|stress|overwhelmed)\b',
                r'\b(fear|afraid|scared|frightened)\b',
                r'\b(racing thoughts|can\'t stop worrying)\b'
            ],
            'sleep_issues': [
                r'\b(can\'t sleep|insomnia|sleep problems)\b',
                r'\b(tossing and turning|wake up|nightmares)\b',
                r'\b(tired|exhausted|sleepy|drowsy)\b'
            ],
            'relationship_issues': [
                r'\b(relationship|partner|boyfriend|girlfriend|spouse)\b',
                r'\b(family|parents|siblings|children)\b',
                r'\b(friends|social|lonely|isolated)\b',
                r'\b(conflict|argument|fight|breakup)\b'
            ],
            'work_stress': [
                r'\b(work|job|career|boss|colleague)\b',
                r'\b(deadline|pressure|overwhelmed|burnout)\b',
                r'\b(workplace|office|meeting|project)\b'
            ],
            'assessment_request': [
                r'\b(assessment|test|evaluation|check)\b',
                r'\b(how am i doing|am i depressed|am i anxious)\b',
                r'\b(mental health check|screening)\b'
            ],
            'recommendation_request': [
                r'\b(help|advice|suggestion|recommendation)\b',
                r'\b(what should i do|how to cope|strategies)\b',
                r'\b(tips|techniques|exercises)\b'
            ],
            'mood_tracking': [
                r'\b(mood|feeling|emotion|track)\b',
                r'\b(how am i feeling|mood today|emotional state)\b',
                r'\b(log|record|journal)\b'
            ],
            'professional_help': [
                r'\b(therapist|psychologist|psychiatrist|counselor)\b',
                r'\b(professional help|therapy|counseling)\b',
                r'\b(mental health professional|doctor)\b'
            ],
            'medication': [
                r'\b(medication|medicine|pills|prescription)\b',
                r'\b(antidepressant|anxiety medication|meds)\b',
                r'\b(side effects|dosage|taking medication)\b'
            ],
            'coping_strategies': [
                r'\b(coping|deal with|handle|manage)\b',
                r'\b(breathing|meditation|mindfulness)\b',
                r'\b(exercise|walk|run|yoga)\b'
            ],
            'general_question': [
                r'\b(what|how|why|when|where|who)\b',
                r'\b(can you|could you|would you)\b',
                r'\b(explain|tell me|describe)\b'
            ]
        }
        
        # Initialize ML model for intent classification
        self.ml_model = None
        self.vectorizer = None
        self.model_path = 'data/models/intent_classifier.pkl'
        self._load_or_train_model()
    
    def detect_intent(self, text: str) -> Dict[str, Any]:
        """Detect user intent from text"""
        text_lower = text.lower().strip()
        
        # Pattern-based detection
        pattern_results = self._detect_by_patterns(text_lower)
        
        # ML-based detection
        ml_results = self._detect_by_ml(text_lower)
        
        # Combine results
        combined_intent = self._combine_results(pattern_results, ml_results)
        
        # Additional context analysis
        context_info = self._analyze_context(text_lower)
        
        return {
            'primary_intent': combined_intent['primary_intent'],
            'confidence': combined_intent['confidence'],
            'all_intents': combined_intent['all_intents'],
            'pattern_matches': pattern_results,
            'ml_predictions': ml_results,
            'context_info': context_info,
            'urgency_level': self._assess_urgency(text_lower, combined_intent['primary_intent'])
        }
    
    def _detect_by_patterns(self, text: str) -> Dict[str, float]:
        """Detect intent using regex patterns"""
        pattern_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = []
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 1
                    matches.append(pattern)
            
            if score > 0:
                # Normalize score by number of patterns
                pattern_scores[intent] = min(score / len(patterns), 1.0)
        
        return pattern_scores
    
    def _detect_by_ml(self, text: str) -> Dict[str, float]:
        """Detect intent using ML model"""
        if not self.ml_model:
            return {}
        
        try:
            # Predict probabilities for all classes
            probabilities = self.ml_model.predict_proba([text])[0]
            class_names = self.ml_model.classes_
            
            ml_scores = {}
            for i, class_name in enumerate(class_names):
                ml_scores[class_name] = float(probabilities[i])
            
            return ml_scores
        except Exception as e:
            print(f"Error in ML intent detection: {e}")
            return {}
    
    def _combine_results(self, pattern_results: Dict, ml_results: Dict) -> Dict[str, Any]:
        """Combine pattern and ML results"""
        all_intents = {}
        
        # Combine scores from both methods
        for intent in set(list(pattern_results.keys()) + list(ml_results.keys())):
            pattern_score = pattern_results.get(intent, 0)
            ml_score = ml_results.get(intent, 0)
            
            # Weighted combination (patterns get higher weight for exact matches)
            combined_score = (pattern_score * 0.7) + (ml_score * 0.3)
            all_intents[intent] = combined_score
        
        # Find primary intent
        if all_intents:
            primary_intent = max(all_intents, key=all_intents.get)
            confidence = all_intents[primary_intent]
        else:
            primary_intent = 'general_question'
            confidence = 0.1
        
        return {
            'primary_intent': primary_intent,
            'confidence': confidence,
            'all_intents': all_intents
        }
    
    def _analyze_context(self, text: str) -> Dict[str, Any]:
        """Analyze additional context information"""
        context = {
            'has_question': '?' in text,
            'has_exclamation': '!' in text,
            'text_length': len(text.split()),
            'has_negation': any(word in text for word in ['not', 'no', 'never', 'can\'t', 'won\'t', 'don\'t']),
            'has_intensifiers': any(word in text for word in ['very', 'really', 'extremely', 'so', 'too']),
            'has_time_references': any(word in text for word in ['today', 'yesterday', 'tomorrow', 'now', 'recently', 'always', 'never']),
            'has_uncertainty': any(word in text for word in ['maybe', 'perhaps', 'might', 'could', 'possibly', 'not sure'])
        }
        
        return context
    
    def _assess_urgency(self, text: str, primary_intent: str) -> str:
        """Assess urgency level of the message"""
        # High urgency indicators
        high_urgency_words = [
            'urgent', 'emergency', 'crisis', 'help', 'now', 'immediately',
            'can\'t take it', 'breaking down', 'falling apart'
        ]
        
        # Crisis intent is always high urgency
        if primary_intent == 'crisis':
            return 'high'
        
        # Check for high urgency words
        if any(word in text for word in high_urgency_words):
            return 'high'
        
        # Medium urgency for certain intents
        medium_urgency_intents = ['depression', 'anxiety', 'professional_help']
        if primary_intent in medium_urgency_intents:
            return 'medium'
        
        return 'low'
    
    def _load_or_train_model(self):
        """Load existing ML model or train a new one"""
        if os.path.exists(self.model_path):
            try:
                model_data = joblib.load(self.model_path)
                self.ml_model = model_data['model']
                self.vectorizer = model_data['vectorizer']
                print("Loaded existing intent classification model")
            except Exception as e:
                print(f"Error loading model: {e}")
                self._train_new_model()
        else:
            self._train_new_model()
    
    def _train_new_model(self):
        """Train a new intent classification model"""
        # Sample training data (in a real application, this would be much larger)
        training_data = [
            ("hi there how are you", "greeting"),
            ("hello good morning", "greeting"),
            ("bye see you later", "farewell"),
            ("thank you goodbye", "farewell"),
            ("i want to kill myself", "crisis"),
            ("i feel like ending it all", "crisis"),
            ("i'm so depressed", "depression"),
            ("feeling hopeless and sad", "depression"),
            ("i'm really anxious", "anxiety"),
            ("worried about everything", "anxiety"),
            ("can't sleep at night", "sleep_issues"),
            ("having trouble sleeping", "sleep_issues"),
            ("problems with my partner", "relationship_issues"),
            ("fighting with family", "relationship_issues"),
            ("stressed at work", "work_stress"),
            ("overwhelmed with work", "work_stress"),
            ("can i take an assessment", "assessment_request"),
            ("how am i doing mentally", "assessment_request"),
            ("what should i do", "recommendation_request"),
            ("need some advice", "recommendation_request"),
            ("how is my mood today", "mood_tracking"),
            ("track my emotions", "mood_tracking"),
            ("need to see a therapist", "professional_help"),
            ("should i get counseling", "professional_help"),
            ("taking medication", "medication"),
            ("side effects of my meds", "medication"),
            ("how to cope with stress", "coping_strategies"),
            ("breathing exercises", "coping_strategies"),
            ("what is depression", "general_question"),
            ("how does therapy work", "general_question")
        ]
        
        try:
            texts, labels = zip(*training_data)
            
            # Create pipeline
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            self.ml_model = MultinomialNB()
            
            # Train model
            X = self.vectorizer.fit_transform(texts)
            self.ml_model.fit(X, labels)
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump({
                'model': self.ml_model,
                'vectorizer': self.vectorizer
            }, self.model_path)
            
            print("Trained new intent classification model")
        except Exception as e:
            print(f"Error training model: {e}")
            self.ml_model = None
            self.vectorizer = None
    
    def get_intent_response_template(self, intent: str) -> str:
        """Get response template for detected intent"""
        templates = {
            'greeting': "Hello! I'm here to support you. How are you feeling today?",
            'farewell': "Take care! Remember, I'm always here if you need to talk.",
            'crisis': "I'm concerned about what you're saying. Please reach out to a crisis hotline immediately. National Suicide Prevention Lifeline: 988",
            'depression': "I hear that you're feeling depressed. That must be really difficult. Would you like to talk about what's been going on?",
            'anxiety': "It sounds like you're experiencing anxiety. That can be overwhelming. What's making you feel anxious right now?",
            'sleep_issues': "Sleep problems can really affect your mental health. What's been keeping you up at night?",
            'relationship_issues': "Relationship problems can be stressful. Would you like to talk about what's happening?",
            'work_stress': "Work stress can be overwhelming. What's been particularly challenging at work lately?",
            'assessment_request': "I'd be happy to help you with an assessment. We have PHQ-9 for depression and GAD-7 for anxiety. Which would you like to take?",
            'recommendation_request': "I'd be glad to suggest some strategies that might help. What specific area would you like support with?",
            'mood_tracking': "Tracking your mood is a great way to understand your patterns. How are you feeling right now on a scale of 1-10?",
            'professional_help': "Seeking professional help is a positive step. I can help you understand what to expect from therapy or counseling.",
            'medication': "Medication can be an important part of mental health treatment. What questions do you have about your medication?",
            'coping_strategies': "There are many effective coping strategies. What situations are you looking to manage better?",
            'general_question': "I'm here to help with your questions. What would you like to know more about?"
        }
        
        return templates.get(intent, "I'm here to listen and support you. How can I help today?")
    
    def should_escalate_to_human(self, intent_result: Dict[str, Any]) -> bool:
        """Determine if conversation should be escalated to human support"""
        primary_intent = intent_result.get('primary_intent')
        confidence = intent_result.get('confidence', 0)
        urgency = intent_result.get('urgency_level', 'low')
        
        # Always escalate crisis situations
        if primary_intent == 'crisis':
            return True
        
        # Escalate high urgency with high confidence
        if urgency == 'high' and confidence > 0.7:
            return True
        
        # Escalate if user explicitly requests professional help
        if primary_intent == 'professional_help' and confidence > 0.8:
            return True
        
        return False