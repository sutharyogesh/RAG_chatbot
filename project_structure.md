# Self-Identifying Mental Health Status and Support ChatBot

## Project Structure

```
mental-health-chatbot/
├── src/
│   ├── nlp/                    # NLP/AI Module (Yash)
│   │   ├── __init__.py
│   │   ├── gpt_handler.py      # GPT API integration
│   │   ├── sentiment_analysis.py
│   │   ├── intent_detection.py
│   │   └── conversation_context.py
│   ├── ml/                     # Machine Learning Module (Suhani)
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── mental_health_classifier.py
│   │   │   └── recommendation_engine.py
│   │   ├── training/
│   │   │   ├── __init__.py
│   │   │   ├── data_preprocessing.py
│   │   │   └── model_training.py
│   │   └── utils.py
│   ├── db/                     # Database Module (Shiksha)
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── pinecone_client.py  # Vector database
│   │   ├── database.py         # Database connection
│   │   └── migrations/
│   ├── web/                    # Web Development Module (Yogesh)
│   │   ├── __init__.py
│   │   ├── app.py              # Flask application
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── dashboard.py
│   │   │   ├── admin.py
│   │   │   └── api.py
│   │   ├── templates/
│   │   │   ├── base.html
│   │   │   ├── login.html
│   │   │   ├── signup.html
│   │   │   ├── chat.html
│   │   │   ├── dashboard.html
│   │   │   ├── about.html
│   │   │   ├── contact.html
│   │   │   ├── features.html
│   │   │   └── admin.html
│   │   ├── static/
│   │   │   ├── css/
│   │   │   │   ├── main.css
│   │   │   │   ├── dark-theme.css
│   │   │   │   └── light-theme.css
│   │   │   ├── js/
│   │   │   │   ├── main.js
│   │   │   │   ├── chat.js
│   │   │   │   ├── dashboard.js
│   │   │   │   └── theme.js
│   │   │   └── images/
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── auth_utils.py
│   │   │   ├── validators.py
│   │   │   └── helpers.py
│   │   └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_nlp.py
│   ├── test_ml.py
│   ├── test_db.py
│   ├── test_web.py
│   └── test_integration.py
├── data/
│   ├── training_data/
│   ├── models/
│   └── exports/
├── docs/
│   ├── README.md
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── PROJECT_SUMMARY.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── run.py
└── setup.py
```

## Technology Stack

- **Backend**: Python 3.11, Flask, SQLAlchemy
- **AI/NLP**: OpenAI GPT API, HuggingFace Transformers, SpaCy
- **ML**: Scikit-learn, TensorFlow/Keras
- **Database**: PostgreSQL, Pinecone Vector DB
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Visualization**: Plotly
- **Deployment**: Docker, Heroku/Render/AWS
- **Authentication**: JWT, Flask-Login
- **Testing**: Pytest, Flask-Testing