"""
模块名称：Pydantic 数据校验模式（schemas）
功能描述：定义 InterviewEcho 全部 API 请求/响应的数据结构。
继承自 ApiSchema（统一配置了 ORM 模式和时间戳序列化），
涵盖以下业务域：
- 用户认证（注册/登录/Token）
- 面试管理（开始/状态/消息/结束）
- 代码练习（题目列表/详情/运行/提交）
- 评估报告（评分/维度/建议）
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


def serialize_utc_datetime(value: datetime) -> str:
    """将 datetime 对象统一转换为 UTC 时区的 ISO 格式字符串。"""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return value.isoformat()


class ApiSchema(BaseModel):
    """
    所有 API Schema 的基类。

    配置说明：
    - from_attributes=True：允许直接从 ORM 对象创建 Schema（替代旧版 orm_mode）
    - json_encoders：datetime 字段输出时自动转为 ISO 格式
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: serialize_utc_datetime},
    )


# ============================================================
# 用户认证相关 Schema
# ============================================================

class UserCreate(ApiSchema):
    """用户注册请求。"""
    username: str
    password: str


class UserResponse(ApiSchema):
    """用户信息响应。"""
    id: int
    username: str
    created_at: datetime


class Token(ApiSchema):
    """登录成功返回的 Token。"""
    access_token: str
    token_type: str


# ============================================================
# 面试管理相关 Schema
# ============================================================

class InterviewStart(ApiSchema):
    """开始面试的请求参数。"""
    role: str
    difficulty: Optional[str] = "medium"
    knowledge_points: Optional[List[str]] = []
    total_rounds: Optional[int] = 5
    repo_urls: Optional[List[str]] = []
    resume_persona: Optional[dict] = None


class ResumePersona(ApiSchema):
    """简历解析后的候选人画像。"""
    skills: List[str] = []
    projects: List[dict] = []
    work_years: int = 0
    education: str = ""
    summary: str = ""


class RepoAnalyzeRequest(ApiSchema):
    """GitHub 仓库分析请求。"""
    url: str


class InterviewResponse(ApiSchema):
    """面试会话基本信息响应。"""
    id: int
    user_id: int
    role: str
    status: str
    start_time: datetime


class IncompleteInterviewDetail(ApiSchema):
    """未完成面试的详情。"""
    id: int
    role: str
    status: str
    start_time: datetime


class IncompleteInterviewResponse(ApiSchema):
    """检查是否有未完成面试的响应。"""
    has_incomplete: bool
    interview: Optional[IncompleteInterviewDetail] = None


class MessageSend(ApiSchema):
    """发送消息请求。"""
    content: str


class MessageResponse(ApiSchema):
    """消息响应（含是否最后一轮标记）。"""
    id: int
    sender: str
    content: str
    created_at: datetime
    is_final: bool = False


# ============================================================
# 评估报告相关 Schema
# ============================================================

class EvaluationSummary(ApiSchema):
    """评估摘要（用于列表展示）。"""
    id: int
    role: str
    difficulty: str
    total_score: float
    created_at: datetime


class EvaluationRoundFeedback(ApiSchema):
    """逐轮回答改进示例。"""
    round: int
    question: str
    answer_summary: str
    strengths: List[str] = []
    issues: List[str] = []
    improved_example: str


class EvaluationDetail(ApiSchema):
    """评估详情（完整报告数据）。"""
    interview_id: int
    role: str
    # ---- 评分 ----
    content_score: float
    expression_score: float
    business_scenario_score: float
    problem_solving_score: float
    total_score: float
    speech_rate_score: Optional[float] = 0.0
    clarity_score: Optional[float] = 0.0
    confidence_score: Optional[float] = 0.0
    # ---- 分析结果 ----
    highlights: List[str]
    weaknesses: List[str]
    recommendations: str
    scores: Optional[dict] = None
    expression_metrics: Optional[dict] = None
    round_feedback: List[EvaluationRoundFeedback] = []
    # ---- 上下文字段（v3/v4 扩展） ----
    repo_context: Optional[List[dict]] = None
    custom_questions: Optional[List[dict]] = None
    study_plan: Optional[dict] = None
    # ---- 时间戳 ----
    created_at: datetime


# ============================================================
# 代码练习相关 Schema
# ============================================================

class CodeProblemListItem(ApiSchema):
    """代码题目列表项（概览信息）。"""
    id: int
    title: str
    slug: str
    difficulty: str
    tags: List[str]
    source: str = "Hot100"
    solved: bool = False
    judgable: bool = False
    sample_count: int = 0
    test_count: int = 0


class CodeProblemDetail(CodeProblemListItem):
    """代码题目详情（完整内容）。"""
    description: str
    input_format: str
    output_format: str
    samples: List[Dict[str, Any]]
    constraints: List[str]
    starter_code: Dict[str, str]


class CodeProblemListResponse(ApiSchema):
    """代码题目列表响应。"""
    items: List[CodeProblemListItem]
    tags: List[str]
    total: int


class CodeRunRequest(ApiSchema):
    """代码运行请求。"""
    language: str
    source_code: str


class CodeCaseResult(ApiSchema):
    """单个测试用例的运行结果。"""
    index: int
    is_sample: bool
    passed: bool
    status: str
    status_description: Optional[str] = None
    input: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    runtime: Optional[float] = None
    memory: Optional[int] = None
    message: Optional[str] = None


class CodeRunResponse(ApiSchema):
    """代码运行响应（所有测试用例结果汇总）。"""
    status: str
    passed_count: int
    total_count: int
    results: List[CodeCaseResult]


class CodeSubmitResponse(CodeRunResponse):
    """代码提交响应（含 submission_id）。"""
    submission_id: int


class CodeSubmissionItem(ApiSchema):
    """提交记录列表项。"""
    id: int
    problem_id: int
    problem_title: Optional[str] = None
    language: str
    status: str
    runtime: Optional[float] = None
    memory: Optional[int] = None
    passed_count: int
    total_count: int
    created_at: datetime


class CodeSubmissionDetail(CodeSubmissionItem):
    """提交记录详情（含源码和所有测试结果）。"""
    source_code: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    compile_output: Optional[str] = None
    results: Optional[List[CodeCaseResult]] = None


# ============================================================
# 面试状态相关 Schema（依赖上述代码题 Schema，放在最后定义）
# ============================================================

class InterviewStateResponse(ApiSchema):
    """面试当前状态的响应。"""
    interview_id: int
    status: str
    phase: str
    knowledge_round_index: int
    knowledge_round_total: int
    can_end: bool
    active_code_problem: Optional[CodeProblemDetail] = None
    active_code_submission_id: Optional[int] = None


class VoiceResponse(ApiSchema):
    """语音消息处理后的响应（含转写文本和 AI 回复）。"""
    transcription: str
    ai_message: MessageResponse


class InterviewCodeSubmitResponse(CodeSubmitResponse):
    """面试中提交代码后的响应（含 AI 反馈消息）。"""
    ai_message: MessageResponse
