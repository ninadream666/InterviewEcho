import asyncio
import json
import uuid

from app.db import models
from app.db.session import SessionLocal
from core import llm_service
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_evaluate_full_interview_includes_resume_summary(monkeypatch):
    captured = {}

    def fake_prompt(**kwargs):
        captured.update(kwargs)
        return "prompt"

    class FakeCompletions:
        async def create(self, **kwargs):
            payload = {
                "evaluations": [
                    {
                        "round": 1,
                        "question": "请介绍一下你最近做的项目。",
                        "answer_summary": "候选人介绍了简历中的推荐系统项目。",
                        "content_score": 82,
                        "expression_score": 80,
                        "business_scenario_score": 78,
                        "problem_solving_score": None,
                        "strengths": ["能说明项目目标"],
                        "issues": ["关键指标不够具体"],
                        "improved_example": "我最近主导了一个推荐系统迭代项目，目标是提升首页 CTR 8%。",
                    }
                ],
                "overall_summary": {
                    "strengths": ["项目经历相关性较强"],
                    "weaknesses": ["指标量化不足"],
                    "recommendations": "补足结果指标。",
                },
            }

            class _Message:
                content = json.dumps(payload, ensure_ascii=False)

            class _Choice:
                message = _Message()

            class _Response:
                choices = [_Choice()]

            return _Response()

    monkeypatch.setattr(llm_service.prompt_manager, "get_evaluator_prompt", fake_prompt)
    monkeypatch.setattr(llm_service.client.chat, "completions", FakeCompletions())
    async def fake_rag_retrieve(history, top_k=3):
        return ""

    monkeypatch.setattr(llm_service, "_rag_retrieve_for_evaluation", fake_rag_retrieve)
    monkeypatch.setattr(llm_service, "_load_excellent_answers_for_role", lambda role: "参考答案")

    history = [
        type("Msg", (), {"sender": "ai", "content": "请介绍一下你最近做的项目。", "category": "resume_question"})(),
        type("Msg", (), {"sender": "user", "content": "我做过一个推荐系统项目。", "category": None})(),
    ]
    resume_persona = {
        "education": "本科",
        "work_years": 2,
        "skills": ["Python", "推荐系统"],
        "summary": "偏算法和推荐方向",
        "projects": [{"name": "推荐系统", "description": "负责召回与排序优化"}],
    }

    result = asyncio.run(llm_service.evaluate_full_interview(history, role="Python算法工程师", resume_persona=resume_persona))

    assert "推荐系统" in captured["resume_summary"]
    assert result["round_feedback"][0]["improved_example"].startswith("我最近主导了一个推荐系统迭代项目")


def test_evaluate_full_interview_backfills_summary_fields(monkeypatch):
    class FakeCompletions:
        async def create(self, **kwargs):
            payload = {
                "evaluations": [
                    {
                        "round": 1,
                        "question": "JVM 内存结构有哪些？",
                        "answer_summary": "提到了堆和栈。",
                        "content_score": 70,
                        "expression_score": 68,
                        "business_scenario_score": None,
                        "problem_solving_score": 72,
                        "strengths": ["知道堆和栈的基本职责"],
                        "issues": ["没有展开方法区、程序计数器与线程共享关系"],
                        "improved_example": "可以先按线程私有区和线程共享区来回答 JVM 内存结构。",
                    }
                ],
                "overall_summary": {},
            }

            class _Message:
                content = json.dumps(payload, ensure_ascii=False)

            class _Choice:
                message = _Message()

            class _Response:
                choices = [_Choice()]

            return _Response()

    monkeypatch.setattr(llm_service.client.chat, "completions", FakeCompletions())
    async def fake_rag_retrieve(history, top_k=3):
        return ""

    monkeypatch.setattr(llm_service, "_rag_retrieve_for_evaluation", fake_rag_retrieve)
    monkeypatch.setattr(llm_service, "_load_excellent_answers_for_role", lambda role: "参考答案")
    monkeypatch.setattr(llm_service.prompt_manager, "get_evaluator_prompt", lambda **kwargs: "prompt")

    history = [
        type("Msg", (), {"sender": "ai", "content": "JVM 内存结构有哪些？", "category": "problem_solving"})(),
        type("Msg", (), {"sender": "user", "content": "我知道堆和栈。", "category": None})(),
    ]

    result = asyncio.run(llm_service.evaluate_full_interview(history, role="Java后端开发工程师", resume_persona=None))

    assert result["highlights"] == ["知道堆和栈的基本职责"]
    assert result["weaknesses"] == ["没有展开方法区、程序计数器与线程共享关系"]
    assert result["recommendations"]


def test_generate_study_plan_returns_fallback_when_llm_fails(monkeypatch):
    class FakeCompletions:
        async def create(self, **kwargs):
            raise RuntimeError("network down")

    monkeypatch.setattr(llm_service.client.chat, "completions", FakeCompletions())

    history = [
        type("Msg", (), {"sender": "ai", "content": "请解释线程池参数。", "category": "problem_solving"})(),
        type("Msg", (), {"sender": "user", "content": "我答得不太完整。", "category": None})(),
    ]
    evaluation_data = {
        "total_score": 72,
        "content_score": 70,
        "expression_score": 74,
        "business_scenario_score": 0,
        "problem_solving_score": 72,
        "weaknesses": ["线程池参数含义和拒绝策略掌握不牢", "回答结构不够清晰"],
    }

    result = asyncio.run(llm_service.generate_study_plan("Java后端开发工程师", evaluation_data, history))

    assert result is not None
    assert len(result["weak_areas"]) >= 1
    assert len(result["plan"]) >= 3
    assert len(result["quick_wins"]) >= 1


def test_fetch_evaluation_returns_round_feedback():
    db = SessionLocal()
    try:
        username = f"round_feedback_user_{uuid.uuid4().hex[:8]}"
        user = models.User(username=username, password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        interview = models.Interview(user_id=user.id, role="Java后端开发工程师", difficulty="中等", status="completed")
        db.add(interview)
        db.commit()
        db.refresh(interview)

        evaluation = models.Evaluation(
            interview_id=interview.id,
            content_score=81,
            expression_score=77,
            business_scenario_score=75,
            problem_solving_score=83,
            total_score=79,
            recommendations="补充量化指标",
            report_json=json.dumps(
                {
                    "highlights": ["基础不错"],
                    "weaknesses": ["回答不够量化"],
                    "round_feedback": [
                        {
                            "round": 1,
                            "question": "请解释一下 JVM 内存模型。",
                            "answer_summary": "回答覆盖了堆和栈，但遗漏线程共享区。",
                            "strengths": ["知道堆和栈的职责"],
                            "issues": ["缺少线程共享区和回收机制说明"],
                            "improved_example": "JVM 内存模型可以先分为线程私有区和线程共享区两大类。",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
        )
        db.add(evaluation)
        db.commit()
        user_id = user.id
        interview_id = interview.id
    finally:
        db.close()

    response = client.get(f"/api/interview/{interview_id}/evaluation", headers={"Authorization": f"Bearer fake-token-{user_id}"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["round_feedback"]) == 1
    assert payload["round_feedback"][0]["question"] == "请解释一下 JVM 内存模型。"


def test_fetch_evaluation_backfills_missing_study_plan():
    db = SessionLocal()
    try:
        username = f"study_plan_user_{uuid.uuid4().hex[:8]}"
        user = models.User(username=username, password_hash="x")
        db.add(user)
        db.commit()
        db.refresh(user)

        interview = models.Interview(user_id=user.id, role="Python算法工程师", difficulty="中等", status="completed")
        db.add(interview)
        db.commit()
        db.refresh(interview)

        evaluation = models.Evaluation(
            interview_id=interview.id,
            content_score=76,
            expression_score=74,
            business_scenario_score=0,
            problem_solving_score=78,
            total_score=76,
            recommendations="加强算法题复盘",
            report_json=json.dumps(
                {
                    "highlights": ["基础思路较完整"],
                    "weaknesses": ["滑动窗口边界处理不稳定", "回答中复杂度分析不够明确"],
                },
                ensure_ascii=False,
            ),
        )
        db.add(evaluation)
        db.commit()
        user_id = user.id
        interview_id = interview.id
    finally:
        db.close()

    response = client.get(f"/api/interview/{interview_id}/evaluation", headers={"Authorization": f"Bearer fake-token-{user_id}"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["study_plan"] is not None
    assert len(payload["study_plan"]["plan"]) >= 1
