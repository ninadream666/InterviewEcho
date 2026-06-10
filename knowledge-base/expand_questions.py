"""
使用 LLM 为 knowledge-base 下的 questions.json 补齐题目数量。

目标：
- 确保每个现有的 (section, difficulty) 组合至少有 5 道题
- 仅为不足的组合补题，保留已有题目
- 直接将生成结果写回对应 questions.json

运行方式：
    python knowledge-base/expand_questions.py
    python knowledge-base/expand_questions.py --role java-backend
    python knowledge-base/expand_questions.py --min-per-combo 6
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402


load_dotenv(PROJECT_ROOT / ".env")

ROLE_DIRS = ["java-backend", "web-frontend", "python-algorithm"]
ROLE_NAMES = {
    "java-backend": "Java后端开发工程师",
    "web-frontend": "Web前端开发工程师",
    "python-algorithm": "Python算法工程师",
}
MIN_PER_COMBO = 5
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}
ALLOWED_CATEGORIES = {"problem_solving", "business_scenario", "project", "behavioral"}


def build_client() -> OpenAI:
    if not settings.LLM_API_KEY:
        raise RuntimeError("未配置 LLM_API_KEY，无法调用 LLM 扩题。")
    return OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


def choose_base_category(items: list[dict]) -> str:
    counts = Counter(item.get("category") or "problem_solving" for item in items)
    if not counts:
        return "problem_solving"
    category, _ = counts.most_common(1)[0]
    return category if category in ALLOWED_CATEGORIES else "problem_solving"


def load_questions(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_questions(path: Path, questions: list[dict]) -> None:
    path.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_key_points(key_points: Any) -> list[str]:
    if not isinstance(key_points, list):
        return []
    normalized = [str(item).strip() for item in key_points if str(item).strip()]
    return normalized[:6]


def normalize_question_item(
    item: dict,
    *,
    job_type: str,
    section: str,
    difficulty: str,
    fallback_category: str,
) -> dict | None:
    question = str(item.get("question") or "").strip()
    if not question:
        return None

    category = str(item.get("category") or fallback_category).strip()
    if category not in ALLOWED_CATEGORIES:
        category = fallback_category

    normalized = {
        "job_type": job_type,
        "category": category,
        "section": section,
        "difficulty": difficulty,
        "question": question,
        "key_points": normalize_key_points(item.get("key_points")),
    }
    if len(normalized["key_points"]) < 3:
        return None
    return normalized


def build_generation_prompt(
    *,
    role_name: str,
    role_key: str,
    section: str,
    difficulty: str,
    category: str,
    need_count: int,
    existing_questions: list[str],
    sample_items: list[dict],
) -> str:
    samples_text = "\n".join(
        f"- 题目：{item['question']}\n  要点：{'; '.join(item.get('key_points') or [])}"
        for item in sample_items[:5]
    ) or "（当前组合暂无参考题）"

    existing_text = "\n".join(f"- {question}" for question in existing_questions) or "（无）"
    difficulty_cn = {"easy": "简单", "medium": "中等", "hard": "困难"}.get(difficulty, difficulty)

    return f"""
你是一名资深技术面试命题专家，需要为 InterviewEcho 生成高质量中文面试题。

目标岗位：{role_name}
岗位标识：{role_key}
知识领域：{section}
难度：{difficulty_cn}（内部值：{difficulty}）
题目类别：{category}
本次需要补充题目数：{need_count}

约束：
1. 生成的题目必须与“{section}”高度相关，符合“{role_name}”真实面试风格。
2. 难度必须匹配 {difficulty_cn}，不要混入明显更低或更高难度的题。
3. 所有题目都必须与下面已有题目不同，不能改写复述、不能只换主语。
4. 输出字段必须严格遵守 questions.json 结构，只返回 JSON。
5. 每道题提供 3 到 5 条 `key_points`，内容要具体、可用于评分，不要写空话。
6. 问题要口语自然，像真正面试官会问的话，不要模板腔，不要解释题意。
7. 不要输出 Markdown 代码块。

当前同组合已有题目：
{existing_text}

当前组合参考题风格：
{samples_text}

请严格输出如下 JSON 结构：
{{
  "questions": [
    {{
      "category": "{category}",
      "question": "题目文本",
      "key_points": ["要点1", "要点2", "要点3"]
    }}
  ]
}}

务必恰好生成 {need_count} 道新题。
""".strip()


def call_llm_generate(
    client: OpenAI,
    *,
    role_name: str,
    role_key: str,
    section: str,
    difficulty: str,
    category: str,
    need_count: int,
    existing_questions: list[str],
    sample_items: list[dict],
) -> list[dict]:
    prompt = build_generation_prompt(
        role_name=role_name,
        role_key=role_key,
        section=section,
        difficulty=difficulty,
        category=category,
        need_count=need_count,
        existing_questions=existing_questions,
        sample_items=sample_items,
    )
    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[{"role": "system", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.9,
    )
    content = (response.choices[0].message.content or "").strip()
    data = json.loads(content)
    questions = data.get("questions")
    if not isinstance(questions, list):
        raise ValueError(f"LLM 输出不含 questions 数组: {content[:200]}")
    return questions


def ensure_questions_with_llm(client: OpenAI, path: Path, min_per_combo: int) -> int:
    questions = load_questions(path)
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in questions:
        groups[(item["section"], item["difficulty"])].append(item)

    additions: list[dict] = []
    for (section, difficulty), items in sorted(groups.items()):
        if difficulty not in ALLOWED_DIFFICULTIES:
            print(f"[skip] {path.parent.name} / {section} / {difficulty}: 不在允许难度集合中")
            continue

        need_count = max(0, min_per_combo - len(items))
        if need_count == 0:
            continue

        role_key = path.parent.name
        role_name = ROLE_NAMES.get(role_key, role_key)
        category = choose_base_category(items)
        existing_questions = [str(item.get("question") or "").strip() for item in items if str(item.get("question") or "").strip()]
        print(f"[generate] {role_key} / {section} / {difficulty}: 现有 {len(items)}，需补 {need_count}")

        generated = call_llm_generate(
            client,
            role_name=role_name,
            role_key=role_key,
            section=section,
            difficulty=difficulty,
            category=category,
            need_count=need_count,
            existing_questions=existing_questions,
            sample_items=items,
        )

        existing_set = set(existing_questions)
        accepted_count = 0
        for raw_item in generated:
            normalized = normalize_question_item(
                raw_item,
                job_type=items[0]["job_type"],
                section=section,
                difficulty=difficulty,
                fallback_category=category,
            )
            if not normalized:
                continue
            if normalized["question"] in existing_set:
                continue
            existing_set.add(normalized["question"])
            additions.append(normalized)
            accepted_count += 1

        if accepted_count < need_count:
            raise RuntimeError(
                f"{role_key} / {section} / {difficulty} 仅成功生成 {accepted_count} 道，少于需要的 {need_count} 道。"
            )

    if additions:
        questions.extend(additions)
        dump_questions(path, questions)
    return len(additions)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="使用 LLM 为 knowledge-base 补齐面试题。")
    parser.add_argument("--role", choices=ROLE_DIRS, help="仅处理某一个岗位题库")
    parser.add_argument("--min-per-combo", type=int, default=MIN_PER_COMBO, help="每个 (section, difficulty) 组合至少保留多少题")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = build_client()
    role_dirs = [args.role] if args.role else ROLE_DIRS

    total = 0
    for role_dir in role_dirs:
        total += ensure_questions_with_llm(client, ROOT / role_dir / "questions.json", args.min_per_combo)
    print(f"added {total} questions")


if __name__ == "__main__":
    main()
