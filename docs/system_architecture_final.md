# InterviewEcho 系统架构最终文档

> 版本：v0.3-rev3 (Final) | 日期：2026-05-24  
> 项目：AI 模拟面试与能力提升平台  
> 团队：SE_Economy_and_Management

---

## 1. 系统概述

InterviewEcho 是一个深度整合 **RAG（检索增强生成）** 与 **LLM（大语言模型）** 的 AI 模拟面试平台，专为计算机相关专业学生打造。系统支持语音/文本双模态交互，提供从简历解析、GitHub 项目深挖、知识库出题到代码在线判题、多维度评估报告的全链路面试模拟体验。

### 1.1 核心能力

| 能力 | 描述 | 技术支撑 |
|------|------|---------|
| 智能面试对话 | 基于 RAG + LLM 的多轮深度面试 | DeepSeek/OpenAI API + 本地知识库 |
| 语音交互 | 语音输入 → Whisper 转写 → AI 回复 | openai-whisper + librosa |
| 简历解析 | PDF/文本简历 → 结构化 Persona → 面试注入 | pypdf + LLM |
| GitHub 深挖 | 公开仓库抓取 → 项目级定制面试题 | GitHub API / 页面抓取 + LLM |
| 代码判题 | 多语言 ACM 模式在线评测 | Judge0 (Docker 自建) |
| 多维度评估 | 内容 + 表达 + 场景 + 解题四维评分 | LLM 评估 + 声学特征分析 |
| 学习计划 | 基于面试弱点的个性化提升方案 | LLM 生成 |

---

## 2. 技术架构

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                    用户层 (Client)                       │
│  ┌──────────────────┐  ┌──────────────────────────────┐ │
│  │   Web 浏览器      │  │   移动端浏览器 (响应式适配)    │ │
│  └────────┬─────────┘  └──────────────┬───────────────┘ │
└───────────┼──────────────────────────┼──────────────────┘
            │          HTTPS            │
            ▼                           ▼
┌─────────────────────────────────────────────────────────┐
│                   接入层 (Gateway)                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │              Nginx (反向代理 + 静态托管)             │ │
│  └────────────────────────┬───────────────────────────┘ │
└───────────────────────────┼──────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│  前端 (Vue 3) │  │ 后端 (FastAPI)│  │ Judge0 (C++) │
│  Vite +       │  │  Python 3.12 │  │ 代码判题服务   │
│  Tailwind CSS │  │  Uvicorn     │  │              │
└───────────────┘  └──────┬───────┘  └──────┬───────┘
                          │                  │
        ┌─────────────────┼──────┬───────────┘
        ▼                 ▼      ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   MySQL 8.0  │  │  Redis 7     │  │ RAG 向量索引  │
│  (持久化存储)  │  │  (缓存/队列)  │  │ (本地 JSON)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 2.2 技术栈

| 层 | 技术 | 版本 | 说明 |
|----|------|------|------|
| **前端框架** | Vue 3 (Composition API) | 3.4 | 响应式 UI |
| **构建工具** | Vite | 5.1 | 开发/构建 |
| **UI 库** | Element Plus + Tailwind CSS | 2.6 / 3.4 | 组件 + 原子化样式 |
| **状态管理** | Pinia | 2.1 | Vue 3 官方推荐 |
| **图表** | ECharts + vue-echarts | 6.0 | 评估报告可视化 |
| **代码编辑器** | Monaco Editor | — | 代码练习沙箱 |
| **后端框架** | FastAPI | 0.135 | 高性能异步 Python |
| **ORM** | SQLAlchemy | 2.0 | 数据库映射 |
| **数据库** | MySQL | 8.0 | 持久化存储 |
| **缓存** | Redis | 7.0 | 分布式缓存（可选） |
| **LLM 客户端** | openai (Python SDK) | 2.29 | OpenAI/DeepSeek API |
| **向量模型** | text-embedding-3-small | — | RAG 嵌入 |
| **语音识别** | openai-whisper | 20250625 | STT 转写 |
| **音频分析** | librosa + soundfile | 0.10 / 0.12 | 语速/音高/停顿 |
| **PDF 解析** | pypdf | 4.3 | 简历 PDF 提取 |
| **代码判题** | Judge0 (Docker) | 1.13 | 多语言在线评测 |
| **容器化** | Docker + Docker Compose | 24+ | 部署编排 |
| **CI/CD** | GitHub Actions | — | 自动测试 + 构建 |

---

## 3. 模块架构

### 3.1 后端模块 (backend/)

```
backend/
├── main.py                     # FastAPI 入口，CORS + 路由注册
├── requirements.txt            # Python 依赖
├── Dockerfile                  # 容器构建
├── core/
│   ├── config.py               # 环境变量配置（Pydantic Settings）
│   ├── llm_service.py          # LLM 调用封装（对话/评估/润色/问题生成）
│   ├── prompts.py              # Prompt 模板管理
│   └── role_criteria.py        # 岗位特定评估标准
├── db/
│   ├── database.py             # 数据库连接（SQLAlchemy + PyMySQL）
│   ├── models.py               # ORM 模型（7 张表）
│   ├── schemas.py              # Pydantic 数据校验
│   ├── seed_code_problems.py   # 题库种子数据
│   └── code_problem_bank.py    # 题库管理
├── routers/
│   ├── auth.py                 # 注册/登录（bcrypt + fake JWT）
│   ├── interview.py            # 面试核心路由（~700 行）
│   └── code.py                 # 代码练习路由
├── services/
│   ├── rag_service.py          # RAG 向量检索
│   ├── stt_service.py          # Whisper 语音转写
│   ├── audio_analysis.py       # 声学特征分析（WPM/停顿/音高）
│   ├── resume_parser.py        # 简历解析（PDF + LLM）
│   ├── repo_analyzer.py        # GitHub 仓库分析
│   ├── judge0_service.py       # Judge0 API 封装
│   └── interrupt_policy.py     # 打断策略（超时/跑题/啰嗦）
├── evaluation/
│   └── expression_evaluator.py # 表达分融合引擎
├── rag/                        # RAG 向量索引存储
├── sql/                        # 数据库迁移脚本（5 个）
└── tests/                      # 测试套件
```

### 3.2 前端模块 (frontend/)

```
frontend/
├── src/
│   ├── main.js                 # Vue 应用入口
│   ├── App.vue                 # 根组件
│   ├── style.css               # 全局样式（Tailwind）
│   ├── api/                    # Axios API 封装
│   ├── router/                 # Vue Router 路由
│   ├── stores/                 # Pinia 状态管理
│   ├── layouts/                # 布局组件
│   ├── components/             # 可复用组件
│   │   ├── ResumeUpload.vue    # 简历上传
│   │   ├── CodeEditor.vue      # Monaco 代码编辑器
│   │   ├── EvalDimensionPanel.vue # 评估维度面板
│   │   └── ...
│   └── views/                  # 页面视图
│       ├── AuthView.vue        # 登录/注册
│       ├── DashboardView.vue   # 岗位选择
│       ├── InterviewRoomView.vue # 面试房间（核心）
│       ├── ReportView.vue      # 评估报告
│       └── ...
└── package.json
```

### 3.3 知识库 (knowledge-base/)

```
knowledge-base/
├── java-backend/
│   ├── questions.json          # 题库（~30 题，business_scenario/problem_solving/behavioral）
│   ├── interview_excellent_answers.md  # 优秀回答范例
│   └── *.md                    # 知识点 Markdown
├── web-frontend/               # 同上结构
└── python-algorithm/           # 同上结构
```

---

## 4. 核心数据流

### 4.1 面试对话流

```
用户输入（文本/语音）
    │
    ▼
┌──────────────────────┐
│ 1. 语音转写（Whisper）│  ← 仅语音路径
│ 2. 文本润色（LLM）    │  ← 加标点 + 修正谐音
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 3. 保存 User Message │  → messages 表
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 4. 阶段判定           │  ← resume / repo / knowledge
│ 5. 题库选题 + 去重    │  ← 含 LLM 自由发挥（题库耗尽时）
│ 6. 打断策略评估       │  ← 超时 / 跑题 / 啰嗦
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 7. RAG 上下文检索     │  ← 向量相似度 Top-K
│ 8. LLM Prompt 组装    │  ← system prompt + RAG + persona
│ 9. LLM 生成回复       │  ← AsyncOpenAI
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 10. 保存 AI Message   │  → messages 表
│ 11. 返回前端展示      │
└──────────────────────┘
```

### 4.2 评估报告流

```
结束面试 POST /end
    │
    ▼
┌──────────────────────────────┐
│ 1. 收集完整对话历史           │
│ 2. 收集 VoiceMetrics（语音）  │
└──────────────┬───────────────┘
               ▼
    ┌─────────┴─────────┐
    ▼                   ▼
┌───────────┐    ┌──────────────┐
│ LLM 评估   │    │ 声学特征分析   │
│ 内容分     │    │ 表达分        │
│ 场景分     │    │ 语速/清晰度/自信│
│ 解题分     │    │              │
└─────┬─────┘    └──────┬───────┘
      │                 │
      └────────┬────────┘
               ▼
┌──────────────────────────────┐
│ 3. 融合打分（expression 覆盖）│
│ 4. 生成学习计划（LLM）        │
│ 5. 写入 evaluations 表       │
│ 6. 返回完整报告 JSON          │
└──────────────────────────────┘
```

---

## 5. 数据库设计

### 5.1 ER 图（核心表）

```
users (1) ──────< (N) interviews ──────< (N) messages
                         │
                         ├──< (1) evaluations
                         └──< (N) voice_metrics (关联 message)

interviews ──< (N) code_submissions
code_problems ──< (N) code_test_cases
```

### 5.2 表清单

| 表名 | 用途 | 关键字段 | 创建脚本 |
|------|------|---------|---------|
| `users` | 用户账户 | id, username, password_hash | init_db.sql |
| `interviews` | 面试会话 | id, user_id, role, status, resume_persona, repo_context | init_db.sql |
| `messages` | 对话消息 | id, interview_id, sender, content, category | init_db.sql |
| `evaluations` | 评估报告 | id, interview_id, content_score, expression_score, total_score, report_json | init_db.sql |
| `questions` | 题库 | id, role, category, difficulty | init_db.sql |
| `voice_metrics` | 语音特征 | id, interview_id, message_id, wpm, pause_ratio, filler_total | migration_v2_voice.sql |
| `code_problems` | 编程题 | id, title, language, difficulty | migration_v5_code_practice.sql |
| `code_test_cases` | 测试用例 | id, problem_id, input, expected_output, is_hidden | migration_v5_code_practice.sql |
| `code_submissions` | 提交记录 | id, user_id, problem_id, status, runtime, memory | migration_v5_code_practice.sql |

---

## 6. 部署架构

### 6.1 Docker Compose 拓扑

```
┌──────────────────────────────────────────┐
│              Docker Host                  │
│                                          │
│  ┌──────────┐  ┌──────────┐             │
│  │ frontend  │  │ backend  │             │
│  │ (Node)   │  │ (Python) │             │
│  │ :5173    │  │ :8000    │             │
│  └──────────┘  └────┬─────┘             │
│                     │                    │
│  ┌──────────┐  ┌────┴─────┐             │
│  │  Redis   │  │  MySQL   │             │
│  │  :6379   │  │  :3306   │             │
│  └──────────┘  └──────────┘             │
│                                          │
│  ┌──────────────────────────┐           │
│  │       Judge0 Stack       │ (独立)     │
│  │  server :2358            │           │
│  │  workers :2358           │           │
│  │  db (PostgreSQL)         │           │
│  │  redis (Judge0 专用)     │           │
│  └──────────────────────────┘           │
└──────────────────────────────────────────┘
```

### 6.2 部署方式

| 环境 | 方式 | 文档 |
|------|------|------|
| 本地开发 | 手动启动各服务 | README.md |
| UAT / 演示 | Docker Compose 一键部署 | docs/deploy.md |
| 云服务器演示 | Docker Compose + Nginx 反向代理 | docs/deploy_demo.md |

---

## 7. 质量保障

### 7.1 测试层级

| 层级 | 工具 | 覆盖范围 | 文件 |
|------|------|---------|------|
| 单元测试 | pytest | 音视频分析、表达评估、仓库分析 | `backend/tests/test_*.py` |
| 集成测试 | pytest | 面试结束 + 表达分融合 | `test_b_integration.py` |
| E2E 测试 | pytest + TestClient | 6 黄金路径 + 10 边界 | `test_e2e.py` |
| 前端 E2E | Playwright | UI 交互流程 | `frontend/tests/e2e/` |

### 7.2 CI/CD

- **GitHub Actions**：`.github/workflows/ci.yml`
- 触发条件：push/PR 到 main
- 包含：后端测试 + 前端构建 + E2E 冒烟

---

## 8. 安全设计

| 层面 | 措施 | 当前状态 |
|------|------|---------|
| 认证 | bcrypt 密码哈希 + Token（MVP: fake-token） | ⚠️ fake-token 仅 MVP |
| 传输 | HTTPS（Nginx 反向代理层） | 部署时配置 |
| 输入 | Pydantic 校验 + SQLAlchemy 参数化查询 | ✅ |
| CORS | FastAPI CORSMiddleware（可配置白名单） | ✅ |
| 代码执行 | Judge0 Docker 沙箱（无网络、内存/时间限制） | ✅ |
| 敏感信息 | `.env` 不入库（`.gitignore`） | ✅ |
| 依赖 | `requirements.txt` 锁定版本 | ✅ |

---

## 9. 项目度量

| 指标 | 值 |
|------|---|
| 后端 Python 文件数 | ~20 |
| 前端 Vue 组件/页面数 | ~15 |
| 数据库表数 | 9 |
| API 端点数 | 15+ |
| RAG 知识库文件数 | ~50 |
| 支持岗位数 | 3（Java / Web / Python） |
| 代码判题语言数 | 4（Python / Java / C++ / JavaScript） |
| 总代码行数（估算） | ~8,000（后端 ~4,000 + 前端 ~4,000） |

---

## 10. 演进路线 (v0.4+)

1. **流式输出 (SSE)**：LLM 回复逐字推送，消除用户等待感
2. **真实 JWT 认证**：替换 fake-token，接入 OAuth 2.0
3. **面试回放**：语音 + 文字同步回放
4. **多轮对话记忆增强**：长短期记忆分离，超长面试不丢上下文
5. **面试题库扩展**：Hot100 算法题库 + 系统设计题
6. **多租户隔离**：企业版面试定制
