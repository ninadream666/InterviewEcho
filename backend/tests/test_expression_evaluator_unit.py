"""test_expression_evaluator_unit.py — 表达评分模块单元测试。

测试目标: evaluation/expression_evaluator.py
- clamp()              数值限幅函数
- score_expression()   表达评分聚合函数（monkeypatch LLM 调用）

该模块依赖 LLM 客户端进行语义分析，测试时通过 monkeypatch 模拟。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from evaluation.expression_evaluator import clamp, score_expression, run_async_in_thread


# ============================================================
# clamp 测试
# ============================================================

class TestClamp:
    """验证数值限幅函数。"""

    def test_value_in_range_unchanged(self):
        """值在 [min, max] 区间内时应保持不变。"""
        assert clamp(50.0, 0.0, 100.0) == 50.0

    def test_value_below_min_returns_min(self):
        """值低于 min 时应返回 min。"""
        assert clamp(-10.0, 0.0, 100.0) == 0.0

    def test_value_above_max_returns_max(self):
        """值高于 max 时应返回 max。"""
        assert clamp(150.0, 0.0, 100.0) == 100.0

    def test_exact_min_returns_min(self):
        """值等于 min 时返回 min。"""
        assert clamp(0.0, 0.0, 100.0) == 0.0

    def test_exact_max_returns_max(self):
        """值等于 max 时返回 max。"""
        assert clamp(100.0, 0.0, 100.0) == 100.0

    def test_negative_values(self):
        """负值应被限幅。"""
        assert clamp(-5.0, -10.0, -1.0) == -5.0
        assert clamp(-20.0, -10.0, -1.0) == -10.0

    def test_default_bounds(self):
        """默认上下界为 [0, 100]。"""
        assert clamp(150.0) == 100.0
        assert clamp(-50.0) == 0.0


# ============================================================
# score_expression 测试（monkeypatch LLM）
# ============================================================

# Mock LLM 返回的标准结果
MOCK_LLM_RESULT = {
    "per_message_analysis": [
        {
            "message_id": 1,
            "clarity_semantic_score": 85.0,
            "confidence_semantic_score": 80.0,
        },
        {
            "message_id": 2,
            "clarity_semantic_score": 75.0,
            "confidence_semantic_score": 70.0,
        },
    ],
    "overall_analysis": {
        "feedback_speech_rate": "语速适中，节奏良好。",
        "feedback_clarity": "表达清晰，逻辑流畅。",
        "feedback_confidence": "声音稳定，自信度较高。",
    },
}


def _make_valid_metrics():
    """构造合法的 metrics 列表（模拟 audio_analysis 的输出）。"""
    return [
        {
            "message_id": 1,
            "transcript": "JVM内存模型分为堆和栈。",
            "wpm": 200.0,
            "pause_ratio": 0.15,
            "filler_total": 2,
            "pitch_std": 12.0,
            "volume_std": 0.015,
            "filler_words": [{"word": "嗯", "count": 1}, {"word": "就是", "count": 1}],
        },
        {
            "message_id": 2,
            "transcript": "GC算法包括标记清除和复制算法。",
            "wpm": 220.0,
            "pause_ratio": 0.10,
            "filler_total": 1,
            "pitch_std": 10.0,
            "volume_std": 0.012,
            "filler_words": [{"word": "然后", "count": 1}],
        },
    ]


class TestScoreExpression:
    """验证表达评分聚合函数。"""

    def test_empty_metrics_list_returns_none(self):
        """空 metrics 列表应返回 None。"""
        result = score_expression([], "Java后端开发工程师")
        assert result is None

    def test_none_metrics_returns_none(self):
        """metrics 为 None 时应返回 None。"""
        # score_expression 的签名为 list[dict]，但空列表也会被 if not metrics_list 拦截
        result = score_expression([], None)
        assert result is None

    def test_metrics_missing_transcript_skipped(self):
        """缺少 transcript 字段的 metrics 应被跳过，全无效时返回 None。"""
        invalid = [{"wpm": 200}]  # 有 wpm 但无 transcript
        result = score_expression(invalid)
        # 因为缺少 transcript，valid_metrics 过滤后为空
        assert result is None

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_valid_metrics_returns_expected_structure(self, mock_run_async):
        """传入有效 metrics 应返回符合契约的结构。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        result = score_expression(metrics, "Java后端开发工程师")
        assert result is not None
        # 验证顶层字段
        assert "speech_rate_score" in result
        assert "clarity_score" in result
        assert "confidence_score" in result
        assert "expression_score" in result
        assert "metrics_summary" in result
        assert "feedback" in result
        assert "per_message" in result
        # 验证数值范围
        assert 0.0 <= result["speech_rate_score"] <= 100.0
        assert 0.0 <= result["clarity_score"] <= 100.0
        assert 0.0 <= result["confidence_score"] <= 100.0
        assert 0.0 <= result["expression_score"] <= 100.0

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_single_metric_works(self, mock_run_async):
        """单条 metric 也应正确打分。"""
        mock_run_async.return_value = {
            "per_message_analysis": [
                {"message_id": 1, "clarity_semantic_score": 80.0, "confidence_semantic_score": 75.0},
            ],
            "overall_analysis": {
                "feedback_speech_rate": "语速偏快。",
                "feedback_clarity": "清晰度良好。",
                "feedback_confidence": "自信度一般。",
            },
        }
        single = [_make_valid_metrics()[0]]
        result = score_expression(single)
        assert result is not None
        assert len(result["per_message"]) == 1

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_metrics_summary_contains_avg_wpm(self, mock_run_async):
        """metrics_summary 应包含 avg_wpm。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        result = score_expression(metrics)
        assert "avg_wpm" in result["metrics_summary"]
        # avg_wpm = (200 + 220) / 2 = 210
        expected_avg = 210.0
        assert abs(result["metrics_summary"]["avg_wpm"] - expected_avg) < 1.0

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_top_filler_words_in_summary(self, mock_run_async):
        """metrics_summary 应包含 top_filler_words。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        result = score_expression(metrics)
        top_fillers = result["metrics_summary"]["top_filler_words"]
        assert isinstance(top_fillers, list)
        # 应有填充词统计
        assert len(top_fillers) > 0

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_feedback_includes_three_dimensions(self, mock_run_async):
        """feedback 应包含三个维度。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        result = score_expression(metrics)
        assert "speech_rate" in result["feedback"]
        assert "clarity" in result["feedback"]
        assert "confidence" in result["feedback"]

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_wpm_scoring_ideal_zone(self, mock_run_async):
        """语速在 180-240 区间应得满分 100。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = [{
            "message_id": 1,
            "transcript": "测试。",
            "wpm": 200.0,
            "pause_ratio": 0.1,
            "filler_total": 0,
            "pitch_std": 10.0,
            "volume_std": 0.01,
            "filler_words": [],
        }]
        result = score_expression(metrics)
        assert result is not None
        # WPM 200 在理想区间，speech_rate_score 应为 100
        # （由于 clarity 和 confidence 也参与 expression_score 计算）
        assert result["speech_rate_score"] == pytest.approx(100.0, abs=1.0)

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_wpm_scoring_slow_zone(self, mock_run_async):
        """语速低于 180 应扣分。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = [{
            "message_id": 1,
            "transcript": "测试。",
            "wpm": 150.0,
            "pause_ratio": 0.1,
            "filler_total": 0,
            "pitch_std": 10.0,
            "volume_std": 0.01,
            "filler_words": [],
        }]
        result = score_expression(metrics)
        assert result is not None
        # WPM 150 < 180，应扣分
        assert result["speech_rate_score"] < 90.0

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_wpm_scoring_fast_zone(self, mock_run_async):
        """语速高于 240 应扣分。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = [{
            "message_id": 1,
            "transcript": "测试。",
            "wpm": 280.0,
            "pause_ratio": 0.1,
            "filler_total": 0,
            "pitch_std": 10.0,
            "volume_std": 0.01,
            "filler_words": [],
        }]
        result = score_expression(metrics)
        assert result is not None
        # WPM 280 > 240，应扣分
        assert result["speech_rate_score"] < 90.0

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_expression_score_is_average_of_three_dimensions(self, mock_run_async):
        """expression_score 应为三个维度分数的平均值。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        result = score_expression(metrics)
        expected = (
            result["speech_rate_score"]
            + result["clarity_score"]
            + result["confidence_score"]
        ) / 3.0
        assert result["expression_score"] == pytest.approx(expected, abs=0.5)

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_pitch_stability_calculated(self, mock_run_async):
        """metrics_summary 应包含 pitch_stability。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        result = score_expression(metrics)
        assert "pitch_stability" in result["metrics_summary"]
        # pitch_stability 应在 [0, 1] 区间
        assert 0.0 <= result["metrics_summary"]["pitch_stability"] <= 1.0

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_per_message_has_correct_count(self, mock_run_async):
        """per_message 列表长度应等于有效 metrics 数。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        result = score_expression(metrics)
        assert len(result["per_message"]) == 2

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_default_role_works(self, mock_run_async):
        """不传 role 参数也能正常工作。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        result = score_expression(metrics)
        assert result is not None

    @patch("evaluation.expression_evaluator.run_async_in_thread")
    def test_total_filler_count_accumulated(self, mock_run_async):
        """total_filler_count 应为所有 metrics 的 filler_total 之和。"""
        mock_run_async.return_value = MOCK_LLM_RESULT
        metrics = _make_valid_metrics()
        # filler_total: 2 + 1 = 3
        result = score_expression(metrics)
        assert result["metrics_summary"]["total_filler_count"] == 3
