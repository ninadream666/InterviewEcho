"""
模块名称：LLM 大语言模型服务（llm_service）
功能描述：封装与 OpenAI 兼容 API 的全部交互逻辑，是面试系统 AI 能力的核心引擎。

核心职责：
1. 对话生成（generate_llm_response）：面试官追问/跳题决策
2. 文本润色（polish_text）：对 Whisper 转写文本添加标点、修正错词
3. 定制问题生成（generate_repo_questions / generate_resume_question / generate_free_question）
4. 代码审查（generate_code_review）：对提交的代码做点评
5. 综合评估（evaluate_full_interview）：内容维度打分 + 亮点/弱点提取
6. 学习计划（generate_study_plan）：根据弱项生成个性化提升方案

配置：
- LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 均从 app.core.config.settings 读取
- 使用 AsyncOpenAI 客户端，支持 DeepSeek 等兼容 API
- 所有 LLM 调用失败时降级兜底，不阻塞主流程
"""

import os
import json
from typing import Any
from openai import AsyncOpenAI
from core.config import settings
from core.prompts import prompt_manager
from services.rag_service import rag_service

# 全局 AsyncOpenAI 客户端（复用连接池）
client = AsyncOpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL
)


def _ensure_text_list(value: Any, *, fallback: list[str] | None = None) -> list[str]:
    """将任意输入规整为非空字符串列表。"""
    items = value if isinstance(value, list) else []
    normalized = [str(item).strip() for item in items if str(item).strip()]
    if normalized:
        return normalized
    return list(fallback or [])


def _derive_overall_summary(evaluations: list[dict]) -> tuple[list[str], list[str]]:
    """从逐轮评估中补齐整体亮点与待提升项。"""
    strengths: list[str] = []
    issues: list[str] = []
    for item in evaluations:
        strengths.extend(_ensure_text_list(item.get("strengths")))
        issues.extend(_ensure_text_list(item.get("issues")))

    dedup_strengths = list(dict.fromkeys(strengths))[:4]
    dedup_issues = list(dict.fromkeys(issues))[:4]
    return dedup_strengths, dedup_issues


def normalize_evaluation_result(data: dict | None) -> dict:
    """规整评估结果，确保报告关键区块始终可展示。"""
    payload = data if isinstance(data, dict) else {}
    evaluations = payload.get("evaluations") if isinstance(payload.get("evaluations"), list) else []
    if isinstance(payload.get("round_feedback"), list) and payload.get("round_feedback"):
        round_feedback = payload.get("round_feedback")
    else:
        round_feedback = _normalize_round_feedback(evaluations)
    summary = payload.get("overall_summary") if isinstance(payload.get("overall_summary"), dict) else {}
    derived_strengths, derived_issues = _derive_overall_summary(evaluations)

    highlights = _ensure_text_list(
        payload.get("highlights", summary.get("strengths")),
        fallback=derived_strengths or ["有一定基础，能够完成主要回答。"],
    )
    weaknesses = _ensure_text_list(
        payload.get("weaknesses", summary.get("weaknesses")),
        fallback=derived_issues or ["当前报告生成不完整，建议重新生成一次评估以获得更细诊断。"],
    )
    recommendations = str(
        payload.get("recommendations")
        or summary.get("recommendations")
        or "建议围绕薄弱点做专项复盘，并继续通过模拟面试巩固表达。"
    ).strip()

    normalized = {
        "content_score": float(payload.get("content_score") or 0),
        "expression_score": float(payload.get("expression_score") or 0),
        "business_scenario_score": float(payload.get("business_scenario_score") or 0),
        "problem_solving_score": float(payload.get("problem_solving_score") or 0),
        "total_score": float(payload.get("total_score") or 0),
        "highlights": highlights,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "evaluations": evaluations,
        "round_feedback": round_feedback,
    }

    for optional_key in ("expression_metrics", "study_plan", "scores"):
        if payload.get(optional_key) is not None:
            normalized[optional_key] = payload.get(optional_key)

    return normalized


def _build_fallback_study_plan(role: str, evaluation_data: dict) -> dict:
    """当 LLM 学习计划生成失败时，构造一个稳定可展示的回退计划。"""
    weakness_items = _ensure_text_list(evaluation_data.get("weaknesses"))
    focus_areas = weakness_items[:3] or [
        f"{role}基础知识体系梳理" if role else "岗位基础知识体系梳理",
        "结构化表达与回答复盘",
        "限时题与手写代码训练",
    ]
    weak_areas = []
    for index, area in enumerate(focus_areas, start=1):
        weak_areas.append(
            {
                "area": area[:40],
                "severity": "高" if index == 1 else "中",
                "diagnosis": area,
            }
        )

    plan = [
        {
            "week": 1,
            "focus": "补齐核心知识点",
            "tasks": [
                f"围绕“{focus_areas[0]}”整理 1 份不少于 20 条的知识清单，并逐条补足原理说明。",
                "针对最近一次面试中回答不完整的问题，补写 3 个 STAR/技术原理版标准答案。",
                "完成 2 道与目标岗位相关的中等难度题，并口述每步思路与复杂度。",
            ],
            "resources": [
                {"type": "article", "title": "项目相关官方文档", "note": "对照薄弱点逐节阅读并做笔记"},
                {"type": "video", "title": "目标岗位高频面试题讲解", "note": "挑 2 个对应薄弱主题观看并复述"},
            ],
        },
        {
            "week": 2,
            "focus": "专项训练与输出",
            "tasks": [
                f"针对“{focus_areas[min(1, len(focus_areas) - 1)]}”完成 1 次专题复盘，输出 800 字总结。",
                "录制 3 段 3 分钟模拟回答，检查语速、停顿和逻辑连接词使用情况。",
                "选择 1 个真实项目模块，补充设计权衡、性能瓶颈和优化方案说明。",
            ],
            "resources": [
                {"type": "book", "title": "深入理解计算机系统 / 对应岗位经典书籍", "note": "精读与薄弱点相关章节"},
                {"type": "course", "title": "面试表达训练课程", "note": "重点练习结构化表达和追问应对"},
            ],
        },
        {
            "week": 3,
            "focus": "模拟面试与查漏补缺",
            "tasks": [
                "进行 1 次完整模拟面试，记录每题得失分点并形成复盘表。",
                f"围绕“{focus_areas[min(2, len(focus_areas) - 1)]}”再补做 2 道题或 2 个知识点口述演练。",
                "把本周所有薄弱问题整理成一页速记卡，下一轮面试前集中回顾。",
            ],
            "resources": [
                {"type": "article", "title": "岗位面经合集", "note": "筛选 10 个高频追问进行自测"},
            ],
        },
    ]

    quick_wins = [
        "本周就能做：挑 3 道上一轮没答好的问题，分别写出 150 字改进答案（30 分钟）",
        "本周就能做：录一段 3 分钟自我介绍并回听，删掉多余语气词（30 分钟）",
        "本周就能做：完成 1 道限时手写题并复盘复杂度（45 分钟）",
    ]
    return {"weak_areas": weak_areas, "plan": plan, "quick_wins": quick_wins}

async def generate_llm_response(role, question, expected_points, conversation_history, target_next_question, difficulty="medium", knowledge_points="", force_next_instruction=""):
    """
    Generate conversational follow-up or next question using AI logic.
    Returns: {"action": "FOLLOW_UP" | "MOVE_NEXT", "text": "..."}
    """
    # 1. Query RAG for expert context
    # Use the current question and the last user message as query for better relevance
    last_user_msg = ""
    if isinstance(conversation_history, list):
        for msg in reversed(conversation_history):
            if isinstance(msg, dict) and msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
    elif isinstance(conversation_history, str):
        # Extract the last "候选人" (Candidate) message from the formatted string
        lines = conversation_history.strip().split("\n")
        for line in reversed(lines):
            if "候选人:" in line:
                last_user_msg = line.split("候选人:")[-1].strip()
                break
            
    rag_query = f"{question} {last_user_msg}"
    rag_context = await rag_service.query_context_async(rag_query)

    # 2. Get system prompt template
    system_prompt = prompt_manager.get_interviewer_prompt(
        role=role,
        question=question,
        expected_points=expected_points,
        conversation_history=conversation_history,
        target_next_question=target_next_question,
        difficulty=difficulty,
        knowledge_points=knowledge_points,
        force_next_instruction=force_next_instruction,
        rag_context=rag_context
    )
    
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return {
            "action": data.get("action", "MOVE_NEXT"),
            "text": data.get("text", "好了，我们进行下一个话题。")
        }
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return {
            "action": "MOVE_NEXT",
            "text": "抱歉，刚才信号有点不好。我们直接看下一个话题： " + target_next_question
        }

async def polish_text(text: str):
    """
    Add punctuation and fix minor typos in transcribed text.
    """
    if not text.strip():
        return text
        
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的语音转文字校对专家。你的任务是对面试者的语音转录结果进行微调：1. 加入恰当的中文标点符号。2. 修正明显的谐音错误或技术词错误（例如将“加瓦”修正为“Java”）。3. **保留**原句的所有信息、语气词和口语化倾向（如“呃”、“那个”、“然后”等），不要进行任何润色或改写。4. 保持最小限度的修改，只做必要的纠错和标点添加。直接返回处理后的文本。"},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error polishing text: {e}")
        return text

async def generate_repo_questions(role: str, repo_summary: dict) -> list[dict]:
    """
    根据 GitHub 仓库摘要，让 LLM 生成 3-5 个定制的项目深挖问题。

    Args:
        role: 岗位名
        repo_summary: services.repo_analyzer.analyze_repo() 的返回值

    Returns:
        问题列表，每条包含 question / expected_points / tech_focus
        如 LLM 调用失败或格式错误则返回空列表（不阻塞主流程）
    """
    if not repo_summary:
        return []

    system_prompt = prompt_manager.get_repo_question_prompt(role, repo_summary)
    if not system_prompt:
        print("[generate_repo_questions] prompt template empty, skip")
        return []

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请根据上述项目资料生成 3-5 条深挖问题，按约定 JSON 格式输出。"},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        questions = data.get("questions", [])
        if not isinstance(questions, list):
            print(f"[generate_repo_questions] unexpected format: {data}")
            return []

        # 给每条加上 source 标记，便于下游识别是"定制问题"
        for q in questions:
            q["source"] = "github_repo"
            q["repo"] = repo_summary.get("full_name", "")
            # 统一字段：让其能直接进 questions.json 格式
            q.setdefault("category", "project")
            q.setdefault("difficulty", "medium")
            q.setdefault("section", f"项目经历·{repo_summary.get('name', '')}")
            q.setdefault("key_points", q.get("expected_points", []))

        print(f"[generate_repo_questions] generated {len(questions)} questions for {repo_summary.get('full_name')}")
        return questions
    except json.JSONDecodeError as e:
        print(f"[generate_repo_questions] JSON parse error: {e}; content: {content[:200] if 'content' in dir() else 'N/A'}")
        return []
    except Exception as e:
        print(f"[generate_repo_questions] LLM error: {type(e).__name__}: {e}")
        return []


async def generate_resume_question(persona: dict) -> dict | None:
    """
    根据简历 Persona 生成 1 个针对性面试问题（纯按简历内容，不引入岗位角色）。

    Args:
        persona: /resume/parse 返回的 persona dict

    Returns:
        {"question": "...", "key_points": [...]} 或 None
    """
    if not persona:
        return None

    system_prompt = prompt_manager.get_resume_question_prompt(persona)
    if not system_prompt:
        print("[generate_resume_question] prompt template empty, skip")
        return None

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请根据上述候选人画像，按约定 JSON 格式生成 1 个面试问题。"},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        q = data.get("question", "")
        kp = data.get("key_points", [])
        if not q:
            print("[generate_resume_question] empty question returned")
            return None
        print(f"[generate_resume_question] generated: {q[:60]}...")
        return {"question": q, "key_points": kp}
    except json.JSONDecodeError as e:
        print(f"[generate_resume_question] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[generate_resume_question] LLM error: {type(e).__name__}: {e}")
        return None


async def generate_free_question(role: str, category: str, difficulty: str, asked_titles: list[str], knowledge_points: str) -> dict | None:
    """
    题库耗尽时，用 LLM 自由发挥生成 1 个不重复的面试问题。

    Args:
        role: 岗位名
        category: 题目类别（如 business_scenario）
        difficulty: 难度
        asked_titles: 已问过的题目文本列表（用于去重）
        knowledge_points: 知识点过滤字符串

    Returns:
        {"question": "...", "key_points": [...]} 或 None
    """
    asked_str = "\n".join(f"- {t}" for t in (asked_titles or [])[-20:])
    if not asked_str:
        asked_str = "（尚无已问问题）"

    system_prompt = prompt_manager.get_free_question_prompt(
        role=role,
        category=category,
        difficulty=difficulty,
        asked_questions=asked_str,
        knowledge_points=knowledge_points or "",
    )
    if not system_prompt:
        print("[generate_free_question] prompt template empty, skip")
        return None

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请按约定 JSON 格式生成 1 个不重复的面试问题。"},
            ],
            temperature=0.8,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        q = data.get("question", "")
        kp = data.get("key_points", [])
        if not q:
            print("[generate_free_question] empty question returned")
            return None
        print(f"[generate_free_question] generated: {q[:60]}...")
        return {"question": q, "key_points": kp}
    except json.JSONDecodeError as e:
        print(f"[generate_free_question] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[generate_free_question] LLM error: {type(e).__name__}: {e}")
        return None


async def generate_code_review(role: str, problem_title: str, problem_description: str, language: str, source_code: str, result_summary: str) -> str:
    prompt = f"""
你是一位资深 {role} 面试官。请对候选人的代码作答给出一次简洁、专业的面试反馈。

题目：{problem_title}
题意摘要：{problem_description}
语言：{language}

判题结果：
{result_summary}

候选人代码：
```{language}
{source_code}
```

请使用中文输出一段 120~220 字的点评，必须包含：
1. 是否通过以及结果解读
2. 时间复杂度和空间复杂度判断
3. 1~2 个可优化点

不要输出标题，不要使用 Markdown 列表。
""".strip()

    fallback = f"你这道《{problem_title}》整体思路已经表达出来了。建议你在说明核心数据结构选择的同时，明确补充时间复杂度和空间复杂度，并再检查一下边界条件、异常输入与代码可读性，这会让你的工程表达更完整。"

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一名严格但鼓励式的技术面试官。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        return (response.choices[0].message.content or "").strip() or fallback
    except Exception as e:
        print(f"[generate_code_review] LLM error: {type(e).__name__}: {e}")
        return fallback


async def generate_study_plan(role: str, evaluation_data: dict, history: list) -> dict | None:
    """
    根据面试评估结果 + 对话历史，让 LLM 生成分周学习计划 + 资源推荐 + 快速收益项。

    Args:
        role: 岗位名
        evaluation_data: evaluate_full_interview 返回的 dict
        history: 面试完整消息列表（models.Message 对象）

    Returns:
        {
            "weak_areas": [...],
            "plan": [...],
            "quick_wins": [...]
        }
        或 None（LLM 失败）
    """
    # 精选对话片段：只取用户回答 + 对应面试官问题，最多 8 轮
    excerpt_parts = []
    round_count = 0
    for m in history:
        if m.sender == "ai" and m.category and "FOLLOW_UP" not in m.category:
            excerpt_parts.append(f"[面试官] {m.content}")
            round_count += 1
        elif m.sender == "user":
            excerpt_parts.append(f"[候选人] {m.content}")
        if round_count >= 8:
            break
    transcript_excerpt = "\n".join(excerpt_parts) if excerpt_parts else "（暂无对话）"

    system_prompt = prompt_manager.get_study_plan_prompt(role, evaluation_data, transcript_excerpt)
    if not system_prompt:
        print("[generate_study_plan] prompt template empty, skip")
        return None

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请根据上述评估结果，按约定 JSON 格式输出学习计划。"},
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        # 简单校验结构
        if not isinstance(data.get("plan"), list):
            print(f"[generate_study_plan] unexpected format: missing 'plan' list")
            return _build_fallback_study_plan(role, evaluation_data)
        if not isinstance(data.get("weak_areas"), list):
            data["weak_areas"] = []
        if not isinstance(data.get("quick_wins"), list):
            data["quick_wins"] = []
        if not data["weak_areas"] or not data["quick_wins"]:
            fallback = _build_fallback_study_plan(role, evaluation_data)
            data["weak_areas"] = data["weak_areas"] or fallback["weak_areas"]
            data["quick_wins"] = data["quick_wins"] or fallback["quick_wins"]
        print(f"[generate_study_plan] generated plan with {len(data.get('plan', []))} weeks, {len(data.get('weak_areas', []))} weak areas")
        return data
    except json.JSONDecodeError as e:
        print(f"[generate_study_plan] JSON parse error: {e}")
        return _build_fallback_study_plan(role, evaluation_data)
    except Exception as e:
        print(f"[generate_study_plan] LLM error: {type(e).__name__}: {e}")
        return _build_fallback_study_plan(role, evaluation_data)


# ================= 评分辅助工具 =================

_ROLE_NAME_TO_KEY = {
    "Java后端开发工程师": "java-backend",
    "Web前端开发工程师": "web-frontend",
    "Python算法工程师": "python-algorithm",
}

_EXCELLENT_ANSWERS_MAX_CHARS = 6000  # 避免 prompt 超限


def _load_excellent_answers_for_role(role: str) -> str:
    """
    读取该岗位的优秀回答范例 Markdown 文件。
    按岗位映射到 knowledge-base/<role_key>/interview_excellent_answers.md。
    """
    role_key = _ROLE_NAME_TO_KEY.get(role, "")
    if not role_key:
        return "（未找到该岗位的优秀回答范例文件）"

    kb_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..",
        "knowledge-base", role_key, "interview_excellent_answers.md"
    ))
    if not os.path.exists(kb_path):
        return f"（{role} 的优秀回答范例文件不存在：{kb_path}）"

    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:_EXCELLENT_ANSWERS_MAX_CHARS]
    except Exception as e:
        return f"（读取优秀回答范例失败：{e}）"


async def _rag_retrieve_for_evaluation(history: list, top_k: int = 3) -> str:
    """
    对候选人回答较长的 2-3 轮，用 RAG 检索对应的优秀答案片段。
    Returns: 拼接好的相关优秀答题片段字符串
    """
    # 收集候选人回答长度排名前 3 的消息
    user_msgs = [m for m in history if m.sender == "user"]
    user_msgs.sort(key=lambda m: len(m.content or ""), reverse=True)
    top_msgs = user_msgs[:3]
    if not top_msgs:
        return ""

    all_snippets = []
    try:
        # 懒导入避免循环依赖
        from services.rag_service import rag_service
        for msg in top_msgs:
            # 以候选人回答为 query 检索相关优秀答案
            snippet = await rag_service.query_context_async(msg.content[:200], k=top_k)
            if snippet and snippet not in all_snippets:
                all_snippets.append(f"--- 相关参考答案 ---\n{snippet}")
    except Exception as e:
        print(f"[rag_retrieve_for_evaluation] error: {e}")
        return ""

    return "\n\n".join(all_snippets[:3])


def _stringify_list(values: list[str]) -> str:
    if not values:
        return "（未提供）"
    return "、".join(str(value) for value in values if value)


def _build_resume_summary(resume_persona: dict | None) -> str:
    if not resume_persona:
        return "（本场面试未提供简历画像）"

    projects = resume_persona.get("projects") or []
    project_lines = []
    for project in projects[:3]:
        if isinstance(project, dict):
            title = project.get("name") or project.get("title") or "未命名项目"
            desc = project.get("description") or project.get("summary") or ""
            project_lines.append(f"- {title}: {desc}".strip())
        else:
            project_lines.append(f"- {project}")

    summary_parts = [
        f"教育背景：{resume_persona.get('education') or '未提供'}",
        f"工作年限：{resume_persona.get('work_years') if resume_persona.get('work_years') is not None else '未提供'}",
        f"核心技能：{_stringify_list(resume_persona.get('skills') or [])}",
        f"个人总结：{resume_persona.get('summary') or '未提供'}",
        "项目经历：",
        "\n".join(project_lines) if project_lines else "- 未提供",
    ]
    return "\n".join(summary_parts)


def _normalize_round_feedback(evaluations: list[dict]) -> list[dict]:
    normalized = []
    for index, item in enumerate(evaluations, start=1):
        question = (item.get("question") or "").strip()
        answer_summary = (item.get("answer_summary") or "").strip()
        improved_example = (item.get("improved_example") or "").strip()
        strengths = item.get("strengths") or []
        issues = item.get("issues") or []
        if not any([question, answer_summary, improved_example, strengths, issues]):
            continue
        normalized.append(
            {
                "round": int(item.get("round") or index),
                "question": question,
                "answer_summary": answer_summary,
                "strengths": [str(entry) for entry in strengths if str(entry).strip()],
                "issues": [str(entry) for entry in issues if str(entry).strip()],
                "improved_example": improved_example,
            }
        )
    return normalized


async def evaluate_full_interview(history: list, role: str = "", resume_persona: dict | None = None):
    """
    Generate the final evaluation report for the complete interview.

    Args:
        history: 消息列表
        role: 岗位名（用于注入岗位差异化评估标准）
        resume_persona: 候选人结构化简历画像
    """
    # 1. Build a rich transcript with categories and context
    transcript_parts = []
    round_blocks = []
    pending_question = None
    pending_category = ""
    round_index = 0
    for m in history:
        if m.sender == "ai":
            category_text = f"【分类: {m.category}】" if m.category else ""
            transcript_parts.append(f"面试官: {m.content} {category_text}")
            pending_question = m.content
            pending_category = m.category or ""
        else:
            transcript_parts.append(f"面试者: {m.content}")
            if (m.content or "").strip():
                round_index += 1
                round_blocks.append(
                    "\n".join(
                        [
                            f"第 {round_index} 轮",
                            f"面试官问题：{pending_question or '（未记录）'}",
                            f"问题分类：{pending_category or '未标注'}",
                            f"候选人回答：{m.content}",
                        ]
                    )
                )

    transcript = "\n".join(transcript_parts)
    if round_blocks:
        transcript = transcript + "\n\n【按轮次整理的问答摘要】\n" + "\n\n".join(round_blocks)

    # 2. 获取岗位特定评估标准
    from core.role_criteria import get_role_criteria
    role_specific_criteria = get_role_criteria(role)
    resume_summary = _build_resume_summary(resume_persona)

    # 3. 加载该岗位的"优秀回答范例"作为评分参照
    excellent_answers_context = _load_excellent_answers_for_role(role)

    # 4. 用 RAG 检索候选人回答对应的优秀答案片段（只对用户回答较长的轮次）
    try:
        rag_hits = await _rag_retrieve_for_evaluation(history, top_k=3)
        if rag_hits:
            excellent_answers_context = (
                excellent_answers_context
                + "\n\n【RAG 检索到的相关优秀答题片段】\n"
                + rag_hits
            )
    except Exception as e:
        print(f"[evaluate_full_interview] RAG retrieve failed (non-fatal): {e}")

    # 5. Get system prompt with the new structure
    system_prompt = prompt_manager.get_evaluator_prompt(
        interview_transcript=transcript,
        excellent_answers_context=excellent_answers_context,
        role=role,
        role_specific_criteria=role_specific_criteria,
        resume_summary=resume_summary,
    )
    
    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        
        # 3. Process the evaluations to get the average
        evals = data.get("evaluations", [])
        round_feedback = _normalize_round_feedback(evals)
        scores = {
            "content_score": [],
            "expression_score": [],
            "business_scenario_score": [],
            "problem_solving_score": []
        }
        
        for e in evals:
            for k in scores.keys():
                val = e.get(k)
                if val is not None and isinstance(val, (int, float)):
                    scores[k].append(val)
        
        # Calculate averages for non-null values
        final_scores = {}
        for k, v in scores.items():
            final_scores[k] = round(sum(v) / len(v), 1) if v else 0.0
            
        # Total score is average of the averages
        active_averages = [v for v in final_scores.values() if v > 0]
        total_score = round(sum(active_averages) / len(active_averages), 1) if active_averages else 0.0
        
        summary = data.get("overall_summary", {})
        
        return normalize_evaluation_result({
            "content_score": final_scores["content_score"],
            "expression_score": final_scores["expression_score"],
            "business_scenario_score": final_scores["business_scenario_score"],
            "problem_solving_score": final_scores["problem_solving_score"],
            "total_score": total_score,
            "highlights": summary.get("strengths", []),
            "weaknesses": summary.get("weaknesses", []),
            "recommendations": summary.get("recommendations", "继续努力！"),
            "evaluations": evals,
            "round_feedback": round_feedback,
        })
        
    except Exception as e:
        print(f"Error generating report: {e}")
        return normalize_evaluation_result({
            "content_score": 0, "expression_score": 0, "business_scenario_score": 0, "problem_solving_score": 0,
            "total_score": 0, "highlights": ["评估生成失败"], "weaknesses": ["评估服务暂时不可用，本次报告未能完整生成。"], "recommendations": "请稍后重试生成评估报告。",
            "evaluations": [], "round_feedback": []
        })
