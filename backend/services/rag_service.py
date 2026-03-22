import os
import json
import numpy as np
from openai import OpenAI
from core.config import settings

VECTOR_INDEX_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rag", "vector_index.json"))

class RAGService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
        self.index_data = []
        self.load_index()

    def load_index(self):
        if os.path.exists(VECTOR_INDEX_FILE):
            with open(VECTOR_INDEX_FILE, "r", encoding="utf-8") as f:
                self.index_data = json.load(f)
        else:
            print(f"提醒: RAG 索引文件 {VECTOR_INDEX_FILE} 未找到，请先运行 build_index.py")

    def get_embedding(self, text: str):
        # Use common embedding model
        response = self.client.embeddings.create(
            input=text,
            model=settings.LLM_EMBEDDING_MODEL
        )
        return response.data[0].embedding

    def query_context(self, query_text: str, k: int = 3):
        if not self.index_data:
            return "知识库未初始化。"

        try:
            query_vec = np.array(self.get_embedding(query_text))
            
            similarities = []
            for item in self.index_data:
                item_vec = np.array(item["embedding"])
                # Cosine Similarity = (A . B) / (||A|| * ||B||)
                # If embeddings are normalized (OpenAI usually does), it's just dot product
                score = np.dot(query_vec, item_vec)
                similarities.append((score, item["content"]))
            
            # Sort by score desc
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_k = similarities[:k]
            
            return "\n\n".join([item[1] for item in top_k])
        except Exception as e:
            print(f"RAG Query Error: {e}")
            return "知识库检索异常。"

rag_service = RAGService()
