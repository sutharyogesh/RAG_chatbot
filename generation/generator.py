import openai
from config import OPENAI_API_KEY

class OpenAIGenerator:
    def __init__(self, api_key=OPENAI_API_KEY):
        openai.api_key = api_key

    def generate(self, context, query):
        prompt = f"Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response['choices'][0]['message']['content'].strip()
