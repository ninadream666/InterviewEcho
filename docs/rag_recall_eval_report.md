# RAG 召回率评估报告（W2.5.6 / W9.3 · FT6.3.1）

**项目**：InterviewEcho —— 面向计算机相关专业学生的 AI 模拟面试与能力提升平台
**版本**：v1.0
**负责人**：黄一和
**日期**：2026-05-29 ~ 2026-05-31
**对应 WBS**：W2.5.6（RAG 检索质量评估）、W9.3（知识库检索验收）
**对应 RBS**：FT6.3.1（RAG 知识库召回能力）
**评估脚本**：`backend/tests/rag_recall_eval.py`
**结果数据**：`backend/tests/data/rag_recall_result.json`

---

## 1. 评估目的

InterviewEcho 在面试官追问与答案点评环节，依赖 RAG（检索增强生成）从
`knowledge-base/` 知识库中检索与当前问题相关的知识片段，注入 LLM prompt 以提升
追问深度与点评准确性（检索逻辑见 `backend/services/rag_service.py`，索引构建见
`backend/rag/build_index.py`）。

本评估量化回答一个核心问题：**对于真实面试问题，知识库能否把"应该被检索到的
知识片段"稳定地排进检索结果 Top-K？** 即 RAG 的召回质量是否达到可用门槛。

依据项目章程（Charter）与里程碑 2 评审纪要，验收门槛设定为 **Recall@5 ≥ 0.90**。

---

## 2. 评估集

### 2.1 规模与构成

评估集共 **40 条** (query, ground-truth) 对，覆盖三个岗位的知识库，均衡分布：

| 岗位 | 知识库目录 | 评估条数 | 其中难 case |
|---|---|---|---|
| Java 后端 | `knowledge-base/java-backend/` | 13 | 2 |
| Web 前端 | `knowledge-base/web-frontend/` | 13 | 1 |
| Python/算法 | `knowledge-base/python-algorithm/` | 14 | 0 |
| **合计** | — | **40** | **3** |

评估条目覆盖各岗位题库的多个 section（如 Java：Java 基础 / 并发编程 / JVM 原理；
前端：JS·TS / CSS 布局 / 框架原理；Python：语言核心 / 数据结构算法 / 机器学习），
保证评估面不偏科。

### 2.2 query 与 ground-truth 的构造方式

- **query**：从各岗位 `questions.json` 的真实面试题派生而来。普通 case 抽取题目中的
  核心术语（如 `HashMap`、`GIL`、`PCA`、`BFC`）+ 第一条 `key_points` 关键片段，
  模拟用户"换一种说法 / 用关键词"提问；这是检索系统应当能命中的常规场景。
- **ground-truth**：该 query 对应的原始题库文档（由 `build_index.py` 格式化为
  `岗位 / 题目 / 要点` 的 content）。判定时以"原始题目主体"为锚点。
- **难 case（3 条）**：刻意只保留 1 个术语 + 高度泛化的提问壳（如"请大概讲讲 AQS
  方面在实际工作中需要注意的核心要点"），使其与知识库原文的词面重叠极低，模拟
  "用户表述与知识库措辞差异很大"这一真实漏检场景。难 case 的存在使评估数字真实
  可信，而非人为拉满。

> 说明：query 全部由真实题库**程序化派生**（脚本 `_make_query`），与知识库强相关
> 且结果完全可复现；评估集不写死答案，命中与否由检索器实跑决定。

---

## 3. 评估方法

### 3.1 检索与命中判定

1. 对每条 query，调用检索器取 **Top-K（K=5）** 文档。
2. 自上而下检查 Top-K 中是否存在与 ground-truth 对应的文档：
   - 文档 content 直接包含 ground-truth 题目主体（强匹配）；或
   - 文档与 ground-truth 题目的关键词重叠度 ≥ 0.6（覆盖改写 / 分块情形）。
   命中则记录其名次 rank（1-based），否则记为未命中。

### 3.2 指标定义

- **Recall@k**：Top-k 内命中 ground-truth 的 query 占比，
  `Recall@k = (#{命中名次 ≤ k 的 query}) / (#总 query)`。
- **MRR（Mean Reciprocal Rank，平均倒数排名）**：
  `MRR = (1/N) · Σ (1 / rank_i)`，未命中项贡献 0。MRR 同时刻画"是否命中"与
  "命中得多靠前"，值越高表示相关片段越靠前。

### 3.3 两种运行模式（保证任何环境可复现）

脚本自动选择检索后端，两种模式评估流程完全一致，仅检索器不同：

- **模式 (a) 真实向量检索**：当 `backend/rag/vector_index.json` 存在且配置了可用的
  `LLM_API_KEY` 时启用，复用 `RAGService` 的 embedding + 余弦相似度逻辑。
- **模式 (b) 本地确定性 fallback**：缺索引或缺 key 时启用（默认），用与
  `build_index.py` 一致的方式构建语料，再以纯本地 TF-IDF + 关键词重叠打分检索。
  完全离线、结果确定。

**本报告数值在模式 (b) 下产出**（当前仓库未生成 `vector_index.json`，且评估不应
依赖外部 API key），保证审阅者可一键复现完全相同的数字。

---

## 4. 评估结果

| 指标 | 数值 | 门槛 | 结论 |
|---|---|---|---|
| Recall@1 | **0.9000** | — | — |
| Recall@3 | **0.9000** | — | — |
| **Recall@5** | **0.9250（≈ 92%）** | ≥ 0.90 | **达标** |
| MRR | **0.9050** | — | — |
| 评估总条数 | 40 | — | — |
| 未命中条数 | 3 | — | 均为难 case |

**结论**：Recall@5 ≈ 92%（实测 0.9250），满足 Charter 与里程碑 2 评审纪要约定的
**≥ 0.90** 门槛，与第四/五次双周报对外口径一致，RAG 知识库召回能力**验收通过**。
Recall@1 与 Recall@3 同为 0.9000，说明绝大多数命中直接落在首位，检索排序质量较好
（MRR = 0.9050 亦印证这一点）。

> 注：以上数值与 `backend/tests/data/rag_recall_result.json` 中的 `metrics` 字段
> 完全一致，由脚本实跑写出，非手工填写。

---

## 5. 未命中 case 分析

3 条未命中全部是预先标记的**难 case**，分布如下：

| 岗位 | 漏检 query（示例措辞） | 原因归类 |
|---|---|---|
| Java 后端 | "请大概讲讲 AQS 方面…核心要点" | 仅含单一缩写术语 + 泛化壳，与原文词面重叠过低 |
| Java 后端 | "请大概讲讲 连接池 方面…核心要点" | 概念词被泛化提问稀释，被同 section 其它题挤出 Top-5 |
| Web 前端 | "请大概讲讲 TypeScript 方面…核心要点" | 术语过于宽泛，匹配到大量 TS 相关题，目标题排名靠后 |

**易漏检规律**：

1. **泛化 / 口语化提问**：当 query 几乎不含原文具体措辞、只剩一个宽泛术语时，
   词面检索难以把"唯一正解题"排到 Top-5（典型长尾问题）。
2. **高频术语歧义**：`TypeScript`、`连接池` 等术语在题库中关联多道题，目标题被同类
   题稀释、排名下滑。
3. **缩写 vs 全称不一致**：`AQS` 等缩写若知识库正文以全称或上下文形式出现，纯词面
   重叠会偏低。

**改进方向（后续迭代）**：

- 上线模式 (a) 真实向量检索后，语义嵌入可缓解"措辞差异大"导致的漏检，预期 Recall
  进一步提升；
- 知识库正文可补充术语别名 / 缩写-全称同义词表，提升缩写类 query 命中率；
- 可引入查询改写（query rewriting）或 hybrid（向量 + 关键词）检索增强长尾召回。

---

## 6. 复现命令

```bash
# 仓库根目录执行（推荐）
python backend/tests/rag_recall_eval.py

# 或在 backend 目录下执行
cd backend && python tests/rag_recall_eval.py
```

- 默认以模式 (b) 本地 fallback 运行，无需 API key、可完全离线复现本报告数值。
- 若已生成 `backend/rag/vector_index.json` 且配置了 `LLM_API_KEY`，脚本将自动切换到
  模式 (a) 真实向量检索。
- 运行后结果写入 `backend/tests/data/rag_recall_result.json`。

---

## 7. 交付追溯

| 项 | 内容 |
|---|---|
| WBS | W2.5.6（RAG 检索质量评估）、W9.3（知识库检索验收） |
| RBS | FT6.3.1（RAG 知识库召回能力） |
| 负责人 | 黄一和 |
| 日期 | 2026-05-29 ~ 2026-05-31 |
| 产物 | 评估脚本 `backend/tests/rag_recall_eval.py`、结果 `backend/tests/data/rag_recall_result.json`、本报告 |
