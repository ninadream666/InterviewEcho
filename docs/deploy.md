# InterviewEcho 部署指南 (W3.6.3)

> 最后更新：2026-05-20  
> 适用版本：v0.3 (rev3, Milestone UAT)

---

## 1. 部署方式概览

| 方式 | 适合场景 | 复杂度 | 说明 |
|------|---------|--------|------|
| **Docker Compose（推荐）** | UAT / 演示 / 小规模部署 | ⭐⭐ | 一键拉起全部服务 |
| **手动部署** | 本地开发 / 调试 | ⭐⭐⭐ | 需手动安装 MySQL、Node.js、Python |
| **云服务器部署** | 生产演示 | ⭐⭐⭐⭐ | 见 `docs/deploy_demo.md` |

---

## 2. Docker Compose 一键部署

### 2.1 前提条件

- **Docker Desktop** ≥ 24.0（Windows/macOS）或 Docker Engine ≥ 24.0（Linux）
- 至少 8 GB 可用内存（含 Judge0 时建议 16 GB）
- 已获取 LLM API Key（OpenAI / DeepSeek）

### 2.2 环境变量配置

项目根目录已提供 `.env.example`，复制并填入真实值：

```powershell
# 从模板创建
copy .env.example .env
```

需要填写的关键变量：

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | 大模型 API Key | `sk-xxxxxxxx` |
| `LLM_BASE_URL` | 大模型接口地址 | `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `LLM_EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-3-small` |
| `DB_PASS` | MySQL root 密码 | `interview_echo_2024` |
| `VITE_API_URL` | 前端 API 地址 | `http://localhost:8000/api` |

### 2.3 启动全部服务

```powershell
# 项目根目录
docker compose up -d
```

首次启动会自动：
1. 拉取 `mysql:8.0`、`node:20-alpine` 镜像
2. 构建 `backend` 镜像
3. 显式执行 `alembic upgrade head`
4. 执行题库 seed 与 RAG 索引构建
4. 启动前端 Vite 开发服务器

### 2.4 启动 Judge0（代码判题）

代码练习功能依赖 Judge0。Judge0 使用独立的 Docker Compose：

```powershell
# 方式一：使用项目自带脚本（推荐）
powershell -ExecutionPolicy Bypass -File scripts\start_judge0.ps1

# 方式二：手动克隆并启动
git clone https://github.com/judge0/judge0.git
cd judge0
docker compose up -d db redis
docker compose up -d
```

Judge0 启动后验证：

```text
http://127.0.0.1:2358/system_info
```

### 2.5 验证部署

| 服务 | 地址 | 预期响应 |
|------|------|---------|
| 后端 API | `http://localhost:8000/` | `{"message":"Welcome to InterviewEcho API"}` |
| 前端 UI | `http://localhost:5173/` | 登录/注册页面 |
| 数据库 | `localhost:3306` | MySQL 8.0 |
| Judge0 | `http://localhost:2358/system_info` | JSON |

### 2.6 停止服务

```powershell
# 停止（保留数据卷）
docker compose down

# 停止并清除所有数据
docker compose down -v
```

---

## 3. 手动部署

### 3.1 环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | ≥ 3.12 |
| Node.js | ≥ 20.x |
| MySQL | 8.0 |
| FFmpeg | 最新 stable（语音处理依赖） |
| Docker Desktop | 仅 Judge0 需要 |

### 3.2 后端部署

```powershell
# 1. 项目根目录创建 .env
copy .env.example .env

# 2. 进入 backend
cd backend

# 3. 安装 Python 依赖
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 4. 数据库迁移
alembic upgrade head

# 5. 题库 seed
python -m app.cli.seed_code_problems

# 6. 构建 RAG 索引
python -m app.cli.build_rag_index

# 7. 启动
uvicorn main:app --reload
```

### 3.3 前端部署

```powershell
# 1. 进入 frontend
cd frontend

# 2. 安装依赖
npm install

# 3. 开发模式启动
npm run dev

# 4. 生产构建
npm run build
# 构建产物在 frontend/dist/，可用任意静态服务器托管
```

### 3.4 数据库初始化

```powershell
$env:MYSQL_PWD="your_password"

mysql -u root -e "CREATE DATABASE IF NOT EXISTS interview_echo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
cd backend
.\.venv\Scripts\activate
alembic upgrade head
```

---

## 4. 常见问题

### Q1: `rag.build_index` 报错 "知识库未初始化"
确保 `knowledge-base/` 目录存在且包含各岗位的 `questions.json` 和知识点 Markdown 文件。

### Q2: Judge0 连接失败
- 确认 Judge0 Docker 容器正在运行：`docker ps | grep judge0`
- 检查 `JUDGE0_BASE_URL` 配置。在 Docker Compose 中后端访问宿主机 Judge0 需使用 `http://host.docker.internal:2358`（Windows/macOS）或 `http://172.17.0.1:2358`（Linux）。

### Q3: 前端热更新不生效
Windows + WSL2 下，将项目放在 WSL2 文件系统中（而非 `/mnt/c/`），否则 inotify 不工作。

### Q4: 数据库连接被拒
- Docker Compose 中 `DB_HOST=mysql`（服务名）
- 手动部署中 `DB_HOST=localhost`

---

## 5. 安全注意事项

1. **`.env` 不入库**：`.gitignore` 已包含 `.env`，切勿提交 API Key。
2. **数据库密码**：生产环境务必修改默认密码。
3. **CORS**：生产部署时，将 `CORS_ORIGINS` 限制为具体前端域名，而非 `*`。
4. **JWT 替代**：当前 MVP 使用 `fake-token-{user_id}` 模拟认证，生产环境需替换为真实 JWT。
