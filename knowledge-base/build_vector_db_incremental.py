"""增量向量数据库构建脚本（W2.7）

与 build_vector_db.py 的区别：
- 全量脚本：每次都把整个知识库切分 + 嵌入 + 重建 Chroma，慢且浪费算力
- 本脚本：维护 .vector_cache.json（文件 sha256 → chunk_ids），只对**变更/新增**文件重建向量，
         同时把已不存在文件的 chunk 从向量库中删除

使用方式：
    python knowledge-base/build_vector_db_incremental.py
    # 首次运行 = 全量构建并落缓存
    # 后续运行 = 仅增量更新

依赖与 build_vector_db.py 一致：
    pip install chromadb langchain langchain-community langchain-huggingface sentence-transformers
"""

import os
import json
import hashlib
import uuid
from typing import Dict, List, Tuple

try:
    from langchain_community.document_loaders import TextLoader
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document
    print("使用了备用导入处理...")


KNOWLEDGE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge-base"))
VECTOR_DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "rag", "chroma_db"))
CACHE_FILE = os.path.join(VECTOR_DB_DIR, ".vector_cache.json")


# ===== 缓存管理 =====

def load_cache() -> Dict[str, dict]:
    """加载缓存：{relative_filepath: {"sha256": str, "chunk_ids": [str, ...]}}"""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[cache] 加载失败，将按全量重建处理：{e}")
        return {}


def save_cache(cache: Dict[str, dict]) -> None:
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ===== 文档加载 =====

def load_json_questions(filepath: str, rel_path: str) -> List[Document]:
    documents = []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            content = f"题目: {item.get('question')}\n"
            content += f"回答要点: {', '.join(item.get('expected_points', []) or item.get('key_points', []))}\n"
            content += f"满分标准: {item.get('evaluation_criteria', {}).get('excellent', '')}\n"
            documents.append(Document(
                page_content=content,
                metadata={
                    "source": rel_path,
                    "question_id": item.get("id", ""),
                    "difficulty": item.get("difficulty", ""),
                    "category": item.get("category", ""),
                },
            ))
    return documents


def load_markdown_knowledge(filepath: str, rel_path: str) -> List[Document]:
    loader = TextLoader(filepath, encoding="utf-8")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = splitter.split_documents(docs)
    # 覆盖 source 用相对路径，方便缓存匹配
    for d in splits:
        d.metadata["source"] = rel_path
    return splits


def load_documents_for_file(filepath: str, rel_path: str) -> List[Document]:
    if filepath.endswith(".json"):
        return load_json_questions(filepath, rel_path)
    if filepath.endswith(".md") and os.path.basename(filepath) != "README.md":
        return load_markdown_knowledge(filepath, rel_path)
    return []


# ===== 主流程 =====

def scan_knowledge_base() -> Dict[str, str]:
    """扫描知识库目录，返回 {rel_path: sha256}。"""
    result = {}
    for root, _, files in os.walk(KNOWLEDGE_BASE_DIR):
        for file in files:
            if not (file.endswith(".json") or (file.endswith(".md") and file != "README.md")):
                continue
            full = os.path.join(root, file)
            rel = os.path.relpath(full, KNOWLEDGE_BASE_DIR).replace("\\", "/")
            try:
                result[rel] = file_sha256(full)
            except Exception as e:
                print(f"[scan] 读取 {rel} 失败，跳过：{e}")
    return result


def diff_files(current: Dict[str, str], cache: Dict[str, dict]) -> Tuple[List[str], List[str], List[str], List[str]]:
    """对比 current 与 cache，返回 (added, changed, unchanged, removed)。"""
    cached_paths = set(cache.keys())
    current_paths = set(current.keys())

    added = sorted(current_paths - cached_paths)
    removed = sorted(cached_paths - current_paths)
    changed = sorted(p for p in (current_paths & cached_paths) if cache[p].get("sha256") != current[p])
    unchanged = sorted(p for p in (current_paths & cached_paths) if cache[p].get("sha256") == current[p])
    return added, changed, unchanged, removed


def build_incremental():
    print("=" * 60)
    print("RAG 向量数据库 - 增量构建")
    print("=" * 60)

    cache = load_cache()
    current = scan_knowledge_base()
    added, changed, unchanged, removed = diff_files(current, cache)

    print(f"\n[scan] 知识库文件总数 = {len(current)}")
    print(f"  新增 (added)      = {len(added)}")
    print(f"  变更 (changed)    = {len(changed)}")
    print(f"  未变 (unchanged)  = {len(unchanged)}")
    print(f"  删除 (removed)    = {len(removed)}")

    if not added and not changed and not removed:
        print("\n知识库无变化，无需重建。")
        return

    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

    # 1. 删除：移除已不存在的文件的 chunk + 变更文件的旧 chunk
    to_delete_paths = removed + changed
    to_delete_ids: List[str] = []
    for p in to_delete_paths:
        ids = cache.get(p, {}).get("chunk_ids") or []
        to_delete_ids.extend(ids)
    if to_delete_ids:
        try:
            vectorstore.delete(ids=to_delete_ids)
            print(f"[delete] 移除了 {len(to_delete_ids)} 个旧 chunk")
        except Exception as e:
            print(f"[delete] 删除失败（可能 id 不存在，将忽略）：{e}")

    # 2. 添加：变更 + 新增的文件重新切分 + 嵌入
    to_add_paths = added + changed
    new_cache = {p: cache[p] for p in unchanged}  # unchanged 直接保留

    for rel in to_add_paths:
        full = os.path.join(KNOWLEDGE_BASE_DIR, rel.replace("/", os.sep))
        docs = load_documents_for_file(full, rel)
        if not docs:
            print(f"[add] {rel} 未产生 chunk，跳过")
            new_cache[rel] = {"sha256": current[rel], "chunk_ids": []}
            continue
        chunk_ids = [str(uuid.uuid4()) for _ in docs]
        vectorstore.add_documents(documents=docs, ids=chunk_ids)
        new_cache[rel] = {"sha256": current[rel], "chunk_ids": chunk_ids}
        print(f"[add] {rel} -> {len(chunk_ids)} chunk")

    # 3. 持久化
    try:
        # 新版 Chroma 自动持久化；老版需手动调
        if hasattr(vectorstore, "persist"):
            vectorstore.persist()
    except Exception as e:
        print(f"[persist] 提示：{e}")

    save_cache(new_cache)
    print(f"\n增量构建完成。缓存已写入 {CACHE_FILE}")


if __name__ == "__main__":
    build_incremental()
