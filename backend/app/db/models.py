"""
模块名称：数据库 ORM 模型（models）
功能描述：定义 InterviewEcho 全部数据库表结构的 SQLAlchemy ORM 模型。
包含以下核心实体：
- User：用户账号
- CodeProblem / CodeTestCase / CodeSubmission：代码题库与判题记录
- Question：面试题库
- Interview：面试会话
- Message：面试对话消息
- Evaluation：面试评估结果
- VoiceMetrics：语音特征指标
"""

from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP, Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


def utcnow() -> datetime:
    """获取当前 UTC 时间（去除时区信息），作为数据库时间戳的默认值。"""
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    """用户表，存储账号基本信息。"""
    __tablename__ = "users"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 账号信息 ----
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # ---- 时间戳 ----
    created_at = Column(TIMESTAMP, default=utcnow)


class CodeProblem(Base):
    """代码题目表，存储编程练习题目的完整信息。"""
    __tablename__ = "code_problems"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 基本信息 ----
    title = Column(String(120), nullable=False)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    difficulty = Column(String(20), nullable=False)
    tags = Column(Text, nullable=False)
    # ---- 题目内容 ----
    description = Column(Text, nullable=False)
    input_format = Column(Text, nullable=False)
    output_format = Column(Text, nullable=False)
    samples = Column(Text, nullable=False)
    constraints = Column(Text, nullable=False)
    starter_code = Column(Text, nullable=False)
    # ---- 元数据 ----
    source = Column(String(50), default="Hot100")
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    # ---- 时间戳 ----
    created_at = Column(TIMESTAMP, default=utcnow)
    updated_at = Column(TIMESTAMP, default=utcnow, onupdate=utcnow)

    # ---- 关联关系 ----
    test_cases = relationship("CodeTestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("CodeSubmission", back_populates="problem")


class CodeTestCase(Base):
    """代码测试用例表，存储每个题目的输入输出测试数据。"""
    __tablename__ = "code_test_cases"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 关联 ----
    problem_id = Column(Integer, ForeignKey("code_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    # ---- 测试数据 ----
    input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_sample = Column(Boolean, default=False)
    explanation = Column(Text, nullable=True)
    # ---- 排序 ----
    sort_order = Column(Integer, default=0)
    # ---- 时间戳 ----
    created_at = Column(TIMESTAMP, default=utcnow)

    # ---- 关联关系 ----
    problem = relationship("CodeProblem", back_populates="test_cases")


class CodeSubmission(Base):
    """代码提交记录表，存储用户每次提交代码的判题结果。"""
    __tablename__ = "code_submissions"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 关联 ----
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(Integer, ForeignKey("code_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    # ---- 提交信息 ----
    language = Column(String(30), nullable=False)
    source_code = Column(Text, nullable=False)
    # ---- 判题结果 ----
    status = Column(String(40), nullable=False)
    runtime = Column(Float, nullable=True)
    memory = Column(Integer, nullable=True)
    passed_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    compile_output = Column(Text, nullable=True)
    result_json = Column(Text, nullable=True)
    # ---- 时间戳 ----
    created_at = Column(TIMESTAMP, default=utcnow)

    # ---- 关联关系 ----
    user = relationship("User")
    problem = relationship("CodeProblem", back_populates="submissions")


class Question(Base):
    """面试题库表，存储各岗位各类型的面试题目及参考答案。"""
    __tablename__ = "questions"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 题目信息 ----
    role = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    reference_answer = Column(Text)
    # ---- 时间戳 ----
    created_at = Column(TIMESTAMP, default=utcnow)


class Interview(Base):
    """
    面试会话表，存储每次模拟面试的完整状态。

    关键字段说明：
    - phase：面试阶段（introduction / knowledge / code / conclusion）
    - status：会话状态（in_progress / finished / abandoned）
    - repo_context：GitHub 项目分析上下文（JSON）
    - resume_persona：简历解析后的候选人画像（JSON）
    - asked_question_titles：已问过的问题标题列表（JSON）
    - active_code_problem_id：当前激活的代码题 ID
    """
    __tablename__ = "interviews"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 关联 ----
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # ---- 面试配置 ----
    role = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=True)
    knowledge_points = Column(Text, nullable=True)
    total_rounds = Column(Integer, default=5)
    # ---- 状态控制 ----
    status = Column(String(20), default="in_progress")
    phase = Column(String(20), default="introduction")
    knowledge_round_index = Column(Integer, default=0)
    # ---- 时间 ----
    start_time = Column(TIMESTAMP, default=utcnow)
    end_time = Column(TIMESTAMP, nullable=True)
    # ---- 上下文数据（JSON 格式） ----
    repo_context = Column(Text, nullable=True)
    custom_questions = Column(Text, nullable=True)
    resume_persona = Column(Text, nullable=True)
    asked_question_titles = Column(Text, nullable=True)
    # ---- 代码题关联 ----
    active_code_problem_id = Column(Integer, nullable=True)
    active_code_submission_id = Column(Integer, nullable=True)

    # ---- 关联关系 ----
    user = relationship("User")
    evaluations = relationship("Evaluation", uselist=False, back_populates="interview")


class Message(Base):
    """面试消息表，存储面试过程中面试官与候选人的每一轮对话。"""
    __tablename__ = "messages"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 关联 ----
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    # ---- 消息内容 ----
    sender = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)
    audio_path = Column(String(255), nullable=True)
    # ---- 时间戳 ----
    created_at = Column(TIMESTAMP, default=utcnow)


class Evaluation(Base):
    """
    面试评估表，存储整场面试的综合评分。

    评分维度：
    - content_score：内容质量
    - expression_score：表达能力
    - business_scenario_score：业务场景分析
    - problem_solving_score：问题解决能力
    - speech_rate_score / clarity_score / confidence_score：语音维度专项评分
    - total_score：综合总分
    - report_json：完整评估报告（JSON，含亮点、弱点、建议等）
    """
    __tablename__ = "evaluations"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 关联（一对一） ----
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True)
    # ---- 综合评分 ----
    content_score = Column(Float, default=0.0)
    expression_score = Column(Float, default=0.0)
    business_scenario_score = Column(Float, default=0.0)
    problem_solving_score = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    # ---- 语音维度评分 ----
    speech_rate_score = Column(Float, default=0.0)
    clarity_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    # ---- 报告内容 ----
    report_json = Column(Text)
    recommendations = Column(Text)
    # ---- 时间戳 ----
    created_at = Column(TIMESTAMP, default=utcnow)

    # ---- 关联关系 ----
    interview = relationship("Interview", back_populates="evaluations")


class VoiceMetrics(Base):
    """
    语音特征指标表，存储候选人每次回答的语音分析原始数据。

    采集维度：
    - wpm：语速（每分钟字数）
    - pause_ratio：停顿比例
    - long_pause_count：长停顿次数
    - filler_total：填充词（语气词）数量
    - pitch_mean / pitch_std：音调均值/标准差
    - volume_mean / volume_std：音量均值/标准差
    """
    __tablename__ = "voice_metrics"

    # ---- 主键 ----
    id = Column(Integer, primary_key=True, index=True)
    # ---- 关联 ----
    interview_id = Column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    # ---- 语音指标 ----
    duration_sec = Column(Float)
    wpm = Column(Float)
    pause_ratio = Column(Float)
    long_pause_count = Column(Integer, default=0)
    filler_total = Column(Integer, default=0)
    pitch_mean = Column(Float)
    pitch_std = Column(Float)
    volume_mean = Column(Float)
    volume_std = Column(Float)
    # ---- 原始数据 ----
    raw_json = Column(Text)
    # ---- 时间戳 ----
    created_at = Column(TIMESTAMP, default=utcnow)
