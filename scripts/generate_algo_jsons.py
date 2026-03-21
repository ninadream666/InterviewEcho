import json
import os

base_dir = os.path.join(os.path.dirname(__file__), '../knowledge-base/python-algorithm/questions')
os.makedirs(base_dir, exist_ok=True)

knowledge_dir = os.path.join(os.path.dirname(__file__), '../knowledge-base/python-algorithm/knowledge')
os.makedirs(knowledge_dir, exist_ok=True)

technical = []

# --- AI算法-python篇 ---
python_basics = [
    ("Python中的GIL（全局解释器锁）是什么？它对多线程有什么影响？", "GIL是CPython解释器为了保证线程安全，在执行Python字节码时获取的互斥锁。它导致同一时刻只有一个线程能执行Python代码，因此Python的多线程在CPU密集型任务中无法实现真正的并行，提升极其有限甚至由于切换开销更慢。解决：使用多进程(multiprocessing)或C拓展，也可以在I/O密集型任务中使用多线程或协程(asyncio)。", ["CPython互斥锁", "CPU密集型局限", "多进程与协程替代"], "Python基础与进阶", "medium"),
    ("Python中的深拷贝和浅拷贝有什么区别？如何实现？", "浅拷贝(copy.copy)仅仅复制对象的容器本身，内部的子对象仍然是原对象的引用。深拷贝(copy.deepcopy)会递归地拷贝对象内部包含的所有子对象，生成完全独立的副本。若遇到循环引用，deepcopy中维护了一个备忘录字典(memo)专门用来防环。", ["引用嵌套拷贝", "deepcopy递归", "memo备忘录防环"], "Python基础与进阶", "easy"),
    ("Python垃圾回收(GC)机制是怎样的？", "Python主要以【引用计数】为主，当对象的引用计数降为0时立刻回收内存。为解决循环引用问题，补充了【标记-清除】（针对容器对象追踪可达性进行清除）和【分代回收】（将对象分为0,1,2代，新对象在0代，存活越久代数越高，触发检测的频率越低，以换取性能）。", ["引用计数为主", "标记清除解环", "分代回收提升性能"], "Python基础与进阶", "hard"),
    ("什么是装饰器？请手写一个记录函数执行时间的装饰器（考虑带参数的函数）。", "装饰器本质是一个返回函数的高阶函数，可以在不修改原函数代码的前提下为其增加额外功能。手写：\n```python\nimport time\nfrom functools import wraps\ndef timer(func):\n    @wraps(func)\n    def wrapper(*args, **kwargs):\n        start = time.time()\n        res = func(*args, **kwargs)\n        print(f'{func.__name__}耗时: {time.time()-start}')\n        return res\n    return wrapper\n```", ["高阶函数", "*args **kwargs兼容", "@wraps保留元数据"], "Python基础与进阶", "medium")
]

# --- AI算法-算法面经篇 ---
ml_dl_basics = [
    ("在机器学习中，Random Forest和XGBoost有什么区别？", "1. 架构：RF是Bagging思想（多棵决策树并行且多数投票），XGB是Boosting思想（残差迭代串行树）。2. 抽样：RF抽样样本和特征，XGB更关注针对预测错的样本提权。3. 剪枝策略：RF树独立互不影响；XGB采用结构风险最小化带正则项（L1/L2）的损失函数，预剪枝与后剪枝结合。4. 处理缺失值：XGB内置稀疏感知算法。5. 方差与偏差：RF主要降方差，XGB主要降偏差。", ["Bagging并行 vs Boosting串行", "正则化防过拟合", "偏差与方差的侧重"], "经典机器学习理论", "hard"),
    ("深度学习中，为什么会发生梯度消失和梯度爆炸？如何解决？", "原因：在反向传播中使用链式法则，连续乘以小于1（如Sigmoid的导数最大才0.25）或者大于1的梯度会导致梯度连乘后指数级缩小（消失）或放大（爆炸）。解决手段：1. 改用ReLU/LeakyReLU代替Sigmoid。2. 使用Batch Normalization（批归一化）稳定数值分布。3. 引入残差连接（ResNet中的Skip Connection）直接跨层流转梯度。4. 梯度裁剪（Gradient Clipping，针对爆炸）。5. 好的权重初始化（如Xavier / Kaiming）。", ["链式法则连乘", "ReLU激活函数", "BN层与残差连接"], "深度学习基础", "hard"),
    ("谈谈交叉熵损失函数（Cross Entropy）的数学本质？为什么分类不用MSE而用交叉熵？", "交叉熵衡量了真实概率分布与预测概率分布的差异。对于分类，若使用MSE与Sigmoid结合，求导时会包含Sigmoid的导数，当预测极其错误（Sigmoid值靠近0或1时）导数几乎为0，导致梯度消失更新停滞；而交叉熵求导能抵消掉Sigmoid的求导项，使得误差越大学习越快，完美契合分类任务的梯度下降特性。", ["衡量分布差异", "避免Sigmoid饱和区求导消失", "错误越大学习越快"], "深度学习基础", "hard"),
    ("优化器SGD、Momentum和Adam的核心区别是什么？", "SGD：每次只利用当前batch的梯度更新，易陷入局部极小或鞍点，且在不同维度梯度差异大时会产生震荡。Momentum：引入动量（指数加权移动平均），记忆过往梯度方向，加速一致方向并平抑震荡。Adam：结合了Momentum(一阶矩，梯度平均)和RMSprop(二阶矩，自适应学习率)优点，不同参数有不同的自适应学习率，并增加偏差修正，是目前深度学习默认首选优化器。", ["动量平抑震荡", "Adam自适应学习率", "一二阶矩估计"], "深度学习基础", "medium")
]

# --- AI算法-大模型基础面 ---
llm_basics = [
    ("详细推导一次Transformer中Self-Attention（自注意力）的计算过程及其时间复杂度？", "输入矩阵X先乘以三组权重矩阵W_q, W_k, W_v得到Q, K, V。然后计算Attention Score = Softmax( Q·K^T / sqrt(d_k) )，最后将其与V相乘得到输出的混合表示：Attention(Q,K,V) = Softmax(QK^T/√d_k)V。时间复杂度主要是QK^T的矩阵乘法，对于序列长度为L，维度为d的模型，复杂度是O(L^2 · d)。因此在长文本上L平方爆棚是瓶颈。", ["Q,K,V特征投影", "除以根号d防softmax梯度消失", "O(L^2)的时间复杂度瓶颈"], "大模型基础架构", "hard"),
    ("为什么在Attention计算时需要除以 $\sqrt{d_{k}}$（根号d_k）？", "如果维度d_k很大，Q和K的点积结果由于是独立正态分布相加，方差也会变得极大（为d_k）。进入Softmax之后，大方差会导致得分出现两极分化（趋近于0或1），使得大部分区域Softmax的导数极其微小（梯度消失）。除以 $\sqrt{d_{k}}$ 缩放，能将方差拉回1，使得Softmax后的数值在梯度饱满区域，保证模型平稳收敛。", ["避免点积方差过大", "防止Softmax进入极值饱和区", "保障稳定梯度反向传播"], "大模型基础架构", "hard"),
    ("Encoder-only (如BERT)、Decoder-only (如GPT)、Encoder-Decoder (如T5) 架构区别与适用场景？", "1. Encoder-only：采用双向注意力能够看到全局上下文，适合NLU（自然语言理解）任务如分类、文本匹配。2. Decoder-only：采用带掩码(Masked)的自注意力，只能看到当前和以前的Token，适合NLG（自然语言生成），在零样本或少样本的自回归生成上呈现强大的涌现能力，是当前LLM（GPT/LLaMA）的主流。3. Encoder-Decoder：编码双向，解码单向，适合Seq2Seq任务如翻译、摘要生成。", ["双向上下文理解(BERT)", "单向掩码自回归生成(GPT)", "翻译/摘要转换型(T5)"], "大模型基础架构", "medium"),
    ("RoPE (旋转位置编码) 的原理与优势是什么？相比绝对位置编码有什么好处？", "相对位置编码RoPE通过复数域上的旋转变换（左乘旋转矩阵），将绝对位置的索引编码到了Query和Key的表示中。在进行内积计算Attention得分时，结果天然包含了两者的相对距离信息。优势：1. 推理时对长度外推性（Length Extrapolation）好，能处理超出预训练长度的语料；2. 保留了相对距离的概念而不是生硬的绝对索引。", ["复数坐标旋转矩阵", "内积计算相对距离", "优秀的长度外推性"], "大模型基础架构", "hard")
]

# --- AI算法-大模型进阶面 ---
llm_advanced = [
    ("微调大模型时，LoRA和QLoRA的核心思想是什么？", "LoRA认为预训练大模型的权重更新过程中存在低秩（Low-Rank）特性。不在原参数上直接更新，而是冻结原模型(W)，在侧边增加两个低秩矩阵A(降维)和B(升维)，前向传播为 W_x + BA_x。大大减少了可训练参数量（仅万分之一到百分之一）。QLoRA在LoRA基础上，引入了4-bit NormalFloat量化技术(NF4)来加载冷冻的大模型原权重，并利用Paged Optimizers解决显存峰值，使得在单张消费级显卡(如24G)即可微调65B模型成为可能。", ["Low-Rank低秩矩阵旁路", "大大降低显存与训练参数", "4-bit NF4量化(QLoRA)"], "大模型微调与对齐", "hard"),
    ("什么是KV Cache？MQA和GQA相比MHA分别做了哪些优化？", "在自回归生成时，每次生成新Token都会重新计算所有历史Token的K和V，非常浪费。KV Cache机制就是将历史Token的K、V存到显存空间中复用，降低计算复杂度，却增加了显存负担。为了拯救显存：\\n1. MHA(Multi-Head)：每个Query头都对应自己的K头和V头。\\n2. MQA(Multi-Query)：所有Query头共享唯一一个K头和V头，极大降低KV Cache显存。\\n3. GQA(Grouped-Query)：折中方法(如LLaMA2/3使用)，将Query头分组，组内共享同一个K组和V组，在保持准确率接近MHA的情况下，获得了接近MQA的推理速度和省显存优势。", ["避免重复计算历史向量", "极度吃显存(显存墙)", "MHA/MQA/GQA群组分组权衡"], "大模型算力与推理优化", "hard"),
    ("在分布式训练中，Zero Redundancy Optimizer（ZeRO 1/2/3）是如何降低显存占用的？", "显存大头不仅是模型参数，更多在优化器状态(Adam的矩)和梯度上。Zero是DeepSpeed提出的切片方案：\\n- ZeRO-1：切分【优化器状态】，各个GPU只保存和更新它负责切片的那部分权重对应的优化器状态。\\n- ZeRO-2：在1基础上切分【梯度】，各个GPU只保存自己负责那部分的梯度。\\n- ZeRO-3：在1、2基础上切分【模型参数】，各个GPU只保存参数切片，在前向/反向传播时，如果需要用到别人的参数，再利用All-Gather通信广播过来拿到后即丢弃（用通信换显存极限）。", ["显存占用三大元凶", "状态、梯度、参数渐进式切分", "All-Gather通信换显存空间"], "大模型训练工程", "hard"),
    ("RAG（检索增强生成）系统相较于大模型直接微调(SFT)有什么优势与劣势？", "RAG将大模型外接向量数据库，回答前先检索关联的知识拼接入Prompt上下文让大模型总结。其优势：1. 数据热更新极快，删改向量即可，无需重新炼丹(SFT)；2. 基于外挂文献可溯源，有效降低幻觉(Hallucination)；3. 低硬件成本，不需要庞大算力集群。\n劣势：1. 受限于检索质量和Retriever的能力(Top-k的召回率)；2. 会消耗大量Token额度，甚至触发模型上下文最大限制长度。对于深度推理、风格模仿或者模型本不存在的内在逻辑认知，微调(SFT)则是刚需。", ["热更新零炼丹成本", "数据溯源降低幻觉", "严重依赖Embedding检索召回率"], "RAG与Agent", "medium")
]

for arr in [python_basics, ml_dl_basics, llm_basics, llm_advanced]:
    for q, a, p, sec, diff in arr:
        technical.append({
            "id": f"algo_tech_{len(technical)}", 
            "job_type": "python-algorithm", 
            "category": "technical", 
            "question": q, 
            "reference_answer": a, 
            "key_points": p, 
            "difficulty": diff, 
            "section": sec
        })

# --- scenarios ---
scenarios = [
    {
        "id": "algo_scn_1",
        "job_type": "python-algorithm",
        "category": "scenario",
        "question": "公司有业务需要在极其有限的推力算力（例如1张3090 / 24G显存）下部署本地大模型跑推理，你会怎样设计落地方案？",
        "reference_answer": "1.【模型择型】放弃70B以上的模型，选择基座例如 Qwen2-7B 或 Llama3-8B。\n2.【量化部署】使用 GPTQ 或 AWQ(如 vLLM/llama.cpp 部署框架)推4-bit或8-bit量化版本，将显存直接从 14G 砍到 6-8G。\n3.【推理引擎优化】采用 vLLM 或 TGI 等推理框架，利用 PagedAttention 进行显存碎片化池化管理抵抗并发打满。利用 FlashAttention 加速显存重采样过程节省算力。\n4. 如果上下文非常长，探索引入滑动窗口注意力或降级 KV Cache 位数。",
        "key_points": ["小身板基座择型", "模型权重量化技术(4/8-bit)", "vLLM的PagedAttention显存池化", "FlashAttention读写优化"],
        "difficulty": "hard",
        "section": "推理提效场景"
    },
    {
        "id": "algo_scn_2",
        "job_type": "python-algorithm",
        "category": "scenario",
        "question": "我们目前自研的一套RAG系统，“大模型回答不准、存在部分幻觉或者乱编”，作为算法工程师你从哪几个维度排查并进行优化？",
        "reference_answer": "RAG系统痛点不一定在生成（G）而在检索（R）。\n1. 【排查切块策略(Chunking)】：文本被切碎可能导致语义割裂。尝试扩大Chunk size与覆盖重叠(Overlap)；或使用父子树/假设性问题(HyDE)反向检索策略。\n2. 【排查Embedding模型】：通用Embedding对垂直赛道词不支持。利用正负样本通过 Contrastive Loss 微调专属领域（BGE等）的向量模型。\n3. 【引入Rerank（重排阶段）】：初筛召回 Top-100后往往噪声太大，增加一个如 BGE-reranker 的交叉编码器给检索结果做精细打分卡点过滤到 Top-5 给 LLM。\n4. 【大模型Prompt对齐】：在Prompt设定严格纪律：“仅根据以下检索到的上下文回答问题，如果你在文中找不到答案，请明确回答'我不知道'”。",
        "key_points": ["Chunk切割颗粒度与重叠(Overlap)", "Embedding词向量微调", "两阶段检索(双流底表+Reranker交叉排序)", "拒绝回答指令对齐"],
        "difficulty": "hard",
        "section": "大模型与RAG落地陷阱"
    },
    {
        "id": "algo_scn_3",
        "job_type": "python-algorithm",
        "category": "scenario",
        "question": "如果训练过程中监控板显示Loss突然变成NaN了，第一时间的排查链路是什么？",
        "reference_answer": "【数据污染】：最常见的是文本数据或者标签里面混入了全0或负数在求log（交叉熵部分），也有可能是脏数据。打印数据预处理后边界分布检查是否含极大极小异常值。\n【梯度爆炸】：查看模型反向传播时某梯度太大计算直接溢出。解决是增加梯度裁剪(Gradient Clipping=1.0)。\n【学习率过大或者混合精度溢出】：如果用了FP16(半精度)训模型，极其容易因为表达范围太窄超出上限而变Nan。尝试打开混合自动精度(AMP / GradScaler动态缩放梯度)或者更换支持更大范围的BF16数据类型。",
        "key_points": ["排查数据脏数据污染(如除零错误)", "增加梯度裁剪(Clipping)", "抛弃纯FP16, 采用FP16+GradScaler或改用BF16防溢出"],
        "difficulty": "hard",
        "section": "炼丹工程故障排查"
    }
]

# --- projects ---
projects = [
    {
        "id": "algo_prj_1",
        "job_type": "python-algorithm",
        "category": "project",
        "question": "介绍一个你从零到一主导微调(SFT)部署过垂类大模型的经历（例如医疗/金融/代码大模型等）。数据怎么造的，流程是什么？",
        "reference_answer": "【考察数据壁垒与流程构建经历】\n1. 基座选型：基于中文支持较好的如 Qwen/Baichuan / GLM。 \n2. 数据清洗Pipeline（核心）：收集到的原始QA非常死板甚至带偏见。通过质量清洗（启发式去重、基于另一个大模型做清洗打分或者重写Self-Instruct扩充指令多样性，构造出 5 万条高质量 {instruction, input, output} 数据格式格式。\n3. 训练成本压降：基于 4 张 A100，放弃全参微调(Full-Parameter FT)，接入 DeepSpeed ZeRO-2 结合 LoRA 进行低秩微调。\n4. 评估(Eval)：抽取保留了一波测试集不进入训练，计算困惑度与Rouge，以及业务专家打分(盲测胜率)，效果相较于原模型提升了 X%。",
        "key_points": ["数据飞轮构造与SFT集提纯", "参数高效微调PEFT(LoRA/Ptuning应用)", "量化明确指标验证模型胜率"],
        "difficulty": "hard",
        "section": "垂类模型微调(SFT)"
    },
    {
        "id": "algo_prj_2",
        "job_type": "python-algorithm",
        "category": "project",
        "question": "在项目推进中，如何解决“样本极端不平衡”（如欺诈检测正负样本 1:99 的情况）导致模型泛化极差的问题？",
        "reference_answer": "这个问题不仅出现在图像视觉或者风控，也在LLM强化学习(RLHF)里频发。\n1. 数据层面：在输入期采用下采样(丢弃部分多数类)和过采样(复制少数类)或者SMOTE算法合成特征。\n2. 权重/损失层面探索：修改损失函数惩罚机制。将常规的交叉熵替换为 Focal Loss 或带权重的交叉熵，强行对把正类（稀少类）给判成负样本的行为进行高额惩罚（提升 Recall）。\n3. 评价指标转换：绝不看单纯的准确率(Accuracy)，全面改用查准率(Precision)、召回率(Recall)、F1-Score与ROC-AUC面积曲线作为验收唯一参考值。",
        "key_points": ["数据采样工程(SMOTE等)", "损失层切入口：Focal Loss与加权交叉熵", "抛弃Accuracy，使用Precision/Recall/F1/AUC"],
        "difficulty": "medium",
        "section": "模型调优与特征工程"
    }
]

# --- behavioral ---
behavioral = [
    {
        "id": "algo_bhv_1",
        "job_type": "python-algorithm",
        "category": "behavioral",
        "question": "你辛辛苦苦清洗了几个星期的数据，但是微调出来的模型，业务方试退后说完全没有效果，甚至相比基座倒退了。此时你会如何处理？",
        "reference_answer": "【展现排错逻辑和情绪稳定性】\n首先绝对不能陷入自证或者跟业务方争吵。先进行客观现象拆分：\n模型倒推灾难性遗忘通常原因有：1）指令集同质化严重或包含了错误引导标签导致。2）微调轮次(Epoch)过大导致过拟合。 \n解决步骤：拿到引发业务方不满的坏案例(Bad Cases)；用预训练基座(原始状态)和微调版并排对比分析；检查这些失败问题的垂类是否在我们的数据集中被“毒化”了；立刻建立一个小样本隔离集进行对齐调参，寻找新的拟合红线。",
        "key_points": ["避免情绪化对抗，回归数据表现", "承认可能是由于灾难性遗忘引发", "进行坏案例提取(Bad Cases Analysis)和双盲测试重修"],
        "difficulty": "medium",
        "section": "跨部门扯皮与信任修复"
    },
    {
        "id": "algo_bhv_2",
        "job_type": "python-algorithm",
        "category": "behavioral",
        "question": "业务系统要求极高实时性要求（低于100ms），组长说要用深度学习甚至大模型技术来包装当噱头，但你评估算力后认为算法耗时至少500ms以上不可能达标，如何向上管理？",
        "reference_answer": "核心在于不当反叛者，当风险管理者提供替代品。\n跟组长私下核实底层算力卡在哪一层。如果算力（无可用GPU）导致单纯过神经网路就500ms，必须客观提出预警：强上一套很深的模型并不能落地，只会带来宕机风险。并抛出阶梯替代方案：\n方案A：使用大模型离线把规则库跑出来，生成海量弱伪标签，在本地我们使用轻量级的纯Python版决策树(XGBoost)去跑预测，不仅能宣发含有大模型的知识增强，且10ms直接出结果。\n方案B：如果强上，需要协调公司资源部署专门的高配服务器。让决策权带着全量技术风险交还给领导定夺。",
        "key_points": ["明确物理限度风险不背锅", "知识蒸馏思想转移(大带小本地跑)", "向上提供可落地的变通方案供选择"],
        "difficulty": "medium",
        "section": "技术路线与业务拉扯"
    }
]

with open(os.path.join(base_dir, 'algorithm_technical.json'), 'w', encoding='utf-8') as f:
    json.dump(technical, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'scenarios.json'), 'w', encoding='utf-8') as f:
    json.dump(scenarios, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'projects.json'), 'w', encoding='utf-8') as f:
    json.dump(projects, f, ensure_ascii=False, indent=4)

with open(os.path.join(base_dir, 'behavioral.json'), 'w', encoding='utf-8') as f:
    json.dump(behavioral, f, ensure_ascii=False, indent=4)

rubrics_content = """# Interview Evaluation Rubrics (Python算法 / 大语言模型岗位)

本文档旨在统一规范大语言模型开发、传统机器学习及Python底层开发的考察维度与通过标准。

## 1. 核心评估模块与分值占比设定 
考察总评将分为五个主要能力群：
- **Python工程与语法穿透能力 (15%)**
- **机器学习与深度学习理论基础矩阵 (20%)**
- **大预言模型(LLM)内部架构与对齐体系 (30%)**
- **大模型工程算力(Zero/KV-Cache)推理与提效 (20%)**
- **场景落地软技能与系统抗压 (15%)**

---

## 2. 详细评分标准矩阵

### 2.1 Python工程与后端原理 (15%)
评估候选人是否精通Python底层原理，防止在大模型部署代码中引入慢I/O。
- **优秀 (4-5分)**：熟练剖析 CPython 的 GIL 原理；手写多版本无 BUG 迭代/装饰器；对垃圾回收（GC引用计数+分代+标记清除）和深浅级拷贝有底层内存池深度的理解。
- **合格 (2.5-3.5分)**：知道 GIL 对于 CPU / IO 密集型的差异，可用框架写过基础的并发请求功能，理解常用的高阶函数机制。
- **不合格 (<2分)**：频繁混用 `is` 和 `==`；说不清多线程到底行不行；无法手动消除防循环引用导致的 OOM。

### 2.2 机器理论与深度学习基础 (20%)
评估候选人对数据分布与旧算法降级处理深度的理解。
- **优秀 (4-5分)**：能详述 XGBoost 对比 Random Forest 对方差偏差的影响；可手推交叉熵针对分类时优于MSE（由于抵消饱和梯度区求导）的数学因果；深刻理解 Adam / SGD 优劣态。
- **合格 (2.5-3.5分)**：可用 ResNet 或 Batch Norm 回答如何减轻梯度积消失；能理清逻辑泛化如何使用正则化（L1/L2）防止过拟合。
- **不合格 (<2分)**：只懂掉包（`clf.fit()` / `clf.predict()`），对链式法则导数发散现象毫无概念；无法表述评估指标区别。

### 2.3 LLM 架构与对齐体系(大模型核心) (30%)
全栈拆解当前市面 LLM 底层，考察候选人是只会部署调用 API 还是通晓机制：
- **优秀 (4-5分)**：可黑板默写自注意力 `Self-Attention` 计算算式并且解释 `sqrt(d_k)` 的防激活消失缩放作用；熟知 RoPE(旋转位置编码)的极数复平面推演对长文本外推的作用；极其清楚 P-Tuning, LoRA 低维乘元与 QLoRA 等 PEFT 对齐策略的细节边界。
- **合格 (2.5-3.5分)**：回答出 Transformer 经典构架的区别( Encoder(Bert) / Decoder(GPT) / Causal LM )之间的关系。熟悉使用 LoRA 参数加载进行微调并防备灾难性偏见。
- **不合格 (<2分)**：不知道 QKV 到底谁乘谁；只用过 OpenAI API，认为大模型是个不能解释的魔法黑盒。

### 2.4 大模型算力与推理优化 (20%)
大模型实操环节，“跑得起”和“算得快”是最主要能力界限：
- **优秀 (4-5分)**：完整构建过 RAG (检索增强)系统全链路（包括切片策略，精重排 BGE-reranker，对比损失微调 Embedding）；精通分布式训练(深入到了 DeepSpeed ZeRO 1/2/3 对显存的暴力切割和 AllGather 机制)；深刻把控模型显存护城河(KV Cache机制以及MQA/GQA群组削减显存)。
- **合格 (2.5-3.5分)**：在有限显存借助量化库推演过本地大模型；理解为什么长度会拉爆模型；懂得针对纯净度不足用 RAG 去消解大模型的严重幻觉。
- **不合格 (<2分)**：回答不出模型训练 Loss NaN 是什么意思及其应对方法；面对单卡 24G 显存无法给出部署百亿大模型的量化或者 vLLM 对策建议。

### 2.5 软素养与情商对抗 (15%)
评估在模型炼崩或无法在工期交付时，如何拉平技术与产品部门预期认知。
- **优秀 (4-5分)**：使用高维度转化策略解决问题对冲。比如抛出非全量重构而是用大带小（逻辑蒸馏出小众传统XGB树）解决高时耗部署危机；并有沉稳的 Bad Case 开源归责能力。
- **合格 (2.5-3.5分)**：具备时间四象限 MVP 对齐技巧；对内卷拉扯时保持数据可视化作为依据不掺扯人身因素。
- **不合格 (<2分)**：过度反叛，盲拒产品插队，并容易推诿模型炼废均因为上游或者基座拉垮。

"""

with open(os.path.join(knowledge_dir, 'interview_evaluation_rubrics.md'), 'w', encoding='utf-8') as f:
    f.write(rubrics_content)
