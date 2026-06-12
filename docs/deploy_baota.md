# InterviewEcho 腾讯云宝塔 Linux 部署指南

> 最后更新：2026-06-11
> 适用版本：v0.3+
> 目标：将 InterviewEcho 部署至腾讯云 CVM + 宝塔 Linux 面板，暴露公网访问

---

## 目录

1. [项目架构概览](#1-项目架构概览)
2. [服务器准备](#2-服务器准备)
3. [宝塔面板安装与初始化](#3-宝塔面板安装与初始化)
4. [环境安装](#4-环境安装)
5. [项目部署](#5-项目部署)
6. [Nginx 反向代理配置](#6-nginx-反向代理配置)
7. [Judge0 代码判题服务（可选）](#7-judge0-代码判题服务可选)
8. [验证部署](#8-验证部署)
9. [运维管理](#9-运维管理)
10. [故障排查](#10-故障排查)
11. [安全加固建议](#11-安全加固建议)

---

## 1. 项目架构概览

```
┌─────────────────────────────────────────────────────┐
│                    用户浏览器                          │
│                  http://<你的IP/域名>                   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              Nginx (宝塔面板管理)                      │
│   ├─ /            → 前端静态文件 (Vue 3 + Vite)        │
│   └─ /api/*       → 反向代理到后端 :8000               │
└────────┬───────────────────┬────────────────────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌──────────────────┐
│  Frontend (Nginx│  │  Backend (Docker) │
│  静态托管)       │  │  FastAPI :8000    │
│  Vue 3 + Vite   │  │  Python 3.12      │
└─────────────────┘  └────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
      ┌──────────┐  ┌──────────────┐  ┌──────────────┐
      │ MySQL 8.0│  │ LLM API      │  │ Judge0       │
      │ (Docker) │  │ (yunwu.ai)   │  │ (Docker)     │
      └──────────┘  └──────────────┘  └──────────────┘
```

**技术栈总结：**

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | Vue 3 + Vite + Element Plus + TailwindCSS | SPA 单页应用，构建为静态文件 |
| 后端 | FastAPI (Python 3.12) | REST API，Uvicorn ASGI 服务器 |
| 数据库 | MySQL 8.0 | 用户、面试记录、题库数据 |
| AI | OpenAI 兼容 API (yunwu.ai 中转) | 面试对话、评分、RAG 检索 |
| 语音 | OpenAI Whisper | 语音转文字 |
| 判题 | Judge0 v1.13.1 | ACM 风格代码执行与评测 |
| 反向代理 | Nginx | 宝塔面板内置 |

---

## 2. 服务器准备

### 2.1 腾讯云 CVM 配置建议

| 配置项 | 最低要求 | 推荐配置 |
|--------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB（含 Judge0 则必须 8 GB） |
| 系统盘 | 40 GB SSD | 60 GB SSD+ |
| 操作系统 | CentOS 7.9+ / Ubuntu 22.04 | Ubuntu 24.04 LTS |
| 带宽 | 3 Mbps | 5 Mbps+ |

> **机型推荐**：腾讯云轻量应用服务器（LH）性价比最高，2c4g 配置约 ¥70/月（学生价更低）。若需更强性能可选 CVM S5.MEDIUM2。

### 2.2 安全组配置

在腾讯云控制台 → 安全组中，添加入站规则：

| 端口 | 协议 | 用途 | 建议 |
|------|------|------|------|
| 22 | TCP | SSH 远程管理 | ✅ 开放（建议限制 IP） |
| 80 | TCP | HTTP（Nginx） | ✅ 开放 |
| 443 | TCP | HTTPS（若配置 SSL） | 可选 |
| 8888 | TCP | 宝塔面板登录 | ✅ 开放 |
| 8000 | TCP | 后端 API（调试用） | ⚠️ 调试时开放，生产可关闭 |
| 2358 | TCP | Judge0 API | ❌ 仅本机访问 |

> **操作方法**：腾讯云控制台 → 云服务器 → 安全组 → 添加规则 → 填入上述端口。

### 2.3 SSH 登录

```bash
# 使用腾讯云控制台提供的公网 IP 登录
ssh root@<你的服务器公网IP>

# 验证系统信息
uname -a
cat /etc/os-release
free -h
df -h
```

---

## 3. 宝塔面板安装与初始化

### 3.1 安装宝塔面板

根据操作系统选择安装命令：

**Ubuntu / Debian（推荐）：**

```bash
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh
```

**CentOS：**

```bash
yum install -y wget && wget -O install.sh https://download.bt.cn/install/install_6.0.sh && sh install.sh
```

安装完成后，终端会输出类似以下的登录信息：

```text
==================================================================
Congratulations! Installed successfully!
==================================================================
外网面板地址: http://<你的IP>:8888/xxxxxxxx
内网面板地址: http://<内网IP>:8888/xxxxxxxx
username: xxxxxxxx
password: xxxxxxxx
==================================================================
```

> ⚠️ **请务必保存好面板地址、用户名和密码！**

### 3.2 登录宝塔面板

1. 浏览器打开 `http://<你的公网IP>:8888/xxxxxxxx`
2. 使用上述用户名和密码登录
3. 首次登录会弹出推荐安装套件选择框

### 3.3 安装宝塔基础套件（可选）

在宝塔面板「软件商店」中，确保安装以下基础软件（如已内置则跳过）：

- **Nginx** ≥ 1.22（用于反向代理）
- **系统防火墙**（宝塔会自动管理安全组规则）

> **注意**：MySQL、Docker 等服务我们会手动安装，不用宝塔的版本，以便更好地控制版本和配置。

---

## 4. 环境安装

### 4.1 安装 Docker 与 Docker Compose

```bash
# 通过 SSH 连接服务器，安装 Docker
curl -fsSL https://get.docker.com | bash

# 启动 Docker 并设置开机自启
systemctl enable docker
systemctl start docker

# 安装 Docker Compose 插件
apt install docker-compose-plugin -y   # Ubuntu/Debian
# 或
yum install docker-compose-plugin -y   # CentOS

# 验证安装
docker --version          # 预期 ≥ 27.0
docker compose version    # 预期 ≥ 2.0
```

### 4.2 安装 Git 并拉取项目

```bash
# 安装 Git
apt install git -y

# 克隆项目到 /opt 目录
cd /opt
git clone https://github.com/ninadream666/InterviewEcho.git
cd InterviewEcho
```

### 4.3 配置环境变量

```bash
# 从模板创建 .env 文件
cp .env.example .env

# 编辑 .env 文件
vim .env
```

以下是**服务器部署专用的 .env 配置**（请替换 `<...>` 为真实值）：

```env
# ========== 应用配置 ==========
APP_HOST=0.0.0.0
APP_PORT=8000
FRONTEND_PORT=5173

# ========== 数据库配置 ==========
# Docker Compose 内部使用 mysql 作为 hostname
DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASS=<请设置一个强密码，至少16位>
DB_NAME=interview_echo

# ========== CORS 跨域配置 ==========
# 生产环境务必限制为实际域名/IP（多个用英文逗号分隔）
CORS_ORIGINS=http://<你的服务器公网IP>,http://localhost:5173

# ========== 前端 API 地址（供 Vite 构建使用） ==========
VITE_API_URL=http://<你的服务器公网IP>/api

# ========== LLM 配置（必须填写真实值） ==========
LLM_API_KEY=<你的LLM API Key>
LLM_BASE_URL=https://yunwu.ai/v1
LLM_MODEL=gpt-4o
LLM_EMBEDDING_MODEL=text-embedding-3-small

# ========== GitHub Token（可选，用于GitHub深挖功能） ==========
GITHUB_TOKEN=

# ========== 语音识别配置 ==========
WHISPER_MODEL=small

# ========== Judge0 代码判题（可选） ==========
JUDGE0_BASE_URL=http://127.0.0.1:2358
JUDGE0_TIMEOUT_SECONDS=12
JUDGE0_POLL_INTERVAL_SECONDS=0.6
JUDGE0_MAX_POLL_ATTEMPTS=90
CODE_MAX_SOURCE_LENGTH=20000
CODE_MAX_TEST_CASES=30
CODE_MAX_CONCURRENT_JUDGE_CASES=8
CODE_OUTPUT_LIMIT=4000
```

> ⚠️ **重要提示**：
> - `DB_PASS` 务必修改为强密码，Docker Compose 中 MySQL 会在首次启动时使用此密码
> - `CORS_ORIGINS` 必须包含前端实际访问的域名/IP，否则浏览器会拦截跨域请求
> - `VITE_API_URL` 填写前端访问后端的实际公网路径。如果使用 Nginx 反向代理（即前后端同域名），填 `http://<你的IP>/api`；如果直接暴露后端端口，填 `http://<你的IP>:8000/api`
> - `.env` 文件包含敏感信息，确保 `.gitignore` 已包含它（项目默认已配置）

---

## 5. 项目部署

### 5.1 方案选择

本项目提供两种部署方式，针对宝塔环境**推荐方案 A（Docker 运行后端 + Nginx 静态前端）**：

| 方案 | 后端 | 前端 | MySQL | 适用场景 |
|------|------|------|-------|---------|
| **方案 A（推荐）** | Docker Compose | Nginx 托管静态文件 | Docker | 生产/演示 |
| 方案 B | Docker Compose（全服务） | Docker Vite 开发服务器 | Docker | 快速启动/调试 |

> 方案 B 前端使用 `npm run dev` 开发模式，不适合长期运行。以下详述方案 A。

### 5.2 方案 A：Docker 后端 + Nginx 静态前端（推荐）

#### 5.2.1 修改 docker-compose.yml（只启动后端+数据库）

创建一个专门用于生产的 Compose 文件，只启动 MySQL 和 Backend：

```bash
# 在项目根目录创建 docker-compose.prod.yml
cat > docker-compose.prod.yml << 'EOF'
version: "3.9"

services:
  mysql:
    image: mysql:8.0
    container_name: interview-echo-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASS}
      MYSQL_DATABASE: interview_echo
      MYSQL_CHARSET: utf8mb4
      MYSQL_COLLATION: utf8mb4_unicode_ci
    ports:
      - "127.0.0.1:${DB_PORT:-3306}:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${DB_PASS}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: interview-echo-backend
    restart: unless-stopped
    environment:
      LLM_API_KEY: ${LLM_API_KEY}
      LLM_BASE_URL: ${LLM_BASE_URL:-https://api.openai.com/v1}
      LLM_MODEL: ${LLM_MODEL:-gpt-3.5-turbo-1106}
      LLM_EMBEDDING_MODEL: ${LLM_EMBEDDING_MODEL:-text-embedding-3-small}
      DB_HOST: mysql
      DB_PORT: 3306
      DB_USER: root
      DB_PASS: ${DB_PASS}
      DB_NAME: interview_echo
      JUDGE0_BASE_URL: ${JUDGE0_BASE_URL:-http://127.0.0.1:2358}
      JUDGE0_TIMEOUT_SECONDS: ${JUDGE0_TIMEOUT_SECONDS:-12}
      JUDGE0_POLL_INTERVAL_SECONDS: ${JUDGE0_POLL_INTERVAL_SECONDS:-0.6}
      JUDGE0_MAX_POLL_ATTEMPTS: ${JUDGE0_MAX_POLL_ATTEMPTS:-90}
      CODE_MAX_SOURCE_LENGTH: ${CODE_MAX_SOURCE_LENGTH:-20000}
      CODE_MAX_TEST_CASES: ${CODE_MAX_TEST_CASES:-30}
      CODE_MAX_CONCURRENT_JUDGE_CASES: ${CODE_MAX_CONCURRENT_JUDGE_CASES:-8}
      CODE_OUTPUT_LIMIT: ${CODE_OUTPUT_LIMIT:-4000}
      CORS_ORIGINS: ${CORS_ORIGINS:-*}
      GITHUB_TOKEN: ${GITHUB_TOKEN}
      WHISPER_MODEL: ${WHISPER_MODEL:-small}
    ports:
      - "127.0.0.1:${APP_PORT:-8000}:8000"
    volumes:
      - rag_data:/app/rag
      - ./knowledge-base:/app/../knowledge-base:ro
    depends_on:
      mysql:
        condition: service_healthy
    command: >
      sh -c "
        alembic upgrade head &&
        python -m app.cli.seed_code_problems &&
        (python -m app.cli.build_rag_index || echo '[warn] RAG index build skipped') &&
        uvicorn main:app --host 0.0.0.0 --port 8000
      "

volumes:
  mysql_data:
    driver: local
  rag_data:
    driver: local
EOF
```

> **关键安全设置**：后端端口映射为 `127.0.0.1:8000:8000`，仅监听本地回环地址，不直接暴露到公网。公网访问通过 Nginx 反向代理，更安全。

#### 5.2.2 启动后端服务

```bash
cd /opt/InterviewEcho

# 启动 MySQL + Backend
docker compose -f docker-compose.prod.yml up -d

# 查看启动日志（等待所有初始化完成）
docker compose -f docker-compose.prod.yml logs -f
```

启动过程中会自动执行：
1. `alembic upgrade head` — 数据库迁移
2. `python -m app.cli.seed_code_problems` — 灌入代码题库（10道）
3. `python -m app.cli.build_rag_index` — 构建 RAG 知识库索引
4. `uvicorn main:app --host 0.0.0.0 --port 8000` — 启动 FastAPI

等待看到类似以下日志时表示启动成功：

```text
interview-echo-backend | INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 5.2.3 构建前端静态文件

```bash
# 安装 Node.js（使用 NodeSource 仓库获取 v20）
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install nodejs -y

# 验证
node --version    # 应 ≥ v20.x
npm --version

# 进入前端目录
cd /opt/InterviewEcho/frontend

# 安装依赖
npm install

# 生产构建（重要：构建时会读取 .env 中的 VITE_API_URL）
npm run build

# 构建产物位于 /opt/InterviewEcho/frontend/dist/
ls -la dist/
# 应看到: index.html + assets/ 目录
```

---

## 6. Nginx 反向代理配置

### 6.1 通过宝塔面板配置 Nginx

#### 步骤 1：进入宝塔网站管理

1. 登录宝塔面板 → 「网站」
2. 点击「添加站点」
3. 填写：
   - **域名**：填入服务器公网 IP（如 `123.123.123.123`），有域名则填域名
   - **根目录**：`/opt/InterviewEcho/frontend/dist`
   - **PHP 版本**：选择「纯静态」
4. 点击「提交」

#### 步骤 2：配置反向代理

1. 在网站列表中找到刚创建的站点，点击「设置」
2. 进入「反向代理」选项卡
3. 点击「添加反向代理」：
   - **代理名称**：`backend-api`
   - **目标 URL**：`http://127.0.0.1:8000`
   - **发送域名**：`$http_host`（默认）
   - **代理目录**：`/api/`
4. 点击「提交」

#### 步骤 3：调整配置文件（SPA 路由支持）

在网站设置 → 「配置文件」中，确保配置包含以下内容：

```nginx
server {
    listen 80;
    server_name <你的IP或域名>;
    root /opt/InterviewEcho/frontend/dist;
    index index.html;

    # ===== 后端 API 反向代理 =====
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 重要：WebSocket 支持（语音实时交互可能用到）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置（LLM 响应可能较慢）
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # ===== 前端 SPA 路由（Vue Router history 模式） =====
    location / {
        try_files $uri $uri/ /index.html;
    }

    # ===== 静态资源缓存 =====
    location /assets/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

点击「保存」后，宝塔会自动重载 Nginx。

### 6.2 配置 HTTPS（推荐）

如果有域名，可在宝塔面板中一键申请免费 SSL 证书：

1. 网站设置 → 「SSL」→ 「Let's Encrypt」
2. 选择「文件验证」，勾选域名，点击「申请」
3. 开启「强制 HTTPS」

> 如果只有 IP 没有域名，HTTPS 需要自签名证书（浏览器会提示不安全，但不影响功能测试）。

---

## 7. Judge0 代码判题服务（可选）

> ⚠️ **Judge0 消耗资源较大（约 2-3GB 内存）**。如果服务器内存不足 8GB，建议先不部署，代码练习功能会提示 "Judge0 服务不可用"，但不影响面试核心功能。

### 7.1 安装 Judge0

```bash
# 下载 Judge0 v1.13.1
cd /opt
wget https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip
unzip judge0-v1.13.1.zip -d judge0
cd judge0

# 修改 docker-compose.yml，限制端口仅本机访问
# 将 "2358:2358" 改为 "127.0.0.1:2358:2358"
sed -i 's/"2358:2358"/"127.0.0.1:2358:2358"/g' docker-compose.yml
sed -i "s/'2358:2358'/'127.0.0.1:2358:2358'/g" docker-compose.yml

# 编辑 judge0.conf 进行基本配置
cat >> judge0.conf << 'EOF'
RESTART_MAX_RETRIES=3
COUNT=2
MAX_QUEUE_SIZE=64
CPU_TIME_LIMIT=2
MAX_CPU_TIME_LIMIT=32
WALL_TIME_LIMIT=6
MAX_WALL_TIME_LIMIT=80
MEMORY_LIMIT=128000
MAX_MEMORY_LIMIT=512000
EOF

# 启动 Judge0
docker compose up -d db redis
sleep 5
docker compose up -d

# 验证 Judge0 是否正常运行
curl http://127.0.0.1:2358/system_info
```

如果返回 JSON 数据，说明 Judge0 启动成功。

> **注意**：如果服务器内存不够，Judge0 可能导致 OOM。可以用 `docker stats` 监控内存占用。

---

## 8. 验证部署

### 8.1 基础健康检查

```bash
# 1. 检查 Docker 容器运行状态
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml ps
# 预期：mysql 和 backend 状态均为 Up

# 2. 测试后端 API（本机）
curl http://127.0.0.1:8000/
# 预期响应：{"message":"Welcome to InterviewEcho API"}

# 3. 测试通过 Nginx 的 API 访问
curl http://127.0.0.1/api/
# 预期响应：{"message":"Welcome to InterviewEcho API"}

# 4. 测试前端页面
curl -I http://127.0.0.1/
# 预期：HTTP/1.1 200 OK，Content-Type: text/html
```

### 8.2 浏览器验证

在浏览器中访问 `http://<你的公网IP>`，确认以下功能：

| 功能 | 验证步骤 | 预期结果 |
|------|---------|---------|
| 首页 | 打开首页 | 显示 InterviewEcho 首页 |
| 注册/登录 | 点击登录，注册新账号 | 成功注册并登录 |
| 模拟面试 | 进入面试大厅，选择岗位开始面试 | AI 面试官正常提问 |
| 文本回答 | 输入文本回答 | AI 正常追问并评分 |
| 面试报告 | 完成一场面试 | 生成评估报告 |
| 语音回答 | 点击麦克风进行语音回答 | Whisper 转写正常（需麦克风权限） |
| 代码练习 | 进入题库练习，选择题目运行 | 判题结果正常返回（需 Judge0） |

### 8.3 通过宝塔面板验证

1. 宝塔「网站」→ 站点状态应显示「运行中」
2. 宝塔「Docker」→ 容器列表应显示 `interview-echo-db` 和 `interview-echo-backend`
3. 宝塔「安全」→ 防火墙应显示已放行端口

---

## 9. 运维管理

### 9.1 常用命令速查

```bash
# ===== Docker 服务管理 =====

# 查看容器运行状态
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml ps

# 查看后端实时日志
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml logs -f backend

# 查看最近 100 行日志
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml logs --tail=100 backend

# 重启后端（修改代码或配置后）
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml restart backend

# 完全重建后端（修改 Dockerfile 或 requirements.txt 后）
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml up -d --build backend

# 停止所有服务
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml down

# 停止并清除数据卷（⚠️ 会删除数据库！）
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml down -v

# ===== Nginx 管理（通过宝塔面板操作更直观） =====

# 测试 Nginx 配置
nginx -t

# 重载 Nginx
nginx -s reload

# ===== 系统监控 =====

# 实时监控容器资源占用
docker stats

# 磁盘使用情况
df -h

# 内存使用情况
free -h
```

### 9.2 更新代码

```bash
cd /opt/InterviewEcho

# 拉取最新代码
git pull origin main

# 如果后端代码有变更，重新构建并启动
docker compose -f /opt/InterviewEcho/docker-compose.prod.yml up -d --build backend

# 如果前端代码有变更，重新构建前端
cd /opt/InterviewEcho/frontend
npm install
npm run build

# Nginx 会自动加载新的静态文件，无需重启
```

### 9.3 数据库备份

```bash
# 备份数据库
docker exec interview-echo-db mysqldump \
  -u root -p<你的数据库密码> interview_echo \
  > /opt/backups/interview_echo_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker exec -i interview-echo-db mysql \
  -u root -p<你的数据库密码> interview_echo \
  < /opt/backups/interview_echo_20260611.sql
```

### 9.4 设置定时备份

在宝塔面板中设置定时任务，或使用 crontab：

```bash
# 编辑 crontab
crontab -e

# 添加每日凌晨 3 点备份数据库（保留最近 7 天的备份）
0 3 * * * docker exec interview-echo-db mysqldump -u root -p<密码> interview_echo > /opt/backups/interview_echo_$(date +\%Y\%m\%d).sql && find /opt/backups/ -name "*.sql" -mtime +7 -delete
```

> 也可通过宝塔面板「计划任务」→ 添加 Shell 脚本来设置。

### 9.5 日志管理

```bash
# Docker 日志可能会占用大量磁盘，设置日志大小限制
# 编辑 /etc/docker/daemon.json，添加：
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker
```

---

## 10. 故障排查

| 问题现象 | 可能原因 | 排查步骤 |
|---------|---------|---------|
| **访问页面 502** | 后端未启动或 Nginx 代理配置错误 | `docker compose ps` 检查后端状态；检查 Nginx 反向代理目标 URL |
| **前端白屏/404** | 静态文件路径错误 | 确认 `/opt/InterviewEcho/frontend/dist/index.html` 存在 |
| **API 跨域报错** | CORS_ORIGINS 未包含前端地址 | 检查 `.env` 中 `CORS_ORIGINS`；重建后端容器 |
| **数据库连接失败** | `DB_HOST` 配置错误 | Docker 中后端访问 MySQL 应为 `mysql`（服务名），非 `localhost` |
| **LLM 调用超时** | API Key 无效或网络不通 | `curl -H "Authorization: Bearer $LLM_API_KEY" $LLM_BASE_URL/models` |
| **RAG 索引构建失败** | 知识库目录缺失或 LLM 不可用 | 检查 `knowledge-base/` 目录结构；确认 LLM API Key 有效 |
| **语音转写失败** | FFmpeg 未安装或模型未下载 | 检查 Docker 容器内 `ffmpeg -version`；Whisper 模型首次使用会自动下载 |
| **代码判题不可用** | Judge0 未启动或内存不足 | `curl http://127.0.0.1:2358/system_info`；`docker stats` 查看内存 |
| **Docker 磁盘满** | 镜像/日志堆积 | `docker system prune -a`（谨慎操作，会删除未使用的镜像） |
| **宝塔面板不可访问** | 8888 端口未开放 | 检查腾讯云安全组是否放行 8888；`bt status` 检查面板状态 |

### 10.1 常用排查命令

```bash
# 后端日志（最常用）
docker logs interview-echo-backend --tail 50

# 后端实时日志
docker logs -f interview-echo-backend

# 数据库连接测试
docker exec interview-echo-backend python -c "
from app.core.config import settings
print('DB URL:', settings.sqlalchemy_database_url)
"

# 进入后端容器调试
docker exec -it interview-echo-backend bash

# 检查端口占用
netstat -tlnp | grep -E '8000|3306|80'

# 查看宝塔面板状态
bt status
```

---

## 11. 安全加固建议

### 11.1 基础安全

```bash
# 1. 修改 SSH 默认端口（宝塔面板 → 安全 → SSH 管理）
# 2. 禁用 root 密码登录，改用密钥登录
# 3. 安装宝塔系统加固插件
```

### 11.2 应用安全

| 安全项 | 建议操作 |
|--------|---------|
| `.env` 文件 | 权限设为 600：`chmod 600 /opt/InterviewEcho/.env` |
| 数据库密码 | 使用 16+ 位随机密码，定期更换 |
| CORS | `CORS_ORIGINS` 限制为实际访问域名，**不要使用 `*`** |
| JWT 认证 | 当前 MVP 使用 `fake-token` 模拟认证，**生产环境务必替换为真实 JWT** |
| HTTPS | 有域名的情况下务必配置 SSL 证书 |
| API 限流 | 生产环境建议添加 Nginx `limit_req` 或 FastAPI 中间件限流 |

### 11.3 宝塔面板安全

1. 修改宝塔面板默认端口（面板设置 → 安全设置 → 面板端口）
2. 开启面板 SSL（面板设置 → 安全设置 → 绑定域名并开启 SSL）
3. 关闭不必要的面板端口（如 FTP、PHPMyAdmin 等）
4. 定期更新宝塔面板：`curl https://download.bt.cn/install/update_panel.sh | bash`

---

## 附录 A：Docker Compose 端口规划总表

| 服务 | 内部端口 | 外部映射 | 说明 |
|------|---------|---------|------|
| MySQL | 3306 | `127.0.0.1:3306` | 仅本机访问 |
| Backend | 8000 | `127.0.0.1:8000` | 仅本机访问，通过 Nginx 代理对外 |
| Judge0 | 2358 | `127.0.0.1:2358` | 仅本机访问 |
| Nginx | 80 | `0.0.0.0:80` | 对外提供 HTTP 服务 |

## 附录 B：宝塔面板快速操作对照表

| 操作 | 宝塔面板路径 |
|------|-------------|
| 网站管理 | 网站 → 站点列表 |
| Nginx 配置 | 网站 → 设置 → 配置文件 |
| 反向代理 | 网站 → 设置 → 反向代理 |
| SSL 证书 | 网站 → 设置 → SSL |
| 防火墙端口 | 安全 → 防火墙 |
| Docker 管理 | Docker → 容器列表 |
| 计划任务 | 计划任务 → 添加 |
| 文件管理 | 文件 → /opt/InterviewEcho |

---

> 📚 **相关文档**：
> - 本地开发部署：[deploy.md](deploy.md)
> - 通用云服务器部署：[deploy_demo.md](deploy_demo.md)
> - 用户使用手册：[user_manual.md](user_manual.md)
