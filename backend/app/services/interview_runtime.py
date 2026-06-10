"""
模块名称：面试运行时引擎（interview_runtime）
功能描述：InterviewEcho 面试系统的核心引擎，管理面试的完整生命周期。

面试状态机流转：
    introduction → resume → repo → code → knowledge → completed
    自我介绍 → 简历深挖 → 项目深挖 → 代码题 → 知识问答 → 结束

核心职责：
1. 面试会话管理（开始/结束/放弃/状态查询）
2. 多阶段对话流转（根据配置自动跳转到下一阶段）
3. 代码题判题集成（调用 Judge0 服务 + LLM 代码审查）
4. 语音消息处理（Whisper 转录 + 语音指标采集）
5. 面试评估生成（综合 LLM 评估 + 表达分析 + 学习计划）

被以下位置调用：
- app/api/routes/interview_session.py（会话管理路由）
- app/api/routes/interview_messages.py（消息发送路由）
- app/api/routes/interview_aux.py（辅助功能路由）
- app/api/routes/interview_reports.py（报告路由）
"""

import json
import os
import random
import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models, schemas
from app.services.interview_catalog import (
    ROLES,
    get_knowledge_questions,
    get_role_info,
    get_role_sections as load_role_sections,
)
from app.core.llm_service import (
    evaluate_full_interview,
    generate_code_review,
    generate_free_question,
    generate_repo_questions,
    generate_resume_question,
    generate_study_plan,
    polish_text,
)
from app.services.audio_analysis import analyze_audio
from app.services.interrupt_policy import evaluate_interrupt
from app.services.judge0_service import Judge0Unavailable, LANGUAGE_IDS, judge0_service, trim_output, truncate_text
from app.services.repo_analyzer import analyze_repo
from app.services.resume_parser import parse_resume_pdf, parse_resume_text
from app.services.stt_service import stt_service

# ============================================================
# 面试阶段常量
# ============================================================
PHASE_INTRODUCTION = "introduction"   # 自我介绍阶段
PHASE_RESUME = "resume"              # 简历深挖阶段
PHASE_REPO = "repo"                  # 项目/仓库深挖阶段
PHASE_CODE = "code"                  # 代码题阶段
PHASE_KNOWLEDGE = "knowledge"        # 知识问答阶段
PHASE_COMPLETED = "completed"        # 面试已完成
RUNNING_SUBMISSION_STATUS = "Running"  # Judge0 判题中状态
FINAL_BLESSING = "本次面试到这里就结束了，感谢你的认真作答，祝你求职顺利、拿到心仪 offer！"


# ============================================================
# 角色/章节辅助函数（对外暴露）
# ============================================================

def get_roles() -> list[dict]:
    """获取所有可用的面试岗位列表。"""
    return ROLES


def get_role_sections(role_key: str) -> list[str]:
    """获取指定岗位的知识点章节列表。"""
    return load_role_sections(role_key)


# ============================================================
# 简历解析
# ============================================================

async def parse_resume_payload(file: Optional[UploadFile], text: Optional[str]) -> dict:
    """
    解析简历上传载荷，支持 PDF 文件和纯文本两种格式。

    Args:
        file: 上传的 PDF 文件（可选）。
        text: 纯文本简历内容（可选）。

    Returns:
        dict: {"persona": {...}, "warning": ""}，warning 非空时表示解析结果不理想。

    Raises:
        HTTPException 400: 既未提供文件也未提供文本，或文件读取失败。
    """
    if file is not None and (file.filename or "").strip():
        try:
            file_bytes = await file.read()
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"读取上传文件失败：{exc}") from exc
        if not file_bytes:
            raise HTTPException(status_code=400, detail="上传文件为空")
        filename = (file.filename or "").lower()
        persona = await parse_resume_pdf(file_bytes) if filename.endswith(".pdf") else await parse_resume_text(
            file_bytes.decode("utf-8", errors="ignore")
        )
    elif text and text.strip():
        persona = await parse_resume_text(text)
    else:
        raise HTTPException(status_code=400, detail="请上传 PDF 文件或提交纯文本简历")

    warning = ""
    if not (persona.get("skills") or persona.get("projects") or persona.get("summary")):
        warning = "简历解析未提取到有效信息，将不会注入 persona 上下文"
    return {"persona": persona, "warning": warning}


# ============================================================
# GitHub 仓库分析
# ============================================================

async def analyze_repo_preview(url: str) -> dict:
    """
    预览分析 GitHub 仓库，获取项目摘要信息。

    Args:
        url: GitHub 仓库 URL。

    Returns:
        dict: 仓库分析摘要。

    Raises:
        HTTPException 400: URL 为空或无法抓取。
    """
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL 不能为空")
    summary = await analyze_repo(url)
    if summary is None:
        raise HTTPException(
            status_code=400,
            detail="无法抓取该仓库。请确认：1) 仓库是公开的 GitHub 仓库；2) URL 格式为 https://github.com/owner/repo；3) 网络连接正常。",
        )
    return summary


# ============================================================
# JSON 序列化/反序列化辅助函数
# ============================================================

def _load_json(value: Optional[str], fallback):
    """
    安全地从 JSON 字符串反序列化，失败时返回 fallback 默认值。

    Args:
        value: JSON 字符串（可为 None）。
        fallback: 解析失败时的默认返回值。
    """
    if not value:
        return fallback
    try:
        return json.loads(value)
    except Exception:
        return fallback


def _dump_json(value) -> str:
    """将 Python 对象序列化为 JSON 字符串（ensure_ascii=False 保留中文）。"""
    return json.dumps(value, ensure_ascii=False)


# ============================================================
# 面试数据库查询辅助函数
# ============================================================

def _get_interview_for_user(db: Session, user_id: int, interview_id: int) -> models.Interview:
    """
    按用户 ID 和面试 ID 查询面试记录，同时校验归属权限。

    Raises:
        HTTPException 404: 面试不存在或不属于该用户。
    """
    interview = (
        db.query(models.Interview)
        .filter(models.Interview.id == interview_id, models.Interview.user_id == user_id)
        .first()
    )
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found or unauthorized")
    return interview


def _load_asked_titles(interview: models.Interview) -> list[str]:
    """从面试记录中读取已问过的问题标题列表（防重复提问）。"""
    return _load_json(interview.asked_question_titles, [])


def _append_asked_title(interview: models.Interview, title: str) -> None:
    """将新问题的标题追加到已问列表中（去重）。"""
    titles = _load_asked_titles(interview)
    if title not in titles:
        titles.append(title)
        interview.asked_question_titles = _dump_json(titles)


# ============================================================
# 代码题辅助函数
# ============================================================

def _find_active_code_problem(db: Session) -> models.CodeProblem:
    """
    从题库中随机选取一道激活的代码题。

    Raises:
        HTTPException 503: 题库为空时需要先执行种子脚本。
    """
    problems = (
        db.query(models.CodeProblem)
        .filter(models.CodeProblem.is_active == True)
        .order_by(models.CodeProblem.order_index.asc(), models.CodeProblem.id.asc())
        .all()
    )
    if not problems:
        raise HTTPException(status_code=503, detail="代码题库为空，请先执行 python -m app.cli.seed_code_problems")
    return random.choice(problems)


def _count_problem_cases(db: Session, problem_id: int) -> tuple[int, int]:
    """
    统计指定题目的样例数量和测试用例总数。

    Returns:
        tuple[int, int]: (样例数, 总用例数)。
    """
    cases = db.query(models.CodeTestCase).filter(models.CodeTestCase.problem_id == problem_id).all()
    sample_count = sum(1 for item in cases if item.is_sample)
    return sample_count, len(cases)


def _build_code_problem_detail(db: Session, user_id: int, problem: Optional[models.CodeProblem]) -> Optional[schemas.CodeProblemDetail]:
    """
    将 ORM 模型转换为前端需要的 CodeProblemDetail Schema。

    会额外查询：
    - 样例/测试用例数量
    - 当前用户是否已解答（solved 标记）
    """
    if problem is None:
        return None
    sample_count, test_count = _count_problem_cases(db, problem.id)
    solved = (
        db.query(models.CodeSubmission.id)
        .filter(
            models.CodeSubmission.user_id == user_id,
            models.CodeSubmission.problem_id == problem.id,
            models.CodeSubmission.status == "Accepted",
        )
        .first()
        is not None
    )
    return schemas.CodeProblemDetail(
        id=problem.id,
        title=problem.title,
        slug=problem.slug,
        difficulty=problem.difficulty,
        tags=_load_json(problem.tags, []),
        source=problem.source or "Hot100",
        solved=solved,
        judgable=test_count > 0,
        sample_count=sample_count,
        test_count=test_count,
        description=problem.description,
        input_format=problem.input_format,
        output_format=problem.output_format,
        samples=_load_json(problem.samples, []),
        constraints=_load_json(problem.constraints, []),
        starter_code=_load_json(problem.starter_code, {}),
    )


# ============================================================
# 面试状态构建
# ============================================================

def _build_interview_state(db: Session, user_id: int, interview: models.Interview) -> schemas.InterviewStateResponse:
    """
    构建面试当前状态的完整响应（含代码题详情、轮次信息等）。

    前端通过轮询此接口来更新 UI 状态（如显示当前阶段、代码题、是否可以结束等）。
    """
    problem = None
    if interview.active_code_problem_id:
        problem = db.query(models.CodeProblem).filter(models.CodeProblem.id == interview.active_code_problem_id).first()
    return schemas.InterviewStateResponse(
        interview_id=interview.id,
        status=interview.status,
        phase=interview.phase or PHASE_INTRODUCTION,
        knowledge_round_index=interview.knowledge_round_index or 0,
        knowledge_round_total=interview.total_rounds or 0,
        can_end=(interview.phase == PHASE_COMPLETED or interview.status == "completed"),
        active_code_problem=_build_code_problem_detail(db, user_id, problem),
        active_code_submission_id=interview.active_code_submission_id,
    )


# ============================================================
# 阶段流转逻辑
# ============================================================

def _resolve_next_phase(interview: models.Interview) -> str:
    """
    根据面试配置决定自我介绍后的下一阶段。

    优先级：简历深挖 > 项目深挖 > 代码题。
    只有在配置了对应上下文（resume_persona / custom_questions）时才会进入前两个阶段。
    """
    if interview.resume_persona:
        return PHASE_RESUME
    if interview.custom_questions:
        return PHASE_REPO
    return PHASE_CODE


def _select_repo_question(interview: models.Interview) -> dict:
    """
    从自定义仓库问题中选一道未问过的题目。

    如果所有题目都已问过，返回一道通用追问。
    """
    asked_titles = set(_load_asked_titles(interview))
    questions = _load_json(interview.custom_questions, [])
    available = [item for item in questions if item.get("question") and item.get("question") not in asked_titles]
    if available:
        return random.choice(available)
    return {"question": "能深入谈谈你在这个项目中的具体技术贡献吗？", "key_points": []}


async def _select_resume_question(interview: models.Interview) -> dict:
    """
    调用 LLM 根据候选人画像生成一道简历深挖问题。

    失败时返回通用追问。
    """
    persona = _load_json(interview.resume_persona, {})
    question = await generate_resume_question(persona)
    return question or {"question": "能详细介绍一下你最有代表性的项目经历吗？", "key_points": []}


def _load_role_questions(interview: models.Interview, knowledge_points: Optional[list[str]] = None) -> list[dict]:
    """
    从知识库加载与当前面试岗位/难度/知识点匹配的题目列表。

    加载策略：
    1. 优先按指定的知识点筛选
    2. 知识点筛选无结果时回退到全量题目
    3. 当前难度无题目时降级尝试其他难度（中等 → 简单 → 困难）
    """
    role_key = get_role_info(interview.role)["key"]
    selected_sections = knowledge_points if knowledge_points is not None else _load_json(interview.knowledge_points, [])
    questions = get_knowledge_questions(role_key, interview.difficulty, selected_sections)
    if not questions and selected_sections:
        questions = get_knowledge_questions(role_key, interview.difficulty, None)
    if not questions:
        for fallback_diff in ["中等", "简单", "困难"]:
            questions = get_knowledge_questions(role_key, fallback_diff, selected_sections or None)
            if questions:
                break
    return questions


async def _generate_non_duplicate_knowledge_question(interview: models.Interview, asked_titles: list[str]) -> dict:
    """
    当知识库题目用完时，调用 LLM 生成一道不重复的知识问答题。

    最多尝试 3 次 LLM 生成，若均重复则构造兜底题目。
    """
    role_key = get_role_info(interview.role)["key"]
    selected_sections = _load_json(interview.knowledge_points, [])
    knowledge_points = selected_sections or load_role_sections(role_key)
    knowledge_points_str = ", ".join(knowledge_points)
    for _ in range(3):
        free_question = await generate_free_question(
            role=interview.role,
            category="知识问答",
            difficulty=interview.difficulty,
            asked_titles=asked_titles,
            knowledge_points=knowledge_points_str,
        )
        if free_question and free_question.get("question") and free_question["question"] not in asked_titles:
            return free_question

    focus = knowledge_points[(len(asked_titles) or 0) % len(knowledge_points)] if knowledge_points else interview.role
    fallback = f"补充知识题 {len(asked_titles) + 1}：请你结合 {focus}，说明它的核心原理、典型应用场景，以及在实际项目中的落地注意点。"
    return {"question": fallback, "key_points": [focus]}


async def _select_next_knowledge_question(interview: models.Interview) -> dict:
    """
    选取下一道知识问答题目。

    优先从知识库中选未问过的，题库耗尽时调用 LLM 生成。
    """
    asked_titles = _load_asked_titles(interview)
    candidates = _load_role_questions(interview)
    available = [item for item in candidates if item.get("question") and item["question"] not in asked_titles]
    if available:
        return random.choice(available)
    return await _generate_non_duplicate_knowledge_question(interview, asked_titles)


# ============================================================
# AI 消息创建
# ============================================================

def _create_ai_message(
    db: Session,
    interview: models.Interview,
    content: str,
    category: str,
    is_final: bool = False,
) -> schemas.MessageResponse:
    """
    创建一条 AI 面试官消息并写入数据库。

    Args:
        db: 数据库会话。
        interview: 面试记录。
        content: 消息文本内容。
        category: 消息类别（如 introduction / knowledge_question / code_question / closing）。
        is_final: 是否为最后一条消息（面试结束）。

    Returns:
        MessageResponse: 包含 is_final 标记的消息响应。
    """
    ai_message = models.Message(interview_id=interview.id, sender="ai", content=content, category=category)
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    response = schemas.MessageResponse.model_validate(ai_message)
    response.is_final = is_final
    return response


def _build_code_prompt(problem: models.CodeProblem) -> str:
    """构建进入代码题阶段时给候选人的提示语。"""
    tags = "、".join(_load_json(problem.tags, [])[:3])
    return (
        f"接下来进入固定代码题环节。我为你随机抽到了一道编程题《{problem.title}》。"
        f"{'这道题主要考察 ' + tags + '。' if tags else ''}"
        "请切换到代码编辑器完成作答，先运行样例确认思路，再提交给我做点评。"
    )


async def _move_to_knowledge_or_close(db: Session, interview: models.Interview, prefix_text: str = "") -> schemas.MessageResponse:
    """
    代码题回答完毕后，转入知识问答阶段或结束面试。

    逻辑：
    - 若 total_rounds > 0：选取一道知识问答题目，进入 knowledge 阶段
    - 若 total_rounds <= 0：直接结束面试，发送祝福语
    """
    total_rounds = interview.total_rounds or 0
    if total_rounds <= 0:
        interview.phase = PHASE_COMPLETED
        interview.status = "completed"
        interview.end_time = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        content = f"{prefix_text}\n\n{FINAL_BLESSING}".strip()
        return _create_ai_message(db, interview, content, "closing", True)

    knowledge_question = await _select_next_knowledge_question(interview)
    interview.phase = PHASE_KNOWLEDGE
    interview.knowledge_round_index = 1
    _append_asked_title(interview, knowledge_question["question"])
    db.commit()
    content = f"{prefix_text}\n\n接下来进入知识问答：{knowledge_question['question']}".strip() if prefix_text else knowledge_question["question"]
    return _create_ai_message(db, interview, content, "knowledge_question")


# ============================================================
# 面试生命周期管理
# ============================================================

async def start_interview(db: Session, user_id: int, payload: schemas.InterviewStart) -> models.Interview:
    """
    开始一场新的模拟面试。

    流程：
    1. 可选：分析 GitHub 仓库并生成定制问题
    2. 可选：保存简历解析后的候选人画像
    3. 随机抽取一道代码题
    4. 创建面试记录，发送开场白（自我介绍引导）

    Args:
        db: 数据库会话。
        user_id: 当前登录用户 ID。
        payload: 面试配置（角色、难度、知识点、轮次、仓库 URL、简历画像）。

    Returns:
        Interview: 新创建的面试 ORM 对象。
    """
    knowledge_points_json = _dump_json(payload.knowledge_points or [])
    repo_context_json = None
    custom_questions_json = None

    # 1. 分析 GitHub 仓库（最多 3 个），生成定制深挖问题
    repo_urls = (payload.repo_urls or [])[:3]
    if repo_urls:
        repo_summaries = []
        all_custom_questions = []
        for url in repo_urls:
            if not url or not url.strip():
                continue
            summary = await analyze_repo(url)
            if summary is None:
                continue
            repo_summaries.append(summary)
            all_custom_questions.extend(await generate_repo_questions(payload.role, summary))
        if repo_summaries:
            repo_context_json = _dump_json(repo_summaries)
        if all_custom_questions:
            custom_questions_json = _dump_json(all_custom_questions)

    # 2. 保存简历画像
    resume_persona_json = _dump_json(payload.resume_persona) if payload.resume_persona else None
    # 3. 随机抽取代码题
    code_problem = _find_active_code_problem(db)

    # 4. 创建面试记录
    interview = models.Interview(
        user_id=user_id,
        role=payload.role,
        difficulty=payload.difficulty,
        knowledge_points=knowledge_points_json,
        total_rounds=payload.total_rounds,
        status="in_progress",
        phase=PHASE_INTRODUCTION,
        knowledge_round_index=0,
        repo_context=repo_context_json,
        custom_questions=custom_questions_json,
        resume_persona=resume_persona_json,
        active_code_problem_id=code_problem.id,
        active_code_submission_id=None,
        asked_question_titles="[]",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # 发送开场白
    greeting = f"你好，我是你的{payload.role}面试官。很高兴见到你。在正式开始前，请先做一个简单的自我介绍。"
    db.add(models.Message(interview_id=interview.id, sender="ai", content=greeting, category="introduction"))
    db.commit()
    return interview


def get_incomplete_interview(db: Session, user_id: int) -> schemas.IncompleteInterviewResponse:
    """
    查询用户是否有未完成的面试。

    用于前端登录后自动恢复未完成的面试会话。
    """
    interview = (
        db.query(models.Interview)
        .filter(models.Interview.user_id == user_id, models.Interview.status == "in_progress")
        .order_by(models.Interview.start_time.desc(), models.Interview.id.desc())
        .first()
    )
    if not interview:
        return schemas.IncompleteInterviewResponse(has_incomplete=False, interview=None)
    return schemas.IncompleteInterviewResponse(
        has_incomplete=True,
        interview=schemas.IncompleteInterviewDetail.model_validate(interview),
    )


def discard_interview(db: Session, user_id: int, interview_id: int) -> dict:
    """放弃当前面试（物理删除）。"""
    interview = _get_interview_for_user(db, user_id, interview_id)
    db.delete(interview)
    db.commit()
    return {"message": "Interview discarded successfully."}


def get_interview_messages(db: Session, user_id: int, interview_id: int):
    """获取指定面试的所有对话消息（按时间顺序）。"""
    interview = _get_interview_for_user(db, user_id, interview_id)
    del interview  # 仅校验权限，不需要使用对象
    return (
        db.query(models.Message)
        .filter(models.Message.interview_id == interview_id)
        .order_by(models.Message.created_at.asc())
        .all()
    )


def get_interview_state(db: Session, user_id: int, interview_id: int) -> schemas.InterviewStateResponse:
    """获取面试当前状态（前端轮询用）。"""
    interview = _get_interview_for_user(db, user_id, interview_id)
    return _build_interview_state(db, user_id, interview)


def get_evaluation_detail(db: Session, user_id: int, interview_id: int) -> schemas.EvaluationDetail:
    """
    获取面试评估详情。

    从 Evaluation 表和 report_json 中提取完整报告数据，
    包括评分、亮点、弱点、建议、学习计划等。
    """
    eval_record = (
        db.query(models.Evaluation)
        .join(models.Interview)
        .filter(models.Evaluation.interview_id == interview_id, models.Interview.user_id == user_id)
        .first()
    )
    if not eval_record:
        raise HTTPException(status_code=404, detail="Evaluation not found or unauthorized")

    report_data = {}
    if eval_record.report_json:
        try:
            report_data = json.loads(eval_record.report_json)
        except Exception:
            report_data = {}

    interview_obj = eval_record.interview
    repo_context = _load_json(interview_obj.repo_context, None)
    custom_questions = _load_json(interview_obj.custom_questions, None)
    round_feedback = report_data.get("round_feedback") or []
    if not round_feedback:
        evaluations = report_data.get("evaluations") or []
        for index, item in enumerate(evaluations, start=1):
            round_feedback.append(
                {
                    "round": int(item.get("round") or index),
                    "question": item.get("question", ""),
                    "answer_summary": item.get("answer_summary", ""),
                    "strengths": item.get("strengths") or [],
                    "issues": item.get("issues") or [],
                    "improved_example": item.get("improved_example", ""),
                }
            )

    return schemas.EvaluationDetail(
        interview_id=eval_record.interview_id,
        role=eval_record.interview.role,
        content_score=eval_record.content_score,
        expression_score=eval_record.expression_score,
        business_scenario_score=eval_record.business_scenario_score,
        problem_solving_score=eval_record.problem_solving_score,
        total_score=eval_record.total_score,
        speech_rate_score=eval_record.speech_rate_score,
        clarity_score=eval_record.clarity_score,
        confidence_score=eval_record.confidence_score,
        expression_metrics=report_data.get("expression_metrics"),
        repo_context=repo_context,
        custom_questions=custom_questions,
        study_plan=report_data.get("study_plan"),
        highlights=report_data.get("highlights", report_data.get("strengths", [])),
        weaknesses=report_data.get("weaknesses", []),
        recommendations=eval_record.recommendations or report_data.get("improvement_suggestions", "继续加油！"),
        scores=report_data.get("scores"),
        round_feedback=round_feedback,
        created_at=eval_record.created_at,
    )


def get_history(db: Session, user_id: int) -> list[schemas.EvaluationSummary]:
    """获取用户的历史面试评估摘要列表（按时间倒序）。"""
    results = (
        db.query(models.Evaluation)
        .join(models.Interview)
        .filter(models.Interview.user_id == user_id, models.Interview.status == "completed")
        .order_by(models.Evaluation.created_at.desc())
        .all()
    )
    return [
        schemas.EvaluationSummary(
            id=item.interview_id,
            role=item.interview.role,
            difficulty=item.interview.difficulty,
            total_score=item.total_score,
            created_at=item.created_at,
        )
        for item in results
    ]


# ============================================================
# 核心消息处理 —— 面试对话状态机
# ============================================================

async def process_message_logic(
    interview_id: int,
    content: str,
    db: Session,
    user_id: int,
    duration_sec: Optional[float] = None,
):
    """
    处理用户消息的核心状态机 —— 根据当前面试阶段执行对应逻辑。

    这是整个面试引擎最重要的函数，负责：
    1. 保存用户消息到数据库
    2. 根据当前 phase 决定面试官的回应
    3. 驱动阶段流转（introduction → resume → repo → code → knowledge）
    4. 在知识问答阶段检测是否需要打断/跳过

    Args:
        interview_id: 面试 ID。
        content: 用户消息文本。
        db: 数据库会话。
        user_id: 用户 ID（权限校验）。
        duration_sec: 语音消息的时长（用于打断策略判定），文字消息为 None。

    Returns:
        tuple[MessageResponse, int | None]: (AI 回复消息, 用户消息 ID)。
        用户消息 ID 用于后续 VoiceMetrics 关联。
    """
    interview = _get_interview_for_user(db, user_id, interview_id)

    # 面试已结束，阻止继续对话
    if interview.phase == PHASE_COMPLETED or interview.status == "completed":
        response = _create_ai_message(db, interview, "本场面试已经结束，请直接生成并查看报告。", "closing", True)
        return response, None

    # 保存用户消息
    user_msg = models.Message(interview_id=interview_id, sender="user", content=content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # ---- 代码题阶段：用户不能在聊天框回答，必须使用代码编辑器 ----
    if interview.phase == PHASE_CODE:
        reminder = '当前处于代码题环节，请在代码编辑器中完成作答并点击「提交代码给面试官」，我会根据判题结果继续推进。'
        response = _create_ai_message(db, interview, reminder, "code_question")
        return response, user_msg.id

    # ---- 自我介绍阶段 → 根据配置跳转到简历/项目/代码阶段 ----
    if interview.phase == PHASE_INTRODUCTION:
        next_phase = _resolve_next_phase(interview)
        if next_phase == PHASE_RESUME:
            resume_question = await _select_resume_question(interview)
            interview.phase = PHASE_RESUME
            _append_asked_title(interview, resume_question["question"])
            db.commit()
            response = _create_ai_message(db, interview, resume_question["question"], "resume_question")
            return response, user_msg.id
        if next_phase == PHASE_REPO:
            repo_question = _select_repo_question(interview)
            interview.phase = PHASE_REPO
            _append_asked_title(interview, repo_question["question"])
            db.commit()
            response = _create_ai_message(db, interview, repo_question["question"], "repo_question")
            return response, user_msg.id
        if next_phase == PHASE_CODE:
            problem = db.query(models.CodeProblem).filter(models.CodeProblem.id == interview.active_code_problem_id).first()
            interview.phase = PHASE_CODE
            db.commit()
            response = _create_ai_message(db, interview, _build_code_prompt(problem), "code_question")
            return response, user_msg.id

    # ---- 简历深挖阶段 → 进入项目深挖或代码题 ----
    if interview.phase == PHASE_RESUME:
        if interview.custom_questions:
            repo_question = _select_repo_question(interview)
            interview.phase = PHASE_REPO
            _append_asked_title(interview, repo_question["question"])
            db.commit()
            response = _create_ai_message(db, interview, repo_question["question"], "repo_question")
            return response, user_msg.id
        interview.phase = PHASE_CODE
        db.commit()
        problem = db.query(models.CodeProblem).filter(models.CodeProblem.id == interview.active_code_problem_id).first()
        response = _create_ai_message(db, interview, _build_code_prompt(problem), "code_question")
        return response, user_msg.id

    # ---- 项目深挖阶段 → 进入代码题 ----
    if interview.phase == PHASE_REPO:
        interview.phase = PHASE_CODE
        db.commit()
        problem = db.query(models.CodeProblem).filter(models.CodeProblem.id == interview.active_code_problem_id).first()
        response = _create_ai_message(db, interview, _build_code_prompt(problem), "code_question")
        return response, user_msg.id

    # ---- 知识问答阶段 ----
    if interview.phase == PHASE_KNOWLEDGE:
        total_rounds = interview.total_rounds or 0
        # 达到总轮次上限 → 结束面试
        if (interview.knowledge_round_index or 0) >= total_rounds:
            interview.phase = PHASE_COMPLETED
            interview.status = "completed"
            interview.end_time = datetime.now(UTC).replace(tzinfo=None)
            db.commit()
            response = _create_ai_message(db, interview, FINAL_BLESSING, "closing", True)
            return response, user_msg.id

        # 检测是否需要打断（离题/超时/赘述）
        try:
            interrupt = evaluate_interrupt(
                user_text=content,
                duration_sec=duration_sec,
                current_question="",
                current_question_key_points=[],
            )
        except Exception:
            interrupt = None

        # 选取下一道知识问答题
        next_question = await _select_next_knowledge_question(interview)
        interview.knowledge_round_index = (interview.knowledge_round_index or 0) + 1
        _append_asked_title(interview, next_question["question"])
        db.commit()

        prefix = ""
        if interrupt and interrupt.triggered:
            prefix = "我先简短记录一下你的回答，我们继续下一题。"
        content = f"{prefix}\n\n{next_question['question']}".strip() if prefix else next_question["question"]
        response = _create_ai_message(db, interview, content, "knowledge_question")
        return response, user_msg.id

    # 兜底（不应到达）
    response = _create_ai_message(db, interview, "我们继续下一步。", "knowledge_question")
    return response, user_msg.id


# ============================================================
# 代码题判题相关函数
# ============================================================

def _validate_code_request(payload: schemas.CodeRunRequest) -> tuple[str, str]:
    """
    校验代码运行/提��请求的合法性。

    Returns:
        tuple[str, str]: (语言, 源码)。

    Raises:
        HTTPException 400: 语言不支持 / 代码为空 / 代码超长。
    """
    language = (payload.language or "").strip().lower()
    if language not in LANGUAGE_IDS:
        raise HTTPException(status_code=400, detail="暂不支持该语言")
    source_code = payload.source_code or ""
    if not source_code.strip():
        raise HTTPException(status_code=400, detail="请先输入完整程序")
    if len(source_code) > settings.CODE_MAX_SOURCE_LENGTH:
        raise HTTPException(status_code=400, detail=f"代码长度不能超过 {settings.CODE_MAX_SOURCE_LENGTH} 个字符")
    return language, source_code


def _status_from_case(status_id: int, raw_status: str, passed: bool) -> str:
    """将 Judge0 状态码 + 输出比对结果转换为可读状态字符串。"""
    if status_id == 3 and passed:
        return "Accepted"
    if status_id == 3:
        return "Wrong Answer"
    return raw_status


def _build_case_result(index: int, case: models.CodeTestCase, result) -> schemas.CodeCaseResult:
    """
    将单个 Judge0 判题结果 + 测试用例信息组装为前端可用的 CodeCaseResult。

    包含：输入、期望输出、实际输出、是否通过、状态、错误信息等。
    """
    actual = trim_output(result.stdout)
    expected = trim_output(case.expected_output)
    passed = result.status_id == 3 and actual == expected
    message = None
    if result.compile_output:
        message = "编译失败，请检查完整程序、类名或语法。"
    elif result.stderr or result.message:
        message = result.stderr or result.message
    elif result.status_id == 3 and not passed:
        message = "输出与期望不一致。"

    return schemas.CodeCaseResult(
        index=index,
        is_sample=bool(case.is_sample),
        passed=passed,
        status=_status_from_case(result.status_id, result.raw_status, passed),
        status_description=result.status_description,
        input=case.input,
        expected_output=expected,
        actual_output=actual,
        stderr=truncate_text(result.stderr),
        compile_output=truncate_text(result.compile_output),
        runtime=result.time,
        memory=result.memory,
        message=message,
    )


async def _run_interview_code_cases(cases: list[models.CodeTestCase], language: str, source_code: str) -> tuple[str, int, int, list[schemas.CodeCaseResult]]:
    """
    依次运行所有测试用例（顺序执行）。

    遇到编译错误或超时立即终止后续用例。

    Returns:
        tuple[str, int, int, list]: (最终状态, 通过数, 总数, 各用例结果列表)。
    """
    results = []
    for index, case in enumerate(cases, start=1):
        result = await judge0_service.run_code(language, source_code, case.input)
        payload = _build_case_result(index, case, result)
        results.append(payload)
        # 编译错误 / 超时 / 运行时错误 → 立即终止
        if payload.status in {"Compile Error", "Time Limit Exceeded"} or payload.status.startswith("Runtime"):
            return payload.status, sum(1 for item in results if item.passed), len(cases), results

    passed_count = sum(1 for item in results if item.passed)
    total_count = len(cases)
    status = "Accepted" if passed_count == total_count else next((item.status for item in results if not item.passed), "Wrong Answer")
    return status, passed_count, total_count, results


def _summarize_interview_submission(results: list[schemas.CodeCaseResult], status: str) -> dict:
    """汇总所有测试用例结果，提取 stdout/stderr/compile_output/runtime/memory。"""
    stdout = "\n\n".join([item.actual_output or "" for item in results if item.actual_output]) or None
    stderr = "\n\n".join([item.stderr or "" for item in results if item.stderr]) or None
    compile_output = "\n\n".join([item.compile_output or "" for item in results if item.compile_output]) or None
    runtime_values = [item.runtime for item in results if item.runtime is not None]
    memory_values = [item.memory for item in results if item.memory is not None]
    return {
        "status": status,
        "runtime": round(sum(runtime_values), 4) if runtime_values else None,
        "memory": max(memory_values) if memory_values else None,
        "stdout": truncate_text(stdout),
        "stderr": truncate_text(stderr),
        "compile_output": truncate_text(compile_output),
        "result_json": truncate_text(_dump_json([item.model_dump() for item in results]), settings.CODE_OUTPUT_LIMIT * 3),
    }


def _build_judge_summary(status: str, passed_count: int, total_count: int, results: list[schemas.CodeCaseResult]) -> str:
    """构建判题摘要文本，供 LLM 代码审查使用。"""
    key_message = next((item.message for item in results if item.message), "无")
    return (
        f"判题状态：{status}\n"
        f"通过用例：{passed_count}/{total_count}\n"
        f"关键反馈：{key_message}"
    )


async def submit_interview_code(
    db: Session,
    user_id: int,
    interview_id: int,
    payload: schemas.CodeRunRequest,
) -> schemas.InterviewCodeSubmitResponse:
    """
    面试中提交代码答案。

    流程：
    1. 校验当前面试是否处于代码题阶段
    2. 调用 Judge0 执行所有测试用例
    3. 保存提交记录
    4. 调用 LLM 对代码做深度点评
    5. 转入知识问答阶段或结束面试

    Returns:
        InterviewCodeSubmitResponse: 包含判题结果、LLM 点评和 AI 回复消息。
    """
    interview = _get_interview_for_user(db, user_id, interview_id)
    if interview.phase != PHASE_CODE:
        raise HTTPException(status_code=400, detail="当前面试不在代码作答阶段")
    if not interview.active_code_problem_id:
        raise HTTPException(status_code=400, detail="当前面试未绑定代码题")

    problem = db.query(models.CodeProblem).filter(models.CodeProblem.id == interview.active_code_problem_id).first()
    if problem is None:
        raise HTTPException(status_code=404, detail="Code problem not found")

    # 1. 校验代码
    language, source_code = _validate_code_request(payload)
    # 2. 获取测试用例
    cases = (
        db.query(models.CodeTestCase)
        .filter(models.CodeTestCase.problem_id == problem.id)
        .order_by(models.CodeTestCase.sort_order.asc(), models.CodeTestCase.id.asc())
        .limit(settings.CODE_MAX_TEST_CASES)
        .all()
    )
    if not cases:
        raise HTTPException(status_code=400, detail="这道题暂未配置判题用例")

    # 3. 运行判题
    try:
        status, passed_count, total_count, results = await _run_interview_code_cases(cases, language, source_code)
    except Judge0Unavailable as exc:
        raise HTTPException(status_code=503, detail=f"判题服务不可用：{exc}") from exc

    # 4. 保存用户提交消息
    summary = _summarize_interview_submission(results, status)
    user_summary = (
        f"我已提交题目《{problem.title}》的 {language} 解答。"
        f" 判题结果为 {status}，通过 {passed_count}/{total_count} 个用例，请继续点评。"
    )
    db.add(models.Message(interview_id=interview_id, sender="user", content=user_summary, category="code_submission"))
    db.commit()

    # 5. 保存提交记录
    submission = models.CodeSubmission(
        user_id=user_id,
        problem_id=problem.id,
        language=language,
        source_code=source_code,
        status=summary["status"],
        runtime=summary["runtime"],
        memory=summary["memory"],
        passed_count=passed_count,
        total_count=total_count,
        stdout=summary["stdout"],
        stderr=summary["stderr"],
        compile_output=summary["compile_output"],
        result_json=summary["result_json"],
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # 6. LLM 代码审查
    interview.active_code_submission_id = submission.id
    review_text = await generate_code_review(
        role=interview.role,
        problem_title=problem.title,
        problem_description=problem.description,
        language=language,
        source_code=source_code,
        result_summary=_build_judge_summary(status, passed_count, total_count, results),
    )

    # 7. 转入知识问答或结束
    response = await _move_to_knowledge_or_close(db, interview, review_text)
    return schemas.InterviewCodeSubmitResponse(
        submission_id=submission.id,
        status=status,
        passed_count=passed_count,
        total_count=total_count,
        results=results,
        ai_message=response,
    )


# ============================================================
# 语音消息处理
# ============================================================

async def handle_voice_message(interview_id: int, upload: UploadFile, db: Session, user_id: int) -> schemas.VoiceResponse:
    """
    处理语音消息上传。

    流程：
    1. 将上传的音频文件保存到临时目录
    2. 调用 Whisper 进行语音转文字（含时间戳）
    3. 调用 LLM 润色转写文本
    4. 调用 process_message_logic 进入对话状态机
    5. 调用音频分析模块提取语音指标并存储

    Args:
        interview_id: 面试 ID。
        upload: 上传的音频文件。
        db: 数据库会话。
        user_id: 用户 ID。

    Returns:
        VoiceResponse: 包含转写文本和 AI 回复消息。
    """
    temp_dir = tempfile.gettempdir()
    extension = os.path.splitext(upload.filename)[1] if upload.filename else ".webm"
    temp_file_path = os.path.join(temp_dir, f"voice_{uuid.uuid4()}{extension}")

    try:
        # 1. 保存音频文件到临时目录
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)

        # 2. Whisper 转录（含时间戳）
        whisper_result = stt_service.transcribe_detailed(temp_file_path)
        if not whisper_result or not whisper_result.get("text"):
            raise HTTPException(status_code=400, detail="语音转录失败，请重试或手动输入")
        raw_transcript = whisper_result["text"]
        # 3. LLM 润色转写文本
        transcript = await polish_text(raw_transcript)

        # 4. 提取语音时长
        voice_duration_sec = None
        try:
            segments = whisper_result.get("segments") or []
            if segments:
                voice_duration_sec = float(segments[-1].get("end", 0.0))
        except Exception:
            voice_duration_sec = None

        # 5. 进入对话状态机
        ai_message, user_message_id = await process_message_logic(
            interview_id=interview_id,
            content=transcript,
            db=db,
            user_id=user_id,
            duration_sec=voice_duration_sec,
        )

        # 6. 音频分析 + 语音指标存储
        try:
            metrics = analyze_audio(temp_file_path, whisper_result)
            if metrics is not None and user_message_id is not None:
                db.add(
                    models.VoiceMetrics(
                        interview_id=interview_id,
                        message_id=user_message_id,
                        duration_sec=metrics["duration_sec"],
                        wpm=metrics["wpm"],
                        pause_ratio=metrics["pause_ratio"],
                        long_pause_count=metrics["long_pause_count"],
                        filler_total=metrics["filler_total"],
                        pitch_mean=metrics["pitch_mean"],
                        pitch_std=metrics["pitch_std"],
                        volume_mean=metrics["volume_mean"],
                        volume_std=metrics["volume_std"],
                        raw_json=_dump_json(metrics),
                    )
                )
                db.commit()
        except Exception:
            pass  # 音频分析失败不阻塞主流程

        return schemas.VoiceResponse(transcription=transcript, ai_message=ai_message)
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass


# ============================================================
# 面试结束与评估生成
# ============================================================

async def end_interview(db: Session, user_id: int, interview_id: int) -> dict:
    """
    结束面试并生成综合评估报告。

    流程：
    1. 将面试状态标记为 completed
    2. 调用 LLM 评估全部对话（内容维度：content / business_scenario / problem_solving）
    3. 从 VoiceMetrics 表中读取所有语音指标，调用表达评分模块
    4. 合并内容评分和表达评分，计算综合总分
    5. 可选：调用 LLM 生成个性化学习计划
    6. 保存/更新 Evaluation 记录

    Returns:
        dict: 包含 message 和 evaluation 详情的字典。
    """
    from evaluation.expression_evaluator import score_expression

    # 1. 标记面试结束
    interview = _get_interview_for_user(db, user_id, interview_id)
    interview.status = "completed"
    interview.phase = PHASE_COMPLETED
    interview.end_time = datetime.now(UTC).replace(tzinfo=None)
    db.commit()

    # 2. LLM 综合评估（内容维度）
    messages = (
        db.query(models.Message)
        .filter(models.Message.interview_id == interview_id)
        .order_by(models.Message.created_at.asc())
        .all()
    )
    evaluation_data = await evaluate_full_interview(
        messages,
        role=interview.role,
        resume_persona=_load_json(interview.resume_persona, None),
    )

    # 3. 语音指标采集 + 表达评分
    voice_records = db.query(models.VoiceMetrics).filter(models.VoiceMetrics.interview_id == interview_id).all()
    metrics_list = []
    for record in voice_records:
        if record.raw_json:
            try:
                metrics_list.append(json.loads(record.raw_json))
            except Exception:
                pass
    expression_result = score_expression(metrics_list, interview.role)

    # 4. 合并评分
    speech_rate_score = 0.0
    clarity_score = 0.0
    confidence_score = 0.0
    if expression_result:
        evaluation_data["expression_score"] = expression_result.get("expression_score", evaluation_data["expression_score"])
        speech_rate_score = expression_result.get("speech_rate_score", 0.0)
        clarity_score = expression_result.get("clarity_score", 0.0)
        confidence_score = expression_result.get("confidence_score", 0.0)
        feedback = expression_result.get("feedback", {})
        extra_feedback = (
            "\n\n【表达分析建议】\n"
            f"- 语速：{feedback.get('speech_rate', '')}\n"
            f"- 清晰度：{feedback.get('clarity', '')}\n"
            f"- 自信度：{feedback.get('confidence', '')}"
        )
        evaluation_data["recommendations"] = evaluation_data.get("recommendations", "") + extra_feedback
        evaluation_data["expression_metrics"] = expression_result

        # 重新计算综合总分（取所有有评分维度的均值）
        active_scores = [
            evaluation_data.get("content_score", 0),
            evaluation_data.get("expression_score", 0),
            evaluation_data.get("business_scenario_score", 0),
            evaluation_data.get("problem_solving_score", 0),
        ]
        valid_scores = [float(score) for score in active_scores if score is not None and float(score) > 0]
        if valid_scores:
            evaluation_data["total_score"] = round(sum(valid_scores) / len(valid_scores), 1)

    # 5. 生成学习计划（失败不影响主流程）
    try:
        study_plan = await generate_study_plan(interview.role, evaluation_data, messages)
        if study_plan:
            evaluation_data["study_plan"] = study_plan
    except Exception:
        pass

    # 6. 保存/更新评估记录
    eval_record = db.query(models.Evaluation).filter(models.Evaluation.interview_id == interview_id).first()
    fields = {
        "content_score": evaluation_data.get("content_score", 0),
        "expression_score": evaluation_data.get("expression_score", 0),
        "business_scenario_score": evaluation_data.get("business_scenario_score", 0),
        "problem_solving_score": evaluation_data.get("problem_solving_score", 0),
        "total_score": evaluation_data.get("total_score", 0),
        "speech_rate_score": speech_rate_score,
        "clarity_score": clarity_score,
        "confidence_score": confidence_score,
        "report_json": _dump_json(evaluation_data),
        "recommendations": evaluation_data.get("recommendations", ""),
    }
    if eval_record is None:
        eval_record = models.Evaluation(interview_id=interview_id, **fields)
        db.add(eval_record)
    else:
        for key, value in fields.items():
            setattr(eval_record, key, value)
    db.commit()
    db.refresh(eval_record)

    return {
        "message": "Interview ended and evaluated successfully.",
        "evaluation": get_evaluation_detail(db, user_id, interview_id).model_dump(),
    }
