# ============================================================
# InterviewEcho Backend - Dockerfile (W3.6.3)
# 多阶段构建：builder 安装依赖 → runtime 运行服务
# ============================================================

FROM python:3.12-slim AS builder

WORKDIR /app

# 系统依赖（librosa / soundfile / torch 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 先拷贝依赖文件，利用 Docker 缓存层
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- runtime 阶段：尽量精简 ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# 安装运行时系统库（ffmpeg 供 Whisper 语音处理使用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 复制已安装的 site-packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制后端源码
COPY . .

# 暴露 FastAPI 默认端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')" || exit 1

# 默认启动命令（可被 docker-compose 覆盖）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
