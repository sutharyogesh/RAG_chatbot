# Mental Health ChatBot

An AI-powered mental health support chatbot that provides empathetic conversations, mood tracking, mental health assessments, and personalized recommendations.

## 🚀 Features

### Core Features
- **AI-Powered Conversations**: Natural, empathetic conversations using OpenAI GPT-4
- **Mood Tracking**: Daily mood logging with interactive visualizations
- **Mental Health Assessments**: PHQ-9, GAD-7, and custom assessments
- **Personalized Recommendations**: Tailored coping strategies and resources
- **Privacy & Security**: Anonymous chat mode and enterprise-grade security
- **Mobile Responsive**: Works seamlessly on all devices

### Advanced Features
- **Sentiment Analysis**: Real-time emotional state analysis
- **Crisis Detection**: Automatic crisis intervention and resource provision
- **Data Export**: Export chat history and mood data
- **Gamification**: Streaks, badges, and achievement tracking
- **Multilingual Support**: English and Hindi language support
- **Theme Toggle**: Light and dark mode support

## 🛠️ Technology Stack

### Backend
- **Python 3.11**: Core programming language
- **Flask**: Web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Primary database
- **Pinecone**: Vector database for semantic search

### AI/ML
- **OpenAI GPT-4**: Conversational AI
- **HuggingFace Transformers**: NLP models
- **SpaCy**: Text processing
- **Scikit-learn**: Machine learning models
- **TensorFlow/Keras**: Deep learning

### Frontend
- **HTML5/CSS3/JavaScript**: Core web technologies
- **Bootstrap 5**: UI framework
- **Plotly**: Data visualization
- **Font Awesome**: Icons

### Deployment
- **Docker**: Containerization
- **Nginx**: Reverse proxy
- **Gunicorn**: WSGI server
- **Redis**: Caching and sessions

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Docker (optional)
- OpenAI API key
- Pinecone API key

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mental-health-chatbot
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Web: http://localhost:5000
   - Admin: http://localhost:5000/admin

### Manual Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd mental-health-chatbot
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize database**
   ```bash
   python run.py
   # This will create the database and tables
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/mental_health_chatbot

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4

# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=your-pinecone-environment
PINECONE_INDEX_NAME=mental-health-embeddings

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### API Keys Setup

1. **OpenAI API Key**
   - Sign up at https://platform.openai.com/
   - Create an API key
   - Add to your `.env` file

2. **Pinecone API Key**
   - Sign up at https://www.pinecone.io/
   - Create an index
   - Add API key and environment to `.env`

## 📁 Project Structure

```
mental-health-chatbot/
├── src/
│   ├── nlp/                    # NLP/AI Module
│   │   ├── gpt_handler.py      # GPT API integration
│   │   ├── sentiment_analysis.py
│   │   ├── intent_detection.py
│   │   └── conversation_context.py
│   ├── ml/                     # Machine Learning Module
│   │   ├── models/
│   │   │   ├── mental_health_classifier.py
│   │   │   └── recommendation_engine.py
│   │   └── training/
│   ├── db/                     # Database Module
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── pinecone_client.py  # Vector database
│   │   └── database.py         # Database connection
│   └── web/                    # Web Development Module
│       ├── app.py              # Flask application
│       ├── routes/             # API routes
│       ├── templates/          # HTML templates
│       └── static/             # CSS/JS files
├── tests/                      # Test files
├── data/                       # Data storage
├── docs/                       # Documentation
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose setup
└── run.py                      # Application entry point
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_nlp.py
```

## 📊 API Documentation

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/refresh` - Refresh JWT token

### Chat Endpoints
- `POST /api/chat/session` - Start chat session
- `POST /api/chat/session/{id}/message` - Send message
- `GET /api/chat/session/{id}/history` - Get chat history

### Mood Tracking Endpoints
- `POST /api/mood/entry` - Add mood entry
- `GET /api/mood/entries` - Get mood entries

### Assessment Endpoints
- `POST /api/assessment` - Submit assessment
- `GET /api/assessment/history` - Get assessment history

## 🔒 Security Features

- **Data Encryption**: All sensitive data is encrypted
- **JWT Authentication**: Secure token-based authentication
- **Input Validation**: Comprehensive input sanitization
- **Rate Limiting**: API rate limiting to prevent abuse
- **CORS Protection**: Cross-origin resource sharing protection
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Cross-site scripting prevention

## 🌍 Deployment

### Heroku Deployment

1. **Install Heroku CLI**
2. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```
3. **Set environment variables**
   ```bash
   heroku config:set OPENAI_API_KEY=your-key
   heroku config:set PINECONE_API_KEY=your-key
   # ... other variables
   ```
4. **Deploy**
   ```bash
   git push heroku main
   ```

### AWS Deployment

1. **Use AWS Elastic Beanstalk**
2. **Configure RDS for PostgreSQL**
3. **Set up ElastiCache for Redis**
4. **Deploy using Docker**

### Docker Deployment

```bash
# Build image
docker build -t mental-health-chatbot .

# Run container
docker run -p 5000:5000 --env-file .env mental-health-chatbot
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Project Wiki](wiki-url)
- **Issues**: [GitHub Issues](issues-url)
- **Email**: support@mentalhealthchatbot.com
- **Crisis Support**: 988 (National Suicide Prevention Lifeline)

## ⚠️ Disclaimer

This chatbot is designed to provide support and guidance, but it is not a replacement for professional mental health care. If you're experiencing a mental health crisis, please contact:

- **National Suicide Prevention Lifeline**: 988
- **Crisis Text Line**: Text HOME to 741741
- **Emergency Services**: 911

## 🙏 Acknowledgments

- OpenAI for providing the GPT API
- Pinecone for vector database services
- The open-source community for various libraries and tools
- Mental health professionals who provided guidance and validation

---

**Made with ❤️ for better mental health support**