"""
模块名称：面试目录服务（interview_catalog）
功能描述：管理面试岗位定义和知识题库的加载与查询。

核心职责：
1. 定义支持的面试岗位列表（Java后端 / Web前端 / Python算法）
2. 从 knowledge-base 目录加载对应岗位的面试题库（JSON 格式）
3. 按类别、难度、知识点筛选题目
4. 提供随机选题和章节列表查询
"""

import json
import os
import random
from typing import List, Optional


# ============================================================
# 岗位定义
# ============================================================
ROLES = [
    {
        "id": 1,
        "name": "Java后端开发工程师",
        "key": "java-backend",
        "icon": "☕",
        "desc": "重点考察自动装配、JVM、并发编程等",
        "gradient": "from-orange-400 to-red-500",
    },
    {
        "id": 2,
        "name": "Web前端开发工程师",
        "key": "web-frontend",
        "icon": "🌐",
        "desc": "重点考察Vue/React原理、性能优化、事件循环等",
        "gradient": "from-blue-400 to-indigo-600",
    },
    {
        "id": 3,
        "name": "Python算法工程师",
        "key": "python-algorithm",
        "icon": "🐍",
        "desc": "重点考察机器学习模型、数据结构、模型调优等",
        "gradient": "from-green-400 to-emerald-600",
    },
]

# 中文难度 → 英文标签的映射
_DIFFICULTY_MAP = {"简单": "easy", "中等": "medium", "困难": "hard"}


def knowledge_base_root() -> str:
    """获取 knowledge-base 目录的绝对路径。"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "knowledge-base"))


def get_role_info(role_name: str) -> dict:
    """
    根据岗位名称查找岗位信息字典。

    Args:
        role_name: 中文岗位名称（如 "Java后端开发工程师"）。

    Returns:
        dict: 岗位信息，未找到时返回第一个岗位作为默认值。
    """
    return next((role for role in ROLES if role["name"] == role_name), ROLES[0])


def get_questions_file(role_key: str) -> str:
    """获取指定岗位的题库 JSON 文件路径。"""
    return os.path.join(knowledge_base_root(), role_key, "questions.json")


def load_questions(role_key: str) -> list[dict]:
    """从 JSON 文件加载指定岗位的全部面试题目。"""
    questions_file = get_questions_file(role_key)
    if not os.path.exists(questions_file):
        return []
    with open(questions_file, "r", encoding="utf-8") as file:
        return json.load(file)


def get_questions_by_category(
    role_key: str,
    category: str,
    difficulty: str = "medium",
    knowledge_points: Optional[List[str]] = None,
) -> list[dict]:
    """
    按类别和难度筛选题目列表。

    Args:
        role_key: 岗位标识（如 "java-backend"）。
        category: 题目类别（如 "business_scenario"）。
        difficulty: 难度（中文："简单"/"中等"/"困难"）。
        knowledge_points: 可选的知识点过滤列表。

    Returns:
        list[dict]: 匹配的题目列表。
    """
    target_diff = _DIFFICULTY_MAP.get(difficulty, difficulty or "medium")
    questions = load_questions(role_key)
    matched = []
    for question in questions:
        if question.get("category") != category or question.get("difficulty") != target_diff:
            continue
        if knowledge_points and question.get("section") not in knowledge_points:
            continue
        matched.append(question)
    return matched


def get_knowledge_questions(
    role_key: str,
    difficulty: str = "medium",
    knowledge_points: Optional[List[str]] = None,
) -> list[dict]:
    """
    获取指定岗位的知识问答题目（不限类别）。

    Args:
        role_key: 岗位标识。
        difficulty: 难度。
        knowledge_points: 可选的知识点过滤列表。

    Returns:
        list[dict]: 匹配的题目列表。
    """
    target_diff = _DIFFICULTY_MAP.get(difficulty, difficulty or "medium")
    questions = load_questions(role_key)
    matched = []
    for question in questions:
        if question.get("difficulty") != target_diff:
            continue
        if knowledge_points and question.get("section") not in knowledge_points:
            continue
        matched.append(question)
    return matched


def get_random_starting_question(role_name: str, difficulty: str = "medium", knowledge_points: Optional[List[str]] = None):
    """
    获取一道随机的开场题（优先业务场景题）。

    用于面试开始时作为引导性问题。
    """
    role_key = get_role_info(role_name)["key"]
    questions = get_questions_by_category(role_key, "business_scenario", difficulty, knowledge_points)
    if not questions:
        questions = load_questions(role_key)
    return random.choice(questions) if questions else "请谈谈你对该岗位的理解。"


def get_role_sections(role_key: str) -> list[str]:
    """
    获取指定岗位的所有知识点章节列表（去重排序）。

    Returns:
        list[str]: 如 ["Spring框架", "多线程", "JVM", ...]。
    """
    sections = {question["section"] for question in load_questions(role_key) if question.get("section")}
    return sorted(sections)
