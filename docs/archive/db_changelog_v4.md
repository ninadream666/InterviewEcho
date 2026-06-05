# 数据库变更
## 1. 变更摘要

新增一列 `interviews.resume_persona`，用于存储候选人上传简历后由 LLM 解析得到的结构化 JSON 数据。该字段在 `process_message_logic` 中被反序列化并注入 system prompt，让面试官能围绕候选人的真实经验出题。

---

## 2. Schema 变更

### 2.1 涉及表

| 表         | 列             | 类型 | 是否可空 | 默认值 | 说明                                                            |
| ---------- | -------------- | ---- | -------- | ------ | --------------------------------------------------------------- |
| interviews | resume_persona | TEXT | YES      | NULL   | JSON 字符串，字段：skills/projects/work_years/education/summary |



## 3. 步骤


### 3.1 装新依赖

`requirements.txt` 新增 `pypdf==4.3.1`（PDF 文本提取）。

```bash
cd backend
pip install -r requirements.txt
```

### 3.3 跑迁移
Powershell
```bash
Get-Content -Raw sql\migration_v4_resume.sql | mysql -u root -p interview_echo
```

### 3.4 验证

```sql
mysql -u root -p interview_echo -e "SHOW COLUMNS FROM interviews LIKE 'resume_persona';"
```

### 3.5 重启后端

```bash
cd backend
uvicorn main:app --reload
```

无报错即正常。

---

## 4. 前端对接（黄弋涵）

### 4.1 新增 API 端点

```
POST /interview/resume/parse
```

**请求形式 A：上传 PDF**

```
Content-Type: multipart/form-data
Body: file=@resume.pdf
```

**请求形式 B：纯文本**

```
Content-Type: multipart/form-data
Body: text=<候选人粘贴的简历文本>
```

**响应**

```json
{
  "persona": {
    "skills": ["Java", "Spring Boot", "Redis"],
    "projects": [
      {
        "name": "校园二手交易平台",
        "role": "后端主力",
        "tech": ["Spring Cloud", "MySQL", "Redis"],
        "highlights": "支撑日活 2k+ 用户"
      }
    ],
    "work_years": 0,
    "education": "XX 大学 计算机科学与技术 本科",
    "summary": "..."
  },
  "warning": ""
}
```

`warning` 非空时（如简历解析未提取到有效字段）应给用户提示。

### 4.2 InterviewStart 请求体新增字段

```json
POST /interview/start
{
  "role": "...",
  "difficulty": "...",
  "knowledge_points": [...],
  "total_rounds": 6,
  "repo_urls": [...],
  "resume_persona": { ... }   // 新增：把上一步拿到的 persona 一并传入
}
```

后端会把它存到 `interviews.resume_persona`，并在后续每轮对话中注入 system prompt。

---
