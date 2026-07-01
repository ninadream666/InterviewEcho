"""test_schemas.py — Pydantic 数据校验模式单元测试。

测试目标: app/db/schemas.py
- serialize_utc_datetime()   时区转换函数
- ApiSchema 基类行为
- UserCreate / UserResponse / Token Schema 验证
- InterviewStart / MessageResponse 默认值
- CodeRunRequest / CodeCaseResult / CodeRunResponse 字段校验
- EvaluationDetail 可选字段处理
- InterviewStateResponse 结构验证
"""

from datetime import UTC, datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from app.db.schemas import (
    serialize_utc_datetime,
    ApiSchema,
    UserCreate,
    UserResponse,
    Token,
    InterviewStart,
    MessageSend,
    MessageResponse,
    CodeRunRequest,
    CodeCaseResult,
    CodeRunResponse,
    CodeSubmitResponse,
    EvaluationDetail,
    InterviewStateResponse,
)


# ============================================================
# serialize_utc_datetime 测试
# ============================================================

class TestSerializeUtcDatetime:
    """验证 datetime 序列化函数。"""

    def test_naive_datetime_converted_to_utc_iso(self):
        """无时区的 datetime 应被标记为 UTC 并返回 ISO 格式。"""
        dt = datetime(2025, 6, 15, 10, 30, 0)
        result = serialize_utc_datetime(dt)
        assert "+00:00" in result or "Z" in result
        assert "2025" in result

    def test_aware_datetime_converted_correctly(self):
        """带时区的 datetime 应正确转换到 UTC。"""
        # CST = UTC+8
        cst = timezone(timedelta(hours=8))
        dt = datetime(2025, 6, 15, 10, 30, 0, tzinfo=cst)
        result = serialize_utc_datetime(dt)
        # 10:30 CST = 02:30 UTC
        assert "02:30" in result or "+00:00" in result

    def test_already_utc_datetime_unchanged(self):
        """已是 UTC 的 datetime 保持不变。"""
        dt = datetime(2025, 6, 15, 10, 30, 0, tzinfo=UTC)
        result = serialize_utc_datetime(dt)
        assert "10:30" in result


# ============================================================
# UserCreate Schema 测试
# ============================================================

class TestUserCreateSchema:
    """验证用户注册 Schema。"""

    def test_valid_input_passes(self):
        """有效输入应通过验证。"""
        user = UserCreate(username="testuser", password="password123")
        assert user.username == "testuser"
        assert user.password == "password123"

    def test_missing_username_fails(self):
        """缺少 username 时应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            UserCreate(password="password123")

    def test_missing_password_fails(self):
        """缺少 password 时应抛出 ValidationError。"""
        with pytest.raises(ValidationError):
            UserCreate(username="testuser")


# ============================================================
# Token Schema 测试
# ============================================================

class TestTokenSchema:
    """验证 Token Schema。"""

    def test_create_token(self):
        """创建 Token 实例。"""
        token = Token(access_token="fake-token-123", token_type="bearer")
        assert token.access_token == "fake-token-123"
        assert token.token_type == "bearer"


# ============================================================
# InterviewStart Schema 测试
# ============================================================

class TestInterviewStartSchema:
    """验证面试开始请求 Schema。"""

    def test_minimal_valid_input(self):
        """仅提供必填字段 role 即可创建。"""
        payload = InterviewStart(role="Java后端开发工程师")
        assert payload.role == "Java后端开发工程师"
        assert payload.difficulty == "medium"
        assert payload.total_rounds == 5

    def test_defaults_applied(self):
        """未提供的可选字段应使用默认值。"""
        payload = InterviewStart(role="Web前端开发工程师")
        assert payload.knowledge_points == []
        assert payload.repo_urls == []
        assert payload.resume_persona is None

    def test_full_config(self):
        """提供所有字段。"""
        payload = InterviewStart(
            role="Python算法工程师",
            difficulty="hard",
            knowledge_points=["机器学习", "深度学习"],
            total_rounds=8,
            repo_urls=["https://github.com/test/repo"],
            resume_persona={"skills": ["Python"]},
        )
        assert payload.difficulty == "hard"
        assert len(payload.knowledge_points) == 2
        assert payload.total_rounds == 8


# ============================================================
# MessageSend / MessageResponse Schema 测试
# ============================================================

class TestMessageSchemas:
    """验证消息相关 Schema。"""

    def test_message_send_valid(self):
        """有效的消息请求。"""
        msg = MessageSend(content="请解释JVM内存模型")
        assert msg.content == "请解释JVM内存模型"

    def test_message_send_missing_content_fails(self):
        """缺少 content 时应失败。"""
        with pytest.raises(ValidationError):
            MessageSend()

    def test_message_response_is_final_defaults_to_false(self):
        """is_final 默认值应为 False。"""
        resp = MessageResponse(
            id=1,
            sender="ai",
            content="你好",
            created_at=datetime(2025, 6, 15, tzinfo=UTC),
        )
        assert resp.is_final is False


# ============================================================
# CodeRunRequest Schema 测试
# ============================================================

class TestCodeRunRequestSchema:
    """验证代码运行请求 Schema。"""

    def test_valid_request(self):
        """有效请求。"""
        req = CodeRunRequest(language="python", source_code="print(1+1)")
        assert req.language == "python"
        assert req.source_code == "print(1+1)"

    def test_missing_language_fails(self):
        """缺少 language 时应失败。"""
        with pytest.raises(ValidationError):
            CodeRunRequest(source_code="print(1+1)")

    def test_missing_source_code_fails(self):
        """缺少 source_code 时应失败。"""
        with pytest.raises(ValidationError):
            CodeRunRequest(language="python")


# ============================================================
# CodeCaseResult Schema 测试
# ============================================================

class TestCodeCaseResultSchema:
    """验证测试用例结果 Schema。"""

    def test_minimal_fields(self):
        """最少字段即可创建。"""
        case = CodeCaseResult(
            index=1,
            is_sample=True,
            passed=True,
            status="Accepted",
        )
        assert case.index == 1
        assert case.passed is True

    def test_optional_fields_default_to_none(self):
        """可选字段默认应为 None。"""
        case = CodeCaseResult(
            index=1,
            is_sample=False,
            passed=False,
            status="Wrong Answer",
        )
        assert case.input is None
        assert case.expected_output is None
        assert case.actual_output is None
        assert case.stderr is None
        assert case.runtime is None
        assert case.memory is None


# ============================================================
# CodeRunResponse / CodeSubmitResponse Schema 测试
# ============================================================

class TestCodeResponseSchemas:
    """验证代码运行/提交响应 Schema。"""

    def test_run_response(self):
        """CodeRunResponse 应包含 results 列表。"""
        resp = CodeRunResponse(
            status="Accepted",
            passed_count=2,
            total_count=2,
            results=[],
        )
        assert resp.status == "Accepted"
        assert resp.passed_count == 2

    def test_submit_response_includes_submission_id(self):
        """CodeSubmitResponse 应包含 submission_id。"""
        resp = CodeSubmitResponse(
            status="Running",
            passed_count=0,
            total_count=3,
            results=[],
            submission_id=42,
        )
        assert resp.submission_id == 42


# ============================================================
# EvaluationDetail Schema 测试
# ============================================================

class TestEvaluationDetailSchema:
    """验证评估详情 Schema。"""

    def test_all_optional_fields_default(self):
        """可选评分字段应有默认值。"""
        detail = EvaluationDetail(
            interview_id=1,
            role="Java后端开发工程师",
            content_score=75.0,
            expression_score=80.0,
            business_scenario_score=70.0,
            problem_solving_score=85.0,
            total_score=77.5,
            highlights=[],
            weaknesses=[],
            recommendations="",
            created_at=datetime(2025, 6, 15, tzinfo=UTC),
        )
        assert detail.speech_rate_score == 0.0
        assert detail.clarity_score == 0.0
        assert detail.confidence_score == 0.0
        assert detail.round_feedback == []
        assert detail.repo_context is None
        assert detail.study_plan is None


# ============================================================
# InterviewStateResponse Schema 测试
# ============================================================

class TestInterviewStateResponseSchema:
    """验证面试状态响应 Schema。"""

    def test_valid_state(self):
        """有效状态响应。"""
        state = InterviewStateResponse(
            interview_id=1,
            status="in_progress",
            phase="introduction",
            knowledge_round_index=0,
            knowledge_round_total=5,
            can_end=True,
        )
        assert state.phase == "introduction"
        assert state.active_code_problem is None
        assert state.active_code_submission_id is None
