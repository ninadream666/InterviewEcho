# AI模拟面试与能力提升软件

面向计算机相关专业学生的AI模拟面试与能力提升平台，支持Java后端、
Web前端、Python算法三类岗位的模拟面试，提供多维度智能评估与个性化提升建议。

---

## 项目结构
```
ai-interview/
├── frontend/              # 前端
├── backend/
│   ├── core/              # 后端核心（对话/存储/推荐）
│   ├── evaluation/        # 评估分析模块
│   ├── rag/               # RAG检索模块
│   └── sql/               # 建表
├── knowledge-base/        # 题库与知识库原始数据
│   ├── java-backend/      # Java后端岗位
│   ├── web-frontend/      # Web前端岗位
│   └── python-algorithm/  # Python算法岗位
├── docs/                  # 项目文档
├── .env.example           # 环境变量模板
├── .gitignore
└── README.md
```
---

## 技术栈

| 层级       | 技术          | 版本     |
| ---------- | ------------- | -------- |
| 前端框架   | Vue 3         | 3.4.x    |
| 构建工具   | Vite          | 5.x      |
| UI组件库   | Element Plus  | 2.x      |
| 数据可视化 | ECharts       | 5.x      |
| 代码编辑器 | Monaco Editor | 0.47.x   |
| HTTP请求   | Axios         | 1.x      |
| 运行环境   | Node.js       | 20.x LTS |
| 后端语言   | Python        | 3.11.x   |
| 后端框架   | FastAPI       | 0.111.x  |
| LLM框架    | LangChain     | 0.2.x    |
| 语音识别   | Whisper       | latest   |
| 代码执行   | Judge0 API    | 云端调用 |
| 主数据库   | MySQL         | 8.0.x    |
| 缓存       | Redis         | 7.x      |
| 向量数据库 | ChromaDB      | 0.5.x    |
| LLM        | DeepSeek API  | -        |

---

## 环境要求

- Python 3.11.x
- Node.js 20.x LTS
- MySQL 8.0.x
- Redis 7.x

---

## 快速启动

### 1. 克隆仓库
\```bash
git clone https://github.com/ninadream666/InterviewEcho.git
\```

### 2. 配置环境变量
\```bash
cp .env.example .env
\```
### 3. 启动后端
\```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
\```

### 4. 启动前端
\```bash
cd frontend
npm install
npm run dev
\```

---


## 开发规范

- 各自在feature分支开发，完成后发PR
- 提交信息格式：
  - `feat: 新功能描述`
  - `fix: 修复问题描述`
  - `docs: 文档更新描述`
  - `refactor: 代码重构描述`
- 禁止直接向main分支推送代码
- `.env`文件禁止提交到仓库


