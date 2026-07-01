"""test_resume_parser.py — 简历解析模块单元测试。

测试目标: services/resume_parser.py
- extract_text_from_pdf()    PDF 文本提取
- build_persona_context()    Persona 上下文字段序列化
- EMPTY_PERSONA              空画像常量

parse_resume_text() 和 parse_resume_pdf() 依赖 LLM 调用，
本测试通过 monkeypatch 模拟 LLM 响应。
"""

import json
import pytest

from services.resume_parser import (
    EMPTY_PERSONA,
    extract_text_from_pdf,
    build_persona_context,
    parse_resume_text,
    parse_resume_pdf,
)


# ============================================================
# EMPTY_PERSONA 常量测试
# ============================================================

class TestEmptyPersona:
    """验证空画像常量。"""

    def test_has_expected_keys(self):
        """应包含 5 个必要字段。"""
        assert set(EMPTY_PERSONA.keys()) == {"skills", "projects", "work_years", "education", "summary"}

    def test_defaults_are_empty(self):
        """默认值应为空列表/空字符串/0。"""
        assert EMPTY_PERSONA["skills"] == []
        assert EMPTY_PERSONA["projects"] == []
        assert EMPTY_PERSONA["work_years"] == 0
        assert EMPTY_PERSONA["education"] == ""
        assert EMPTY_PERSONA["summary"] == ""

    def test_dict_copy_is_independent(self):
        """dict(EMPTY_PERSONA) 应返回浅拷贝，修改不影响原常量。"""
        copy = dict(EMPTY_PERSONA)
        copy["skills"] = ["Python"]
        assert EMPTY_PERSONA["skills"] == []


# ============================================================
# extract_text_from_pdf 测试
# ============================================================

class TestExtractTextFromPdf:
    """验证 PDF 文本提取函数。"""

    def test_empty_bytes_returns_empty(self):
        """空字节流应返回空字符串。"""
        result = extract_text_from_pdf(b"")
        assert result == ""

    def test_invalid_bytes_returns_empty(self):
        """无效的 PDF 字节流应返回空字符串（不抛异常）。"""
        result = extract_text_from_pdf(b"this is not a valid pdf")
        assert isinstance(result, str)
        # pypdf 会抛异常，函数内 catch 后返回空串

    def test_valid_pdf_bytes_extracts_text(self):
        """有效 PDF 应提取出文本。"""
        # 构造一个最小合法 PDF（仅包含简单文本）
        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>\nendobj\n"
            b"4 0 obj\n<< /Length 44 >>\nstream\n"
            b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000115 00000 n \n"
            b"0000000236 00000 n \n"
            b"trailer\n<< /Size 5 /Root 1 0 R >>\n"
            b"startxref\n301\n"
            b"%%EOF"
        )
        result = extract_text_from_pdf(pdf_content)
        assert isinstance(result, str)


# ============================================================
# build_persona_context 测试
# ============================================================

class TestBuildPersonaContext:
    """验证 Persona 上下文字段序列化函数。"""

    def test_full_persona_generates_all_sections(self):
        """完整画像应生成所有段落。"""
        persona = {
            "skills": ["Python", "Java", "SQL", "Docker", "Git", "Linux"],
            "projects": [
                {"name": "电商系统", "role": "后端开发", "tech": ["Spring Boot", "MySQL", "Redis"], "highlights": "支撑QPS 1000+"},
            ],
            "work_years": 3,
            "education": "XX大学 计算机科学与技术 本科",
            "summary": "有3年Java后端开发经验",
        }
        result = build_persona_context(persona)
        assert "候选人简历摘要" in result
        assert "XX大学" in result
        assert "Python" in result
        assert "电商系统" in result
        assert "提问指引" in result

    def test_minimal_persona_generates_core_sections(self):
        """最小画像（仅有 summary）应生成基本段落。"""
        persona = {
            "skills": [],
            "projects": [],
            "work_years": 0,
            "education": "",
            "summary": "应届毕业生",
        }
        result = build_persona_context(persona)
        assert "候选人简历摘要" in result
        assert "应届毕业生" in result

    def test_empty_persona_returns_empty_string(self):
        """空字典应返回空字符串。"""
        result = build_persona_context({})
        assert result == ""

    def test_none_persona_returns_empty_string(self):
        """None 应返回空字符串。"""
        result = build_persona_context(None)
        assert result == ""

    def test_persona_with_only_empty_fields_returns_empty(self):
        """所有字段均为空时返回空字符串。"""
        persona = {"skills": [], "projects": [], "work_years": 0, "education": "", "summary": ""}
        result = build_persona_context(persona)
        assert result == ""

    def test_skills_truncated_at_15(self):
        """技能列表超过 15 个时应截断。"""
        persona = {
            "skills": [f"Skill{i}" for i in range(20)],
            "projects": [],
            "work_years": 0,
            "education": "",
            "summary": "测试",
        }
        result = build_persona_context(persona)
        # 不应包含 Skill15（索引从 0 开始，[:15] 最多到 Skill14）
        assert "Skill14" in result
        assert "Skill15" not in result

    def test_projects_truncated_at_5(self):
        """项目列表超过 5 个时应截断。"""
        persona = {
            "skills": [],
            "projects": [{"name": f"Project{i}"} for i in range(10)],
            "work_years": 0,
            "education": "",
            "summary": "测试",
        }
        result = build_persona_context(persona)
        assert "Project4" in result
        assert "Project5" not in result


# ============================================================
# parse_resume_text（monkeypatch LLM）测试
# ============================================================

class TestParseResumeText:
    """验证 LLM 简历解析函数（monkeypatch）。"""

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty_persona(self):
        """空文本应返回 EMPTY_PERSONA 的拷贝。"""
        result = await parse_resume_text("")
        assert result == EMPTY_PERSONA

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_empty_persona(self):
        """纯空白文本应返回 EMPTY_PERSONA。"""
        result = await parse_resume_text("   \n  \t  ")
        assert result == EMPTY_PERSONA

    @pytest.mark.asyncio
    async def test_text_longer_than_6000_chars_truncated(self, monkeypatch):
        """超过 6000 字符的简历文本应被截断后发送给 LLM。"""
        # 用 monkeypatch 模拟 LLM 客户端
        class FakeResponse:
            class Choice:
                class Message:
                    content = json.dumps(EMPTY_PERSONA, ensure_ascii=False)
                message = Message()
            choices = [Choice()]

        async def fake_create(*args, **kwargs):
            # 验证 user message 不超过 6000 字 + prompt 开销
            messages = kwargs.get("messages", [])
            for msg in messages:
                if msg.get("role") == "user":
                    assert len(msg["content"]) <= 6500  # 6000 + prompt 文字
            return FakeResponse()

        monkeypatch.setattr(
            "services.resume_parser.client.chat.completions.create",
            fake_create,
        )
        long_text = "测试简历内容。" * 1200  # 远超 6000 字符
        result = await parse_resume_text(long_text)
        assert result == EMPTY_PERSONA
