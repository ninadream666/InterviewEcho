"""test_models.py — ORM 数据库模型单元测试。

测试目标: app/db/models.py
- utcnow()                    时间戳生成
- User 模型                  CRUD + 唯一约束
- CodeProblem 模型           CRUD + JSON 字段
- CodeTestCase 模型          关联 + is_sample
- CodeSubmission 模型        关联 + 状态字段
- Interview 模型             CRUD + 默认值
- Message 模型               用户/AI 消息
- Evaluation 模型            一对一关联 interview
- VoiceMetrics 模型          语音指标

依赖: conftest.py 提供的 SQLite 测试数据库。
"""

from datetime import datetime, UTC
import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    utcnow,
    User,
    CodeProblem,
    CodeTestCase,
    CodeSubmission,
    Interview,
    Message,
    Evaluation,
    VoiceMetrics,
)
from app.db.session import SessionLocal


# ============================================================
# utcnow 测试
# ============================================================

class TestUtcnow:
    """验证时间戳生成函数。"""

    def test_returns_datetime_object(self):
        """应返回 datetime 对象。"""
        now = utcnow()
        assert isinstance(now, datetime)

    def test_has_no_timezone_info(self):
        """应返回去除时区信息的 UTC 时间。"""
        now = utcnow()
        assert now.tzinfo is None


# ============================================================
# User 模型测试
# ============================================================

class TestUserModel:
    """验证用户模型。"""

    def test_create_user(self):
        """创建用户应成功。"""
        db = SessionLocal()
        try:
            user = User(username="test_model_user", password_hash="hashed_pw")
            db.add(user)
            db.commit()
            db.refresh(user)
            assert user.id is not None
            assert user.username == "test_model_user"
            assert user.created_at is not None
        finally:
            db.rollback()
            db.close()

    def test_unique_username_constraint(self):
        """重复用户名应抛出 IntegrityError。"""
        db = SessionLocal()
        try:
            user1 = User(username="unique_test_user", password_hash="pw1")
            db.add(user1)
            db.commit()
            user2 = User(username="unique_test_user", password_hash="pw2")
            db.add(user2)
            with pytest.raises(IntegrityError):
                db.commit()
        finally:
            db.rollback()
            db.close()

    def test_timestamps_auto_set(self):
        """created_at 应自动设置。"""
        db = SessionLocal()
        try:
            user = User(username="ts_test_user", password_hash="pw")
            db.add(user)
            db.commit()
            db.refresh(user)
            assert user.created_at is not None
        finally:
            db.rollback()
            db.close()


# ============================================================
# CodeProblem 模型测试
# ============================================================

class TestCodeProblemModel:
    """验证代码题目模型。"""

    def test_create_problem_with_minimal_fields(self):
        """最少字段即可创建题目。"""
        db = SessionLocal()
        try:
            problem = CodeProblem(
                title="Test Problem",
                slug="test-problem",
                difficulty="easy",
                description="A test problem",
                input_format="string",
                output_format="string",
                tags="[]",
                samples="[]",
                constraints="[]",
                starter_code="{}",
            )
            db.add(problem)
            db.commit()
            db.refresh(problem)
            assert problem.id is not None
            assert problem.is_active is True
        finally:
            db.rollback()
            db.close()

    def test_tag_json_stored_as_text(self):
        """tags 以 JSON 文本存储。"""
        db = SessionLocal()
        try:
            problem = CodeProblem(
                title="Tag Test",
                slug="tag-test",
                difficulty="medium",
                description="test",
                input_format="none",
                output_format="none",
                tags='["Array", "Hash Table"]',
                samples="[]",
                constraints="[]",
                starter_code="{}",
            )
            db.add(problem)
            db.commit()
            db.refresh(problem)
            assert "Array" in problem.tags
        finally:
            db.rollback()
            db.close()


# ============================================================
# CodeTestCase 模型测试
# ============================================================

class TestCodeTestCaseModel:
    """验证测试用例模型。"""

    def test_create_test_case_linked_to_problem(self):
        """创建关联到题目的测试用例。"""
        db = SessionLocal()
        try:
            problem = CodeProblem(
                title="TestCase Problem",
                slug="testcase-problem",
                difficulty="easy",
                description="test",
                input_format="string",
                output_format="string",
                tags="[]",
                samples="[]",
                constraints="[]",
                starter_code="{}",
            )
            db.add(problem)
            db.commit()
            db.refresh(problem)

            test_case = CodeTestCase(
                problem_id=problem.id,
                input="1 2",
                expected_output="3",
                is_sample=True,
                sort_order=1,
            )
            db.add(test_case)
            db.commit()
            db.refresh(test_case)
            assert test_case.id is not None
            assert test_case.problem_id == problem.id
            assert test_case.is_sample is True
        finally:
            db.rollback()
            db.close()


# ============================================================
# CodeSubmission 模型测试
# ============================================================

class TestCodeSubmissionModel:
    """验证代码提交模型。"""

    def test_create_submission(self):
        """创建提交记录。"""
        db = SessionLocal()
        try:
            user = User(username="submission_user", password_hash="pw")
            db.add(user)
            db.commit()

            problem = CodeProblem(
                title="Submission Problem",
                slug="submission-problem",
                difficulty="medium",
                description="test",
                input_format="none",
                output_format="none",
                tags="[]",
                samples="[]",
                constraints="[]",
                starter_code="{}",
            )
            db.add(problem)
            db.commit()

            submission = CodeSubmission(
                user_id=user.id,
                problem_id=problem.id,
                language="python",
                source_code="print(1+1)",
                status="Running",
                passed_count=0,
                total_count=3,
            )
            db.add(submission)
            db.commit()
            db.refresh(submission)
            assert submission.id is not None
            assert submission.status == "Running"
        finally:
            db.rollback()
            db.close()


# ============================================================
# Interview 模型测试
# ============================================================

class TestInterviewModel:
    """验证面试会话模型。"""

    def test_create_interview_with_defaults(self):
        """使用默认值创建面试会话。"""
        db = SessionLocal()
        try:
            user = User(username="interview_user", password_hash="pw")
            db.add(user)
            db.commit()

            interview = Interview(
                user_id=user.id,
                role="Java后端开发工程师",
                difficulty="medium",
                total_rounds=5,
            )
            db.add(interview)
            db.commit()
            db.refresh(interview)
            assert interview.status == "in_progress"
            assert interview.phase == "introduction"
            assert interview.knowledge_round_index == 0
            assert interview.knowledge_points is None
        finally:
            db.rollback()
            db.close()

    def test_create_with_full_config(self):
        """使用完整配置创建面试。"""
        db = SessionLocal()
        try:
            user = User(username="full_interview_user", password_hash="pw")
            db.add(user)
            db.commit()

            interview = Interview(
                user_id=user.id,
                role="Python算法工程师",
                difficulty="hard",
                total_rounds=8,
                knowledge_points='["ML", "DL"]',
                repo_context='[{"full_name": "test/repo"}]',
                resume_persona='{"skills": ["Python"]}',
            )
            db.add(interview)
            db.commit()
            db.refresh(interview)
            assert interview.difficulty == "hard"
            assert interview.total_rounds == 8
        finally:
            db.rollback()
            db.close()


# ============================================================
# Message 模型测试
# ============================================================

class TestMessageModel:
    """验证消息模型。"""

    def test_create_ai_message(self):
        """创建 AI 消息。"""
        db = SessionLocal()
        try:
            user = User(username="msg_user", password_hash="pw")
            db.add(user)
            db.commit()
            interview = Interview(user_id=user.id, role="Web前端开发工程师")
            db.add(interview)
            db.commit()

            msg = Message(
                interview_id=interview.id,
                sender="ai",
                content="欢迎参加面试",
                category="greeting",
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            assert msg.sender == "ai"
            assert msg.category == "greeting"
        finally:
            db.rollback()
            db.close()

    def test_create_user_message(self):
        """创建用户消息。"""
        db = SessionLocal()
        try:
            user = User(username="user_msg_user", password_hash="pw")
            db.add(user)
            db.commit()
            interview = Interview(user_id=user.id, role="Web前端开发工程师")
            db.add(interview)
            db.commit()

            msg = Message(
                interview_id=interview.id,
                sender="user",
                content="请解释闭包",
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            assert msg.sender == "user"
            assert msg.category is None
        finally:
            db.rollback()
            db.close()


# ============================================================
# Evaluation 模型测试
# ============================================================

class TestEvaluationModel:
    """验证评估模型。"""

    def test_create_evaluation(self):
        """创建评估记录。"""
        db = SessionLocal()
        try:
            user = User(username="eval_user", password_hash="pw")
            db.add(user)
            db.commit()
            interview = Interview(user_id=user.id, role="Java后端开发工程师")
            db.add(interview)
            db.commit()

            evaluation = Evaluation(
                interview_id=interview.id,
                content_score=75.0,
                expression_score=80.0,
                business_scenario_score=70.0,
                problem_solving_score=85.0,
                total_score=77.5,
                report_json="{}",
                recommendations="继续学习JVM",
            )
            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)
            assert evaluation.total_score == 77.5
        finally:
            db.rollback()
            db.close()

    def test_unique_interview_constraint(self):
        """同一 interview 不应有两个 evaluation。"""
        db = SessionLocal()
        try:
            user = User(username="unique_eval_user", password_hash="pw")
            db.add(user)
            db.commit()
            interview = Interview(user_id=user.id, role="Java后端开发工程师")
            db.add(interview)
            db.commit()

            eval1 = Evaluation(
                interview_id=interview.id,
                content_score=70.0,
                expression_score=70.0,
                business_scenario_score=70.0,
                problem_solving_score=70.0,
                total_score=70.0,
            )
            db.add(eval1)
            db.commit()

            eval2 = Evaluation(
                interview_id=interview.id,
                content_score=80.0,
                expression_score=80.0,
                business_scenario_score=80.0,
                problem_solving_score=80.0,
                total_score=80.0,
            )
            db.add(eval2)
            with pytest.raises(IntegrityError):
                db.commit()
        finally:
            db.rollback()
            db.close()


# ============================================================
# VoiceMetrics 模型测试
# ============================================================

class TestVoiceMetricsModel:
    """验证语音指标模型。"""

    def test_create_voice_metrics(self):
        """创建语音指标记录。"""
        db = SessionLocal()
        try:
            user = User(username="voice_user", password_hash="pw")
            db.add(user)
            db.commit()
            interview = Interview(user_id=user.id, role="Web前端开发工程师")
            db.add(interview)
            db.commit()
            msg = Message(interview_id=interview.id, sender="user", content="测试回答")
            db.add(msg)
            db.commit()

            vm = VoiceMetrics(
                interview_id=interview.id,
                message_id=msg.id,
                duration_sec=30.0,
                wpm=200.0,
                pause_ratio=0.15,
                long_pause_count=1,
                filler_total=3,
                pitch_mean=120.0,
                pitch_std=15.0,
                volume_mean=0.05,
                volume_std=0.02,
                raw_json="{}",
            )
            db.add(vm)
            db.commit()
            db.refresh(vm)
            assert vm.wpm == 200.0
            assert vm.filler_total == 3
        finally:
            db.rollback()
            db.close()
