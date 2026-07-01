"""test_role_criteria.py — 岗位评估标准模块单元测试。

测试目标: core/role_criteria.py
- get_role_criteria()  按岗位返回评估标准
- ROLE_SPECIFIC_CRITERIA 常量字典结构

该模块为零外部依赖的纯 Python 字典查询函数。
"""

import pytest
from core.role_criteria import get_role_criteria, ROLE_SPECIFIC_CRITERIA


# ============================================================
# get_role_criteria 测试
# ============================================================

class TestGetRoleCriteria:
    """验证岗位评估标准查询函数。"""

    # ---- 已知岗位 ----

    def test_java_backend_returns_specific_criteria(self):
        """Java后端岗位应返回特定的评估标准。"""
        criteria = get_role_criteria("Java后端开发工程师")
        assert len(criteria) > 50
        assert "JVM" in criteria
        assert "扣分项" in criteria

    def test_web_frontend_returns_specific_criteria(self):
        """Web前端岗位应返回特定的评估标准。"""
        criteria = get_role_criteria("Web前端开发工程师")
        assert len(criteria) > 50
        assert "JavaScript" in criteria or "Vue" in criteria or "React" in criteria
        assert "扣分项" in criteria

    def test_python_algorithm_returns_specific_criteria(self):
        """Python算法岗位应返回特定的评估标准。"""
        criteria = get_role_criteria("Python算法工程师")
        assert len(criteria) > 50
        assert "机器学习" in criteria or "深度学习" in criteria or "PyTorch" in criteria
        assert "扣分项" in criteria

    # ---- 未知岗位 ----

    def test_unknown_role_returns_generic_message(self):
        """未注册的岗位应返回通用评估提示。"""
        criteria = get_role_criteria("未知岗位测试")
        assert "通用" in criteria
        assert "暂无定制评估标准" in criteria

    def test_empty_role_returns_generic_message(self):
        """空字符串应返回通用提示。"""
        criteria = get_role_criteria("")
        assert "通用计算机岗位标准评估" in criteria

    # ---- 所有岗位 ----

    def test_all_known_roles_return_non_empty(self):
        """所有已注册的岗位都应返回非空评估标准。"""
        for role_name in ROLE_SPECIFIC_CRITERIA:
            criteria = get_role_criteria(role_name)
            assert criteria, f"岗位 '{role_name}' 返回了空评估标准"
            assert isinstance(criteria, str)

    def test_each_criteria_contains_evaluation_and_deduction(self):
        """每个岗位的评估标准应包含考察重点和扣分项。"""
        for role_name, criteria_text in ROLE_SPECIFIC_CRITERIA.items():
            assert "重点考察" in criteria_text or "考察" in criteria_text, \
                f"岗位 '{role_name}' 的评估标准缺少考察重点"
            assert "扣分项" in criteria_text, \
                f"岗位 '{role_name}' 的评估标准缺少扣分项"


# ============================================================
# ROLE_SPECIFIC_CRITERIA 常量结构测试
# ============================================================

class TestRoleSpecificCriteriaConstants:
    """验证 ROLE_SPECIFIC_CRITERIA 常量的结构完整性。"""

    def test_all_three_roles_registered(self):
        """应有恰好三个岗位注册。"""
        assert "Java后端开发工程师" in ROLE_SPECIFIC_CRITERIA
        assert "Web前端开发工程师" in ROLE_SPECIFIC_CRITERIA
        assert "Python算法工程师" in ROLE_SPECIFIC_CRITERIA
        assert len(ROLE_SPECIFIC_CRITERIA) == 3

    def test_all_values_are_strings(self):
        """所有值应为字符串类型。"""
        for role_name, criteria_text in ROLE_SPECIFIC_CRITERIA.items():
            assert isinstance(criteria_text, str), \
                f"岗位 '{role_name}' 的评估标准不是字符串"

    def test_java_criteria_contains_jvm(self):
        """Java 岗位评估标准应包含 JVM 相关内容。"""
        assert "JVM" in ROLE_SPECIFIC_CRITERIA["Java后端开发工程师"]

    def test_frontend_criteria_contains_browser(self):
        """前端岗位评估标准应包含浏览器相关内容。"""
        criteria = ROLE_SPECIFIC_CRITERIA["Web前端开发工程师"]
        assert "浏览器" in criteria or "JavaScript" in criteria

    def test_python_criteria_contains_ml(self):
        """Python 岗位评估标准应包含 ML/DL 相关内容。"""
        criteria = ROLE_SPECIFIC_CRITERIA["Python算法工程师"]
        has_ml = any(term in criteria for term in ["机器学习", "深度学习", "PyTorch", "TensorFlow", "神经网络"])
        assert has_ml, "Python算法岗位评估标准未找到机器学习相关内容"
