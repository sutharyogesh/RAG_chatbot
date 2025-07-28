from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import os
import pandas as pd
import datetime
import json

from embeddings.embedder import Embedder
from retrieval.retriever import Retriever
from generation.generator import OpenAIGenerator
from utils.multilingual import translate_to_english, translate_from_english
from utils.logger import save_log

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = 'data/'
CHAT_LOG_FOLDER = 'chat_logs/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHAT_LOG_FOLDER, exist_ok=True)

embedder = Embedder()
generator = OpenAIGenerator(api_key="your_openai_api_key_here")

df = pd.read_csv(os.path.join(UPLOAD_FOLDER, "Training Dataset.csv"))
texts = df.astype(str).apply(lambda x: ' | '.join(x), axis=1).tolist()
text_embeddings = embedder.embed(texts)
retriever = Retriever(text_embeddings, texts)

chat_log = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        df = pd.read_csv(path)
        texts = df.astype(str).apply(lambda x: ' | '.join(x), axis=1).tolist()
        text_embeddings = embedder.embed(texts)
        global retriever
        retriever = Retriever(text_embeddings, texts)
    return redirect(url_for('chat'))

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logs')
def logs():
    return render_template('logs.html', chat_log=chat_log)

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form['message']
    lang = request.form.get('lang', 'en')
    translated_input = translate_to_english(user_input, lang) if lang != 'en' else user_input

    query_embedding = embedder.embed([translated_input])[0]
    relevant_chunks = retriever.query(query_embedding)

    context = "\n".join(relevant_chunks)
    answer = generator.generate(context, translated_input)
    final_answer = translate_from_english(answer, lang) if lang != 'en' else answer

    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "query": user_input,
        "answer": final_answer
    }
    chat_log.append(log_entry)
    save_log(CHAT_LOG_FOLDER, chat_log)

    return jsonify({"answer": final_answer})

@app.route('/download')
def download():
    filename = f"{CHAT_LOG_FOLDER}/chat_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(chat_log, f, indent=2)
    return send_file(filename, as_attachment=True)

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    chat_log[-1]["feedback"] = data.get("feedback")
    return jsonify({"status": "received"})

if __name__ == '__main__':
    app.run(debug=True)
