"""test_judge0_service.py — Judge0 代码判题服务单元测试。

测试目标: services/judge0_service.py
- trim_output()     文本统一处理
- truncate_text()   文本截断
- decode_judge0_text()  Base64 解码
- Judge0Result      结果数据类与 raw_status 属性
- Judge0Service     构造函数
- LANGUAGE_IDS      语言 ID 映射
"""

import base64
import pytest
from services.judge0_service import (
    trim_output,
    truncate_text,
    decode_judge0_text,
    Judge0Result,
    Judge0Service,
    LANGUAGE_IDS,
    RUNNING_STATUS_IDS,
)


# ============================================================
# trim_output 测试
# ============================================================

class TestTrimOutput:
    """验证文本统一处理函数。"""

    def test_empty_string_returns_empty(self):
        """空字符串应返回空字符串。"""
        assert trim_output("") == ""

    def test_none_returns_empty(self):
        """None 应返回空字符串。"""
        assert trim_output(None) == ""

    def test_normalizes_crlf_to_lf(self):
        """\\r\\n 应统一为 \\n。"""
        assert trim_output("hello\r\nworld") == "hello\nworld"

    def test_normalizes_cr_to_lf(self):
        """单独的 \\r 应统一为 \\n。"""
        assert trim_output("hello\rworld") == "hello\nworld"

    def test_strips_whitespace(self):
        """首尾空白字符应被去除。"""
        assert trim_output("  hello world  \n") == "hello world"

    def test_preserves_internal_whitespace(self):
        """中间的空白字符应保留。"""
        assert trim_output("hello  world") == "hello  world"

    def test_mixed_line_endings(self):
        """混合换行符应全部统一。"""
        assert trim_output("line1\r\nline2\rline3\nline4") == "line1\nline2\nline3\nline4"


# ============================================================
# truncate_text 测试
# ============================================================

class TestTruncateText:
    """验证文本截断函数。"""

    def test_short_text_unchanged(self):
        """短文本不应被截断。"""
        assert truncate_text("hello") == "hello"

    def test_none_returns_empty(self):
        """None 应返回空字符串。"""
        assert truncate_text(None) == ""

    def test_empty_returns_empty(self):
        """空字符串应返回空字符串。"""
        assert truncate_text("") == ""

    def test_truncates_with_custom_limit(self):
        """超过自定义限制时应截断并添加标记。"""
        result = truncate_text("a" * 100, limit=10)
        assert len(result) < 100
        assert "[truncated]" in result

    def test_appends_truncated_marker(self):
        """截断后应包含 [truncated] 标记。"""
        result = truncate_text("hello world", limit=5)
        assert "[truncated]" in result

    def test_exact_limit_no_truncation(self):
        """刚好等于限制长度时不截断。"""
        text = "12345"
        result = truncate_text(text, limit=5)
        assert "[truncated]" not in result
        assert result == text


# ============================================================
# decode_judge0_text 测试
# ============================================================

class TestDecodeJudge0Text:
    """验证 Base64 解码函数。"""

    def test_none_returns_empty(self):
        """None 应返回空字符串。"""
        assert decode_judge0_text(None) == ""

    def test_empty_returns_empty(self):
        """空字符串应返回空字符串。"""
        assert decode_judge0_text("") == ""

    def test_valid_base64_decodes_utf8(self):
        """有效的 Base64 编码 UTF-8 文本应正确解码。"""
        encoded = base64.b64encode("hello world".encode("utf-8")).decode("utf-8")
        assert decode_judge0_text(encoded) == "hello world"

    def test_valid_base64_decodes_ascii(self):
        """有效的 Base64 编码纯 ASCII 文本应正确解码。"""
        encoded = base64.b64encode(b"print(1+1)").decode("utf-8")
        assert decode_judge0_text(encoded) == "print(1+1)"

    def test_invalid_base64_returns_original(self):
        """无效的 Base64 字符串应返回原值（fallback 行为）。"""
        original = "not-valid-base64!!!"
        result = decode_judge0_text(original)
        # 无效 Base64 无法解码时返回原值
        assert result == original

    def test_chinese_base64_roundtrip(self):
        """中文 Base64 编解码应正确往返。"""
        text = "你好世界"
        encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        assert decode_judge0_text(encoded) == text


# ============================================================
# Judge0Result 数据类测试
# ============================================================

class TestJudge0Result:
    """验证 Judge0Result 数据类和 raw_status 属性。"""

    def test_raw_status_finished(self):
        """status_id=3 应返回 Finished。"""
        result = Judge0Result(status_id=3, status_description="Accepted")
        assert result.raw_status == "Finished"

    def test_raw_status_compile_error(self):
        """status_id=6 应返回 Compile Error。"""
        result = Judge0Result(status_id=6, status_description="Compilation Error")
        assert result.raw_status == "Compile Error"

    def test_raw_status_time_limit_exceeded(self):
        """status_id=5 应返回 Time Limit Exceeded。"""
        result = Judge0Result(status_id=5, status_description="Time Limit Exceeded")
        assert result.raw_status == "Time Limit Exceeded"

    def test_raw_status_wrong_answer(self):
        """status_id=4 应返回 Wrong Answer。"""
        result = Judge0Result(status_id=4, status_description="Wrong Answer")
        assert result.raw_status == "Wrong Answer"

    def test_raw_status_runtime_error(self):
        """status_id≥7 应返回 Runtime Error。"""
        result = Judge0Result(status_id=7, status_description="Runtime Error (SIGSEGV)")
        assert result.raw_status == "Runtime Error"

    def test_raw_status_unknown_fallback(self):
        """未知状态码应回退到 status_description。"""
        result = Judge0Result(status_id=1, status_description="In Queue")
        assert result.raw_status == "In Queue"

    def test_result_fields_defaults(self):
        """未提供可选字段时应使用默认值。"""
        result = Judge0Result(status_id=3, status_description="Accepted")
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.compile_output == ""
        assert result.time is None
        assert result.memory is None
        assert result.message == ""

    def test_result_with_all_fields(self):
        """提供所有字段时应正确设置。"""
        result = Judge0Result(
            status_id=3,
            status_description="Accepted",
            stdout="hello\n",
            stderr="",
            compile_output="",
            time=0.05,
            memory=12345,
            message="",
        )
        assert result.stdout == "hello\n"
        assert result.time == 0.05
        assert result.memory == 12345


# ============================================================
# Judge0Service 构造函数测试
# ============================================================

class TestJudge0ServiceConstruction:
    """验证 Judge0Service 的构造函数行为。"""

    def test_default_constructor_creates_instance(self):
        """默认构造函数应成功创建实例。"""
        service = Judge0Service()
        assert service is not None
        assert hasattr(service, "base_url")

    def test_custom_base_url_constructor(self):
        """自定义 base_url 构造时应被正确设置。"""
        service = Judge0Service(base_url="http://localhost:9999")
        assert service.base_url == "http://localhost:9999"

    def test_base_url_trailing_slash_stripped(self):
        """base_url 尾部斜杠应被自动移除。"""
        service = Judge0Service(base_url="http://localhost:2358/")
        assert service.base_url == "http://localhost:2358"


# ============================================================
# LANGUAGE_IDS 和常量测试
# ============================================================

class TestLanguageIds:
    """验证语言 ID 映射表。"""

    def test_python_id(self):
        """Python 应映射到 71。"""
        assert LANGUAGE_IDS["python"] == 71

    def test_java_id(self):
        """Java 应映射到 62。"""
        assert LANGUAGE_IDS["java"] == 62

    def test_cpp_id(self):
        """C++ 应映射到 54。"""
        assert LANGUAGE_IDS["cpp"] == 54

    def test_javascript_id(self):
        """JavaScript 应映射到 63。"""
        assert LANGUAGE_IDS["javascript"] == 63

    def test_running_status_ids(self):
        """RUNNING_STATUS_IDS 应包含 {1, 2}。"""
        assert RUNNING_STATUS_IDS == {1, 2}
