# InterviewEcho 功能点分析（FPA）报告

---

## 1. 摘要

本报告对 InterviewEcho（AI 模拟面试平台）当前已交付的后端系统进行 IFPUG 功能点分析，量化软件规模，为工作量估算、方法对比（FPA vs UCP）与最终项目方案提供度量基准。

**核心结论：**

| 指标 | 数值 |
| ---- | ---- |
| 未调整功能点 UFP | 179 |
| 价值调整因子 VAF | 1.10 |
| 调整后功能点 AFP | **≈ 197 FP** |
| 稳健区间（不同 EIF 口径） | 173 ~ 197 FP |

---

## 2. 计数边界与方法

- **应用边界**：`backend/` FastAPI 应用对外的全部 REST 接口及其维护的数据存储。
- **计数类型**：开发项目功能点计数。
- **数据来源**：路由层（auth / interview / code 三个 router，共 20 个端点）、数据层（`db/models.py` 9 张表 + 知识库 JSON + RAG 索引）、外部服务（LLM / Judge0 / GitHub / Whisper）。

功能点 = 数据功能（ILF + EIF）+ 事务功能（EI + EO + EQ），各按 IFPUG 复杂度矩阵定权重。

---

## 3. 未调整功能点（UFP）

### 3.1 汇总

| 功能类型 | 低 | 中 | 高 | 个数 | FP 小计 |
| -------- | -- | -- | -- | ---- | ------- |
| ILF | 7 | 2 | 0 | 9 | 69 |
| EIF | 3 | 1 | 0 | 4 | 22 |
| EI  | 2 | 0 | 4 | 6 | 30 |
| EO  | 1 | 3 | 1 | 5 | 26 |
| EQ  | 4 | 5 | 0 | 9 | 32 |
| **合计** | | | | **33** | **179** |

### 3.2 数据功能要点

- **9 个 ILF（69 FP）**：User、Interview、Message、Evaluation、VoiceMetrics、CodeSubmission、Question Bank 为 Low；CodeProblem（含测试用例子记录）、RAG 向量索引为 Average。
- **4 个 EIF（22 FP）**：LLM 服务（Average）、Judge0 / GitHub / Whisper（Low）。

### 3.3 事务功能要点

- **6 个 EI（30 FP）**：register、login 为 Low；start、message、voice、code submit 因多文件引用 + 外部服务编排判 High。
- **5 个 EO（26 FP）**：`/end` 综合评估为 High；resume parse、repo analyze、code run 为 Average；polish 为 Low。
- **9 个 EQ（32 FP）**：roles、sections、messages、submissions 为 Low；evaluation、history、problems、problem detail、submission detail 为 Average。

> 各功能点的 RET/DET/FTR 复杂度判定依据汇总于本节表格，附录 A 提供端点—功能点映射速查。

---

## 4. 价值调整因子（VAF）

14 项通用系统特性影响度合计 **TDI = 45**：

> 高影响项（DI=5）：在线数据录入（文本+语音双通道）、复杂处理（LLM 评分 + RAG + 音频分析 + 代码判题）。
> 中高影响项（DI=4）：数据通信、终端用户效率（Monaco/图表）、在线更新。
> 低影响项（DI=1~2）：多站点、高负载配置、安装简易性。

**VAF = 0.65 + 0.01 × 45 = 1.10。**

VAF = 1.10 表示系统技术复杂度略高于基准，主要由 AI 推理、多服务编排与富交互前端驱动，与 InterviewEcho 的实际工程特征相符。

---

## 5. 调整后功能点（AFP）

```
AFP = UFP × VAF = 179 × 1.10 = 196.9 ≈ 197 FP
```

---

## 6. 工作量参考换算

以行业经验生产率区间换算（仅供参考，非承诺）：

| 生产率假设 | 估算工作量 |
| ---------- | ---------- |
| 8 人时 / FP（含 AI 集成等复杂因素，偏保守） | ≈ 1576 人时 |
| 6 人时 / FP（中等） | ≈ 1182 人时 |

> 注：生产率受团队熟练度、技术栈与复用程度影响大，本换算仅作工作量量级参考。

---

## 7. 结论

- InterviewEcho 后端规模约 **197 调整后功能点**，在不同 EIF 计数口径下稳定于 173~197 区间。
- 规模主要集中在事务功能（88 FP，占 UFP 约 49%），反映系统“交互密集 + AI 处理密集”的特征。
- 本结果可作为后续工作量估算与项目方案规模度量的基准。

---

## 附录 A：端点—功能点映射速查

| 端点 | 类型 | FP |
| ---- | ---- | -- |
| POST /api/auth/register | EI | 3 |
| POST /api/auth/login | EI | 3 |
| POST /api/interview/start | EI | 6 |
| POST /api/interview/{id}/message | EI | 6 |
| POST /api/interview/{id}/voice | EI | 6 |
| POST /api/code/problems/{id}/submit | EI | 6 |
| POST /api/interview/{id}/end | EO | 7 |
| POST /api/interview/resume/parse | EO | 5 |
| POST /api/interview/repo/analyze | EO | 5 |
| POST /api/interview/polish | EO | 4 |
| POST /api/code/problems/{id}/run | EO | 5 |
| GET /api/interview/roles | EQ | 3 |
| GET /api/interview/roles/{key}/sections | EQ | 3 |
| GET /api/interview/{id}/messages | EQ | 3 |
| GET /api/interview/{id}/evaluation | EQ | 4 |
| GET /api/interview/history | EQ | 4 |
| GET /api/code/problems | EQ | 4 |
| GET /api/code/problems/{id} | EQ | 4 |
| GET /api/code/submissions | EQ | 3 |
| GET /api/code/submissions/{id} | EQ | 4 |
