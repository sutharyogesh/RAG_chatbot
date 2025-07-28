import faiss
import numpy as np

class Retriever:
    def __init__(self, embeddings, texts):
        self.index = faiss.IndexFlatL2(len(embeddings[0]))
        self.index.add(np.array(embeddings).astype('float32'))
        self.texts = texts

    def query(self, query_embedding, top_k=5):
        query_embedding = np.array([query_embedding]).astype('float32')
        _, indices = self.index.search(query_embedding, top_k)
        return [self.texts[i] for i in indices[0]]
