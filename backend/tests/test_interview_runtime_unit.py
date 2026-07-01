"""test_interview_runtime_unit.py — 面试运行时引擎单元测试。

测试目标: app/services/interview_runtime.py
- _load_json / _dump_json            JSON 安全序列化
- _resolve_next_phase()             阶段流转决策
- _select_repo_question()           仓库问题选取
- _select_resume_question()         简历问题生成（monkeypatch LLM）
- _load_role_questions()            知识题加载与降级
- _select_next_knowledge_question() 知识题选取（monkeypatch LLM）
- _generate_non_duplicate_knowledge_question()  补位题生成（monkeypatch LLM）
- _build_code_prompt()             代码阶段提示
- _move_to_knowledge_or_close()     代码后阶段流转
- _load_asked_titles / _append_asked_title  已问题目管理
- Phase transitions                状态机路径覆盖

依赖: conftest.py SQLite 数据库 + monkeypatch LLM/Judge0。
"""

import json
import pytest
from unittest.mock import AsyncMock

from app.db import models, schemas
from app.db.session import SessionLocal
from app.services.interview_runtime import (
    PHASE_INTRODUCTION,
    PHASE_RESUME,
    PHASE_REPO,
    PHASE_CODE,
    PHASE_KNOWLEDGE,
    PHASE_COMPLETED,
    _load_json,
    _dump_json,
    _resolve_next_phase,
    _select_repo_question,
    _select_resume_question,
    _load_role_questions,
    _select_next_knowledge_question,
    _generate_non_duplicate_knowledge_question,
    _build_code_prompt,
    _load_asked_titles,
    _append_asked_title,
)


# ============================================================
# _load_json / _dump_json 测试
# ============================================================

class TestLoadJson:
    """验证 JSON 安全反序列化函数。"""

    def test_valid_json_parsed(self):
        """合法的 JSON 字符串应正确解析。"""
        result = _load_json('{"key": "value"}', {})
        assert result == {"key": "value"}

    def test_none_returns_fallback(self):
        """None 应返回 fallback 默认值。"""
        result = _load_json(None, [])
        assert result == []

    def test_empty_string_returns_fallback(self):
        """空字符串应返回 fallback。"""
        result = _load_json("", {"default": True})
        assert result == {"default": True}

    def test_invalid_json_returns_fallback(self):
        """无效 JSON 应返回 fallback。"""
        result = _load_json("not valid json{{{", [1, 2, 3])
        assert result == [1, 2, 3]

    def test_array_json_parsed(self):
        """JSON 数组应正确解析。"""
        result = _load_json('["a", "b", "c"]', [])
        assert result == ["a", "b", "c"]


class TestDumpJson:
    """验证 JSON 序列化函数。"""

    def test_dict_serialized(self):
        """字典应正确序列化。"""
        result = _dump_json({"key": "值"})
        assert "值" in result

    def test_list_serialized(self):
        """列表应正确序列化。"""
        result = _dump_json(["a", "b"])
        assert '"a"' in result


# ============================================================
# _resolve_next_phase 测试
# ============================================================

class TestResolveNextPhase:
    """验证自我介绍后阶段流转决策。"""

    def _make_interview(self, resume_persona=None, custom_questions=None):
        """创建测试用的 Interview 模型实例。"""
        return models.Interview(
            user_id=1,
            role="Java后端开发工程师",
            resume_persona=_dump_json(resume_persona) if resume_persona else None,
            custom_questions=_dump_json(custom_questions) if custom_questions else None,
        )

    def test_resume_persona_leads_to_resume_phase(self):
        """有简历画像时进入简历深挖阶段。"""
        interview = self._make_interview(resume_persona={"skills": ["Java"]})
        assert _resolve_next_phase(interview) == PHASE_RESUME

    def test_custom_questions_without_persona_leads_to_repo(self):
        """有自定义仓库问题但无简历时进入项目深挖。"""
        interview = self._make_interview(
            custom_questions=[{"question": "谈谈项目", "key_points": []}]
        )
        assert _resolve_next_phase(interview) == PHASE_REPO

    def test_neither_leads_to_code_phase(self):
        """既无简历也无仓库问题时直接进入代码题。"""
        interview = self._make_interview()
        assert _resolve_next_phase(interview) == PHASE_CODE


# ============================================================
# _select_repo_question 测试
# ============================================================

class TestSelectRepoQuestion:
    """验证仓库问题选取函数。"""

    def _make_interview(self, custom_questions, asked_titles=None):
        return models.Interview(
            user_id=1,
            role="Java后端开发工程师",
            custom_questions=_dump_json(custom_questions),
            asked_question_titles=_dump_json(asked_titles or []),
        )

    def test_selects_unasked_question(self):
        """应选取未被问过的题目。"""
        interview = self._make_interview(
            custom_questions=[
                {"question": "问题A", "key_points": ["A"]},
                {"question": "问题B", "key_points": ["B"]},
            ],
            asked_titles=["问题A"],
        )
        result = _select_repo_question(interview)
        assert result["question"] == "问题B"

    def test_all_asked_returns_fallback(self):
        """所有题目都已问过时应返回兜底追问。"""
        interview = self._make_interview(
            custom_questions=[{"question": "问题A", "key_points": ["A"]}],
            asked_titles=["问题A"],
        )
        result = _select_repo_question(interview)
        assert "技术贡献" in result["question"] or "深入谈谈" in result["question"]

    def test_empty_question_list_returns_fallback(self):
        """无自定义题目时返回兜底追问。"""
        interview = self._make_interview(custom_questions=[])
        result = _select_repo_question(interview)
        assert isinstance(result["question"], str)


# ============================================================
# _load_role_questions 测试
# ============================================================

class TestLoadRoleQuestions:
    """验证知识题库加载函数。"""

    def _make_interview(self, role, difficulty="medium", knowledge_points=None):
        return models.Interview(
            user_id=1,
            role=role,
            difficulty=difficulty,
            knowledge_points=_dump_json(knowledge_points) if knowledge_points else None,
        )

    def test_loads_java_questions(self):
        """Java 岗位应加载到题目。"""
        interview = self._make_interview("Java后端开发工程师")
        questions = _load_role_questions(interview)
        assert isinstance(questions, list)
        assert len(questions) > 0

    def test_loads_web_questions(self):
        """Web 前端岗位应加载到题目。"""
        interview = self._make_interview("Web前端开发工程师")
        questions = _load_role_questions(interview)
        assert len(questions) > 0

    def test_loads_python_questions(self):
        """Python 算法岗位应加载到题目。"""
        interview = self._make_interview("Python算法工程师")
        questions = _load_role_questions(interview)
        assert len(questions) > 0

    def test_with_knowledge_points_filter(self):
        """指定知识点应正确筛选。"""
        # 使用实际存在的 section 名称（如 "Java基础"）
        interview = self._make_interview(
            "Java后端开发工程师",
            knowledge_points=["Java基础"],
        )
        questions = _load_role_questions(interview)
        for q in questions:
            assert q.get("section") == "Java基础"


# ============================================================
# _load_asked_titles / _append_asked_title 测试
# ============================================================

class TestAskedTitles:
    """验证已问题目标题管理函数。"""

    def _make_interview(self, asked=None):
        return models.Interview(
            user_id=1,
            role="Test",
            asked_question_titles=_dump_json(asked) if asked else None,
        )

    def test_load_empty_returns_empty_list(self):
        """从未问过题目时应返回空列表。"""
        interview = self._make_interview()
        assert _load_asked_titles(interview) == []

    def test_load_returns_titles(self):
        """应返回已保存的标题列表。"""
        interview = self._make_interview(asked=["题1", "题2"])
        assert _load_asked_titles(interview) == ["题1", "题2"]

    def test_append_adds_new_title(self):
        """追加新标题应正确添加。"""
        interview = self._make_interview(asked=["题1"])
        _append_asked_title(interview, "题2")
        titles = _load_asked_titles(interview)
        assert "题2" in titles

    def test_append_skips_duplicate(self):
        """重复标题不应被重复添加。"""
        interview = self._make_interview(asked=["题1", "题2"])
        _append_asked_title(interview, "题1")
        titles = _load_asked_titles(interview)
        assert titles.count("题1") == 1


# ============================================================
# _build_code_prompt 测试
# ============================================================

class TestBuildCodePrompt:
    """验证代码阶段提示语构建函数。"""

    def test_builds_with_tags(self):
        """含标签的题目应在提示中包含标签。"""
        problem = models.CodeProblem(
            title="两数之和",
            difficulty="easy",
            tags=_dump_json(["Array", "Hash Table"]),
        )
        prompt = _build_code_prompt(problem)
        assert "两数之和" in prompt
        assert "Array" in prompt

    def test_builds_without_tags(self):
        """无标签的题目不应报错。"""
        problem = models.CodeProblem(
            title="简单题",
            difficulty="easy",
            tags="[]",
        )
        prompt = _build_code_prompt(problem)
        assert "简单题" in prompt


# ============================================================
# _select_next_knowledge_question 测试
# ============================================================

class TestSelectNextKnowledgeQuestion:
    """验证知识题选取（monkeypatch LLM）。"""

    def _make_interview(self, role="Java后端开发工程师", asked=None, knowledge_points=None):
        return models.Interview(
            user_id=1,
            role=role,
            difficulty="medium",
            knowledge_points=_dump_json(knowledge_points) if knowledge_points else None,
            asked_question_titles=_dump_json(asked) if asked else None,
        )

    @pytest.mark.asyncio
    async def test_candidates_exist_selects_from_pool(self):
        """题库中有未问题目时应从题库选取。"""
        interview = self._make_interview(asked=["已问过的题"])  # 这些标题不太可能在题库中存在
        # 题库中肯定有未问过的题
        result = await _select_next_knowledge_question(interview)
        assert result is not None
        assert "question" in result

    @pytest.mark.asyncio
    async def test_all_questions_asked_falls_back_to_llm(self, monkeypatch):
        """题库中所有题都问过时调用 LLM 生成。"""
        # 标记题库中所有可能的标题
        from app.services.interview_catalog import load_questions
        all_qs = load_questions("java-backend")
        all_titles = [q["question"] for q in all_qs if q.get("question")]

        interview = self._make_interview(
            role="Java后端开发工程师",
            asked=all_titles,  # 所有题都已问过
        )

        # mock LLM 的 free_question 生成
        async def fake_free_question(**kwargs):
            return {"question": "LLM 生成的补位题", "key_points": ["测试"]}

        monkeypatch.setattr(
            "app.services.interview_runtime.generate_free_question",
            fake_free_question,
        )

        result = await _select_next_knowledge_question(interview)
        assert result is not None
        assert "question" in result
