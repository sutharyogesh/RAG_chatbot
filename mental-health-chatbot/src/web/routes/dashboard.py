"""
Dashboard Routes - User dashboard and analytics
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.db.models import User, MoodEntry, Assessment, Recommendation, db
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.utils
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@dashboard_bp.route('/api/mood-data')
@login_required
def get_mood_data():
    """Get mood tracking data for charts"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    # Get mood entries for the period
    mood_entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= start_date
    ).order_by(MoodEntry.created_at).all()
    
    # Prepare data for charts
    dates = [entry.created_at.strftime('%Y-%m-%d') for entry in mood_entries]
    mood_scores = [entry.mood_score for entry in mood_entries]
    stress_levels = [entry.stress_level for entry in mood_entries if entry.stress_level]
    energy_levels = [entry.energy_level for entry in mood_entries if entry.energy_level]
    
    # Create mood trend chart
    mood_chart = go.Figure()
    mood_chart.add_trace(go.Scatter(
        x=dates,
        y=mood_scores,
        mode='lines+markers',
        name='Mood Score',
        line=dict(color='#3498db', width=2),
        marker=dict(size=6)
    ))
    
    mood_chart.update_layout(
        title='Mood Trend Over Time',
        xaxis_title='Date',
        yaxis_title='Mood Score (1-10)',
        yaxis=dict(range=[1, 10]),
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Create stress level chart
    stress_chart = go.Figure()
    if stress_levels:
        stress_chart.add_trace(go.Scatter(
            x=dates[:len(stress_levels)],
            y=stress_levels,
            mode='lines+markers',
            name='Stress Level',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=6)
        ))
    
    stress_chart.update_layout(
        title='Stress Level Over Time',
        xaxis_title='Date',
        yaxis_title='Stress Level (1-10)',
        yaxis=dict(range=[1, 10]),
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Create energy level chart
    energy_chart = go.Figure()
    if energy_levels:
        energy_chart.add_trace(go.Scatter(
            x=dates[:len(energy_levels)],
            y=energy_levels,
            mode='lines+markers',
            name='Energy Level',
            line=dict(color='#2ecc71', width=2),
            marker=dict(size=6)
        ))
    
    energy_chart.update_layout(
        title='Energy Level Over Time',
        xaxis_title='Date',
        yaxis_title='Energy Level (1-10)',
        yaxis=dict(range=[1, 10]),
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Calculate statistics
    avg_mood = sum(mood_scores) / len(mood_scores) if mood_scores else 0
    avg_stress = sum(stress_levels) / len(stress_levels) if stress_levels else 0
    avg_energy = sum(energy_levels) / len(energy_levels) if energy_levels else 0
    
    # Mood distribution
    mood_distribution = {}
    for score in mood_scores:
        mood_distribution[score] = mood_distribution.get(score, 0) + 1
    
    return jsonify({
        'mood_chart': json.dumps(mood_chart, cls=plotly.utils.PlotlyJSONEncoder),
        'stress_chart': json.dumps(stress_chart, cls=plotly.utils.PlotlyJSONEncoder),
        'energy_chart': json.dumps(energy_chart, cls=plotly.utils.PlotlyJSONEncoder),
        'statistics': {
            'avg_mood': round(avg_mood, 2),
            'avg_stress': round(avg_stress, 2),
            'avg_energy': round(avg_energy, 2),
            'total_entries': len(mood_entries),
            'mood_distribution': mood_distribution
        }
    })

@dashboard_bp.route('/api/assessment-history')
@login_required
def get_assessment_history():
    """Get assessment history"""
    assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.created_at.desc()).all()
    
    assessment_data = []
    for assessment in assessments:
        assessment_data.append({
            'id': assessment.id,
            'type': assessment.assessment_type,
            'total_score': assessment.total_score,
            'severity_level': assessment.severity_level,
            'created_at': assessment.created_at.isoformat(),
            'responses': assessment.get_responses()
        })
    
    return jsonify({
        'assessments': assessment_data,
        'total_count': len(assessment_data)
    })

@dashboard_bp.route('/api/recommendations')
@login_required
def get_recommendations():
    """Get user recommendations"""
    recommendations = Recommendation.query.filter_by(user_id=current_user.id).order_by(Recommendation.created_at.desc()).all()
    
    rec_data = []
    for rec in recommendations:
        rec_data.append({
            'id': rec.id,
            'type': rec.recommendation_type,
            'title': rec.title,
            'description': rec.description,
            'priority': rec.priority,
            'is_completed': rec.is_completed,
            'completed_at': rec.completed_at.isoformat() if rec.completed_at else None,
            'created_at': rec.created_at.isoformat()
        })
    
    return jsonify({
        'recommendations': rec_data,
        'total_count': len(rec_data)
    })

@dashboard_bp.route('/api/mood-entry', methods=['POST'])
@login_required
def add_mood_entry():
    """Add a new mood entry"""
    data = request.get_json()
    
    try:
        mood_entry = MoodEntry(
            user_id=current_user.id,
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

@dashboard_bp.route('/api/mood-entry/<int:entry_id>', methods=['PUT'])
@login_required
def update_mood_entry(entry_id):
    """Update a mood entry"""
    mood_entry = MoodEntry.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if not mood_entry:
        return jsonify({'error': 'Mood entry not found'}), 404
    
    data = request.get_json()
    
    try:
        mood_entry.mood_score = data.get('mood_score', mood_entry.mood_score)
        mood_entry.mood_label = data.get('mood_label', mood_entry.mood_label)
        mood_entry.notes = data.get('notes', mood_entry.notes)
        mood_entry.energy_level = data.get('energy_level', mood_entry.energy_level)
        mood_entry.sleep_hours = data.get('sleep_hours', mood_entry.sleep_hours)
        mood_entry.stress_level = data.get('stress_level', mood_entry.stress_level)
        
        if 'activities' in data:
            mood_entry.set_activities(data['activities'])
        
        db.session.commit()
        
        return jsonify({'message': 'Mood entry updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update mood entry'}), 500

@dashboard_bp.route('/api/mood-entry/<int:entry_id>', methods=['DELETE'])
@login_required
def delete_mood_entry(entry_id):
    """Delete a mood entry"""
    mood_entry = MoodEntry.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if not mood_entry:
        return jsonify({'error': 'Mood entry not found'}), 404
    
    try:
        db.session.delete(mood_entry)
        db.session.commit()
        
        return jsonify({'message': 'Mood entry deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete mood entry'}), 500

@dashboard_bp.route('/api/recommendation/<int:rec_id>/complete', methods=['POST'])
@login_required
def complete_recommendation(rec_id):
    """Mark a recommendation as completed"""
    recommendation = Recommendation.query.filter_by(id=rec_id, user_id=current_user.id).first()
    if not recommendation:
        return jsonify({'error': 'Recommendation not found'}), 404
    
    data = request.get_json()
    feedback = data.get('feedback', '')
    
    try:
        recommendation.mark_completed(feedback)
        db.session.commit()
        
        return jsonify({'message': 'Recommendation marked as completed'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to complete recommendation'}), 500

@dashboard_bp.route('/api/export-data')
@login_required
def export_user_data():
    """Export user data as CSV"""
    format_type = request.args.get('format', 'csv')
    
    if format_type == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Export mood entries
        writer.writerow(['Data Type', 'Date', 'Mood Score', 'Mood Label', 'Stress Level', 'Energy Level', 'Sleep Hours', 'Notes'])
        
        mood_entries = MoodEntry.query.filter_by(user_id=current_user.id).order_by(MoodEntry.created_at).all()
        for entry in mood_entries:
            writer.writerow([
                'Mood Entry',
                entry.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                entry.mood_score,
                entry.mood_label,
                entry.stress_level or '',
                entry.energy_level or '',
                entry.sleep_hours or '',
                entry.notes or ''
            ])
        
        # Export assessments
        assessments = Assessment.query.filter_by(user_id=current_user.id).order_by(Assessment.created_at).all()
        for assessment in assessments:
            writer.writerow([
                'Assessment',
                assessment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                assessment.total_score,
                assessment.severity_level,
                '',
                '',
                '',
                f"{assessment.assessment_type} - {assessment.interpretation}"
            ])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=mental_health_data_{current_user.username}.csv'}
        )
    
    return jsonify({'error': 'Invalid format'}), 400

@dashboard_bp.route('/api/insights')
@login_required
def get_insights():
    """Get personalized insights based on user data"""
    # Get recent mood data
    recent_mood_entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= datetime.now() - timedelta(days=30)
    ).all()
    
    # Get recent assessments
    recent_assessments = Assessment.query.filter(
        Assessment.user_id == current_user.id,
        Assessment.created_at >= datetime.now() - timedelta(days=30)
    ).all()
    
    insights = []
    
    # Mood trend insights
    if recent_mood_entries:
        mood_scores = [entry.mood_score for entry in recent_mood_entries]
        avg_mood = sum(mood_scores) / len(mood_scores)
        
        if avg_mood >= 7:
            insights.append({
                'type': 'positive',
                'title': 'Great Mood Trend!',
                'message': f'Your average mood over the last 30 days is {avg_mood:.1f}/10. Keep up the great work!',
                'recommendation': 'Continue your current practices and consider sharing what\'s working well.'
            })
        elif avg_mood <= 4:
            insights.append({
                'type': 'concern',
                'title': 'Mood Support Needed',
                'message': f'Your average mood over the last 30 days is {avg_mood:.1f}/10. Consider reaching out for support.',
                'recommendation': 'Consider talking to a mental health professional or trusted friend.'
            })
    
    # Assessment insights
    if recent_assessments:
        latest_assessment = recent_assessments[-1]
        if latest_assessment.severity_level in ['moderate', 'severe']:
            insights.append({
                'type': 'important',
                'title': 'Assessment Results',
                'message': f'Your recent {latest_assessment.assessment_type} assessment shows {latest_assessment.severity_level} levels.',
                'recommendation': 'Consider professional support and follow the recommendations provided.'
            })
    
    # Activity insights
    all_activities = []
    for entry in recent_mood_entries:
        all_activities.extend(entry.get_activities())
    
    if all_activities:
        activity_counts = {}
        for activity in all_activities:
            activity_counts[activity] = activity_counts.get(activity, 0) + 1
        
        most_common_activity = max(activity_counts, key=activity_counts.get)
        insights.append({
            'type': 'info',
            'title': 'Activity Pattern',
            'message': f'Your most common activity recently is "{most_common_activity}".',
            'recommendation': 'Consider trying new activities to add variety to your routine.'
        })
    
    return jsonify({
        'insights': insights,
        'data_period': '30 days',
        'total_entries': len(recent_mood_entries),
        'total_assessments': len(recent_assessments)
    })