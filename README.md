# InterviewEcho

InterviewEcho 是一个 AI 模拟面试平台，支持文本/语音面试、GitHub 项目深挖、简历画像注入、题库练习与评估报告生成。当前仓库已经按“功能保持不变、结构更清晰、初始化单一化”的目标完成重构，主开发链路以本地开发为准，数据库结构以 `Alembic` 迁移为唯一事实来源。

## 功能概览
- 模拟面试：按岗位、难度、知识点发起面试，支持多轮追问。
- 语音交互：Whisper 转写 + 文本润色 + 表达分析。
- 简历画像：上传 PDF 或文本简历，自动生成 Persona 注入面试上下文。
- GitHub 深挖：分析公开仓库并生成项目定制问题。
- 评估报告：输出内容、表达、场景、解题等多维度结果和学习计划。
- 题库练习：Judge0 驱动的 ACM 风格代码评测。

## 目录说明
- `backend/`：FastAPI 后端、Alembic 迁移、业务服务与测试。
- `frontend/`：Vue 3 + Vite 前端。
- `knowledge-base/`：岗位题库、优秀答案与 RAG 原始资料。
- `scripts/start_judge0.ps1`：本地启动 Judge0。
- `docs/`：补充部署与设计文档；历史性交付材料保存在 `docs/archive/`。
- `backend/sql/archive/`：旧 SQL 初始化与历史迁移脚本，仅供参考，不再作为主初始化路径。

## 先决条件
1. Python 3.12
2. Node.js 20+
3. MySQL 8.0
4. Docker Desktop
5. FFmpeg

### FFmpeg 安装要求
Windows 本地语音功能依赖 `ffmpeg`。

```powershell
# 期望最终可执行文件路径
C:\ffmpeg\bin\ffmpeg.exe
```

把 `C:\ffmpeg\bin` 加入系统 `PATH` 后重新打开终端。

## 环境变量
复制根目录 `.env.example` 为 `.env`，至少填写以下项目：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASS=你的密码
DB_NAME=interview_echo

LLM_API_KEY=你的Key
LLM_BASE_URL=https://yunwu.ai/v1
LLM_MODEL=gpt-4o-mini
LLM_EMBEDDING_MODEL=text-embedding-3-small

VITE_API_URL=http://localhost:8000/api
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

JUDGE0_BASE_URL=http://127.0.0.1:2358
```

兼容旧变量名：
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `EMBEDDING_MODEL`

这些旧变量仍可读取，但已经标记为 deprecated，后续请统一使用 `LLM_*`。

## 本地初始化

### 1. 安装后端依赖
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 创建数据库
```powershell
mysql -u root -p -e "CREATE DATABASE interview_echo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. 执行数据库迁移
```powershell
cd backend
.\.venv\Scripts\activate
alembic upgrade head
```

说明：
- `backend/sql/archive/` 中保留了旧 `init_db.sql` 和历史增量脚本，便于追溯，但当前仓库只认 Alembic 迁移链路。

### 4. 灌入代码题库
```powershell
cd backend
.\.venv\Scripts\activate
python -m app.cli.seed_code_problems
```

默认会灌入 10 道可判题的 ACM 风格代码题；新建数据库后如果跳过这一步，题库练习与代码面试环节都不会有题目。

### 5. 构建 RAG 索引
```powershell
cd backend
.\.venv\Scripts\activate
python -m app.cli.build_rag_index
```

如果未配置 `LLM_API_KEY`，这一步会失败；面试中的 RAG 能力也会不可用。
如果你们当前走 `yunwu.ai` 中转，请确认 `LLM_MODEL` 填的是该账号实际可用的模型名。

### 6. 启动 Judge0
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_judge0.ps1
```

验证：
```text
http://127.0.0.1:2358/system_info
```

### 7. 启动后端
```powershell
cd backend
.\.venv\Scripts\activate
uvicorn main:app --reload
```

### 8. 启动前端
```powershell
cd frontend
npm install
npm run dev
```

默认访问：
- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`

## 验证步骤
1. 打开首页，进入登录页，注册新账号。
2. 进入“模拟面试大厅”，选择岗位并开始面试。
3. 完成一场文本面试，确认可以生成报告。
4. 进入“题库练习”，打开题目详情并运行样例。
5. 如启用了语音和 LLM，测试语音回答、简历解析与 GitHub 深挖。

## 常用命令
```powershell
# 后端编译检查
python -m compileall backend

# 前端生产构建
cd frontend
npm run build

# 后端测试
cd backend
pytest
```

## 常见问题

### `Unknown column ... resume_persona`
当前数据库还是旧结构。重新执行：

```powershell
cd backend
alembic upgrade head
```

### 前端请求地址不对
确认前端读取的是：

```env
VITE_API_URL=http://localhost:8000/api
```

不是旧的 `VITE_API_BASE_URL`。

### `Judge0 service is unavailable`
先启动 Docker Desktop，再执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_judge0.ps1
```

### 语音功能不可用
检查：
1. `ffmpeg` 是否在 `PATH`
2. `WHISPER_MODEL` 是否可加载
3. 麦克风权限是否已授予浏览器

## Docker 补充路径
如果你更希望用容器跑主服务：

```powershell
docker compose up -d --build
```

容器内后端会显式执行：
1. `alembic upgrade head`
2. `python -m app.cli.seed_code_problems`
3. `python -m app.cli.build_rag_index`
4. `uvicorn main:app --host 0.0.0.0 --port 8000`

说明：
- `docker-compose.yml` 不再依赖 Redis 主服务。
- Judge0 仍然保持独立启动，继续使用 `scripts/start_judge0.ps1`。
- 生产/演示部署的补充说明可参考 `docs/deploy.md` 与 `docs/deploy_demo.md`。
