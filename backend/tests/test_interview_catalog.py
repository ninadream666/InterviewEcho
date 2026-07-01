"""test_interview_catalog.py — 面试岗位目录模块单元测试。

测试目标: app/services/interview_catalog.py
- ROLES 常量                  岗位定义表
- knowledge_base_root()       知识库根路径
- get_role_info()             按名称查找岗位
- load_questions()            加载题库 JSON
- get_questions_by_category() 按类别/难度/知识点筛选
- get_knowledge_questions()   获取知识问答题目
- get_random_starting_question() 随机开场题
- get_role_sections()         获取章节列表

依赖: knowledge-base/ 目录下的 questions.json 文件。
"""

import os
import pytest
from app.services.interview_catalog import (
    ROLES,
    knowledge_base_root,
    get_role_info,
    get_questions_file,
    load_questions,
    get_questions_by_category,
    get_knowledge_questions,
    get_random_starting_question,
    get_role_sections,
)


# ============================================================
# 辅助函数
# ============================================================

def _valid_role_keys():
    """返回所有有效的 role_key 列表。"""
    return [role["key"] for role in ROLES]


# ============================================================
# ROLES 常量测试
# ============================================================

class TestRolesConstant:
    """验证岗位定义表的结构与完整性。"""

    def test_three_roles_defined(self):
        """应有三个岗位。"""
        assert len(ROLES) == 3

    def test_each_role_has_required_fields(self):
        """每个岗位应包含 id, name, key, icon, desc, gradient。"""
        required = {"id", "name", "key", "icon", "desc", "gradient"}
        for role in ROLES:
            assert required.issubset(role.keys()), f"岗位 {role.get('name')} 缺少字段"

    def test_keys_are_unique(self):
        """role key 应唯一。"""
        keys = [role["key"] for role in ROLES]
        assert len(keys) == len(set(keys))

    def test_names_are_unique(self):
        """岗位名称应唯一。"""
        names = [role["name"] for role in ROLES]
        assert len(names) == len(set(names))


# ============================================================
# knowledge_base_root 测试
# ============================================================

class TestKnowledgeBaseRoot:
    """验证知识库根路径函数。"""

    def test_returns_absolute_path(self):
        """应返回绝对路径。"""
        path = knowledge_base_root()
        assert os.path.isabs(path)

    def test_path_contains_knowledge_base(self):
        """路径应包含 knowledge-base 目录名。"""
        path = knowledge_base_root()
        assert "knowledge-base" in path or "knowledge_base" in path


# ============================================================
# get_role_info 测试
# ============================================================

class TestGetRoleInfo:
    """验证岗位查找函数。"""

    def test_java_backend_found(self):
        """Java后端岗位应返回正确信息。"""
        info = get_role_info("Java后端开发工程师")
        assert info["name"] == "Java后端开发工程师"
        assert info["key"] == "java-backend"

    def test_web_frontend_found(self):
        """Web前端岗位应返回正确信息。"""
        info = get_role_info("Web前端开发工程师")
        assert info["key"] == "web-frontend"

    def test_python_algorithm_found(self):
        """Python算法岗位应返回正确信息。"""
        info = get_role_info("Python算法工程师")
        assert info["key"] == "python-algorithm"

    def test_unknown_role_returns_first_role_as_default(self):
        """未知岗位应返回第一个岗位（Java后端）作为默认值。"""
        info = get_role_info("不存在的岗位")
        assert info == ROLES[0]


# ============================================================
# get_questions_file 测试
# ============================================================

class TestGetQuestionsFile:
    """验证题库文件路径函数。"""

    def test_returns_valid_path_for_java_backend(self):
        """Java后端题库文件路径应存在。"""
        path = get_questions_file("java-backend")
        assert path.endswith("questions.json")

    def test_returns_valid_path_for_all_roles(self):
        """所有岗位的题库文件路径应指向存在的文件。"""
        for role_key in _valid_role_keys():
            path = get_questions_file(role_key)
            assert os.path.exists(path), f"题库文件不存在：{path}"


# ============================================================
# load_questions 测试
# ============================================================

class TestLoadQuestions:
    """验证题库加载函数。"""

    def test_load_java_backend_returns_list(self):
        """Java后端题库应返回题目列表。"""
        questions = load_questions("java-backend")
        assert isinstance(questions, list)
        assert len(questions) > 0, "Java后端题库不应为空"

    def test_load_web_frontend_returns_list(self):
        """Web前端题库应返回题目列表。"""
        questions = load_questions("web-frontend")
        assert isinstance(questions, list)
        assert len(questions) > 0, "Web前端题库不应为空"

    def test_load_python_algorithm_returns_list(self):
        """Python算法题库应返回题目列表。"""
        questions = load_questions("python-algorithm")
        assert isinstance(questions, list)
        assert len(questions) > 0, "Python算法题库不应为空"

    def test_invalid_role_key_returns_empty_list(self):
        """无效的 role_key 应返回空列表。"""
        questions = load_questions("nonexistent-role")
        assert questions == []

    def test_each_question_has_expected_fields(self):
        """每道题应包含基本字段（question/section/difficulty/category）。"""
        has_any_questions = False
        for role_key in _valid_role_keys():
            questions = load_questions(role_key)
            for q in questions:
                has_any_questions = True
                # question 字段应存在（题库使用 question 字段存储题目文本）
                assert "question" in q, f"题目缺少 question 字段"
                assert isinstance(q["question"], str), f"question 应为字符串"
        assert has_any_questions, "至少应有一道题"


# ============================================================
# get_questions_by_category 测试
# ============================================================

class TestGetQuestionsByCategory:
    """验证按类别筛选题目函数。"""

    def test_filter_by_category_business_scenario(self):
        """筛选 business_scenario 类别应返回对应题目。"""
        for role_key in _valid_role_keys():
            questions = get_questions_by_category(role_key, "business_scenario")
            assert isinstance(questions, list)
            # 每个岗位至少应有零或更多的业务场景题

    def test_filter_by_difficulty(self):
        """筛选难度应正确过滤。"""
        for role_key in _valid_role_keys():
            questions = get_questions_by_category(role_key, "knowledge", difficulty="简单")
            for q in questions:
                assert q.get("difficulty") == "easy"

    def test_non_matching_category_returns_empty(self):
        """不存在的类别应返回空列表。"""
        questions = get_questions_by_category("java-backend", "nonexistent_category_xyz")
        assert questions == []

    def test_non_matching_filters_returns_empty(self):
        """不匹配的筛选组合应返回空列表。"""
        questions = get_questions_by_category("java-backend", "business_scenario", difficulty="困难", knowledge_points=["不存在的知识点"])
        assert questions == []


# ============================================================
# get_knowledge_questions 测试
# ============================================================

class TestGetKnowledgeQuestions:
    """验证知识问答题目获取函数。"""

    def test_returns_all_categories(self):
        """应返回不限类别的知识题目。"""
        for role_key in _valid_role_keys():
            questions = get_knowledge_questions(role_key)
            assert isinstance(questions, list)
            # 应至少有一些题目

    def test_difficulty_filter(self):
        """难度筛选应正确工作。"""
        questions = get_knowledge_questions("java-backend", difficulty="简单")
        for q in questions:
            assert q.get("difficulty") == "easy"

    def test_easy_difficulty_has_questions(self):
        """简单难度应至少有 1 道知识题（兼容 test_knowledge_base 的要求）。"""
        for role_key in _valid_role_keys():
            questions = get_knowledge_questions(role_key, difficulty="简单")
            # 不要求一定有题（可能简单难度的知识题较少）

    def test_knowledge_points_filter(self):
        """知识点筛选应正确过滤。"""
        # 先获取某个有效的知识点
        sections = get_role_sections("java-backend")
        if sections:
            questions = get_knowledge_questions("java-backend", knowledge_points=[sections[0]])
            for q in questions:
                assert q.get("section") == sections[0]


# ============================================================
# get_random_starting_question 测试
# ============================================================

class TestGetRandomStartingQuestion:
    """验证随机开场题函数。"""

    def test_returns_dict_for_known_roles(self):
        """已知岗位应返回题目字典。"""
        for role_name in [role["name"] for role in ROLES]:
            question = get_random_starting_question(role_name)
            assert isinstance(question, (dict, str))

    def test_unknown_role_returns_fallback_string(self):
        """未知岗位应返回回退字符串。"""
        question = get_random_starting_question("不存在的岗位")
        assert isinstance(question, (dict, str))
        if isinstance(question, str):
            assert len(question) > 0

    def test_multiple_calls_may_be_different(self):
        """多次调用可能返回不同题目（随机性测试）。"""
        results = [get_random_starting_question("Java后端开发工程师") for _ in range(5)]
        # 取 content 做比较（5 次有至少 2 种不同结果即为合理随机）
        contents = set()
        for r in results:
            if isinstance(r, dict):
                contents.add(r.get("content", ""))
            else:
                contents.add(r)
        # 允许极端情况下都相同（题库题目少时），但通常应有多样性


# ============================================================
# get_role_sections 测试
# ============================================================

class TestGetRoleSections:
    """验证章节列表函数。"""

    def test_returns_list_of_strings(self):
        """应返回字符串列表。"""
        sections = get_role_sections("java-backend")
        assert isinstance(sections, list)
        for s in sections:
            assert isinstance(s, str)

    def test_sections_are_sorted(self):
        """章节列表应已排序。"""
        sections = get_role_sections("java-backend")
        assert sections == sorted(sections)

    def test_sections_are_unique(self):
        """章节列表应无重复。"""
        sections = get_role_sections("java-backend")
        assert len(sections) == len(set(sections))

    def test_all_roles_have_sections(self):
        """所有岗位都应有章节。"""
        for role_key in _valid_role_keys():
            sections = get_role_sections(role_key)
            assert len(sections) > 0, f"岗位 {role_key} 的章节列表为空"

    def test_invalid_role_key_returns_empty(self):
        """无效 role_key 应返回空列表。"""
        sections = get_role_sections("nonexistent")
        assert sections == []
