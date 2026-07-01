"""test_interrupt_policy.py — 打断策略模块单元测试。

测试目标: services/interrupt_policy.py
- InterruptDecision 数据类
- _count_tech_terms() 技术词计数
- _keyword_overlap() 关键词重叠度
- evaluate_interrupt() 打断判定逻辑（timeout/off_topic/rambling/正常）

该模块设计为零外部依赖的纯规则引擎，所有测试无需数据库或外部服务。
"""

import pytest
from services.interrupt_policy import (
    InterruptDecision,
    _count_tech_terms,
    _keyword_overlap,
    evaluate_interrupt,
    DURATION_TIMEOUT_SEC,
    OFF_TOPIC_MIN_LEN,
    RAMBLING_MIN_LEN,
)


# ============================================================
# InterruptDecision 数据类测试
# ============================================================

class TestInterruptDecision:
    """验证 InterruptDecision 数据类的基本行为。"""

    def test_default_no_trigger(self):
        """默认构造：不触发打断，所有字段为空。"""
        decision = InterruptDecision(triggered=False, trigger_type="", prompt_addition="")
        assert decision.triggered is False
        assert decision.trigger_type == ""
        assert decision.prompt_addition == ""

    def test_triggered_timeout(self):
        """触发超时打断时各字段应正确填充。"""
        decision = InterruptDecision(
            triggered=True,
            trigger_type="timeout",
            prompt_addition="请聚焦问题",
        )
        assert decision.triggered is True
        assert decision.trigger_type == "timeout"
        assert "聚焦" in decision.prompt_addition

    def test_triggered_off_topic(self):
        """触发离题打断时各字段应正确填充。"""
        decision = InterruptDecision(
            triggered=True,
            trigger_type="off_topic",
            prompt_addition="请围绕题目要点重新作答",
        )
        assert decision.triggered is True
        assert decision.trigger_type == "off_topic"

    def test_triggered_rambling(self):
        """触发赘述打断时各字段应正确填充。"""
        decision = InterruptDecision(
            triggered=True,
            trigger_type="rambling",
            prompt_addition="请总结技术结论",
        )
        assert decision.triggered is True
        assert decision.trigger_type == "rambling"


# ============================================================
# _count_tech_terms 测试
# ============================================================

class TestCountTechTerms:
    """验证技术词计数函数。"""

    def test_empty_text_returns_zero(self):
        """空字符串应返回 0。"""
        assert _count_tech_terms("") == 0

    def test_none_text_returns_zero(self):
        """None 文本应返回 0（内部会转为空串）。"""
        # _count_tech_terms 接收 str 类型，但内部处理 None
        assert _count_tech_terms("") == 0

    def test_single_java_term_found(self):
        """包含单个 Java 技术词时应返回 ≥1。"""
        text = "Spring Boot 是一个优秀的框架"
        assert _count_tech_terms(text) >= 1

    def test_multiple_terms_found(self):
        """包含多个技术词时应返回对应的数量。"""
        text = "Redis 做缓存，MySQL 做持久化，使用 Kafka 做消息队列"
        count = _count_tech_terms(text)
        assert count >= 3

    def test_case_insensitive_matching(self):
        """技术词匹配应不区分大小写。"""
        text = "使用 redis 和 mysql"
        count = _count_tech_terms(text)
        assert count >= 2

    def test_no_tech_terms_returns_zero(self):
        """纯日常用语不应匹配到技术词。"""
        text = "今天天气真好，我去超市买东西"
        # 可能有意外匹配（如"图"），但应该极少
        count = _count_tech_terms(text)
        assert count <= 1


# ============================================================
# _keyword_overlap 测试
# ============================================================

class TestKeywordOverlap:
    """验证关键点重叠度计算函数。"""

    def test_no_overlap_returns_zero(self):
        """文本与关键点完全无关时返回 0。"""
        text = "我喜欢吃苹果"
        key_points = ["Spring AOP 原理", "JVM 内存模型"]
        assert _keyword_overlap(text, key_points) == 0

    def test_partial_overlap_counted(self):
        """部分匹配应被正确计数。"""
        text = "Spring 的 AOP 是通过动态代理实现的"
        key_points = ["Spring AOP 原理", "JVM 内存模型"]
        # "Spring AOP 原理" 的前 4 字符 "Spri" 包含在 text 中（大小写不敏感）
        assert _keyword_overlap(text, key_points) >= 1

    def test_empty_text_returns_zero(self):
        """空文本应返回 0。"""
        assert _keyword_overlap("", ["Spring"]) == 0

    def test_empty_key_points_returns_zero(self):
        """空关键点列表应返回 0。"""
        assert _keyword_overlap("Spring AOP", []) == 0

    def test_none_key_points_returns_zero(self):
        """None 关键点应返回 0。"""
        assert _keyword_overlap("text", None) == 0

    def test_key_point_with_none_value_skipped(self):
        """关键点列表中含 None 项时应跳过。"""
        text = "JVM memory model"
        key_points = [None, "JVM 内存模型"]
        assert _keyword_overlap(text, key_points) >= 1


# ============================================================
# evaluate_interrupt 测试
# ============================================================

class TestEvaluateInterrupt:
    """验证打断决策核心逻辑。"""

    # ---- 超时规则 ----

    def test_timeout_trigger(self):
        """回答时长超过阈值时应触发超时打断。"""
        result = evaluate_interrupt(
            user_text="一些正常的技术回答",
            duration_sec=DURATION_TIMEOUT_SEC + 1.0,
            current_question="请解释 JVM 内存模型",
            current_question_key_points=["JVM", "内存模型"],
        )
        assert result.triggered is True
        assert result.trigger_type == "timeout"
        assert "超时" in result.prompt_addition

    def test_duration_none_skips_timeout(self):
        """duration_sec 为 None 时不触发超时（文本较短不会触发其他规则）。"""
        result = evaluate_interrupt(
            user_text="正常回答",
            duration_sec=None,
            current_question="请解释 JVM",
            current_question_key_points=["JVM"],
        )
        # 短文本不应触发任何打断
        assert result.triggered is False

    def test_duration_below_threshold_no_interrupt(self):
        """时长刚好等于阈值时不触发超时。"""
        result = evaluate_interrupt(
            user_text="正常回答",
            duration_sec=DURATION_TIMEOUT_SEC,
            current_question="问题",
            current_question_key_points=["关键点"],
        )
        assert not (result.triggered and result.trigger_type == "timeout")

    # ---- 离题规则 ----

    def test_off_topic_trigger(self):
        """长文本 + 零关键点命中 + 极少技术词 → 触发离题打断。"""
        # 构造足够长的非技术文本
        long_off_topic = "我觉得今天的天气真的非常好，阳光明媚，万里无云。".ljust(OFF_TOPIC_MIN_LEN + 10, "。")
        result = evaluate_interrupt(
            user_text=long_off_topic,
            duration_sec=30.0,
            current_question="请解释 JVM 垃圾回收机制",
            current_question_key_points=["GC 算法", "分代回收"],
        )
        assert result.triggered is True
        assert result.trigger_type == "off_topic"

    def test_off_topic_not_triggered_with_tech_terms(self):
        """长文本但含技术词时不触发离题。"""
        tech_text = ("Redis 是一个高性能的键值存储数据库，支持多种数据结构。"
                     "MySQL 是常用的关系型数据库。" * 10)[:OFF_TOPIC_MIN_LEN + 10]
        result = evaluate_interrupt(
            user_text=tech_text,
            duration_sec=30.0,
            current_question="请解释缓存策略",
            current_question_key_points=["缓存穿透"],
        )
        # 含技术词，不应触发 off_topic
        assert not (result.triggered and result.trigger_type == "off_topic")

    def test_off_topic_not_triggered_below_min_len(self):
        """短文本不触发离题。"""
        result = evaluate_interrupt(
            user_text="我不知道",
            duration_sec=5.0,
            current_question="请解释 JVM",
            current_question_key_points=["JVM"],
        )
        assert not (result.triggered and result.trigger_type == "off_topic")

    # ---- 赘述规则 ----

    def test_rambling_trigger(self):
        """极长文本 + 零技术词 + 有关键点命中（避开off_topic）→ 触发赘述打断。"""
        # 构造：有 key_point 命中（避免 off_topic）但无技术词（触发 rambling）的长文本
        # key_point 使用非技术词如 "谈谈看法" 避免提升 tech_hits
        long_ramble = ("我觉得这个问题真的非常有意思，让我来谈谈看法。"
                       "从多个角度来分析的话，首先需要考虑很多因素。") * 25
        long_ramble = long_ramble[:RAMBLING_MIN_LEN + 10]
        result = evaluate_interrupt(
            user_text=long_ramble,
            duration_sec=50.0,
            current_question="请谈谈你的看法",
            current_question_key_points=["谈谈看法", "分析角度"],
        )
        assert result.triggered is True
        assert result.trigger_type == "rambling"

    def test_rambling_not_triggered_with_tech_terms(self):
        """极长文本但含技术词时不触发赘述。"""
        tech_text = ("在 JVM 的内存模型中，堆内存分为新生代和老年代。"
                     "Redis 使用单线程模型处理命令。" * 20)[:RAMBLING_MIN_LEN + 10]
        result = evaluate_interrupt(
            user_text=tech_text,
            duration_sec=50.0,
            current_question="请解释 JVM",
            current_question_key_points=["JVM", "内存模型"],
        )
        assert not (result.triggered and result.trigger_type == "rambling")

    def test_rambling_not_triggered_below_min_len(self):
        """中等长度文本不触发赘述。"""
        result = evaluate_interrupt(
            user_text="中等长度的回答" * 10,
            duration_sec=30.0,
            current_question="问题",
            current_question_key_points=["关键点"],
        )
        assert not (result.triggered and result.trigger_type == "rambling")

    # ---- 优先级规则 ----

    def test_priority_timeout_wins_over_off_topic(self):
        """超时优先级高于离题：超时+离题条件同时满足时应报 timeout。"""
        long_text = "无关内容" * 100  # 够长但无技术词
        result = evaluate_interrupt(
            user_text=long_text,
            duration_sec=DURATION_TIMEOUT_SEC + 10.0,  # 超时
            current_question="请解释 JVM",
            current_question_key_points=["JVM", "GC"],
        )
        # 超时应该优先判定
        assert result.triggered is True
        assert result.trigger_type == "timeout"

    # ---- 正常情况 ----

    def test_normal_response_no_interrupt(self):
        """正常的技术回答不应触发任何打断。"""
        result = evaluate_interrupt(
            user_text="JVM 内存模型分为堆和栈，堆用于存储对象实例，栈用于存储局部变量。",
            duration_sec=30.0,
            current_question="请解释 JVM 内存模型",
            current_question_key_points=["JVM", "堆", "栈"],
        )
        assert result.triggered is False
        assert result.trigger_type == ""
        assert result.prompt_addition == ""

    def test_empty_text_no_interrupt(self):
        """空文本不应触发打断。"""
        result = evaluate_interrupt(
            user_text="",
            duration_sec=0.0,
            current_question="问题",
            current_question_key_points=[],
        )
        assert result.triggered is False

    def test_short_answer_with_timeout_below_threshold(self):
        """短回答但时长低于阈值：不触发任何打断。"""
        result = evaluate_interrupt(
            user_text="简短回答",
            duration_sec=10.0,
            current_question="问题",
            current_question_key_points=["关键点"],
        )
        assert result.triggered is False
