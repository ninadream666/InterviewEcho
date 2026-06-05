# InterviewEcho 云服务器部署文档 (W7.3.1)

> 日期：2026-05-24  
> 目标：将 InterviewEcho 部署至云服务器并暴露公网演示 URL

---

## 1. 服务器选型与配置

### 1.1 推荐配置

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 系统盘 | 40 GB SSD | 60 GB SSD |
| 操作系统 | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| 带宽 | 3 Mbps | 5 Mbps+ |

> **注意**：若同时运行 Judge0（Docker 代码判题），至少需要 8 GB 内存。

### 1.2 云服务商选择

| 服务商 | 推荐机型 | 月费参考 | 备注 |
|--------|---------|---------|------|
| 阿里云 ECS | ecs.c6.large (2c4g) | ~¥120 | 学生优惠可更低 |
| 腾讯云 CVM | S5.MEDIUM2 (2c4g) | ~¥110 | 有学生机套餐 |
| 华为云 ECS | s6.large.2 (2c4g) | ~¥100 | — |

---

## 2. 环境初始化

### 2.1 基础软件安装

```bash
# SSH 登录服务器
ssh root@<your-server-ip>

# 更新系统
apt update && apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | bash
systemctl enable docker
systemctl start docker

# 安装 Docker Compose 插件
apt install docker-compose-plugin -y

# 验证
docker --version          # ≥ 24.0
docker compose version    # ≥ 2.0
```

### 2.2 安装 Git 并拉取代码

```bash
apt install git -y

cd /opt
git clone https://github.com/ninadream666/InterviewEcho.git
cd InterviewEcho
```

### 2.3 配置环境变量

```bash
# 从模板创建 .env
cp .env.example .env

# 编辑 .env，填入真实值
vim .env
```

必须填写的变量：

```env
# LLM（必须）
LLM_API_KEY=sk-your-actual-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_EMBEDDING_MODEL=text-embedding-3-small

# 数据库密码（修改默认值！）
DB_PASS=<strong-random-password>

# CORS（限制为你的域名或服务器 IP）
CORS_ORIGINS=http://<your-server-ip>:5173

# 前端 API 地址
VITE_API_URL=http://<your-server-ip>:8000/api

# Judge0（使用同一台服务器的 Docker Judge0）
JUDGE0_BASE_URL=http://127.0.0.1:2358
```

---

## 3. 启动服务

### 3.1 启动核心服务

```bash
cd /opt/InterviewEcho

# 启动所有核心服务（后端 + 前端 + MySQL）
docker compose up -d

# 查看启动日志
docker compose logs -f
```

### 3.2 启动 Judge0（可选）

```bash
# 克隆 Judge0
cd /opt
git clone https://github.com/judge0/judge0.git
cd judge0

# 启动 Judge0
docker compose up -d db redis
sleep 5
docker compose up -d

# 验证
curl http://127.0.0.1:2358/system_info
```

### 3.3 验证服务状态

```bash
# 检查容器运行状态
docker compose -f /opt/InterviewEcho/docker-compose.yml ps

# 测试后端
curl http://127.0.0.1:8000/
# 预期: {"message":"Welcome to InterviewEcho API"}

# 测试前端
curl http://127.0.0.1:5173/
# 预期: HTML 页面
```

---

## 4. 公网访问配置

### 4.1 开放安全组端口

在云服务商控制台的安全组中开放以下入站端口：

| 端口 | 协议 | 用途 | 建议 |
|------|------|------|------|
| 5173 | TCP | 前端 Vite 开发服务器 | **对外** |
| 8000 | TCP | 后端 FastAPI | 仅开发调试时对外 |
| 22 | TCP | SSH | 限制 IP 访问 |
| 2358 | TCP | Judge0 API | 不对公网开放 |

### 4.2 配置 Nginx 反向代理（推荐）

Vite 开发模式不适合长期运行。建议构建前端并用 Nginx 托管：

```bash
# 安装 Nginx
apt install nginx -y

# 构建前端
cd /opt/InterviewEcho/frontend
npm install
npm run build
# 产物在 frontend/dist/

# 配置 Nginx
cat > /etc/nginx/sites-available/interviewecho << 'EOF'
server {
    listen 80;
    server_name <your-domain-or-ip>;

    # 前端静态文件
    location / {
        root /opt/InterviewEcho/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/interviewecho /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

### 4.3 演示 URL

配置完成后，演示 URL 为：

```text
http://<your-server-ip>
```

（若配置了域名，则为 `http://<your-domain>`）

---

## 5. 运维管理

### 5.1 常用命令

```bash
# 查看日志
docker compose -f /opt/InterviewEcho/docker-compose.yml logs -f backend

# 重启服务
docker compose -f /opt/InterviewEcho/docker-compose.yml restart backend

# 停止所有服务
docker compose -f /opt/InterviewEcho/docker-compose.yml down

# 更新代码并重启
cd /opt/InterviewEcho
git pull
docker compose up -d --build backend
```

### 5.2 数据库备份

```bash
# 备份
docker exec interview-echo-db mysqldump -u root -p<password> interview_echo > backup_$(date +%Y%m%d).sql

# 恢复
docker exec -i interview-echo-db mysql -u root -p<password> interview_echo < backup_20260524.sql
```

### 5.3 监控建议

```bash
# 资源占用
docker stats

# 磁盘
df -h

# 设置定时重启（每天凌晨 4 点）
crontab -l | { cat; echo "0 4 * * * docker compose -f /opt/InterviewEcho/docker-compose.yml restart backend"; } | crontab -
```

---

## 6. 故障排查

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| 502 Bad Gateway | 后端未启动 | `docker compose ps` 检查 backend 状态 |
| 数据库连接失败 | DB_HOST 配置错误 | Docker 中应为 `mysql`（服务名） |
| LLM 调用超时 | API Key 无效或网络不通 | 检查 `.env` 中 LLM_API_KEY；测试 `curl $LLM_BASE_URL` |
| 磁盘满 | Docker 日志/镜像堆积 | `docker system prune -a`（谨慎） |
| 前端白屏 | Vite 未构建或 Nginx 路径错误 | 检查 `/opt/InterviewEcho/frontend/dist/` 是否存在 |
