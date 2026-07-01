"""test_prompts.py — 提示词管理器单元测试。

测试目标: core/prompts.py
- PromptManager.__init__()   构造与自动加载
- PromptManager.load_prompts()   Markdown 文件解析
- get_interviewer_prompt()   面试官提示词格式化
- get_evaluator_prompt()     评估者提示词格式化
- get_resume_parser_prompt() 简历解析提示词（无占位符）
- get_repo_question_prompt() 项目深挖提示词
- get_resume_question_prompt() 简历提问提示词
- get_free_question_prompt() 自由发挥提示词
- get_study_plan_prompt()    学习计划提示词
- get_expression_evaluator_prompt() 表达分析提示词

依赖: knowledge-base/system_prompts.md 文件。
"""

import os
import pytest
from core.prompts import PromptManager, prompt_manager, PROMPT_FILE


# ============================================================
# 测试辅助
# ============================================================

def _get_prompt_file_path():
    """获取 system_prompts.md 的实际路径。"""
    return PROMPT_FILE


# ============================================================
# PromptManager 初始化测试
# ============================================================

class TestPromptManagerInit:
    """验证 PromptManager 的构造和文件加载。"""

    def test_loads_from_existing_file(self):
        """从存在的文件构造时应成功加载模板。"""
        pm = PromptManager(_get_prompt_file_path())
        assert pm.prompts, "应至少加载一个提示词模板"
        assert isinstance(pm.prompts, dict)

    def test_prompt_file_exists(self):
        """确保 system_prompts.md 文件存在于指定路径。"""
        assert os.path.exists(_get_prompt_file_path()), \
            f"提示词文件不存在: {_get_prompt_file_path()}"

    def test_loads_expected_prompt_keys(self):
        """应至少加载 interviewer 和 evaluator 两个核心提示词键。"""
        pm = PromptManager(_get_prompt_file_path())
        assert "interviewer" in pm.prompts, "缺少 interviewer 提示词"
        assert "evaluator" in pm.prompts, "缺少 evaluator 提示词"

    def test_handles_missing_file_gracefully(self):
        """不存在的文件不应抛出异常，prompts 应为空字典。"""
        pm = PromptManager("/nonexistent/path/to/prompts.md")
        assert pm.prompts == {}

    def test_global_singleton_loaded(self):
        """全局 prompt_manager 单例应已正确加载。"""
        assert prompt_manager.prompts, "全局单例未加载提示词"
        assert "interviewer" in prompt_manager.prompts


# ============================================================
# get_interviewer_prompt 测试
# ============================================================

class TestGetInterviewerPrompt:
    """验证面试官提示词的格式化。"""

    def test_formats_with_all_args(self):
        """传入所有参数后应返回包含岗位和问题的格式化文本。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_interviewer_prompt(
            role="Java后端开发工程师",
            question="请解释JVM内存模型",
            expected_points="堆、栈、方法区",
            conversation_history=[],
            target_next_question="请解释GC机制",
            difficulty="medium",
            knowledge_points="JVM,GC",
            force_next_instruction="",
            rag_context="",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_result_contains_injected_values(self):
        """格式化后的结果应包含注入的参数值。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_interviewer_prompt(
            role="Python算法工程师",
            question="请解释梯度下降",
            expected_points="学习率、局部最优",
            conversation_history=[],
            target_next_question="请解释过拟合",
        )
        assert "Python算法工程师" in result
        assert "梯度下降" in result


# ============================================================
# get_evaluator_prompt 测试
# ============================================================

class TestGetEvaluatorPrompt:
    """验证评估者提示词的格式化。"""

    def test_formats_with_full_args(self):
        """传入完整参数后应返回格式化文本。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_evaluator_prompt(
            interview_transcript="[面试对话记录]",
            excellent_answers_context="[优秀回答参考]",
            role="Web前端开发工程师",
            role_specific_criteria="重点考察JavaScript和Vue",
            resume_summary="3年经验，熟悉React",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_result_contains_role_info(self):
        """结果应包含岗位信息。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_evaluator_prompt(
            interview_transcript="测试对话",
            role="Java后端开发工程师",
        )
        assert "Java后端开发工程师" in result

    def test_handles_empty_optional_fields(self):
        """可选字段为空时不报错。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_evaluator_prompt(
            interview_transcript="测试对话",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_something_even_with_keyerror_fallback(self):
        """即使模板缺少某些占位符，KeyError fallback 也应返回结果。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_evaluator_prompt(
            interview_transcript="test transcript",
            excellent_answers_context="",
            role="",
            role_specific_criteria="",
            resume_summary="",
        )
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================
# get_resume_parser_prompt 测试
# ============================================================

class TestGetResumeParserPrompt:
    """验证简历解析提示词。"""

    def test_returns_template_as_is(self):
        """简历解析提示词应不含 .format() 调用（避免花括号冲突），直接返回模板。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_resume_parser_prompt()
        # 如果模板不存在则返回空串（不抛错）
        assert isinstance(result, str)


# ============================================================
# get_repo_question_prompt 测试
# ============================================================

class TestGetRepoQuestionPrompt:
    """验证项目深挖问题提示词。"""

    def test_formats_with_repo_summary(self):
        """传入仓库摘要后应正确格式化。"""
        pm = PromptManager(_get_prompt_file_path())
        repo_summary = {
            "full_name": "test/repo",
            "description": "A test repository",
            "main_language": "Python",
            "languages": {"Python": 80, "JavaScript": 20},
            "stars": 100,
            "tech_keywords": ["Python", "FastAPI"],
            "top_level_files": ["main.py", "README.md"],
            "recent_commits": ["fix: bug", "feat: add feature"],
            "readme_excerpt": "# Test Repo",
            "key_files": [{"path": "main.py", "content": "print('hello')"}],
        }
        result = pm.get_repo_question_prompt("Python算法工程师", repo_summary)
        assert isinstance(result, str)
        if result:  # 如果模板存在
            assert "test/repo" in result

    def test_handles_empty_key_files(self):
        """空 key_files 时不应报错。"""
        pm = PromptManager(_get_prompt_file_path())
        repo_summary = {
            "full_name": "test/empty-repo",
            "description": "Empty",
            "main_language": "",
            "languages": {},
            "stars": 0,
            "tech_keywords": [],
            "top_level_files": [],
            "recent_commits": [],
            "readme_excerpt": "",
            "key_files": [],
        }
        result = pm.get_repo_question_prompt("Web前端开发工程师", repo_summary)
        assert isinstance(result, str)


# ============================================================
# get_resume_question_prompt 测试
# ============================================================

class TestGetResumeQuestionPrompt:
    """验证简历提问提示词。"""

    def test_formats_with_full_persona(self):
        """传入完整画像后应正确格式化。"""
        pm = PromptManager(_get_prompt_file_path())
        persona = {
            "skills": ["Python", "Java", "SQL", "Docker", "Git", "Linux"],
            "projects": [
                {"name": "电商系统", "tech": ["Spring Boot", "MySQL", "Redis"], "highlights": "QPS 1000+", "role": "后端开发"},
            ],
            "work_years": 3,
            "education": "本科",
            "summary": "有3年Java后端开发经验",
        }
        result = pm.get_resume_question_prompt(persona)
        assert isinstance(result, str)
        if result:
            assert "Python" in result

    def test_handles_empty_projects(self):
        """空项目列表时不应报错。"""
        pm = PromptManager(_get_prompt_file_path())
        persona = {
            "skills": [],
            "projects": [],
            "work_years": 0,
            "education": "",
            "summary": "",
        }
        result = pm.get_resume_question_prompt(persona)
        assert isinstance(result, str)


# ============================================================
# get_free_question_prompt 测试
# ============================================================

class TestGetFreeQuestionPrompt:
    """验证自由发挥提示词。"""

    def test_formats_all_placeholders(self):
        """传入完整参数后应正确格式化。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_free_question_prompt(
            role="Java后端开发工程师",
            category="knowledge",
            difficulty="medium",
            asked_questions="JVM内存模型, GC算法",
            knowledge_points="JVM",
        )
        assert isinstance(result, str)
        if result:
            assert "Java后端开发工程师" in result

    def test_handles_empty_asked_questions(self):
        """未传已问问题时使用默认值。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_free_question_prompt(
            role="Python算法工程师",
            category="business_scenario",
            difficulty="hard",
            asked_questions="",
            knowledge_points="",
        )
        assert isinstance(result, str)


# ============================================================
# get_study_plan_prompt 测试
# ============================================================

class TestGetStudyPlanPrompt:
    """验证学习计划提示词。"""

    def test_formats_with_evaluation_data(self):
        """传入评估数据后应正确格式化。"""
        pm = PromptManager(_get_prompt_file_path())
        eval_data = {
            "total_score": 75.0,
            "content_score": 70.0,
            "expression_score": 80.0,
            "business_scenario_score": 65.0,
            "problem_solving_score": 85.0,
            "weaknesses": ["JVM理解不够深入", "分布式经验不足"],
        }
        result = pm.get_study_plan_prompt(
            role="Java后端开发工程师",
            evaluation_data=eval_data,
            transcript_excerpt="[面试对话节选]",
        )
        assert isinstance(result, str)

    def test_handles_empty_weaknesses(self):
        """无弱点时使用默认文本。"""
        pm = PromptManager(_get_prompt_file_path())
        eval_data = {
            "total_score": 90.0,
            "content_score": 90.0,
            "expression_score": 90.0,
            "business_scenario_score": 90.0,
            "problem_solving_score": 90.0,
            "weaknesses": [],
        }
        result = pm.get_study_plan_prompt(
            role="Web前端开发工程师",
            evaluation_data=eval_data,
            transcript_excerpt="[面试对话节选]",
        )
        assert isinstance(result, str)


# ============================================================
# get_expression_evaluator_prompt 测试
# ============================================================

class TestGetExpressionEvaluatorPrompt:
    """验证表达分析提示词。"""

    def test_returns_template_as_is(self):
        """表达分析提示词应无动态占位符，直接返回模板。"""
        pm = PromptManager(_get_prompt_file_path())
        result = pm.get_expression_evaluator_prompt()
        assert isinstance(result, str)
