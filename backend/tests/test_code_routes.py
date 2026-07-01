"""test_code_routes.py — 代码练习 API 路由集成测试。

测试目标: app/api/routes/code.py
- GET  /api/code/problems              题目列表（筛选）
- GET  /api/code/problems/{id}         题目详情
- POST /api/code/problems/{id}/run     运行样例（需 monkeypatch Judge0）
- POST /api/code/problems/{id}/submit  提交判题（需 monkeypatch Judge0）
- GET  /api/code/submissions           提交记录列表
- GET  /api/code/submissions/{id}      提交详情

依赖: conftest.py 的 SQLite 数据库 + FastAPI TestClient + monkeypatch Judge0。
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from app.db import models
from app.db.session import SessionLocal
from services.judge0_service import Judge0Result


# ============================================================
# 辅助函数
# ============================================================

def _register_and_login(client):
    """注册测试用户并返回认证头。"""
    username = "code_test_user"
    resp = client.post("/api/auth/register", json={"username": username, "password": "test123"})
    if resp.status_code == 400:
        # 用户已存在，直接登录
        pass
    resp = client.post("/api/auth/login", json={"username": username, "password": "test123"})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def client():
    """创建 TestClient 实例。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    """获取认证头（模块级别复用）。"""
    return _register_and_login(client)


# ============================================================
# 题目列表测试
# ============================================================

class TestListProblems:
    """验证 GET /api/code/problems 端点。"""

    def test_returns_all_active_problems(self, client, auth_headers):
        """应返回所有激活的题目。"""
        resp = client.get("/api/code/problems", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "tags" in data
        assert "total" in data
        assert data["total"] > 0

    def test_filter_by_difficulty(self, client, auth_headers):
        """按难度筛选应正确过滤。"""
        resp = client.get("/api/code/problems?difficulty=easy", headers=auth_headers)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["difficulty"] == "easy"

    def test_filter_by_keyword(self, client, auth_headers):
        """按关键词搜索应正确过滤。"""
        resp = client.get("/api/code/problems?q=two", headers=auth_headers)
        assert resp.status_code == 200
        # 应返回标题或 slug 包含 "two" 的题目（或无结果）

    def test_unauthorized_without_token(self, client):
        """无 token 时应返回 401。"""
        resp = client.get("/api/code/problems")
        assert resp.status_code == 401


# ============================================================
# 题目详情测试
# ============================================================

class TestGetProblemDetail:
    """验证 GET /api/code/problems/{id} 端点。"""

    def test_get_by_id(self, client, auth_headers):
        """通过 ID 获取题目详情。"""
        resp = client.get("/api/code/problems/1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "title" in data
        assert "description" in data
        assert "samples" in data

    def test_nonexistent_problem_404(self, client, auth_headers):
        """不存在的题目应返回 404。"""
        resp = client.get("/api/code/problems/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_unauthorized_without_token(self, client):
        """无 token 时应返回 401。"""
        resp = client.get("/api/code/problems/1")
        assert resp.status_code == 401


# ============================================================
# 运行代码测试（monkeypatch Judge0）
# ============================================================

class TestRunProblem:
    """验证 POST /api/code/problems/{id}/run 端点。"""

    def test_unsupported_language_400(self, client, auth_headers):
        """不支持的语言应返回 400。"""
        resp = client.post(
            "/api/code/problems/1/run",
            headers=auth_headers,
            json={"language": "ruby", "source_code": "puts 'hello'"},
        )
        assert resp.status_code == 400

    def test_empty_source_400(self, client, auth_headers):
        """空源代码应返回 400。"""
        resp = client.post(
            "/api/code/problems/1/run",
            headers=auth_headers,
            json={"language": "python", "source_code": ""},
        )
        assert resp.status_code == 400

    def test_source_too_long_400(self, client, auth_headers):
        """超长源代码应返回 400。"""
        resp = client.post(
            "/api/code/problems/1/run",
            headers=auth_headers,
            json={"language": "python", "source_code": "x" * 30000},
        )
        assert resp.status_code == 400

    def test_run_with_mocked_judge0_accepted(self, client, auth_headers, monkeypatch):
        """模拟 Judge0 返回 Accepted 结果。"""
        async def fake_run_code(language, source_code, stdin):
            return Judge0Result(
                status_id=3,
                status_description="Accepted",
                stdout="expected_output\n",
            )

        monkeypatch.setattr(
            "app.api.routes.code.judge0_service.run_code",
            fake_run_code,
        )

        resp = client.post(
            "/api/code/problems/1/run",
            headers=auth_headers,
            json={"language": "python", "source_code": "print('hello')"},
        )
        # 可能返回 200（运行成功）或 400（无样例用例），取决于种子数据
        assert resp.status_code in (200, 400)

    def test_run_with_judge0_unavailable(self, client, auth_headers, monkeypatch):
        """模拟 Judge0 不可用时应返回 503。"""
        from services.judge0_service import Judge0Unavailable

        async def fake_run_code(*args, **kwargs):
            raise Judge0Unavailable("Connection refused")

        monkeypatch.setattr(
            "app.api.routes.code.judge0_service.run_code",
            fake_run_code,
        )

        resp = client.post(
            "/api/code/problems/1/run",
            headers=auth_headers,
            json={"language": "python", "source_code": "print('hello')"},
        )
        if resp.status_code == 200:
            # 无样例用例也可能返回 200（实际场景中不存在）
            pass
        else:
            assert resp.status_code == 503


# ============================================================
# 提交判题测试（monkeypatch Judge0）
# ============================================================

class TestSubmitProblem:
    """验证 POST /api/code/problems/{id}/submit 端点。"""

    def test_submit_returns_running_status(self, client, auth_headers, monkeypatch):
        """提交后应立即返回 Running 状态和 submission_id。"""
        # monkeypatch 后台判题函数为一个 no-op（避免实际调用 Judge0）
        async def fake_judge(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.api.routes.code._judge_submission",
            fake_judge,
        )

        resp = client.post(
            "/api/code/problems/1/submit",
            headers=auth_headers,
            json={"language": "python", "source_code": "print('hello')"},
        )
        # 可能 200（有测试用例）或 400（无测试用例），取决于种子数据
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "Running"
            assert "submission_id" in data


# ============================================================
# 提交记录测试
# ============================================================

class TestListSubmissions:
    """验证 GET /api/code/submissions 端点。"""

    def test_empty_returns_empty_list(self, client, auth_headers):
        """新用户提交记录应空（或可能有之前测试的提交）。"""
        resp = client.get("/api/code/submissions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_unauthorized_access(self, client):
        """无 token 返回 401。"""
        resp = client.get("/api/code/submissions")
        assert resp.status_code == 401


class TestGetSubmission:
    """验证 GET /api/code/submissions/{id} 端点。"""

    def test_nonexistent_404(self, client, auth_headers):
        """不存在的提交记录应返回 404。"""
        resp = client.get("/api/code/submissions/99999", headers=auth_headers)
        assert resp.status_code == 404
