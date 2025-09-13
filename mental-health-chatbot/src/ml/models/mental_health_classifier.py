"""
Mental Health Classifier - ML models for mental health status classification
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

class MentalHealthClassifier:
    """Multi-class mental health status classifier"""
    
    def __init__(self, model_type: str = 'random_forest'):
        """Initialize classifier"""
        self.model_type = model_type
        self.model = None
        self.vectorizer = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.model_path = 'data/models/mental_health_classifier.pkl'
        self.vectorizer_path = 'data/models/mental_health_vectorizer.pkl'
        self.scaler_path = 'data/models/mental_health_scaler.pkl'
        self.label_encoder_path = 'data/models/mental_health_label_encoder.pkl'
        
        # Load existing model or train new one
        self._load_or_train_model()
    
    def predict_mental_health_status(self, 
                                   text_features: List[str],
                                   numerical_features: Dict[str, float] = None) -> Dict[str, Any]:
        """Predict mental health status from features"""
        if not self.model or not self.vectorizer:
            return self._get_default_prediction()
        
        try:
            # Process text features
            text_vector = self.vectorizer.transform([' '.join(text_features)])
            
            # Process numerical features
            if numerical_features and self.scaler:
                numerical_array = np.array([[
                    numerical_features.get('mood_score', 5),
                    numerical_features.get('stress_level', 5),
                    numerical_features.get('sleep_hours', 8),
                    numerical_features.get('energy_level', 5),
                    numerical_features.get('social_activity', 5),
                    numerical_features.get('physical_activity', 5)
                ]])
                numerical_scaled = self.scaler.transform(numerical_array)
            else:
                numerical_scaled = np.zeros((1, 6))
            
            # Combine features
            combined_features = np.hstack([text_vector.toarray(), numerical_scaled])
            
            # Make prediction
            prediction = self.model.predict(combined_features)[0]
            probabilities = self.model.predict_proba(combined_features)[0]
            
            # Get class labels
            if self.label_encoder:
                predicted_class = self.label_encoder.inverse_transform([prediction])[0]
                class_probabilities = dict(zip(
                    self.label_encoder.classes_,
                    probabilities
                ))
            else:
                predicted_class = f"class_{prediction}"
                class_probabilities = {f"class_{i}": prob for i, prob in enumerate(probabilities)}
            
            return {
                'predicted_class': predicted_class,
                'confidence': max(probabilities),
                'class_probabilities': class_probabilities,
                'risk_level': self._assess_risk_level(predicted_class, max(probabilities)),
                'recommendations': self._get_class_recommendations(predicted_class)
            }
            
        except Exception as e:
            print(f"Error in prediction: {e}")
            return self._get_default_prediction()
    
    def predict_depression_severity(self, phq9_scores: List[int]) -> Dict[str, Any]:
        """Predict depression severity from PHQ-9 scores"""
        total_score = sum(phq9_scores)
        
        if total_score <= 4:
            severity = 'minimal'
            risk_level = 'low'
        elif total_score <= 9:
            severity = 'mild'
            risk_level = 'low'
        elif total_score <= 14:
            severity = 'moderate'
            risk_level = 'medium'
        elif total_score <= 19:
            severity = 'moderately_severe'
            risk_level = 'high'
        else:
            severity = 'severe'
            risk_level = 'high'
        
        return {
            'total_score': total_score,
            'severity': severity,
            'risk_level': risk_level,
            'max_score': 27,
            'interpretation': f'PHQ-9 score of {total_score} indicates {severity} depression',
            'recommendations': self._get_depression_recommendations(severity)
        }
    
    def predict_anxiety_severity(self, gad7_scores: List[int]) -> Dict[str, Any]:
        """Predict anxiety severity from GAD-7 scores"""
        total_score = sum(gad7_scores)
        
        if total_score <= 4:
            severity = 'minimal'
            risk_level = 'low'
        elif total_score <= 9:
            severity = 'mild'
            risk_level = 'low'
        elif total_score <= 14:
            severity = 'moderate'
            risk_level = 'medium'
        else:
            severity = 'severe'
            risk_level = 'high'
        
        return {
            'total_score': total_score,
            'severity': severity,
            'risk_level': risk_level,
            'max_score': 21,
            'interpretation': f'GAD-7 score of {total_score} indicates {severity} anxiety',
            'recommendations': self._get_anxiety_recommendations(severity)
        }
    
    def predict_stress_level(self, stress_indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Predict stress level from various indicators"""
        # Weighted scoring system
        stress_score = 0
        
        # Work stress (0-3)
        work_stress = stress_indicators.get('work_stress', 0)
        stress_score += work_stress * 0.3
        
        # Relationship stress (0-3)
        relationship_stress = stress_indicators.get('relationship_stress', 0)
        stress_score += relationship_stress * 0.25
        
        # Financial stress (0-3)
        financial_stress = stress_indicators.get('financial_stress', 0)
        stress_score += financial_stress * 0.2
        
        # Health stress (0-3)
        health_stress = stress_indicators.get('health_stress', 0)
        stress_score += health_stress * 0.15
        
        # Sleep quality (0-3, inverted)
        sleep_quality = stress_indicators.get('sleep_quality', 2)
        stress_score += (3 - sleep_quality) * 0.1
        
        # Normalize to 0-10 scale
        stress_level = min(10, max(0, stress_score * 10 / 3))
        
        if stress_level <= 3:
            level = 'low'
        elif stress_level <= 6:
            level = 'moderate'
        else:
            level = 'high'
        
        return {
            'stress_level': stress_level,
            'level': level,
            'score_breakdown': {
                'work_stress': work_stress,
                'relationship_stress': relationship_stress,
                'financial_stress': financial_stress,
                'health_stress': health_stress,
                'sleep_impact': 3 - sleep_quality
            },
            'recommendations': self._get_stress_recommendations(level)
        }
    
    def _load_or_train_model(self):
        """Load existing model or train a new one"""
        if self._load_existing_model():
            print("Loaded existing mental health classifier model")
        else:
            print("Training new mental health classifier model...")
            self._train_new_model()
    
    def _load_existing_model(self) -> bool:
        """Load existing trained model"""
        try:
            if (os.path.exists(self.model_path) and 
                os.path.exists(self.vectorizer_path) and
                os.path.exists(self.scaler_path) and
                os.path.exists(self.label_encoder_path)):
                
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.scaler = joblib.load(self.scaler_path)
                self.label_encoder = joblib.load(self.label_encoder_path)
                return True
        except Exception as e:
            print(f"Error loading existing model: {e}")
        
        return False
    
    def _train_new_model(self):
        """Train a new mental health classifier model"""
        # Generate synthetic training data
        training_data = self._generate_synthetic_data()
        
        try:
            # Prepare features
            X_text = training_data['text_features']
            X_numerical = training_data['numerical_features']
            y = training_data['labels']
            
            # Vectorize text features
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            X_text_vectorized = self.vectorizer.fit_transform(X_text)
            
            # Scale numerical features
            self.scaler = StandardScaler()
            X_numerical_scaled = self.scaler.fit_transform(X_numerical)
            
            # Combine features
            X_combined = np.hstack([X_text_vectorized.toarray(), X_numerical_scaled])
            
            # Encode labels
            self.label_encoder = LabelEncoder()
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_combined, y_encoded, test_size=0.2, random_state=42
            )
            
            # Train model based on type
            if self.model_type == 'random_forest':
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            elif self.model_type == 'gradient_boosting':
                self.model = GradientBoostingClassifier(random_state=42)
            elif self.model_type == 'logistic_regression':
                self.model = LogisticRegression(random_state=42, max_iter=1000)
            elif self.model_type == 'svm':
                self.model = SVC(probability=True, random_state=42)
            else:
                self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            print(f"Model accuracy: {accuracy:.3f}")
            
            # Save model components
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.vectorizer, self.vectorizer_path)
            joblib.dump(self.scaler, self.scaler_path)
            joblib.dump(self.label_encoder, self.label_encoder_path)
            
            print("Mental health classifier model trained and saved successfully")
            
        except Exception as e:
            print(f"Error training model: {e}")
            self.model = None
            self.vectorizer = None
            self.scaler = None
            self.label_encoder = None
    
    def _generate_synthetic_data(self) -> Dict[str, Any]:
        """Generate synthetic training data for mental health classification"""
        # Mental health categories
        categories = ['healthy', 'mild_depression', 'moderate_depression', 'severe_depression',
                     'mild_anxiety', 'moderate_anxiety', 'severe_anxiety', 'stress', 'bipolar']
        
        # Text features for each category
        text_features_by_category = {
            'healthy': [
                "feeling good today", "happy and content", "life is great", "feeling positive",
                "everything is fine", "good mood", "feeling optimistic", "life is good"
            ],
            'mild_depression': [
                "feeling a bit down", "not my usual self", "feeling blue", "low energy",
                "not motivated", "feeling sad", "down mood", "not feeling great"
            ],
            'moderate_depression': [
                "feeling very depressed", "can't get out of bed", "hopeless", "worthless",
                "no interest in anything", "feeling empty", "very sad", "no motivation"
            ],
            'severe_depression': [
                "want to die", "suicidal thoughts", "can't go on", "end it all",
                "not worth living", "better off dead", "hopeless", "worthless"
            ],
            'mild_anxiety': [
                "feeling anxious", "worried about things", "nervous", "stressed",
                "can't stop worrying", "feeling tense", "anxious thoughts"
            ],
            'moderate_anxiety': [
                "very anxious", "panic attacks", "can't control worry", "overwhelmed",
                "constant worry", "anxiety is bad", "can't relax"
            ],
            'severe_anxiety': [
                "crippling anxiety", "panic all the time", "can't function", "terrified",
                "constant panic", "anxiety is destroying me", "can't cope"
            ],
            'stress': [
                "stressed out", "overwhelmed", "too much pressure", "can't handle it",
                "work stress", "burned out", "need a break", "stressed"
            ],
            'bipolar': [
                "mood swings", "manic episode", "feeling high", "racing thoughts",
                "can't sleep", "too much energy", "mood cycling", "up and down"
            ]
        }
        
        # Generate training data
        text_features = []
        numerical_features = []
        labels = []
        
        for category in categories:
            texts = text_features_by_category[category]
            for _ in range(50):  # 50 samples per category
                # Random text feature
                text_features.append(np.random.choice(texts))
                
                # Random numerical features
                if category == 'healthy':
                    mood_score = np.random.normal(7, 1)
                    stress_level = np.random.normal(3, 1)
                    sleep_hours = np.random.normal(8, 1)
                    energy_level = np.random.normal(7, 1)
                    social_activity = np.random.normal(6, 1)
                    physical_activity = np.random.normal(6, 1)
                elif 'depression' in category:
                    mood_score = np.random.normal(3, 1)
                    stress_level = np.random.normal(6, 1)
                    sleep_hours = np.random.normal(10, 2) if 'severe' in category else np.random.normal(9, 1)
                    energy_level = np.random.normal(3, 1)
                    social_activity = np.random.normal(3, 1)
                    physical_activity = np.random.normal(2, 1)
                elif 'anxiety' in category:
                    mood_score = np.random.normal(4, 1)
                    stress_level = np.random.normal(8, 1) if 'severe' in category else np.random.normal(6, 1)
                    sleep_hours = np.random.normal(6, 1)
                    energy_level = np.random.normal(5, 1)
                    social_activity = np.random.normal(4, 1)
                    physical_activity = np.random.normal(4, 1)
                elif category == 'stress':
                    mood_score = np.random.normal(5, 1)
                    stress_level = np.random.normal(7, 1)
                    sleep_hours = np.random.normal(7, 1)
                    energy_level = np.random.normal(4, 1)
                    social_activity = np.random.normal(5, 1)
                    physical_activity = np.random.normal(5, 1)
                else:  # bipolar
                    mood_score = np.random.normal(6, 2)
                    stress_level = np.random.normal(6, 2)
                    sleep_hours = np.random.normal(6, 2)
                    energy_level = np.random.normal(6, 2)
                    social_activity = np.random.normal(6, 2)
                    physical_activity = np.random.normal(6, 2)
                
                # Clip values to valid ranges
                mood_score = max(1, min(10, mood_score))
                stress_level = max(1, min(10, stress_level))
                sleep_hours = max(3, min(12, sleep_hours))
                energy_level = max(1, min(10, energy_level))
                social_activity = max(1, min(10, social_activity))
                physical_activity = max(1, min(10, physical_activity))
                
                numerical_features.append([
                    mood_score, stress_level, sleep_hours, 
                    energy_level, social_activity, physical_activity
                ])
                labels.append(category)
        
        return {
            'text_features': text_features,
            'numerical_features': np.array(numerical_features),
            'labels': labels
        }
    
    def _get_default_prediction(self) -> Dict[str, Any]:
        """Get default prediction when model is not available"""
        return {
            'predicted_class': 'healthy',
            'confidence': 0.5,
            'class_probabilities': {'healthy': 0.5, 'mild_depression': 0.3, 'mild_anxiety': 0.2},
            'risk_level': 'low',
            'recommendations': ['Consider regular mood tracking', 'Maintain healthy lifestyle habits']
        }
    
    def _assess_risk_level(self, predicted_class: str, confidence: float) -> str:
        """Assess risk level based on prediction"""
        high_risk_classes = ['severe_depression', 'severe_anxiety']
        medium_risk_classes = ['moderate_depression', 'moderate_anxiety', 'bipolar']
        
        if predicted_class in high_risk_classes and confidence > 0.7:
            return 'high'
        elif predicted_class in medium_risk_classes and confidence > 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _get_class_recommendations(self, predicted_class: str) -> List[str]:
        """Get recommendations based on predicted class"""
        recommendations = {
            'healthy': [
                'Continue maintaining healthy habits',
                'Regular exercise and good sleep',
                'Stay connected with friends and family'
            ],
            'mild_depression': [
                'Consider talking to a counselor',
                'Try regular exercise',
                'Maintain a consistent sleep schedule',
                'Engage in activities you enjoy'
            ],
            'moderate_depression': [
                'Seek professional help from a therapist',
                'Consider medication evaluation',
                'Join a support group',
                'Practice mindfulness and meditation'
            ],
            'severe_depression': [
                'Seek immediate professional help',
                'Consider crisis intervention',
                'Contact a mental health professional',
                'Reach out to support systems'
            ],
            'mild_anxiety': [
                'Practice deep breathing exercises',
                'Try progressive muscle relaxation',
                'Limit caffeine intake',
                'Maintain regular sleep schedule'
            ],
            'moderate_anxiety': [
                'Consider therapy (CBT recommended)',
                'Practice mindfulness meditation',
                'Regular exercise',
                'Consider anxiety management techniques'
            ],
            'severe_anxiety': [
                'Seek immediate professional help',
                'Consider medication evaluation',
                'Practice grounding techniques',
                'Avoid triggers when possible'
            ],
            'stress': [
                'Practice stress management techniques',
                'Take regular breaks',
                'Prioritize tasks',
                'Consider time management strategies'
            ],
            'bipolar': [
                'Seek professional psychiatric evaluation',
                'Maintain mood tracking',
                'Follow treatment plan consistently',
                'Monitor sleep patterns'
            ]
        }
        
        return recommendations.get(predicted_class, ['Consider professional evaluation'])
    
    def _get_depression_recommendations(self, severity: str) -> List[str]:
        """Get depression-specific recommendations"""
        recommendations = {
            'minimal': ['Continue current practices', 'Monitor mood regularly'],
            'mild': ['Consider counseling', 'Regular exercise', 'Social activities'],
            'moderate': ['Professional therapy recommended', 'Consider medication evaluation'],
            'moderately_severe': ['Immediate professional help', 'Consider medication', 'Crisis support'],
            'severe': ['Emergency professional intervention', 'Crisis hotline contact', 'Immediate support needed']
        }
        return recommendations.get(severity, ['Professional evaluation recommended'])
    
    def _get_anxiety_recommendations(self, severity: str) -> List[str]:
        """Get anxiety-specific recommendations"""
        recommendations = {
            'minimal': ['Continue current practices', 'Monitor anxiety levels'],
            'mild': ['Breathing exercises', 'Mindfulness practice', 'Regular exercise'],
            'moderate': ['Professional therapy (CBT)', 'Anxiety management techniques'],
            'severe': ['Immediate professional help', 'Consider medication evaluation', 'Crisis support']
        }
        return recommendations.get(severity, ['Professional evaluation recommended'])
    
    def _get_stress_recommendations(self, level: str) -> List[str]:
        """Get stress-specific recommendations"""
        recommendations = {
            'low': ['Maintain current stress management', 'Regular check-ins'],
            'moderate': ['Stress management techniques', 'Time management', 'Regular breaks'],
            'high': ['Professional stress counseling', 'Workload evaluation', 'Support system activation']
        }
        return recommendations.get(level, ['Stress management evaluation recommended'])