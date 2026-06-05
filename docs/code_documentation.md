# InterviewEcho 核心代码文档与编码规范说明

本文档面向课程评审与教师审阅，说明本项目当前实现中的核心文件组织、关键函数设计、代码命名规范、样式规范与注释规范。本文档所描述内容均以当前仓库实现为准。

## 一、项目代码结构概览

### 1.1 后端结构概览

后端采用 `FastAPI + SQLAlchemy + Alembic` 组合，当前以 `backend/app/` 为应用主入口，`backend/main.py` 仅保留启动兼容入口。

```text
backend/
├── main.py
├── alembic.ini
├── alembic/                          # 数据库迁移
├── app/
│   ├── __init__.py                   # create_app() 工厂
│   ├── api/
│   │   ├── router.py                 # 总路由
│   │   ├── deps/                     # 依赖注入
│   │   └── routes/                   # 认证、面试、代码题接口
│   ├── core/
│   │   ├── config.py                 # 配置系统
│   │   └── llm_service.py            # LLM 桥接入口
│   ├── db/
│   │   ├── base.py                   # Base
│   │   ├── session.py                # SessionLocal / get_db
│   │   ├── models.py                 # ORM 模型
│   │   ├── schemas.py                # Pydantic Schema
│   │   ├── default_code_problem_bank.py
│   │   └── seed_code_problems.py
│   ├── cli/
│   │   ├── seed_code_problems.py     # 题库初始化命令
│   │   └── build_rag_index.py        # RAG 索引构建命令
│   └── services/
│       ├── interview_catalog.py      # 岗位与知识点目录
│       ├── interview_runtime.py      # 面试状态机核心
│       ├── judge0_service.py         # 判题桥接入口
│       ├── repo_analyzer.py          # GitHub 分析桥接入口
│       ├── resume_parser.py          # 简历解析桥接入口
│       ├── stt_service.py            # 语音转写桥接入口
│       ├── audio_analysis.py         # 音频分析桥接入口
│       └── interrupt_policy.py       # 打断策略桥接入口
├── core/                             # 当前仍承载部分真实实现
├── services/                         # 当前仍承载部分真实实现
├── evaluation/                       # 表达评分模块
├── db/                               # 题库数据源与 seed 实现
├── rag/                              # RAG 索引构建实现
└── tests/                            # 测试
```

### 1.2 前端结构概览

前端采用 `Vue 3 + Vite + Pinia + Element Plus + Tailwind CSS`，页面已按功能收口到 `features/` 目录。

```text
frontend/src/
├── main.js
├── App.vue
├── router/index.js
├── stores/auth.js
├── api/index.js
├── layouts/
│   ├── DefaultLayout.vue
│   └── InterviewLayout.vue
├── components/
│   ├── business/
│   └── analytics/
├── features/
│   ├── shared/views/HomeView.vue
│   ├── auth/views/LoginView.vue
│   ├── interview/views/
│   │   ├── DashboardView.vue
│   │   └── InterviewRoomView.vue
│   ├── report/views/
│   │   ├── ProfileView.vue
│   │   └── ReportView.vue
│   └── code-practice/views/
│       ├── CodePracticeView.vue
│       └── CodeProblemView.vue
└── utils/datetime.js
```

该结构体现了两点：
- 路由层、业务层、组件层职责分离；
- 页面路径保持稳定，但实现文件按业务域组织，便于后续维护。

## 二、核心文件及其职责说明

### 2.1 `backend/main.py`

该文件是后端的启动兼容入口，职责非常单一：导入应用工厂并生成 `app`。

```python
from app import create_app

app = create_app()
```

这种写法的好处是：
- 启动命令保持稳定：`uvicorn main:app --reload`
- 应用初始化逻辑集中在 `create_app()` 中，不散落在启动脚本里
- 有利于测试、部署和后续扩展

### 2.2 `backend/app/__init__.py`

该文件中的 `create_app()` 是后端应用装配中心，负责：
- 创建 FastAPI 实例
- 配置 CORS
- 挂载统一的 `/api` 路由

这使得框架配置与业务逻辑分离，避免在路由文件中混入全局初始化代码。

### 2.3 `backend/app/api/router.py`

该文件是后端总路由器，负责将认证、面试、代码题等子路由统一挂载到 `/api` 前缀下。其价值主要体现在：
- 路由层次清晰；
- 后续新增业务模块时改动集中；
- 便于教师或开发者快速理解接口分区。

### 2.4 `backend/app/services/interview_runtime.py`

该文件是整个系统最核心的业务文件，承担了以下职责：
- 面试启动；
- 面试状态机推进；
- 代码题阶段推进；
- 语音消息接入；
- 中断恢复；
- 报告生成前的数据准备。

可以理解为：它是整个“模拟面试引擎”的运行时总控模块。

### 2.5 `backend/app/db/models.py`

该文件定义了全部核心 ORM 模型，包括：
- 用户 `User`
- 面试会话 `Interview`
- 消息 `Message`
- 评估 `Evaluation`
- 语音指标 `VoiceMetrics`
- 代码题、测试用例、提交记录等

其设计重点在于：
- 用结构化字段保存面试状态机进度；
- 用 JSON 文本字段保存简历、仓库、已问题目等柔性上下文；
- 用独立提交表保存代码题评测记录。

### 2.6 `frontend/src/features/interview/views/InterviewRoomView.vue`

该文件是前端面试房间的核心视图，负责：
- 聊天消息展示；
- 语音录音与上传；
- 代码题编辑器区域展示；
- 当前阶段显示；
- 倒计时与自动结束触发；
- 与 `/state`、`/messages`、`/code/submit` 等接口联动。

它对应了系统中“用户最复杂的单页交互场景”。

### 2.7 `frontend/src/api/index.js`

该文件是前端接口封装的统一入口，负责：
- 创建 Axios 实例；
- 注入登录态 token；
- 抽出 `resumeApi`、`evaluationApi`、`interviewApi`、`codeApi`；
- 让页面层尽量少直接书写裸请求。

这种封装降低了页面与后端 URL 细节的耦合度。

## 三、核心函数源码及其解释

本节选择最能体现系统设计思想的几个核心函数进行说明。

### 3.1 面试状态机核心函数：`process_message_logic()`

文件：`backend/app/services/interview_runtime.py`

该函数是整场面试推进的关键，决定候选人每回答一次后，系统应进入哪个阶段并给出什么回应。

```python
async def process_message_logic(
    interview_id: int,
    content: str,
    db: Session,
    user_id: int,
    duration_sec: Optional[float] = None,
):
    interview = _get_interview_for_user(db, user_id, interview_id)

    if interview.phase == PHASE_COMPLETED or interview.status == "completed":
        response = _create_ai_message(db, interview, "本场面试已经结束，请直接生成并查看报告。", "closing", True)
        return response, None

    user_msg = models.Message(interview_id=interview_id, sender="user", content=content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    if interview.phase == PHASE_CODE:
        reminder = '当前处于代码题环节，请在代码编辑器中完成作答并点击「提交代码给面试官」，我会根据判题结果继续推进。'
        response = _create_ai_message(db, interview, reminder, "code_question")
        return response, user_msg.id

    if interview.phase == PHASE_INTRODUCTION:
        next_phase = _resolve_next_phase(interview)
        if next_phase == PHASE_RESUME:
            resume_question = await _select_resume_question(interview)
            interview.phase = PHASE_RESUME
            _append_asked_title(interview, resume_question["question"])
            db.commit()
            response = _create_ai_message(db, interview, resume_question["question"], "resume_question")
            return response, user_msg.id
```

该函数的设计价值主要体现在：

1. 将“流程控制”集中到一个状态机函数中，而不是分散在多个路由里。
2. 使用 `phase` 明确表达当前阶段，而不是依赖消息类型猜测状态。
3. 在代码题阶段强制由编辑器提交，避免聊天框回答扰乱流程。
4. 通过 `_resolve_next_phase()` 和 `_append_asked_title()` 将“阶段流转”和“去重记录”模块化。

从系统工程角度看，这种写法比“按 if/else 到处穿插业务条件”的结构更稳定，也更容易测试。

### 3.2 面试启动函数：`start_interview()`

文件：`backend/app/services/interview_runtime.py`

该函数负责创建一场新的面试会话，并在开始时完成上下文注入与代码题绑定。

```python
interview = models.Interview(
    user_id=user_id,
    role=payload.role,
    difficulty=payload.difficulty,
    knowledge_points=knowledge_points_json,
    total_rounds=payload.total_rounds,
    status="in_progress",
    phase=PHASE_INTRODUCTION,
    knowledge_round_index=0,
    repo_context=repo_context_json,
    custom_questions=custom_questions_json,
    resume_persona=resume_persona_json,
    active_code_problem_id=code_problem.id,
    active_code_submission_id=None,
    asked_question_titles="[]",
)
db.add(interview)
db.commit()
db.refresh(interview)
```

该实现体现了如下思想：
- 面试一开始就绑定固定代码题，保证恢复时题目不变；
- 仓库分析、简历画像等上下文在启动时一次性注入；
- 知识问答轮次和已问题目列表都在数据层显式记录，方便恢复与测试。

### 3.3 面试代码提交函数：`submit_interview_code()`

文件：`backend/app/services/interview_runtime.py`

该函数实现了“代码题阶段提交后自动进入知识问答”的完整闭环。

```python
if interview.phase != PHASE_CODE:
    raise HTTPException(status_code=400, detail="当前面试不在代码作答阶段")

problem = db.query(models.CodeProblem).filter(models.CodeProblem.id == interview.active_code_problem_id).first()
language, source_code = _validate_code_request(payload)

cases = (
    db.query(models.CodeTestCase)
    .filter(models.CodeTestCase.problem_id == problem.id)
    .order_by(models.CodeTestCase.sort_order.asc(), models.CodeTestCase.id.asc())
    .limit(settings.CODE_MAX_TEST_CASES)
    .all()
)

status, passed_count, total_count, results = await _run_interview_code_cases(cases, language, source_code)
```

随后，该函数会继续完成三件事：
- 保存 `CodeSubmission`；
- 调用 `generate_code_review()` 生成代码点评；
- 调用 `_move_to_knowledge_or_close()` 推进到后续阶段。

这一设计的优点是：
- 代码题阶段不再是前端自行拼接逻辑，而是真正由后端接管；
- 判题、落库、点评、阶段推进形成单一事务链路；
- 接口返回值既包含判题结果，也包含下一条 AI 消息，前端接入简单。

### 3.4 代码题列表接口：`list_problems()`

文件：`backend/app/api/routes/code.py`

该函数是代码练习模块的入口接口，负责列表筛选与已通过状态聚合。

```python
@router.get("/problems", response_model=schemas.CodeProblemListResponse)
def list_problems(
    difficulty: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    rows = (
        db.query(models.CodeProblem)
        .filter(models.CodeProblem.is_active == True)
        .order_by(models.CodeProblem.order_index.asc(), models.CodeProblem.id.asc())
        .all()
    )
```

该函数的意义在于：
- 它不是简单返回数据库原始记录，而是把筛选、标签汇总、判题可用状态、已通过状态一起整理为前端友好的响应结构；
- 这体现了“路由层做协议适配，服务/模型层保存业务事实”的分工。

### 3.5 前端核心视图：`InterviewRoomView.vue`

文件：`frontend/src/features/interview/views/InterviewRoomView.vue`

该文件中最重要的设计不是单个按钮事件，而是对“面试状态”的统一计算。

```javascript
const showCodePanel = computed(() => interviewState.value?.phase === 'code' && !!currentProblem.value)
const phaseLabel = computed(() => {
  const phase = interviewState.value?.phase
  const map = {
    introduction: '当前阶段：自我介绍',
    resume: '当前阶段：简历深挖',
    repo: '当前阶段：项目深挖',
    code: '当前阶段：代码题作答',
    knowledge: `当前阶段：知识问答 ${interviewState.value?.knowledge_round_index || 0}/${interviewState.value?.knowledge_round_total || 0}`,
    completed: '当前阶段：面试收尾'
  }
  return map[phase] || '当前阶段：准备中'
})
```

这一写法的重要性在于：
- 前端不再自行推断当前流程，而是信任后端 `/state` 返回的状态；
- `showCodePanel` 与 `phaseLabel` 都由同一个状态源驱动，降低了 UI 不一致风险；
- 代码题面板、倒计时、消息区等多个区域围绕同一个 `interviewState` 协同更新。

### 3.6 ORM 模型中的状态字段设计：`Interview`

文件：`backend/app/db/models.py`

```python
class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=True)
    knowledge_points = Column(Text, nullable=True)
    total_rounds = Column(Integer, default=5)
    status = Column(String(20), default="in_progress")
    phase = Column(String(20), default="introduction")
    knowledge_round_index = Column(Integer, default=0)
    start_time = Column(TIMESTAMP, default=utcnow)
    end_time = Column(TIMESTAMP, nullable=True)
    repo_context = Column(Text, nullable=True)
    custom_questions = Column(Text, nullable=True)
    resume_persona = Column(Text, nullable=True)
    asked_question_titles = Column(Text, nullable=True)
    active_code_problem_id = Column(Integer, nullable=True)
    active_code_submission_id = Column(Integer, nullable=True)
```

该模型体现了本项目数据库设计中的一个核心思想：  
**不仅存业务结果，也存业务过程状态。**

这样做的直接收益是：
- 面试中断后可恢复；
- 同一场面试的代码题保持一致；
- 知识问答轮次和去重状态可以跨请求保存；
- 接口测试可以直接断言阶段推进是否正确。

## 四、代码命名规范

### 4.1 Python 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | `snake_case` | `interview_runtime.py` |
| 类名 | `PascalCase` | `InterviewStateResponse` |
| 函数名 | `snake_case` | `submit_interview_code` |
| 变量名 | `snake_case` | `knowledge_round_index` |
| 常量 | `UPPER_CASE` | `PHASE_CODE` |
| 私有辅助函数 | `_` 前缀 | `_resolve_next_phase` |

### 4.2 Vue / JavaScript 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件文件 | `PascalCase` | `InterviewRoomView.vue` |
| JS 文件 | `camelCase` 或语义清晰的短横线形式 | `datetime.js` |
| 变量/函数 | `camelCase` | `showCodePanel` |
| Store | `useXxxStore` | `useAuthStore` |
| 计算属性 | `camelCase` | `phaseLabel` |

### 4.3 API 与数据库字段命名

- API 路径统一采用 REST 风格，如 `/api/interview/{id}/state`
- 数据库字段统一使用 `snake_case`
- 前后端字段语义尽量保持一致，如：
  - `knowledge_round_index`
  - `active_code_submission_id`
  - `resume_persona`

## 五、代码风格与样式规范

### 5.1 Python 代码风格

当前项目后端遵循以下风格：
- 遵循 PEP 8；
- 缩进 4 空格；
- 采用类型注解；
- 导入顺序为：标准库 → 第三方库 → 本地模块；
- 复杂文件使用“分隔注释块”组织逻辑段落；
- 对核心函数使用文档字符串说明用途、参数和返回值。

### 5.2 Vue / JavaScript 代码风格

当前项目前端遵循以下风格：
- 统一使用 Vue 3 `script setup`；
- 缩进 2 空格；
- 页面样式以 Tailwind 原子类为主；
- 状态管理优先使用 `ref`、`computed`、`watch`；
- API 调用统一从 `src/api/index.js` 进入；
- 复杂视图通过“计算属性 + 事件函数 + 生命周期”组织逻辑。

### 5.3 样式组织方式

前端页面样式整体上采用三层策略：

1. **布局层**：`DefaultLayout.vue` 与 `InterviewLayout.vue`
2. **页面层**：在页面组件中直接使用 Tailwind 类组合结构和视觉
3. **组件层**：复用 `ChatBubble`、`CodeEditor`、`ResumeDialog` 等业务组件

该方式的优点是：
- 页面视觉开发效率较高；
- 样式与结构贴近，便于单页维护；
- 公共交互组件可在多个页面复用。

## 六、注释规范

### 6.1 Python 注释规范

项目后端目前使用如下注释方式：

#### 1. 模块级文档字符串

```python
"""
模块名称：数据库 ORM 模型（models）
功能描述：定义 InterviewEcho 全部数据库表结构的 SQLAlchemy ORM 模型。
"""
```

#### 2. 函数文档字符串

```python
def get_interview_state(db: Session, user_id: int, interview_id: int) -> schemas.InterviewStateResponse:
    """获取面试当前状态（前端轮询用）。"""
```

#### 3. 段落分隔注释

```python
# ============================================================
# 核心消息处理 —— 面试对话状态机
# ============================================================
```

#### 4. 字段分组注释

```python
# ---- 主键 ----
id = Column(Integer, primary_key=True, index=True)
# ---- 账号信息 ----
username = Column(String(50), unique=True, index=True, nullable=False)
```

这套注释风格的作用是：
- 降低大文件阅读门槛；
- 让模型字段、逻辑段落、功能边界一目了然；
- 便于教师快速定位各模块职责。

### 6.2 Vue / JavaScript 注释规范

前端组件通常采用以下形式：

#### 1. 组件头部注释

```html
<!--
  组件名称：InterviewRoomView（面试房间视图）
  功能描述：面试的核心交互界面
-->
```

#### 2. 脚本分段注释

```javascript
// ============================================================
// 面试房间 — 核心交互逻辑
// ============================================================
```

#### 3. 行内解释注释

```javascript
// 前端不自行推断阶段，直接以 /state 返回结果为准
```

这种注释风格强调“解释意图”，而不只是复述代码本身。

## 七、总结

从当前实现来看，本项目的代码组织遵循了以下原则：

1. **启动入口单一**：前后端入口清晰，数据库初始化主路径统一。
2. **状态显式建模**：面试流程通过 `phase` 和相关字段显式控制。
3. **前后端职责清晰**：后端主导流程状态机，前端负责展示与交互。
4. **可维护性优先**：通过功能目录、桥接层、统一 API 封装和规范注释降低维护成本。
5. **教学可解释性较强**：核心业务逻辑集中，文件职责明确，适合课程项目展示与讲解。

因此，当前版本不仅能够满足系统运行需求，也具备较好的课程答辩与教师评审可读性。
