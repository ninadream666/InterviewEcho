# 算法/大模型工程师必备核心技术栈 (Core Tech Stack)

在Python及AI大语言模型开发序列中，以下为主流通识要求的生态分布与使用切入点：

## 一、 语言底层与重型数据引擎 (Python Eco)
* **CPython解释器运行原理** (深入 GC, GIL 多线程限制与多进程并发方案)。
* **Numpy底层阵列内存管控** (Ndarray, strides 步幅切割及无缝拷贝拉伸Broadcasting)。
* **Pandas / PyArrow / Polars** 数据清理重塑与极速转换分析矩阵。

## 二、 机器学习理论架构池 (ML Structure)
* **XGBoost & LightGBM** - 表格结构数据场景中的高效集成树模型，具备缺失值处理和异常值鲁棒性。
* **Sklearn 全栈数据处理** - 对特征进行 Scaler, Encoder 及 SMOTE 插值采样处理。
* **推荐召回粗精排算法** - DeepFM，多门控混合专家网络（MMOE）的联合打分落地。

## 三、 大语言模型网络架构及演进 (LLM Foundations)
* **Transformer 架构原理掌握** (Self-Attention 及缩放因子防止梯度消失，Pre-RMSNorm 稳定深层梯度)。
* **Decoder-Only 架构霸权** (GPT, LLaMA, Qwen系列主推原理)。
* **长序列位置编码方案** (RoPE 旋转位置编码、ALiBi长度外推机制，解决长序列建模问题)。
* **Token分词化工程** (BPE, BBPE 跨语种的生词 OOV 降本策略)。

## 四、 大语言工程实战栈与显存极致压榨 (LLM Engineering)
* **Parameter-Efficient 轻量化微调** - LoRA (低秩瓶颈拆分训练), QLoRA(NF4精细降维装载), P-tuning 等降低全参计算红线的微调主流策略。
* **Rerank & Embedding(检索增强)** - 掌握 Faiss / Milvus 等向量数据库的检索机制，利用分块、重排序和混合检索策略缓解模型幻觉问题。
* **ZeRO （显存剥离通信）** - Microsoft DeepSpeed 体系下的分布式冗余优化机制，打破 OOM 界限。
* **vLLM 推理框架** - 运用 PagedAttention 实现 KV-Cache 分页管理，提升并发推理效率和显存利用率。
* **模型对齐与奖励网络** - 理解 SFT，并在对齐层面了解 DPO 等新一代代替 PPO 强化学习极简人类偏好对齐手段。
