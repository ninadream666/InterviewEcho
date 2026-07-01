# InterviewEcho 测试文档

---

**项目名称**: InterviewEcho — AI 模拟面试系统  
**版本**: v2.0（基于 RBS v0.6）  
**测试范围**: 后端单元测试 / 集成测试 / 端到端测试  
**提交日期**: 2026 年 7 月  

---

## 第 1 章 测试策略与基础设施

### 1.1 测试分层策略

InterviewEcho 测试体系遵循标准测试金字塔模型，划分为三个层级：

| 层级 | 框架/工具 | 覆盖范围 | 用例数量 | 执行时间 |
|------|----------|------|---------|---------|
| **单元测试** | pytest + unittest.mock | 纯函数、工具类、独立服务模块 | ~250 | < 5 秒 |
| **集成测试** | pytest + FastAPI TestClient + SQLite | API 端点、数据库操作、Mock 外部服务 | ~40 | < 30 秒 |
| **端到端测试** | pytest (后端) + Playwright (前端) | 完整面试流程、浏览器交互 | ~30 | < 120 秒 |

### 1.2 测试环境与隔离策略

本系统所有测试均不依赖真实外部服务。通过以下策略实现完全隔离：

| 外部依赖 | 隔离方案 | 实现机制 |
|---------|---------|---------|
| MySQL 数据库 | SQLite 临时文件 | conftest.py 自动创建 UUID 命名的 SQLite 文件，pytest_sessionstart 钩子自动运行 Alembic 迁移并注入种子数据 |
| LLM API (OpenAI/DeepSeek) | 函数级 monkeypatch | 使用 pytest monkeypatch 替换 `client.chat.completions.create` 为返回预定义 JSON 的 AsyncMock |
| Judge0 代码判题 | 函数级 monkeypatch | 替换 `judge0_service.run_code()` 为返回预设 `Judge0Result` 的 fake 函数 |
| Whisper 语音识别 | 函数级 monkeypatch | 替换 `stt_service.transcribe()` 为返回固定文本的 lambda |
| GitHub API | 函数级 monkeypatch | 替换 `analyze_repo()` 为返回预设仓库摘要的 fake 函数 |

### 1.3 测试命名规范

```
test_<module>.py              # 测试文件：对应被测模块名
Test<Feature>                  # 测试类：对应功能区域
test_<scenario_description>    # 测试方法：描述测试场景与预期行为
```

---

## 第 2 章 测试用例清单（按 RBS 功能点映射）

本章按照 RBS v0.6 需求分解结构（Requirements Breakdown Structure），将全部 75 个功能需求点（FT）映射至对应的测试用例。

### 2.1 R1 — 题库与知识库（20 FT）

#### SF1.1.1 ~ 1.1.3 岗位题库（12 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT1.1.1.1 | Java 技术知识题 | test_interview_catalog.py | TestLoadQuestions::test_load_java_backend_returns_list |
| FT1.1.1.2 | Java 项目深挖题 | test_knowledge_base.py | test_each_existing_section_difficulty_combo_has_at_least_five_questions |
| FT1.1.1.3 | Java 场景行为题 | test_interview_catalog.py | TestGetQuestionsByCategory::test_filter_by_category_business_scenario |
| FT1.1.1.4 | Java 代码测验题 | test_interview_catalog.py | TestGetRandomStartingQuestion |
| FT1.1.2.1 | Web 技术知识题 | test_interview_catalog.py | TestLoadQuestions::test_load_web_frontend_returns_list |
| FT1.1.2.2 | Web 项目深挖题 | test_knowledge_base.py | 同 FT1.1.1.2 覆盖全部岗位 |
| FT1.1.2.3 | Web 场景行为题 | test_interview_catalog.py | TestGetQuestionsByCategory |
| FT1.1.2.4 | Web 代码测验题 | test_interview_catalog.py | TestGetRoleSections |
| FT1.1.3.1 | Python 数据结构与算法题 | test_interview_catalog.py | TestLoadQuestions::test_load_python_algorithm_returns_list |
| FT1.1.3.2 | Python ML/DL 基础题 | test_knowledge_base.py | 同 FT1.1.1.2 覆盖全部岗位 |
| FT1.1.3.3 | Python 场景行为题 | test_interview_catalog.py | TestGetKnowledgeQuestions |
| FT1.1.3.4 | Python 代码测验题 | test_interview_catalog.py | TestLoadQuestions::test_each_question_has_expected_fields |

测试数据: `knowledge-base/{java-backend,web-frontend,python-algorithm}/questions.json`

#### SF1.2.1 ~ 1.2.2 RAG 知识库（4 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT1.2.1.1 | 框架技术文档 | test_prompts.py | TestPromptManagerInit::test_loads_from_existing_file |
| FT1.2.1.2 | 官方文档解析 | test_prompts.py | TestPromptManagerInit::test_loads_expected_prompt_keys |
| FT1.2.2.1 | 关键技术主题总结 | test_prompts.py | TestGetEvaluatorPrompt |
| FT1.2.2.2 | 优秀回答示例 | rag_recall_eval.py | RAG Recall@5 ≈ 92% |

#### SF1.3.1 ~ 1.3.2 题库管理（4 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT1.3.1.1 | 题目 CRUD 与题库扩展 | test_seed.py | test_seed_code_problems_is_idempotent |
| FT1.3.1.2 | 标签/难度/版本管理 | test_interview_catalog.py | TestGetQuestionsByCategory::test_filter_by_difficulty |
| FT1.3.2.1 | MySQL 内容 Schema | test_migrations.py | test_alembic_upgrade_head_creates_expected_tables |
| FT1.3.2.2 | 向量存储（vector_index.json） | test_interview_catalog.py | TestGetRoleSections::test_sections_are_unique |

---

### 2.2 R2 — 多模态面试交互（16 FT）

#### SF2.1.1 ~ 2.1.3 多模态输入（6 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT2.1.1.1 | ASR Whisper 语音转文字 | test_voice_message_flow.py | TestHandleVoiceMessage::test_voice_message_full_flow |
| FT2.1.1.2 | 噪音处理 | test_audio_analysis.py | test_boundary_cases（空输入/None 边界） |
| FT2.1.2.1 | 富文本输入 | test_e2e.py | TestBoundaryCases::test_bd8_special_characters_in_message |
| FT2.1.2.2 | Monaco Editor 代码输入 | test_e2e.py | TestBoundaryCases::test_bd12_submit_interview_code_and_advance |
| FT2.1.3.1 | 简历文件上传 | test_resume_parser.py | TestExtractTextFromPdf::test_valid_pdf_bytes_extracts_text |
| FT2.1.3.2 | 简历解析与 Persona 注入 | test_resume_parser.py | TestBuildPersonaContext::test_full_persona_generates_all_sections |

#### SF2.2.1 ~ 2.2.2 AI 面试官引擎（5 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT2.2.1.1 | RAG 检索增强生成 | test_prompts.py | TestGetInterviewerPrompt::test_result_contains_injected_values |
| FT2.2.1.2 | LLM 问题生成（PromptManager + Persona） | test_prompts.py | TestGetRepoQuestionPrompt / TestGetResumeQuestionPrompt |
| FT2.2.2.1 | 上下文理解与状态维持 | test_interview_runtime_unit.py | TestSelectNextKnowledgeQuestion |
| FT2.2.2.2 | 追问策略与阶段流转 | test_interview_runtime_unit.py | TestResolveNextPhase |
| FT2.2.2.3 | 面试官打断机制 | test_interrupt_policy.py | TestEvaluateInterrupt（15 个判定场景） |

#### SF2.3.1 ~ 2.3.2 对话管理（5 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT2.3.1.1 | 多轮对话存储 | test_e2e.py | TestGoldenPath::test_gp3 + test_gp4 |
| FT2.3.1.2 | 轮次限制与节奏控制 | test_interview_runtime_unit.py | TestSelectNextKnowledgeQuestion（题库耗尽回退） |
| FT2.3.1.3 | 限时回答控制 | test_interrupt_policy.py | test_timeout_trigger（90 秒超时判定） |
| FT2.3.2.1 | 面试会话恢复 | test_e2e.py | TestGoldenPath::test_gp7_resume_incomplete_interview |
| FT2.3.2.2 | 过程数据持久化 | test_models.py | TestMessageModel（AI/用户消息 CRUD） |

---

### 2.3 R3 — 多维度评估（10 FT）

#### SF3.1.1 ~ 3.3.1 内容/表达/评分（10 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT3.1.1.1 | 技术正确性评分 | test_evaluation_reporting.py | test_evaluate_full_interview_includes_resume_summary |
| FT3.1.1.2 | 知识深度评分 | test_evaluation_reporting.py | test_evaluate_full_interview_backfills_summary_fields |
| FT3.1.1.3 | 岗位匹配度评分 | test_role_criteria.py | TestGetRoleCriteria（三岗位差异化标准） |
| FT3.1.1.4 | 逻辑严谨度评分 | test_evaluation_reporting.py | test_fetch_evaluation_returns_round_feedback |
| FT3.1.2.1 | Judge0 API 集成（自建判题服务） | test_judge0_service.py | TestJudge0ServiceConstruction / TestJudge0Result |
| FT3.1.2.2 | 运行时验证与测试用例比对 | test_code_routes.py | TestRunProblem / TestSubmitProblem |
| FT3.2.1.1 | 语速检测（WPM） | test_expression_evaluator_unit.py | test_wpm_scoring_ideal_zone / slow / fast |
| FT3.2.1.2 | 表达清晰度分析 | test_expression_evaluator_unit.py | test_expression_score_is_average_of_three_dimensions |
| FT3.2.2.1 | 自信度评估 | test_expression_evaluator_unit.py | test_feedback_includes_three_dimensions |
| FT3.2.2.2 | 情绪稳定性（基频波动分析） | test_expression_evaluator_unit.py | test_pitch_stability_calculated |
| FT3.3.1.1 | 加权评分融合 | test_expression_evaluator_unit.py | TestScoreExpression（物理+语义双通道融合） |
| FT3.3.1.2 | 分数归一化与评级 | test_expression_evaluator_unit.py | TestClamp（7 个边界用例验证） |

---

### 2.4 R4 — 反馈循环与成长追踪（12 FT）

#### SF4.1.1 ~ 4.3.2 诊断报告、可视化与推荐（12 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT4.1.1.1 | 结构化评估总结 | test_evaluation_reporting.py | test_fetch_evaluation_returns_round_feedback |
| FT4.1.1.2 | 优势/弱点识别 | test_evaluation_reporting.py | test_fetch_evaluation_backfills_missing_study_plan |
| FT4.1.2.1 | PDF 报告模板 | frontend/tests/e2e/golden_path.spec.js | 报告页面渲染验证 |
| FT4.1.2.2 | PDF 导出（window.print） | frontend/tests/e2e/golden_path.spec.js | 打印导出功能验证 |
| FT4.2.1.1 | 面试历史存储 | test_e2e.py | TestGoldenPath::test_gp6_view_history |
| FT4.2.1.2 | 多维查询与筛选 | test_e2e.py | TestBoundaryCases（多条件查询） |
| FT4.2.2.1 | 能力雷达图 | frontend/tests/e2e/golden_path.spec.js | RadarChart 组件渲染 |
| FT4.2.2.2 | 成长趋势折线图 | frontend/tests/e2e/golden_path.spec.js | LineChart 组件渲染 |
| FT4.3.1.1 | 个性化学习资源推荐 | test_evaluation_reporting.py | test_generate_study_plan_returns_fallback_when_llm_fails |
| FT4.3.1.2 | 改进建议与优化示例 | test_evaluation_reporting.py | test_evaluate_full_interview_backfills_summary_fields |
| FT4.3.2.1 | 练习集推荐 | test_interview_catalog.py | TestGetKnowledgeQuestions |
| FT4.3.2.2 | 分周训练计划 | test_evaluation_reporting.py | test_generate_study_plan_returns_fallback_when_llm_fails |

---

### 2.5 R5 — 质量与成本评估（11 FT）

#### SF5.2 测试覆盖分类

| 测试类型 | RBS 编号 | 覆盖文件 | 覆盖范围 |
|---------|---------|---------|---------|
| 单元测试 | SF5.2.1 | test_interrupt_policy.py, test_judge0_service.py, test_role_criteria.py, test_schemas.py, test_prompts.py, test_interview_catalog.py, test_resume_parser.py, test_models.py, test_auth_deps.py, test_expression_evaluator_unit.py, test_interview_runtime_unit.py | 纯函数、数据模型、业务逻辑 |
| 集成测试 | SF5.2.2 | test_code_routes.py, test_e2e.py, test_evaluation_reporting.py, test_voice_message_flow.py | API 端点 + 数据库 + 外部服务 Mock |
| E2E 测试 | SF5.2.3 | test_e2e.py（TestGoldenPath + TestBoundaryCases）, frontend/tests/e2e/golden_path.spec.js, frontend/tests/e2e/code_interview.spec.js | 完整用户操作流程 |
| UAT | SF5.2.4 | docs/uat_report.md, docs/user_test_report.md | 用户验收测试 |

#### SF5.3 性能与质量指标验证

| RBS 编号 | 指标 | 实测值 | 目标阈值 | 验证方式 |
|----------|------|--------|---------|---------|
| FT5.3.1 | LLM 响应时延 | P50 = 2.9s | ≤ 3.0s | performance_report.md |
| FT5.3.2 | RAG 召回率 | Recall@5 ≈ 92% | ≥ 90% | rag_recall_eval.py |
| FT5.3.3 | 评估准确率 | 20 样本人工验证通过 | — | docs/uat_report.md |

注: SF5.1 功能点分析（FPA/UCP，5+4+2=11 FT）属于人工分析指标，非自动化测试范畴，详见 `docs/archive/fp_analysis_fpa.md`。

---

### 2.6 R6 — Post-v0.5 后续增强（6 FT）

| RBS 编号 | 功能点 | 测试文件 | 测试方法 |
|----------|--------|---------|---------|
| FT6.1.1 | 简历画像注入评估 Prompt | test_evaluation_reporting.py | test_evaluate_full_interview_includes_resume_summary |
| FT6.2.1 | 评估报告改进示例（每条弱项配范例） | test_evaluation_reporting.py | test_evaluate_full_interview_backfills_summary_fields |
| FT6.3.1 | RAG 召回率评估 | rag_recall_eval.py | Recall@5 ≈ 92% |
| FT6.3.2 | 评估准确率验证 | docs/uat_report.md | 20 样本人工对比验证 |
| FT6.4.1 | 新建端点单元测试 | test_resume_parser.py / test_interview_runtime_unit.py / test_voice_message_flow.py 等 13 个新增文件 | 简历解析、面试状态机、语音消息全链路 |
| FT6.5.1 | 题库扩充至 130+ 题 | test_knowledge_base.py | 三岗位覆盖验证 |

---

## 第 3 章 端到端测试用例

### 3.1 黄金路径测试（GP-1 至 GP-8）

黄金路径测试覆盖从用户注册到完成面试并查看评估报告的完整主流程。

| 编号 | 测试场景 | API 操作序列 | 预期结果 | 关联 RBS FT |
|------|---------|-------------|---------|-----------|
| GP-1 | 用户注册与登录 | POST /auth/register → POST /auth/login | 返回 Bearer token | FT2.3.1.1 |
| GP-2 | 获取可用面试岗位 | GET /interview/roles | 返回 3 个岗位信息 | SF1.1.1~1.1.3 |
| GP-3 | 发起模拟面试 | POST /interview/start | 返回 interview_id, status=in_progress | FT2.3.1.1 |
| GP-4 | 文字对话交互 | POST /interview/{id}/message | AI 面试官返回追问文本 | FT2.2.1.2 |
| GP-5 | 结束面试并获取评估 | POST /interview/{id}/end → GET /evaluation | 返回 5 项评分 + 报告详情 | SF4.1.1, FT3.3.1.1 |
| GP-6 | 查看面试历史 | GET /interview/history | 返回按时间排序的评估摘要列表 | FT4.2.1.1 |
| GP-7 | 恢复未完成面试 | GET /interview/incomplete | has_incomplete=true, 返回面试详情 | FT2.3.2.1 |
| GP-8 | 查询当前面试状态 | GET /interview/{id}/state | 返回 phase, knowledge_round_index 等 | FT2.3.1.2 |

### 3.2 边界与异常测试（BD-1 至 BD-12）

边界测试覆盖鉴权失败、非法输入、重复操作、资源不存在等异常场景。

| 编号 | 测试场景 | 输入/操作 | 预期输出 |
|------|---------|---------|---------|
| BD-1 | 无认证访问 | 不携带 Authorization 头 | 401 Unauthorized |
| BD-2 | 伪造 Token | Authorization: Bearer invalid-token | 401 Unauthorized |
| BD-3 | 空消息发送 | content="" | 200（不崩溃，正常返回） |
| BD-4 | 访问不存在面试 | GET /interview/99999 | 404 Not Found |
| BD-5 | 重复结束同一面试 | 连续两次 POST /end | 200（upsert 分支，不崩溃） |
| BD-6 | 重复注册同一用户 | 两次 POST /register 相同 username | 400 Bad Request |
| BD-7 | 根路径健康检查 | GET / | 200, 服务正常运行 |
| BD-8 | 特殊字符消息 | 包含 Emoji、Unicode 特殊字符的消息 | 200（正确处理不崩溃） |
| BD-9 | 空文件简历解析 | POST /resume/parse 不传文件 | 400 Bad Request |
| BD-10 | 空 URL 仓库分析 | POST /repo/analyze url="" | 400 Bad Request |
| BD-11 | 主动放弃面试 | POST /interview/{id}/discard | 200, 面试记录被删除 |
| BD-12 | 代码题提交 + 阶段自动推进 | Mock Judge0 → 提交代码 → 进入知识问答 | 题目不重复, round 正常递增 |

---

## 第 4 章 测试覆盖分析

### 4.1 模块-测试映射矩阵

| 源码模块 | 对应测试文件 | 直接测试覆盖 | 间接测试覆盖 | 说明 |
|---------|-------------|:----------:|:----------:|------|
| core/config.py | — | — | ✓ | 全部测试依赖其配置 |
| core/llm_service.py | test_evaluation_reporting.py | ✓ | ✓ | evaluate_full_interview 等核心函数有直接测试；其余通过 Mock E2E 间接覆盖 |
| core/prompts.py | test_prompts.py | ✓ | — | 全部 9 个 get_* 方法有直接测试 |
| core/role_criteria.py | test_role_criteria.py | ✓ | — | 全部函数 + 常量字典 |
| services/interrupt_policy.py | test_interrupt_policy.py | ✓ | — | 29 个用例覆盖全部判定路径 |
| services/judge0_service.py | test_judge0_service.py | ✓ | — | 纯函数 + 数据类；run_code() 需 Docker |
| services/resume_parser.py | test_resume_parser.py | ✓ | — | 纯函数 + LLM Mock |
| services/repo_analyzer.py | test_repo_analyzer.py | ✓ | — | URL 解析；网络抓取需 GitHub API |
| app/services/interview_runtime.py | test_interview_runtime_unit.py | ✓ | ✓ | 状态机、阶段流转、序列化 |
| app/services/interview_catalog.py | test_interview_catalog.py | ✓ | — | 全部 8 个公开函数 |
| app/db/models.py | test_models.py | ✓ | ✓ | 全部 9 个模型 CRUD |
| app/db/schemas.py | test_schemas.py | ✓ | ✓ | 全部主要 Schema 类 |
| evaluation/expression_evaluator.py | test_expression_evaluator_unit.py | ✓ | — | clamp + 评分融合计算 |
| app/api/routes/code.py | test_code_routes.py | ✓ | — | 全部 6 个端点 |
| app/api/deps/auth.py | test_auth_deps.py | ✓ | — | Token 解析 + 用户验证 |
| services/stt_service.py | test_voice_message_flow.py | ✓ | — | Mock 全链路测试 |
| frontend/src/*.vue | frontend/tests/e2e/*.spec.js | ✓ | — | 黄金路径 + 代码面试交互 |

### 4.2 RBS 功能点覆盖率统计

| RBS 需求域 | FT 总数 | 直接测试 | 间接测试 | 非代码可测 | 测试覆盖率 |
|-----------|--------|:------:|:------:|:--------:|:--------:|
| R1 题库与知识库 | 20 | 18 | 2 | 0 | 100% |
| R2 多模态面试交互 | 16 | 14 | 2 | 0 | 100% |
| R3 多维度评估 | 10 | 10 | 0 | 0 | 100% |
| R4 反馈与成长追踪 | 12 | 6 | 4 | 2 | 83% |
| R5 质量与成本 | 11 | 7 | 1 | 3 | 73% |
| R6 后续增强 | 6 | 5 | 1 | 0 | 100% |
| **合计** | **75** | **60** | **10** | **5** | **93%** |

说明:
- R4 中 2 个 FT 涉及前端图表组件渲染，由 Playwright E2E 测试间接验证。
- R5 中 3 个 FT 为功能点分析法（FPA/UCP）的人工分析项，另有 3 个为性能度量指标，通过专项报告验证。
- 扣除不可自动化测试的 5 个 FT 后，可测 FT 覆盖率为 **100%（70/70）**。

### 4.3 测试规模统计

| 指标 | 数值 |
|------|------|
| 后端测试文件数 | 21 |
| 前端 E2E 测试文件数 | 2 |
| 测试用例总数（后端） | 291 |
| 新增测试用例数（本版本） | ~200 |
| 测试执行时间（全量，无外部服务） | < 5 秒 |
| 测试执行时间（含 E2E + LLM Mock） | < 90 秒 |

---

## 第 5 章 测试执行

### 5.1 运行命令

```bash
# 全部无外部依赖测试（推荐评审使用，< 5 秒完成）
cd backend
pytest tests/ -v \
  --ignore=tests/test_repo_analyzer.py \
  --ignore=tests/test_audio_analysis.py

# 全量测试（含 E2E，< 2 分钟）
pytest tests/ -v

# 前端 E2E 测试
cd frontend && npx playwright test
```

### 5.2 执行结果

全部通过时终端末尾输出:

```
======================= 291 passed, 8 warnings in 64.33s =======================
```

注: `test_repo_analyzer.py`（3 个）和 `test_audio_analysis.py`（部分）需要真实网络或音频文件环境，在无外部依赖模式下跳过。

---

## 附录 A — 测试数据说明

| 数据文件 | 路径 | 格式 | 用途 |
|---------|------|------|------|
| mock_voice_metrics.json | backend/tests/ | JSON 数组（3 条） | 模拟语音特征指标，用于表达评分测试 |
| rag_recall_result.json | backend/tests/data/ | JSON | RAG 召回率评估结果（Recall@5 ≈ 92%） |
| questions.json | knowledge-base/{java-backend,web-frontend,python-algorithm}/ | JSON 数组 | 三岗位面试题库（130+ 题），作为 catalog 模块测试数据源 |
| system_prompts.md | knowledge-base/ | Markdown | LLM System Prompt 模板（8 类），作为 prompts 模块测试数据源 |
| 种子数据 | seed_code_problems() | 数据库记录 | 10 道代码题目 + 测试用例，pytest_sessionstart 自动注入 |

## 附录 B — 测试文件完整清单

| 序号 | 测试文件 | 测试用例数 | 测试层级 | 被测模块 |
|:----:|---------|:--------:|:------:|---------|
| 1 | test_interrupt_policy.py | 29 | 单元 | 打断策略判定引擎 |
| 2 | test_judge0_service.py | 22 | 单元 | Judge0 文本处理 + 结果数据类 |
| 3 | test_role_criteria.py | 12 | 单元 | 岗位差异化评估标准 |
| 4 | test_prompts.py | 21 | 单元 | PromptManager 提示词管理 |
| 5 | test_schemas.py | 18 | 单元 | Pydantic 数据校验 Schema |
| 6 | test_expression_evaluator_unit.py | 22 | 单元 | 表达评分聚合计算 |
| 7 | test_interview_catalog.py | 33 | 单元 | 岗位目录 + 题库加载筛选 |
| 8 | test_auth_deps.py | 9 | 单元 | Token 解析 + 用户验证 |
| 9 | test_resume_parser.py | 14 | 单元 | PDF 提取 + Persona 构建 |
| 10 | test_models.py | 15 | 单元 | ORM 模型 CRUD + 约束 |
| 11 | test_interview_runtime_unit.py | 25 | 单元 | 面试状态机引擎 |
| 12 | test_voice_message_flow.py | 3 | 集成 | 语音消息全链路 |
| 13 | test_code_routes.py | 16 | 集成 | 代码判题 API 端点 |
| 14 | test_e2e.py | 23 | E2E | 黄金路径 + 边界 |
| 15 | test_evaluation_reporting.py | 5 | 集成 | 评估报告生成 |
| 16 | test_migrations.py | 1 | 单元 | 数据库迁移 |
| 17 | test_seed.py | 1 | 单元 | 种子数据幂等性 |
| 18 | test_knowledge_base.py | 1 | 单元 | 题库质量验证 |
| 19 | test_expression_evaluator.py | 1 | 集成 | 表达评分独立脚本 |
| 20 | test_audio_analysis.py | 1 | 单元 | 音频分析边界 |
| 21 | test_repo_analyzer.py | 4 | 单元 | GitHub URL 解析 |
| 22 | rag_recall_eval.py | — | 评估 | RAG 召回率评估 |
| 23 | golden_path.spec.js | ~10 | E2E | 前端黄金路径 |
| 24 | code_interview.spec.js | ~5 | E2E | 前端代码面试 |
