// Chat Interface JavaScript

class ChatInterface {
    constructor(options = {}) {
        this.sessionId = options.sessionId || null;
        this.anonymous = options.anonymous || false;
        this.isTyping = false;
        this.messageCount = 0;
        this.sessionStartTime = Date.now();
        
        this.elements = {
            chatMessages: document.getElementById('chat-messages'),
            messageInput: document.getElementById('message-input'),
            sendButton: document.getElementById('send-button'),
            chatForm: document.getElementById('chat-form'),
            clearChat: document.getElementById('clear-chat'),
            exportChat: document.getElementById('export-chat'),
            moodSlider: document.getElementById('mood-slider'),
            moodScore: document.getElementById('mood-score'),
            saveMood: document.getElementById('save-mood'),
            messagesCount: document.getElementById('messages-count'),
            sessionDuration: document.getElementById('session-duration'),
            quickActions: document.querySelectorAll('.quick-action'),
            startAssessment: document.getElementById('start-assessment'),
            getRecommendations: document.getElementById('get-recommendations'),
            voiceInput: document.getElementById('voice-input')
        };
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.startSession();
        this.startSessionTimer();
        this.loadWelcomeMessage();
    }
    
    bindEvents() {
        // Send message
        this.elements.chatForm.addEventListener('submit', (e) => this.handleSendMessage(e));
        
        // Enter key to send
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage(e);
            }
        });
        
        // Clear chat
        if (this.elements.clearChat) {
            this.elements.clearChat.addEventListener('click', () => this.clearChat());
        }
        
        // Export chat
        if (this.elements.exportChat) {
            this.elements.exportChat.addEventListener('click', () => this.exportChat());
        }
        
        // Mood tracking
        if (this.elements.moodSlider) {
            this.elements.moodSlider.addEventListener('input', (e) => this.updateMoodScore(e.target.value));
        }
        
        if (this.elements.saveMood) {
            this.elements.saveMood.addEventListener('click', () => this.saveMood());
        }
        
        // Quick actions
        this.elements.quickActions.forEach(button => {
            button.addEventListener('click', (e) => this.handleQuickAction(e.target.dataset.action));
        });
        
        // Assessment
        if (this.elements.startAssessment) {
            this.elements.startAssessment.addEventListener('click', () => this.startAssessment());
        }
        
        // Recommendations
        if (this.elements.getRecommendations) {
            this.elements.getRecommendations.addEventListener('click', () => this.getRecommendations());
        }
        
        // Voice input
        if (this.elements.voiceInput) {
            this.elements.voiceInput.addEventListener('click', () => this.toggleVoiceInput());
        }
    }
    
    async startSession() {
        try {
            const response = await fetch('/api/chat/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    anonymous: this.anonymous
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                console.log('Chat session started:', this.sessionId);
            } else {
                console.error('Failed to start chat session');
            }
        } catch (error) {
            console.error('Error starting chat session:', error);
        }
    }
    
    async handleSendMessage(e) {
        e.preventDefault();
        
        const message = this.elements.messageInput.value.trim();
        if (!message || this.isTyping) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        this.elements.messageInput.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await fetch(`/api/chat/session/${this.sessionId}/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.hideTypingIndicator();
                this.addMessage('bot', data.message, data);
                
                // Handle special responses
                if (data.crisis_detected) {
                    this.handleCrisisResponse();
                }
                
                if (data.recommendations && data.recommendations.length > 0) {
                    this.showRecommendations(data.recommendations);
                }
            } else {
                this.hideTypingIndicator();
                this.addMessage('bot', 'I apologize, but I encountered an error. Please try again.');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage('bot', 'I apologize, but I encountered an error. Please try again.');
        }
    }
    
    addMessage(sender, content, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        if (sender === 'user') {
            this.messageCount++;
            this.updateStats();
        }
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        this.elements.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }
    
    handleQuickAction(action) {
        const messages = {
            mood: "How are you feeling today? I'd like to understand your current mood.",
            stress: "I understand you're feeling stressed. Can you tell me more about what's causing your stress?",
            help: "I'm here to help you. What specific support do you need right now?",
            crisis: "I'm concerned about what you're saying. If you're having thoughts of self-harm, please contact the National Suicide Prevention Lifeline at 988 or text HOME to 741741. You can also call 911 for immediate help."
        };
        
        const message = messages[action];
        if (message) {
            this.elements.messageInput.value = message;
            this.handleSendMessage({ preventDefault: () => {} });
        }
    }
    
    handleCrisisResponse() {
        // Show crisis resources prominently
        const crisisDiv = document.createElement('div');
        crisisDiv.className = 'alert alert-danger mt-3';
        crisisDiv.innerHTML = `
            <h6><i class="fas fa-exclamation-triangle"></i> Crisis Support Resources</h6>
            <p><strong>National Suicide Prevention Lifeline:</strong> 988</p>
            <p><strong>Crisis Text Line:</strong> Text HOME to 741741</p>
            <p><strong>Emergency Services:</strong> 911</p>
            <p>You are not alone. Help is available 24/7.</p>
        `;
        
        this.elements.chatMessages.appendChild(crisisDiv);
        this.scrollToBottom();
    }
    
    showRecommendations(recommendations) {
        const recDiv = document.createElement('div');
        recDiv.className = 'recommendations mt-3';
        recDiv.innerHTML = '<h6><i class="fas fa-lightbulb"></i> Personalized Recommendations</h6>';
        
        recommendations.forEach(rec => {
            const recItem = document.createElement('div');
            recItem.className = 'recommendation-item';
            recItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6>${rec.title}</h6>
                        <p class="mb-1">${rec.description}</p>
                        <small class="text-muted">Duration: ${rec.duration}</small>
                    </div>
                    <span class="recommendation-priority priority-${rec.priority}">Priority ${rec.priority}</span>
                </div>
            `;
            recDiv.appendChild(recItem);
        });
        
        this.elements.chatMessages.appendChild(recDiv);
        this.scrollToBottom();
    }
    
    updateMoodScore(score) {
        if (this.elements.moodScore) {
            this.elements.moodScore.textContent = score;
        }
    }
    
    async saveMood() {
        const score = this.elements.moodSlider.value;
        const moodLabels = ['😢', '😔', '😐', '🙂', '😊', '😄', '🤩', '🥳', '🎉', '💖'];
        const label = moodLabels[score - 1];
        
        try {
            const response = await fetch('/api/mood/entry', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mood_score: parseInt(score),
                    mood_label: label,
                    created_at: new Date().toISOString()
                })
            });
            
            if (response.ok) {
                this.addMessage('bot', `Thank you for sharing your mood (${score}/10). I've saved this information to help track your progress.`);
                this.elements.saveMood.innerHTML = '<i class="fas fa-check"></i> Saved!';
                this.elements.saveMood.disabled = true;
                
                setTimeout(() => {
                    this.elements.saveMood.innerHTML = '<i class="fas fa-save"></i> Save Mood';
                    this.elements.saveMood.disabled = false;
                }, 2000);
            }
        } catch (error) {
            console.error('Error saving mood:', error);
        }
    }
    
    updateStats() {
        if (this.elements.messagesCount) {
            this.elements.messagesCount.textContent = this.messageCount;
        }
    }
    
    startSessionTimer() {
        setInterval(() => {
            if (this.elements.sessionDuration) {
                const duration = Math.floor((Date.now() - this.sessionStartTime) / 1000 / 60);
                this.elements.sessionDuration.textContent = `${duration}m`;
            }
        }, 60000); // Update every minute
    }
    
    loadWelcomeMessage() {
        // Welcome message is already in the HTML template
        // This method can be used to customize it based on user data
    }
    
    clearChat() {
        if (confirm('Are you sure you want to clear the chat? This action cannot be undone.')) {
            this.elements.chatMessages.innerHTML = `
                <div class="welcome-message text-center text-muted py-5">
                    <i class="fas fa-heart fa-3x mb-3 text-primary"></i>
                    <h4>Welcome to your Mental Health Support Chat</h4>
                    <p>I'm here to listen, support, and help you on your wellness journey.</p>
                </div>
            `;
            this.messageCount = 0;
            this.updateStats();
        }
    }
    
    async exportChat() {
        try {
            const response = await fetch(`/api/chat/session/${this.sessionId}/export?format=csv`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `chat_history_${this.sessionId}.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Error exporting chat:', error);
        }
    }
    
    async startAssessment() {
        // This would open the assessment modal
        const modal = new bootstrap.Modal(document.getElementById('assessmentModal'));
        modal.show();
        
        // Load assessment questions
        try {
            const response = await fetch(`/api/chat/session/${this.sessionId}/assessment/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: 'PHQ-9'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.loadAssessmentQuestions(data.questions);
            }
        } catch (error) {
            console.error('Error starting assessment:', error);
        }
    }
    
    loadAssessmentQuestions(questions) {
        const content = document.getElementById('assessment-content');
        content.innerHTML = '';
        
        questions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'assessment-question';
            questionDiv.innerHTML = `
                <h6>Question ${index + 1}: ${question.question}</h6>
                <div class="assessment-options">
                    ${question.options.map(option => `
                        <div class="form-check assessment-option">
                            <input class="form-check-input" type="radio" name="q${index}" id="q${index}_${option.value}" value="${option.value}">
                            <label class="form-check-label" for="q${index}_${option.value}">
                                ${option.text}
                            </label>
                        </div>
                    `).join('')}
                </div>
            `;
            content.appendChild(questionDiv);
        });
    }
    
    async getRecommendations() {
        try {
            const response = await fetch(`/api/chat/session/${this.sessionId}/recommendations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_profile: {
                        mental_health_status: 'healthy',
                        mood_score: this.elements.moodSlider ? this.elements.moodSlider.value : 5,
                        stress_level: 5
                    },
                    current_context: {
                        current_mood: 'neutral',
                        time_of_day: new Date().getHours() < 12 ? 'morning' : 'afternoon',
                        available_time: 30
                    }
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showRecommendations(data.recommendations);
            }
        } catch (error) {
            console.error('Error getting recommendations:', error);
        }
    }
    
    toggleVoiceInput() {
        // Voice input functionality would be implemented here
        console.log('Voice input not implemented yet');
    }
}

// Export for use in other scripts
window.ChatInterface = ChatInterface;