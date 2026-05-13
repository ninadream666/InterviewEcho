"""简历解析与 Persona 构造（W3.2.8 / FT2.1.3.2）

职责：
1. 从纯文本或 PDF 字节流中提取候选人简历内容
2. 用 LLM 把简历结构化为 persona JSON
3. 把 persona 序列化成可注入 system prompt 的中文段落

被以下位置调用：
- routers/interview.py :: POST /resume/parse
- routers/interview.py :: process_message_logic（注入 Persona 上下文）
"""

import json
import io
from typing import Optional

from core.config import settings
from core.prompts import prompt_manager
from core.llm_service import client  # 复用同一个 AsyncOpenAI 实例

# pypdf 在 requirements.txt 中声明，运行时若缺失给清晰报错
try:
    from pypdf import PdfReader
    _HAS_PYPDF = True
except ImportError:
    _HAS_PYPDF = False


EMPTY_PERSONA = {
    "skills": [],
    "projects": [],
    "work_years": 0,
    "education": "",
    "summary": "",
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """从 PDF 字节流提取纯文本。失败返回空串。"""
    if not _HAS_PYPDF:
        print("[resume_parser] pypdf 未安装，无法解析 PDF")
        return ""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            try:
                pages_text.append(page.extract_text() or "")
            except Exception as e:
                print(f"[resume_parser] 单页提取失败：{e}")
        return "\n".join(pages_text).strip()
    except Exception as e:
        print(f"[resume_parser] PDF 解析失败：{type(e).__name__}: {e}")
        return ""


async def parse_resume_text(text: str) -> dict:
    """调 LLM 把简历纯文本结构化为 persona JSON。

    返回结构：
        {
          "skills": ["Java", "Spring Boot", ...],
          "projects": [
              {"name": "...", "role": "...", "tech": [...], "highlights": "..."}
          ],
          "work_years": 0,        # 实习/工作年限（无则 0）
          "education": "...",     # 学历 + 学校 + 专业，单行
          "summary": "..."        # 50-120 字总体画像
        }
    LLM 失败或解析异常时返回 EMPTY_PERSONA 的浅拷贝（不抛异常，确保面试主流程不被阻塞）。
    """
    if not text or not text.strip():
        return dict(EMPTY_PERSONA)

    # 限制 token 数：超长简历截断到 6000 字（约 4k tokens 中文）
    truncated = text.strip()[:6000]

    system_prompt = prompt_manager.get_resume_parser_prompt()
    if not system_prompt:
        print("[resume_parser] 简历 prompt 模板缺失，跳过结构化")
        return dict(EMPTY_PERSONA)

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"以下是候选人简历内容，请按约定 JSON 格式输出：\n\n{truncated}"},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        data = json.loads(content)
        # 字段兜底 + 类型校验
        persona = {
            "skills": data.get("skills", []) if isinstance(data.get("skills"), list) else [],
            "projects": data.get("projects", []) if isinstance(data.get("projects"), list) else [],
            "work_years": int(data.get("work_years", 0)) if isinstance(data.get("work_years"), (int, float)) else 0,
            "education": str(data.get("education", "")),
            "summary": str(data.get("summary", "")),
        }
        print(f"[resume_parser] 解析成功：{len(persona['skills'])} 技能，{len(persona['projects'])} 项目")
        return persona
    except json.JSONDecodeError as e:
        print(f"[resume_parser] LLM 输出非 JSON：{e}")
        return dict(EMPTY_PERSONA)
    except Exception as e:
        print(f"[resume_parser] LLM 调用失败：{type(e).__name__}: {e}")
        return dict(EMPTY_PERSONA)


async def parse_resume_pdf(file_bytes: bytes) -> dict:
    """从 PDF 字节流解析 persona。"""
    text = extract_text_from_pdf(file_bytes)
    if not text:
        return dict(EMPTY_PERSONA)
    return await parse_resume_text(text)


def build_persona_context(persona: Optional[dict]) -> str:
    """把 persona dict 序列化为可拼到 system prompt 中的中文段落。

    输出示例：
        【候选人简历摘要】
        - 总体：本科应届，2 年校内项目经验，主攻后端
        - 学历：XX 大学 计算机科学与技术 本科
        - 技能栈：Java, Spring Boot, Redis, MySQL
        - 主要项目：
          * 校园二手交易平台 (后端主力)：Spring Cloud, MySQL, Redis - 支撑日活 2k+
          * ...

    persona 为空或 None 时返回空字符串（调用方据此跳过注入）。
    """
    if not persona:
        return ""

    skills = persona.get("skills") or []
    projects = persona.get("projects") or []
    work_years = persona.get("work_years", 0)
    education = persona.get("education", "").strip()
    summary = persona.get("summary", "").strip()

    if not (skills or projects or education or summary):
        return ""

    lines = ["【候选人简历摘要】"]
    if summary:
        lines.append(f"- 总体：{summary}")
    if education:
        lines.append(f"- 学历：{education}")
    if work_years:
        lines.append(f"- 经验年限：{work_years} 年")
    if skills:
        # 控制长度避免污染 prompt
        skills_str = ", ".join(str(s) for s in skills[:15])
        lines.append(f"- 技能栈：{skills_str}")
    if projects:
        lines.append("- 主要项目：")
        for p in projects[:5]:
            if not isinstance(p, dict):
                continue
            name = p.get("name", "未命名项目")
            role = p.get("role", "")
            tech = p.get("tech", [])
            tech_str = ", ".join(str(t) for t in tech[:6]) if isinstance(tech, list) else ""
            highlights = p.get("highlights", "")
            line = f"  * {name}"
            if role:
                line += f" ({role})"
            if tech_str:
                line += f"：{tech_str}"
            if highlights:
                line += f" - {highlights[:80]}"
            lines.append(line)

    lines.append("【提问指引】请在追问/选题时优先围绕候选人上述技能与项目展开，避免脱离其经验背景的纯理论题。")
    return "\n".join(lines)
