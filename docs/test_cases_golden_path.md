# InterviewEcho 黄金路径测试用例与边界测试 (W7.2.1-2)

> 版本：v0.3-rev3 | 日期：2026-05-19 | 测试环境：UAT

---

## 1. 测试策略概述

本测试套件覆盖 InterviewEcho 的两类测试场景：

- **黄金路径（5 条）**：模拟真实用户从注册到获取评估报告的完整流程
- **边界测试（10 条）**：验证系统在异常输入、缺失鉴权、重复操作等边界条件下的健壮性

测试框架：`pytest` + `pytest-asyncio` + FastAPI `TestClient`  
测试文件：`backend/tests/test_e2e.py`

---

## 2. 黄金路径测试用例

### GP-1: 用户注册与登录

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证注册和登录流程正常 |
| **前置条件** | 数据库可用，用户不存在 |
| **步骤** | 1. POST `/api/auth/register` 注册新用户<br>2. POST `/api/auth/login` 使用相同凭据登录 |
| **预期结果** | 注册返回 200 + username；登录返回 200 + access_token |
| **对应函数** | `test_gp1_register_and_login` |

### GP-2: 获取岗位列表

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证岗位接口返回 3 个预设岗位 |
| **前置条件** | 无 |
| **步骤** | GET `/api/interview/roles` |
| **预期结果** | 200，返回 3 个岗位（Java / Web / Python），每个包含 name/key/icon/desc |
| **对应函数** | `test_gp2_get_roles` |

### GP-3: 开始一场面试

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证用户选择岗位后可成功开始面试 |
| **前置条件** | 用户已登录（有效 token） |
| **步骤** | POST `/api/interview/start`，携带 role/difficulty/knowledge_points/total_rounds |
| **预期结果** | 200，返回 interview 对象（id/status=in_progress/role），AI 发送开场自我介绍引导 |
| **对应函数** | `test_gp3_start_interview` |

### GP-4: 发送消息并收到 AI 回复

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证面试中的消息往返（核心交互链） |
| **前置条件** | 面试已开始（status=in_progress） |
| **步骤** | 1. 开始面试<br>2. POST `/api/interview/{id}/message` 发送用户回答 |
| **预期结果** | 200，返回 AI 面试官消息（sender=ai），含追问或下一题 |
| **对应函数** | `test_gp4_send_message_and_get_ai_reply` |

### GP-5: 结束面试并获取评估

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证面试结束 → LLM 评估 → 报告生成完整链路 |
| **前置条件** | 面试已开始，至少有 1 条用户消息 |
| **步骤** | 1. 开始面试<br>2. 发送用户回答<br>3. POST `/api/interview/{id}/end` |
| **预期结果** | 200，返回 evaluation 对象（content_score/expression_score/total_score/highlights/weaknesses），数据库 evaluations 表写入成功 |
| **对应函数** | `test_gp5_end_interview_and_get_evaluation` |

### GP-6: 查看面试历史

| 项目 | 内容 |
|------|------|
| **测试目标** | 验证用户可查看自己的历史面试记录 |
| **前置条件** | 用户已完成至少 1 场面试 |
| **步骤** | GET `/api/interview/history` |
| **预期结果** | 200，返回列表（可为空），每项含 id/role/difficulty/total_score/created_at |
| **对应函数** | `test_gp6_view_history` |

---

## 3. 边界测试用例

| ID | 测试场景 | 输入/条件 | 预期行为 | 对应函数 |
|----|---------|-----------|---------|---------|
| BD-1 | 未授权访问 | 无 Authorization Header 访问 /history | 401 | `test_bd1_unauthorized_access` |
| BD-2 | 伪造 Token | Bearer fake-token-99999（不存在的用户） | 401 或 200（空列表） | `test_bd2_invalid_token` |
| BD-3 | 空消息发送 | content="" | 200 接受 或 422 拒绝 | `test_bd3_empty_message` |
| BD-4 | 不存在的面试 ID | GET /interview/99999/messages | 404 | `test_bd4_nonexistent_interview` |
| BD-5 | 重复结束面试 | 对同一 interview 调用两次 /end | 两次均 200（upsert） | `test_bd5_double_end_interview` |
| BD-6 | 重复注册 | 同一 username 注册两次 | 第一次 200，第二次 400 | `test_bd6_duplicate_registration` |
| BD-7 | 根路径冒烟 | GET / | 200 + "InterviewEcho" | `test_bd7_smoke_api_root` |
| BD-8 | 特殊字符 & Emoji | 消息含 @、中文标点、👍🚀 | 200，AI 正常回复 | `test_bd8_special_characters_in_message` |
| BD-9 | 空简历解析请求 | POST /resume/parse 无 file 无 text | 400 | `test_bd9_resume_parse_without_file` |
| BD-10 | 空 GitHub URL | /repo/analyze url="" | 400 | `test_bd10_repo_analyze_empty_url` |

---

## 4. 测试执行方式

### 4.1 冒烟测试（无需 LLM Key）

```powershell
cd backend
pytest tests/test_e2e.py -v -k "smoke"
```

### 4.2 完整边界测试（无需 LLM Key）

```powershell
pytest tests/test_e2e.py -v -k "boundary or smoke"
```

### 4.3 黄金路径测试（需要 LLM_API_KEY）

```powershell
pytest tests/test_e2e.py -v -k "golden"
```

### 4.4 全量测试

```powershell
# 设置环境变量
$env:LLM_API_KEY = "sk-xxx"
$env:LLM_BASE_URL = "https://api.deepseek.com"
$env:DB_HOST = "localhost"
$env:DB_PASS = "your_password"

pytest tests/test_e2e.py -v --tb=long
```

---

## 5. 已知限制与后续计划

| 限制 | 说明 | 计划 |
|------|------|------|
| LLM 依赖 | GP-4/5 依赖真实 LLM API | 引入 mock LLM fixture（v0.4） |
| 语音测试 | E2E 未覆盖语音上传路径 | 需要 Whisper 环境的集成测试（v0.4） |
| 代码判题 | Judge0 路径未在 E2E 中覆盖 | 需要 Docker Judge0 环境的专项测试 |
| 前端 E2E | 本文件仅覆盖后端 API | 前端 Playwright 测试见 `frontend/tests/e2e/` |
