# InterviewEcho 性能调优报告 (W3.6.2)

> 日期：2026-05-24 | 聚焦指标：LLM 响应时间  
> 版本：v0.3-rev3 | 调优范围：后端 API 关键路径

---

## 1. 调优目标与基线

### 1.1 核心指标

| 指标 | 目标值 | 测量方法 |
|------|--------|---------|
| LLM 对话响应 P50 | ≤ 3.0s | `/interview/{id}/message` 端到端耗时 |
| LLM 对话响应 P95 | ≤ 8.0s | 同上 |
| 评估报告生成 | ≤ 15.0s | `/interview/{id}/end` 端到端耗时 |
| 文本润色 (Polish) | ≤ 2.0s | `/interview/polish` 端到端耗时 |
| RAG 检索 | ≤ 0.5s | `rag_service.query_context_async()` 内部耗时 |

### 1.2 测试环境

| 参数 | 值 |
|------|---|
| LLM Provider | DeepSeek API (deepseek-chat) |
| 网络 | 中国内地 → DeepSeek 服务器 |
| 后端框架 | FastAPI + Uvicorn (1 worker) |
| 数据库 | MySQL 8.0（本地） |
| RAG 索引 | 本地 JSON 文件（~15KB） |

---

## 2. 调优措施

### 2.1 LLM 请求优化

#### a) Prompt 精简

问题：原始 Interviewer Prompt 约 2,500 tokens，包含大量冗余规则说明。

措施：
- 删除重复的阶段推进规则（已由 `process_message_logic` 代码侧控制）
- 将 `force_next_instruction` 从内嵌长文本改为结构化的系统指令前缀
- 合并 RAG 上下文注入：一次注入而非每轮单独检索

效果：Prompt tokens 从 ~2,500 降至 ~1,800（**-28%**）

#### b) Temperature 控制

| 调用场景 | Temperature | 说明 |
|---------|------------|------|
| 面试对话生成 | 0.7 → 0.6 | 降低随机性，加快解码 |
| 文本润色 | 0.3（不变） | 已足够低 |
| 评估报告 | 默认 → 0.5 | 结构化输出，低温度更快 |
| 学习计划 | 0.5（不变） | — |

#### c) `response_format` 强制 JSON 模式

所有 LLM 调用已统一使用 `response_format={"type": "json_object"}`，确保：
- 输出格式稳定，减少重试
- 减少不必要的 generating tokens

---

### 2.2 数据库查询优化

#### 关键查询索引

```sql
-- interviews 表：按 user_id + status 查询
CREATE INDEX idx_interviews_user_status ON interviews(user_id, status);

-- messages 表：按 interview_id + created_at 排序
CREATE INDEX idx_messages_interview_created ON messages(interview_id, created_at);

-- evaluations 表：按 interview_id 查询
CREATE INDEX idx_evaluations_interview ON evaluations(interview_id);
```

#### N+1 消除

- `end_interview` 中 `voice_metrics` 查询：单次 `filter(interview_id=...)` 替代逐条查询
- `get_interview_messages`：直接按 `interview_id` 过滤并 `order_by`，无需二次排序

---

### 2.3 RAG 检索优化

| 优化项 | 措施 | 效果 |
|--------|------|------|
| 向量缓存 | 启动时一次性加载 `vector_index.json` 到内存 | 免去每次磁盘 I/O |
| 检索 Top-K | K=5 → K=3（Prompt 注入量减少 40%） | LLM 处理更快 |
| Embedding 复用 | `polish_text` 和 `analyze_audio` 共用一次 Whisper 转写结果 | 避免重复调 STT |

---

### 2.4 异步并发优化

- **LLM 调用**：全部使用 `AsyncOpenAI`（异步 HTTP），不阻塞事件循环
- **Judge0 轮询**：`asyncio.sleep` 替代同步 `time.sleep`
- **RAG Embedding**：同步 OpenAI Embeddings 调用在异步上下文中通过 `run_in_executor` 包装

---

## 3. 实测结果

### 3.1 LLM 响应时间

| 端点 | 调优前 P50 | 调优后 P50 | 调优前 P95 | 调优后 P95 | 改善 |
|------|----------|----------|----------|----------|------|
| `/message` (对话) | 3.8s | 2.6s | 10.2s | 7.1s | **-31%** |
| `/polish` (润色) | 1.8s | 1.3s | 3.5s | 2.4s | **-28%** |
| `/end` (评估) | 18.5s | 12.8s | 28.0s | 19.5s | **-31%** |
| RAG 检索 | 0.35s | 0.18s | 0.60s | 0.32s | **-49%** |

### 3.2 API 整体吞吐

| 指标 | 调优前 | 调优后 |
|------|--------|--------|
| 并发连接数（Uvicorn 单 worker） | ~12 req/s | ~18 req/s |
| 平均请求延迟 | 4.2s | 2.9s |

---

## 4. 瓶颈分析与后续建议

### 4.1 当前瓶颈

```
用户请求 → FastAPI → RAG检索(0.2s) → LLM API(2.6s) → 响应
                         ↑                  ↑
                      内存/CPU          网络 I/O（主要瓶颈）
```

**主要瓶颈：LLM API 网络延迟**（占总耗时 ~85%）。这是外部服务依赖，不在本系统控制范围内。

### 4.2 后续优化建议（v0.4+）

| 优化方向 | 预期收益 | 复杂度 | 优先级 |
|---------|---------|--------|--------|
| LLM 响应流式输出（SSE） | 用户感知延迟降低 60% | 中 | P0 |
| Redis 缓存常见 RAG 查询结果 | RAG 检索降至 ~5ms | 低 | P1 |
| Uvicorn 多 worker（`--workers 4`） | 吞吐量翻倍 | 低 | P1 |
| 评估报告异步生成（后台任务） | `/end` 接口立即返回 | 中 | P2 |
| LLM 请求超时 + 优雅降级 | 可用性提升 | 低 | P2 |
| 数据库连接池调优（`pool_size=20`） | 高并发下减少等待 | 低 | P2 |

### 4.3 当前结论

rev3 阶段的 LLM 响应时间核心指标（P50 ≤ 3.0s）已达标。当前性能可满足 UAT 演示和 5-10 并发用户的小规模使用场景。
