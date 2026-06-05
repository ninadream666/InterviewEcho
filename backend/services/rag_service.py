"""
模块名称：RAG 检索增强生成服务（rag_service）
功能描述：基于预构建的向量索引实现文档检索功能。

工作流程：
1. 启动时加载向量索引文件（vector_index.json）
2. 接收查询文本，调用嵌入模型生成查询向量
3. 使用余弦相似度（内积）在索引中检索 Top-K 最相关文档片段
4. 将检索结果拼接为上下文文本，注入 LLM prompt

依赖：
- 向量索引由 backend/rag/build_index.py 预先生成
- 嵌入模型通过 LLM_EMBEDDING_MODEL 配置（默认 text-embedding-3-small）
"""

import os
import json
import numpy as np
from openai import OpenAI
from core.config import settings

# 向量索引文件路径
VECTOR_INDEX_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rag", "vector_index.json"))


class RAGService:
    """
    RAG 检索服务，基于向量相似度的知识库文档检索。

    使用方式：
        rag_service = RAGService()  # 全局单例
        context = await rag_service.query_context_async("什么是Spring的自动装配？")
    """

    def __init__(self):
        """初始化 OpenAI 客户端并加载向量索引。"""
        self.client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
        self.index_data = []
        self.load_index()

    def load_index(self):
        """从磁盘加载预构建的向量索引文件。"""
        if os.path.exists(VECTOR_INDEX_FILE):
            with open(VECTOR_INDEX_FILE, "r", encoding="utf-8") as f:
                self.index_data = json.load(f)
        else:
            print(f"提醒: RAG 索引文件 {VECTOR_INDEX_FILE} 未找到，请先运行 build_index.py")

    def get_embedding(self, text: str):
        """
        调用嵌入模型生成文本的向量表示。

        Args:
            text: 输入文本。

        Returns:
            list[float]: 嵌入向量。
        """
        response = self.client.embeddings.create(
            input=text,
            model=settings.LLM_EMBEDDING_MODEL
        )
        return response.data[0].embedding

    async def query_context_async(self, query_text: str, k: int = 3):
        """
        根据查询文本异步检索最相关的 k 个文档片段。

        注意：当前实现使用同步 OpenAI 客户端，在异步上下文中通过线程池执行。
        正式环境建议改用 AsyncOpenAI。

        Args:
            query_text: 查询文本（通常是面试官的问题）。
            k: 返回的文档片段数量，默认 3。

        Returns:
            str: 拼接后的上下文文本（以双换行符分隔），或错误提示字符串。
        """
        if not self.index_data:
            return "知识库未初始化。"

        try:
            # 生成查询向量
            query_vec = np.array(self.get_embedding(query_text))

            # 计算余弦相似度（归一化向量可直接用内积）
            similarities = []
            for item in self.index_data:
                item_vec = np.array(item["embedding"])
                score = np.dot(query_vec, item_vec)
                similarities.append((score, item["content"]))

            # 取 Top-K
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_k = similarities[:k]

            return "\n\n".join([item[1] for item in top_k])
        except Exception as e:
            print(f"RAG Async Query Error: {e}")
            return "知识库检索异常。"


# 全局单例
rag_service = RAGService()
