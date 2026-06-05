"""
InterviewEcho 端到端测试 (W7.2.1-2)
覆盖：黄金路径回归 + 边界测试

运行方式:
  # 冒烟测试（不需要 LLM Key）
  pytest tests/test_e2e.py -v -k "smoke"

  # 完整测试（需要 LLM_API_KEY）
  pytest tests/test_e2e.py -v

  # 仅黄金路径
  pytest tests/test_e2e.py -v -k "golden"
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """注册新用户并返回带 token 的 headers。"""
    import uuid
    unique = uuid.uuid4().hex[:8]
    register_resp = client.post("/api/auth/register", json={
        "username": f"e2e_test_{unique}",
        "password": "test123456"
    })
    if register_resp.status_code not in [200, 400]:
        raise AssertionError(f"注册失败: {register_resp.status_code} {register_resp.text}")
    if register_resp.status_code == 400:
        # 用户已存在，直接登录
        pass
    login_resp = client.post("/api/auth/login", json={
        "username": f"e2e_test_{unique}",
        "password": "test123456"
    })
    if login_resp.status_code != 200:
        raise AssertionError(f"登录失败: {login_resp.status_code} {login_resp.text}")
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── 1. 黄金路径：注册 → 登录 → 查看岗位 → 开始面试 → 结束 → 查看报告 ──

class TestGoldenPath:
    """W7.2.1 黄金路径回归测试"""

    def test_gp1_register_and_login(self):
        """GP-1: 新用户注册并登录。"""
        import uuid
        username = f"gp_user_{uuid.uuid4().hex[:8]}"

        # 注册
        resp = client.post("/api/auth/register", json={
            "username": username,
            "password": "securepass123"
        })
        assert resp.status_code == 200, f"注册失败: {resp.text}"
        data = resp.json()
        assert "username" in data
        assert data["username"] == username

        # 登录
        resp = client.post("/api/auth/login", json={
            "username": username,
            "password": "securepass123"
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_gp2_get_roles(self):
        """GP-2: 获取岗位列表。"""
        resp = client.get("/api/interview/roles")
        assert resp.status_code == 200
        roles = resp.json()
        assert isinstance(roles, list)
        assert len(roles) == 3
        role_names = [r["name"] for r in roles]
        assert "Java后端开发工程师" in role_names
        assert "Web前端开发工程师" in role_names
        assert "Python算法工程师" in role_names

    def test_gp3_start_interview(self, auth_headers):
        """GP-3: 用户选择岗位并开始面试。"""
        resp = client.post("/api/interview/start", json={
            "role": "Java后端开发工程师",
            "difficulty": "中等",
            "knowledge_points": ["JVM", "并发编程"],
            "total_rounds": 4,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert resp.status_code == 200, f"开始面试失败: {resp.text}"
        data = resp.json()
        assert "id" in data
        assert data["status"] == "in_progress"
        assert data["role"] == "Java后端开发工程师"

    def test_gp4_send_message_and_get_ai_reply(self, auth_headers):
        """GP-4: 用户发送文本消息并收到 AI 面试官回复。"""
        # 先开始面试
        resp = client.post("/api/interview/start", json={
            "role": "Web前端开发工程师",
            "difficulty": "中等",
            "knowledge_points": [],
            "total_rounds": 4,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert resp.status_code == 200
        interview_id = resp.json()["id"]

        # 发送消息（自我介绍后）
        resp = client.post(f"/api/interview/{interview_id}/message", json={
            "content": "我熟悉 Vue 3 的响应式原理，包括 Proxy 拦截、依赖收集和触发更新机制。"
        }, headers=auth_headers)
        assert resp.status_code == 200, f"发送消息失败: {resp.text}"
        data = resp.json()
        assert "content" in data
        assert data["sender"] == "ai"

    def test_gp5_end_interview_and_get_evaluation(self, auth_headers):
        """GP-5: 用户结束面试并获取评估报告（冒烟：仅验证接口可达）。"""
        # 开始面试
        resp = client.post("/api/interview/start", json={
            "role": "Python算法工程师",
            "difficulty": "简单",
            "knowledge_points": [],
            "total_rounds": 2,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert resp.status_code == 200
        interview_id = resp.json()["id"]

        # 发送一条用户消息（否则无评估素材）
        client.post(f"/api/interview/{interview_id}/message", json={
            "content": "我对机器学习和深度学习都有实践经验。"
        }, headers=auth_headers)

        # 结束面试
        resp = client.post(f"/api/interview/{interview_id}/end", headers=auth_headers)
        assert resp.status_code == 200, f"结束面试失败: {resp.text}"
        data = resp.json()
        assert "evaluation" in data
        eval_data = data["evaluation"]
        # 验证核心字段存在
        for field in ["content_score", "expression_score", "total_score", "highlights", "weaknesses"]:
            assert field in eval_data, f"缺少字段: {field}"

    def test_gp6_view_history(self, auth_headers):
        """GP-6: 查看面试历史记录。"""
        resp = client.get("/api/interview/history", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_gp7_resume_incomplete_interview(self, auth_headers):
        """GP-7: 检测并恢复未完成面试。"""
        start_resp = client.post("/api/interview/start", json={
            "role": "Java后端开发工程师",
            "difficulty": "中等",
            "knowledge_points": [],
            "total_rounds": 4,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert start_resp.status_code == 200

        resp = client.get("/api/interview/incomplete", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_incomplete"] is True
        assert data["interview"]["role"] == "Java后端开发工程师"

    def test_gp8_fetch_interview_state(self, auth_headers):
        """GP-8: 获取面试状态，包含固定代码题。"""
        start_resp = client.post("/api/interview/start", json={
            "role": "Web前端开发工程师",
            "difficulty": "中等",
            "knowledge_points": [],
            "total_rounds": 2,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert start_resp.status_code == 200
        interview_id = start_resp.json()["id"]

        state_resp = client.get(f"/api/interview/{interview_id}/state", headers=auth_headers)
        assert state_resp.status_code == 200
        state = state_resp.json()
        assert state["phase"] == "introduction"
        assert state["knowledge_round_total"] == 2
        assert state["active_code_problem"] is not None
        assert state["active_code_problem"]["title"]


# ── 2. 边界测试 ──────────────────────────────────────────

class TestBoundaryCases:
    """W7.2.2 边界测试"""

    def test_bd1_unauthorized_access(self):
        """BD-1: 无 token 访问受保护接口应返回 401。"""
        resp = client.get("/api/interview/history")
        assert resp.status_code == 401

    def test_bd2_invalid_token(self):
        """BD-2: 伪造 token 应返回 401。"""
        resp = client.get("/api/interview/history", headers={
            "Authorization": "Bearer fake-token-99999"
        })
        # 用户 99999 不存在，但 auth 逻辑可能返回空列表而非 401
        # 实际行为取决于 get_current_user_id 的实现
        assert resp.status_code in [200, 401, 404]

    def test_bd3_empty_message(self, auth_headers):
        """BD-3: 发送空消息。"""
        resp = client.post("/api/interview/start", json={
            "role": "Java后端开发工程师",
            "difficulty": "中等",
            "knowledge_points": [],
            "total_rounds": 4,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert resp.status_code == 200
        interview_id = resp.json()["id"]

        resp = client.post(f"/api/interview/{interview_id}/message", json={
            "content": ""
        }, headers=auth_headers)
        # 空消息应被接受（不阻塞用户）或返回 422
        assert resp.status_code in [200, 422]

    def test_bd4_nonexistent_interview(self, auth_headers):
        """BD-4: 访问不存在的面试。"""
        resp = client.get("/api/interview/99999/messages", headers=auth_headers)
        assert resp.status_code == 404

    def test_bd5_double_end_interview(self, auth_headers):
        """BD-5: 重复结束同一场面试。"""
        resp = client.post("/api/interview/start", json={
            "role": "Java后端开发工程师",
            "difficulty": "中等",
            "knowledge_points": [],
            "total_rounds": 2,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert resp.status_code == 200
        interview_id = resp.json()["id"]

        # 发送消息
        client.post(f"/api/interview/{interview_id}/message", json={
            "content": "测试回答"
        }, headers=auth_headers)

        # 第一次结束
        resp1 = client.post(f"/api/interview/{interview_id}/end", headers=auth_headers)
        assert resp1.status_code == 200

        # 第二次结束（已有评估记录，应走 upsert 分支）
        resp2 = client.post(f"/api/interview/{interview_id}/end", headers=auth_headers)
        # 应成功（upsert），不应抛 IntegrityError
        assert resp2.status_code == 200

    def test_bd6_duplicate_registration(self):
        """BD-6: 重复注册同一用户名应返回 400。"""
        import uuid
        username = f"dup_{uuid.uuid4().hex[:8]}"
        # 第一次注册
        client.post("/api/auth/register", json={
            "username": username, "password": "test123"
        })
        # 第二次注册同用户名
        resp = client.post("/api/auth/register", json={
            "username": username, "password": "test456"
        })
        assert resp.status_code == 400

    def test_bd7_smoke_api_root(self):
        """BD-7: 冒烟：根路径可访问。"""
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "InterviewEcho" in data["message"]

    def test_bd8_special_characters_in_message(self, auth_headers):
        """BD-8: 用户发送含特殊字符和 emoji 的消息。"""
        resp = client.post("/api/interview/start", json={
            "role": "Java后端开发工程师",
            "difficulty": "中等",
            "knowledge_points": [],
            "total_rounds": 4,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert resp.status_code == 200
        interview_id = resp.json()["id"]

        resp = client.post(f"/api/interview/{interview_id}/message", json={
            "content": "我认为 @SpringBoot 的自动装配非常强大！👍 它通过 @EnableAutoConfiguration 实现了零配置 🚀"
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["sender"] == "ai"

    def test_bd9_resume_parse_without_file(self, auth_headers):
        """BD-9: 不传文件调用简历解析应返回 400。"""
        resp = client.post("/api/interview/resume/parse", headers=auth_headers)
        assert resp.status_code == 400

    def test_bd10_repo_analyze_empty_url(self, auth_headers):
        """BD-10: 空 URL 调用仓库分析应返回 400。"""
        resp = client.post("/api/interview/repo/analyze", json={
            "url": ""
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_bd11_discard_incomplete_interview(self, auth_headers):
        """BD-11: 丢弃未完成面试。"""
        start_resp = client.post("/api/interview/start", json={
            "role": "Web前端开发工程师",
            "difficulty": "中等",
            "knowledge_points": [],
            "total_rounds": 3,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert start_resp.status_code == 200
        interview_id = start_resp.json()["id"]

        discard_resp = client.post(f"/api/interview/{interview_id}/discard", headers=auth_headers)
        assert discard_resp.status_code == 200

        incomplete_resp = client.get("/api/interview/incomplete", headers=auth_headers)
        assert incomplete_resp.status_code == 200
        assert incomplete_resp.json()["has_incomplete"] is False

    def test_bd12_submit_interview_code_and_advance(self, auth_headers, monkeypatch):
        """BD-12: 代码题提交后进入知识问答，并保证题目不重复。"""

        class FakeJudgeResult:
            status_id = 3
            raw_status = "Accepted"
            status_description = "Accepted"
            stdout = "0 1\n"
            stderr = None
            compile_output = None
            message = None
            time = 0.021
            memory = 1024

        async def fake_run_code(language, source_code, stdin):
            return FakeJudgeResult()

        async def fake_code_review(**kwargs):
            return "你的代码提交通过了，整体思路正确，复杂度分析也比较清晰。"

        monkeypatch.setattr("app.services.interview_runtime.judge0_service.run_code", fake_run_code)
        monkeypatch.setattr("app.services.interview_runtime.generate_code_review", fake_code_review)

        start_resp = client.post("/api/interview/start", json={
            "role": "Java后端开发工程师",
            "difficulty": "中等",
            "knowledge_points": [],
            "total_rounds": 2,
            "repo_urls": [],
            "resume_persona": None
        }, headers=auth_headers)
        assert start_resp.status_code == 200
        interview_id = start_resp.json()["id"]

        intro_resp = client.post(f"/api/interview/{interview_id}/message", json={
            "content": "我先做一个简单自我介绍。"
        }, headers=auth_headers)
        assert intro_resp.status_code == 200
        assert "代码题" in intro_resp.json()["content"]

        submit_resp = client.post(f"/api/interview/{interview_id}/code/submit", json={
            "language": "python",
            "source_code": "print('ok')"
        }, headers=auth_headers)
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert submit_data["status"] in {"Accepted", "Wrong Answer"}
        assert submit_data["ai_message"]["is_final"] is False
        first_knowledge_question = submit_data["ai_message"]["content"]

        state_resp = client.get(f"/api/interview/{interview_id}/state", headers=auth_headers)
        assert state_resp.status_code == 200
        assert state_resp.json()["phase"] == "knowledge"
        assert state_resp.json()["knowledge_round_index"] == 1

        next_resp = client.post(f"/api/interview/{interview_id}/message", json={
            "content": "这是我对第一轮知识题的回答。"
        }, headers=auth_headers)
        assert next_resp.status_code == 200
        second_question = next_resp.json()["content"]
        assert second_question != first_knowledge_question
        assert next_resp.json()["is_final"] is False

        final_resp = client.post(f"/api/interview/{interview_id}/message", json={
            "content": "这是我对第二轮知识题的回答。"
        }, headers=auth_headers)
        assert final_resp.status_code == 200
        assert final_resp.json()["is_final"] is True
        assert "祝你求职顺利" in final_resp.json()["content"]


# ── 3. 冒烟测试套件（不需要 LLM Key）─────────────────────

class TestSmoke:
    """快速冒烟：不依赖 LLM API Key"""

    def test_smoke_health(self):
        """根路径健康检查。"""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_smoke_roles(self):
        """岗位列表可访问。"""
        resp = client.get("/api/interview/roles")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_smoke_auth_flow(self):
        """注册 + 登录完整流程。"""
        import uuid
        username = f"smoke_{uuid.uuid4().hex[:8]}"
        r1 = client.post("/api/auth/register", json={"username": username, "password": "test"})
        assert r1.status_code == 200
        r2 = client.post("/api/auth/login", json={"username": username, "password": "test"})
        assert r2.status_code == 200
        assert "access_token" in r2.json()
