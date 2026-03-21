import json
import os

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../knowledge-base/python-algorithm/questions')
knowledge_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../knowledge-base/python-algorithm/knowledge')
os.makedirs(base_dir, exist_ok=True)
os.makedirs(knowledge_dir, exist_ok=True)

# ==========================================
# 1. AI算法-python篇
# ==========================================
python_qs = [
    ("Python的GIL是什么？有什么优缺点？在处理哪种任务时是瓶颈，如何绕过？", 
     "GIL（全局解释器锁）是CPython解释器用来保证线程安全的机制，导致同一进程内多线程无法同时利用多核CPU。优点：单线程执行极快，C扩展（扩展模块）编写容易。缺点：限制了多核并发并行。它是CPU密集型任务的瓶颈。绕过方法：使用多进程（multiprocessing）、使用C原生扩展释放GIL、或在I/O密集型任务中使用多线程/协程。", 
     ["CPython特有", "CPU密集型受限", "多进程与C扩展替代"], "AI算法-python篇", "medium"),
    ("Python中列表推导式(List Comprehension)为什么比普通的for循环快？", 
     "列表推导式在底层由C语言直接执行，且在创建列表时直接在底层分配内存，避免了for循环每次调用.append()方法时的环境检查和函数调用开销。但在涉及非常庞大数据时，应使用生成器表达式()以节省内存。", 
     ["底层C执行", "避免append函数调用开销", "内存与生成器的权衡"], "AI算法-python篇", "easy"),
    ("介绍一下Python的垃圾回收机制（GC）？", 
     "Python GC以“引用计数”为主，辅以“标记-清除”和“分代回收”。引用计数：对象被引用计数+1，撤销引用-1，为0释放（高效但无法解决循环引用）。标记-清除：用于解决双向链表等循环引用，从GC Root遍历，标记活动对象，清除不可达对象。分代回收：基于空间换时间，把对象分三代，越久未被回收的对象放入高代，降低扫描频率。", 
     ["引用计数", "标记-清除解决循环引用", "分代回收集优化性能"], "AI算法-python篇", "hard"),
    ("迭代器(Iterator)和生成器(Generator)有什么区别？", 
     "迭代器是实现了__iter__()和__next__()魔法方法的对象，能用内置的next()访问。生成器是一类特殊的迭代器，通过yield关键字返回，无需手动实现类方法。它们都支持惰性计算，不会一次性把数据加载到内存，非常适合AI中的海量数据（如大规模Dataset加载）。", 
     ["__iter__与__next__", "yield惰性求值", "海量数据加载省内存"], "AI算法-python篇", "medium"),
    ("描述Python中的装饰器的原理及其在AI工程中的常见应用？", 
     "装饰器本质上是一个闭包函数，可以在不修改原函数代码的前提下，拦截原函数的调用并扩展其功能。AI工程常见应用：1. 耗时统计（记录模型Forward耗时）；2. PyTorch中的@torch.no_grad()用于关闭梯度图计算；3. 内存显存监控；4. 重试机制（当API调用失败时重试）。", 
     ["闭包原理", "不改变原函数签名", "耗时与无梯度计算等场景"], "AI算法-python篇", "medium"),
    ("什么是Numpy中的广播机制(Broadcasting)？它的底层原理是什么？", 
     "广播是指Numpy在对不同形状的数组进行数值计算时，自动将较小数组映射拉伸为一个与较大数组形状兼容的数组机制。规则：从尾部维度对比，如果维度相等或其中一个为1，则可以广播。底层并没有实际复制内存数据，而是通过内部strides（步幅）的调整使其在访问时表现出扩展后的形状，极大节省内存和提速。", 
     ["后缘维度匹配", "某维度为1", "strides零内存拷贝拉伸"], "AI算法-python篇", "hard")
]

# ==========================================
# 2. AI算法-算法面经篇 (经典ML/DL)
# ==========================================
ml_dl_qs = [
    ("随机森林(Random Forest)和XGBoost的核心区别是什么？", 
     "1. 集成策略：RF使用Bagging并行构建多棵独立树；XGBoost使用Boosting串行构建，新树拟合上一棵树的残差。2. 偏差-方差权衡：RF主要通过特征和样本的随机抽样降低模型的方差；XGBoost通过残差迭代降低偏差。3. 损失函数与导数：XGBoost对目标函数进行二阶泰勒展开，利用一阶和二阶导数信息寻优，支持自定义损失函数。", 
     ["Bagging降低方差", "Boosting残差迭代降偏差", "二阶泰勒展开使用Hessian"], "AI算法-算法面经篇", "hard"),
    ("SVM(支持向量机)为什么需要核函数？常见的核函数有哪些？", 
     "当数据在低维特征空间线性不可分时，SVM通过升维将数据映射到高维空间寻找超平面。直接计算高维内积计算量爆炸，核函数的巧妙在于能够在低维空间计算出等效于高维空间的内积，即“核技巧(Kernel Trick)”。常见：线性核、多项式核、RBF径向基函数（高斯核，是最常用的，可映射到无限维）。", 
     ["解决线性不可分", "核技巧替代高维内积降极算量", "RBF高斯核函数"], "AI算法-算法面经篇", "medium"),
    ("逻辑回归(LR)为什么要使用交叉熵而不用MSE作为损失函数？", 
     "MSE在LR配合Sigmoid函数时，其损失曲面是非凸的，极易陷入局部最优；其次，在预测严重错误时（如预测值为0，真实为1），Sigmoid处于饱和区，其导数极小会导致梯度的消失（参数更新停滞）。交叉熵的对数求导恰好能抵消掉Sigmoid的导数，使得误差越大学习更新越快。", 
     ["非凸函数多极小值", "抵消Sigmoid饱和梯度", "学习率维持饱满"], "AI算法-算法面经篇", "hard"),
    ("请详细解释下各种优化器(SGD, Momentum, AdaGrad, Adam)的演进逻辑？", 
     "1. SGD：依赖当前Batch梯度，容易在峡谷震荡。2. Momentum：引入一阶矩(动量)，记录历史梯度平滑更新方向，加速冲出鞍点。3. AdaGrad：引入二阶矩(历史梯度平方和)做分母，自适应降低频繁更新特征的学习率，但后期学习率近乎0；4. RMSProp：改成指数加权移动平均，解决学习率归零；5. Adam：结合Momentum(一阶矩)和RMSProp(二阶矩)，并加上偏差修正，是目前默认基准优化器。", 
     ["动量一阶矩平滑", "自适应学习率二阶矩", "结合体Adam加偏差修正"], "AI算法-算法面经篇", "hard"),
    ("如何解决神经网络中的梯度消失和梯度爆炸问题？", 
     "原因：在深层网络中连乘导致数值指数级衰减或放大。解决梯度消失：1. 改变激活函数(用ReLU替换Sigmoid/Tanh)；2. Batch Normalization规范化输出；3. 引入残差连接(ResNet的Skip Connection)提供短路梯度流。解决梯度爆炸：1. 梯度裁剪(Gradient Clipping)强制截断；2. 好的权重初始化(Xavier/Kaiming)；3. 正则化权重惩罚。", 
     ["ReLU解决饱和区", "BatchNorm强制分布", "ResNet残差连接直通"], "AI算法-算法面经篇", "medium"),
    ("L1正则化与L2正则化的根本区别是什么？为什么L1会产生稀疏解？", 
     "L1正则化是在损失函数后加参数绝对值求和，L2是参数平方和。区别：L1倾向于产生稀疏解（权重矩阵很多特征权重直接变为0），自带特征选择功能；L2更倾向于让各参数均衡地变小，能防止过拟合但不稀疏。原因：在Loss等高线与正则项约束函数相交时，由于L1是一个菱形，相交点更易落在坐标轴顶点上，从而导致某维度为0。", 
     ["L1菱形等高线", "特征选择与稀疏解", "L2圆形衰减惩罚"], "AI算法-算法面经篇", "hard")
]

# ==========================================
# 3. AI算法-大模型基础面
# ==========================================
llm_basic_qs = [
    ("详细阐述Transformer中Self-Attention机制的数学计算步骤。除以sqrt(d_k)的作用是什么？", 
     "输入X与权重Wq, Wk, Wv相乘得到Q, K, V。分数=Softmax( (Q内积K的转置) / sqrt(d_k) )。计算结果再乘V。除以缩放因子sqrt(d_k)的原因：如果不除，当维度d_k很大时，两个独立分布的随机变量内积结果的方差会变得极大(为d_k)，大方差会导致Softmax进入两极分化的饱和区，使得梯度接近0引发梯度消失。", 
     ["QKV投影", "方差缩放", "防Softmax饱和梯度消失"], "AI算法-大模型基础面", "hard"),
    ("Decoder-only(GPT系) 与 Encoder-only(BERT系)、Encoder-Decoder(T5) 的架构选择有何不同？为什么现在LLM几乎都是Decoder-only？", 
     "Encoder(BERT)双向自注意力，适合判别和特征提取(NLU)；Decoder(GPT)采用Masked掩码自注意力(只能看前面的Token)，适合生成任务(NLG)。Encoder-Decoder(T5)适合Seq2Seq翻译等。主流选择Decoder-only原因：1. 无上下文泄露(通过自回归实现严格时序生成)；2. 具有极强的Few-shot和Zero-shot的“涌现能力”（In-context Learning）；3. KV Cache等推理加速手段对其更友好。", 
     ["掩码机制防止未来信息泄漏", "统一自回归生成范式", "涌现能力表现更好"], "AI算法-大模型基础面", "medium"),
    ("大模型常用的激活函数是什么？相比ReLU好在哪里？（例如SwiGLU）", 
     "LLM（如LLaMA）目前普遍使用SwiGLU（Swish + Gated Linear Unit）。相比传统的ReLU（丢弃全部负值产生死神经元），Swish/GeLU在0附近存在平滑的非单调过渡区域，既能阻挡大量负信号，又能保留少许负梯度防止神经元“彻底死亡”；而GLU通过门控机制（类似乘法开关）增强了特征筛选能力。综合下来网络表达能力更强，收敛更快。", 
     ["门控线性单元GLU", "非单调平滑保护负梯度", "避免死神经元(Dead ReLU)"], "AI算法-大模型基础面", "hard"),
    ("Transformer的LayerNorm为何发展出了 Pre-Norm 和 Post-Norm 甚至 RMSNorm？区别是什么？", 
     "原始Transformer使用 Post-Norm（残差相加之后再Norm），这会使得随着网络变深梯度的方差累积，深层较难起作用甚至导致训练不稳定（发散）。现在常用 Pre-Norm（进入Attention或FFN前先Norm，残差旁路不经过Norm），这让梯度可以直接反传到底层，训练极度稳定。目前LLaMA进一步简化使用 RMSNorm（Root Mean Square Norm），直接去掉了均值计算，只计算均方根，在保证精度的前提下极大地提升了计算速度。", 
     ["Post-Norm容易梯度爆炸", "Pre-Norm深层训练稳定", "RMSNorm移除均值计算提速"], "AI算法-大模型基础面", "hard"),
    ("详细讲解LLaMA中使用的旋转位置编码（RoPE）的核心思想是什么？", 
     "与用正余弦相加的绝对位置编码不同，RoPE通过将Query和Key映射到复平面空间，并根据其所处绝对位置左乘一个旋转矩阵。由于复数乘法的性质，QK内积运算展开后自然会带出两者之间的相对位置偏移量（m - n）。这既囊括了绝对位置，又在内积层面体现了相对距离，且具有极好的长度外推性（Length Extrapolation）。", 
     ["绝对位置的旋转矩阵", "内积产生相对距离", "卓越的外推扩展性"], "AI算法-大模型基础面", "hard"),
    ("什么是词表分词 (Tokenization) 中的 BPE 算法？", 
     "BPE（Byte Pair Encoding）是一种数据压缩技术，广泛用于LLM分词。先将词表拆分为全量基础字符，然后统计语料中相邻字符对的出现频率，将频率最高的子词对合并成一个新Token并加入词表，循环直到达到设定的词表大小（vocab size）。这种设计能有效地解决OOV（未登录词/生僻词）问题，又不会像纯字符切分模型那样推长序列长度。", 
     ["词频合并", "解决OOV", "介于Word与Char之间"], "AI算法-大模型基础面", "medium")
]

# ==========================================
# 4. AI算法-大模型进阶面
# ==========================================
llm_advanced_qs = [
    ("微调全参数与PEFT（Parameter-Efficient Fine-Tuning）技术有什么优劣？详细说下LoRA的原理。", 
     "全参微调（Full SFT）吃尽显存（1个参数占4字节，加上优化器矩占很大空间）。PEFT通过冻结基座只注入极少参数来极度降低成本。LoRA假设模型更新存在内在低秩子空间（Low-Rank）。原理是将冻结的原权重矩阵W旁路挂载两个小矩阵A和B（A负责降维，B负责升维），前向传播为W_x+BA_x，只训练A和B。训练完还可以合并(Merge)进W内保证推理无延迟。", 
     ["低秩本质假设", "旁路增量训练与原权重冻结", "可并入不增推理延迟"], "AI算法-大模型进阶面", "hard"),
    ("在分布式训练大模型时，DeepSpeed ZeRO阶段（1/2/3）是怎么划分显存并优化的？", 
     "单卡装不下百亿参数时需切片。DeepSpeed基于数据并行分发（DP）的冗余分析，提出了Zero技术。ZeRO-1：把Adam状态（一阶二阶矩参数，最吃显存）切分进不同的GPU；ZeRO-2：在此基础上切分反向传播算出的梯度（Gradient）；ZeRO-3：在1和2基础上，把模型原参数本身全部切分成碎片，训练时如果有算子需要参数通过All-Gather向其他卡借完后直接丢弃。是用通讯带宽换存容量的极致发挥。", 
     ["优化器状态切割", "梯度切割", "参数切割及All-Gather借取计算"], "AI算法-大模型进阶面", "hard"),
    ("讲讲KV Cache机制？以及MQA和GQA是如何在这个基础上进一步省显存加速推理的？", 
     "生成式模型自回归生成下一个字时，前置Token的K和V是不变的，每次重算巨耗算力，因此产生KV Cache存入显存以空间换时间。但太长上下文会撑爆显存。优化：MQA(Multi-Query Attention)让所有的Query头共享同一个K和一个V头，极大降低KV参数量；而GQA(Grouped-Query，LLaMA2/3使用)是将Query头分组，每组内共享一个K和V，不仅降显存还保持了非常接近原版MHA的准确性。", 
     ["自回归保留键值以空间换时间", "MQA单K单V", "GQA分组权衡(效果与性能居中)"], "AI算法-大模型进阶面", "hard"),
    ("SFT、RM、PPO与DPO分别在大模型的预训练之后的RLHF对齐阶段扮演什么角色？", 
     "这是人类偏好对齐链。1. SFT(监督微调)：教模型“回答该长什么样”，喂优质问答样本。 2. RM(奖励模型)：让人工对微调后的多条输出打分排序，训练一个当评委的模型。3. PPO(近端策略优化)：强化学习，用RM给生成模型打分作为奖罚刺激模型更新参数（链路太长极易崩溃）。 4. DPO(直接偏好优化)：近年主流，用数学等价推导直接把强化学习奖励转化为二分类交叉熵交叉验证损失，免去了训练RM和PPO复杂训练，单阶段极简对齐。", 
     ["SFT行为克隆", "被抛弃的PPO复杂强化打分", "DPO数学闭环跨越RM模型直接微调分布"], "AI算法-大模型进阶面", "hard"),
    ("RAG（检索增强生成）系统的常见架构是什么？它如何缓解幻觉？为什么有了无限上下文长文本(Long Context)还是需要RAG？", 
     "架构：召回切片-文本向量化(Embedding)-存入Faiss/Milvus等向量库。用户咨询时，系统Embedding化用户的Query找Top-K外挂知识拼接到Prompt喂给大模型。缓解幻觉：强制要求模型基于检索文档作答，做到知识可溯源更新。\n不可替代：长文本长且贵，速度慢，每次提问带着一整本书去算Attention（O(n^2)）；而且有Lost in the middle（长文本中间遗忘）效应；RAG依然是目前性价比、时效性和精细过滤首选。", 
     ["外挂溯源抗幻觉", "规避每次O(N^2)极限长序列推流开销", "长文本存在中间遗忘效应(needle in haystack)"], "AI算法-大模型进阶面", "medium")
]

#合并所有Technical问题
tech_data = []
for arr in [python_qs, ml_dl_qs, llm_basic_qs, llm_advanced_qs]:
    for q, a, kp, sec, diff in arr:
        tech_data.append({
            "id": f"algo_tech_{len(tech_data)}", "job_type": "python-algorithm", 
            "category": "technical", "question": q, "reference_answer": a, 
            "key_points": kp, "difficulty": diff, "section": sec
        })


# ==========================================
# 5. 算法实战场景题 (Scenarios)
# ==========================================
scenarios_data = [
    {
        "id": "algo_scenario_1", "job_type": "python-algorithm", "category": "scenario",
        "question": "如果你部署的单机小显存（例如24G）线上服务，遭遇了并发调用被打爆导致OOM(Out Of Memory)的问题，你该如何排查改造优化？",
        "reference_answer": "1. 抛弃HuggingFace原生的Transformers调用，采用vLLM或者TGI部署框架。 2. 分析原因：并发激增会导致每个序列在显存中单独开辟KV Cache，很快达到上限。引入vLLM核心的 PagedAttention 机制，将显存分页按需分配给KV，彻底消除显存碎片。并配合 Continuous Batching (动态流式组Batch)来让处理完的请求立刻退出，插上新请求。 3. 最后防线使用 8-bit 或 4-bit(GPTQ/AWQ) 权重量化。",
        "key_points": ["接入vLLM等推理引擎", "PagedAttention显存池化无碎片", "连续批处理(Continuous Batching)挤满算力"],
        "difficulty": "hard", "section": "推理提流与显存优化"
    },
    {
        "id": "algo_scenario_2", "job_type": "python-algorithm", "category": "scenario",
        "question": "公司自研的RAG模型老是有“大海捞针”捞不到的情况（准确率太差），且回答经常拼接断裂，你会从哪几个思路系统性做调优工作？",
        "reference_answer": "1.【切分层(Chunking)】采用语义切分而不是机械数字切块，加大 Overlap 覆盖上下文，引入基于父子文档结构的检索和 HyDE (假设性回答扩写检索词)。 2.【向量模型层(Embedding)】通用Embedding无法理解垂直业务（如内部项目代号等）。使用 Contrastive Loss 的微调策略去微调专属领域 BGE 模型打通局限。 3.【重排打分层(Reranker)】向量距离靠前的未必符合业务逻辑需求，用交叉编码器(Cross-Encoder)对提取得Top 10做二次过滤打分。 4.【大模型侧】Prompt内卡死约束纪律：“如果文档不涵盖该信息，必须回答不知道，严禁编造”。",
        "key_points": ["双阶段检索(粗排召回+精排打分层)", "HyDE与父子文档拼接", "专属词汇采用领域语料微调Embedding模型"],
        "difficulty": "hard", "section": "RAG系统全链路调优"
    },
    {
        "id": "algo_scenario_3", "job_type": "python-algorithm", "category": "scenario",
        "question": "在训练大模型期间Loss发散突然变成NaN，排查分析链路是怎么样的？",
        "reference_answer": "1. 数据问题：检查最近加载几批的 Data / Label 是否混入极端污染（空串导致除0，类别标记越界等）。 2. 梯度问题：反向计算过激产生梯度爆炸，打印 `grad_norm` 验证，解决办法是加梯度裁剪 `torch.nn.utils.clip_grad_norm_`。 3. 混合精度溢出问题：如果开启了 FP16 混合训练（AMP），经常由于浮点动态范围太小溢出导致 NaN。解决方法是使用 GradScaler 动态放缩，或高端显卡上直接切换到动态范围更大的 BF16 格式数据类型。",
        "key_points": ["梯度裁剪规避绝对的过大导数", "半精度FP16天生上限窄易爆导致溢出", "使用BF16替换"],
        "difficulty": "medium", "section": "训练奔溃故障排查"
    },
    {
        "id": "algo_scenario_4", "job_type": "python-algorithm", "category": "scenario",
        "question": "针对风控或者交易检测场景中出现黑产刷单往往在全量样本中的比例只有 1%，样本极度不平衡。你在建模（传统机器学习或深度学习时）打算怎么应对？",
        "reference_answer": "绝不看Accuracy，因为全盲猜正类都有99%准确率，需全部看Recall及F1。解决方法：1. 数据分布：针对罕见黑负样应用 SMOTE 等算法人工创造拟合插值或者下采样健康样本平衡底盘。2. 损失函数开刀：放弃普通交叉熵并引入带权重的交叉熵，或者加入 Focal Loss：强行将模型识别极度难判别的长尾孤本的损失权重拉高，以惩罚其对少数样本的偏见。3. 评估指标只抓 PR(查准查全)曲线及 ROC-AUC 面积。",
        "key_points": ["采样切入口(下采样/SMOTE过采样)", "Focal Loss处理难分长尾样本", "全面换掉Accuracy改监控AUC与F1"],
        "difficulty": "medium", "section": "数据非平衡长尾处理"
    }
]

# ==========================================
# 6. 项目深度挖掘设计 (Projects)
# ==========================================
projects_data = [
    {
        "id": "algo_prj_1", "job_type": "python-algorithm", "category": "project",
        "question": "详细展开说说你简历中做过的这个领域微调（SFT）模型的全周期经历？",
        "reference_answer": "【宏观系统把控与管线流复盘】 第一步，基座把脉：尝试各开源基座进行验证（Qwen, ChatGLM, LLaMA）评估其对系统语言或垂类天生支持能力。 第二步，【数据飞轮（重点吃分项）】：使用启发式算法或 LLM 即为大号打分器清洗过滤掉同质化问答对。使用 Self-Instruct 去扩增几十种多指令模板增强变异多样性结构产生三万条指令对。 第三步，训练卡点：因算力资源束限（如仅几块V100/A100）应用了分布式框架（DeepSpeed2）并加载 LoRA/QLoRA 高效算子参数。 第四步，指标交付：剥离预留盲测集利用 Rouge / BLEU 自动化打分与人工标注定责验收模型效果的超越指标。",
        "key_points": ["自动化数据清洗去重去重防毒化", "通过DeepSpeed+LoRA节约部署训练硬开销", "明确的对比前后的客观验收度量(Rouge/人工胜率)"],
        "difficulty": "hard", "section": "预训练 / 微调管线实战"
    },
    {
        "id": "algo_prj_2", "job_type": "python-algorithm", "category": "project",
        "question": "如果利用推荐系统、NLP或机器学习去对某项旧有的业务进行提效或赋能，它的技术债和业务收益如何量化？",
        "reference_answer": "不要单纯罗列堆了什么算法名字，而是要阐述系统如何嵌入业务。例如项目中采用了基于 XGBoost 加 LightGBM 进行信贷风险卡控 / 或双塔模型作短视频重排。强调痛点：旧业务人工审核慢且客诉高。处理难点在于将结构化表格数据和大量非结构化文本混合抽取特征输入。收益量化：设计A/B实验，新规则放开10%流量灰度，最后给出如客诉率下降了30%、拦截精准度(AUC指标)提升15个基底等实权数据支撑自己的技术栈价值。",
        "key_points": ["突出混合入特征融合工程", "落地强推A/B测试进行收益评估", "算法和基线版差异指标对齐业务线"],
        "difficulty": "medium", "section": "多模态多模型业务结合实战"
    }
]

# ==========================================
# 7. 软技能行为题 (Behavioral)
# ==========================================
behavioral_data = [
    {
        "id": "algo_bhv_1", "job_type": "python-algorithm", "category": "behavioral",
        "question": "你们辛辛苦苦做的数据清洗并且SFT后的大模型，被业务方反映线上盲测比开源版效果还差（甚至犯智障错误灾难性遗忘）。你要怎么面对并且修复？",
        "reference_answer": "1.【情绪处理规避推诿】不能直接怪别人或者怪开源基座，立刻承认线上情况并在本地做紧急回归隔离跑库。 2.【精准溯源(抓坏案Bad Cases)】：提取业务方指出的全部发抽风案例，将其输入原始未SFT模型看是否变差。如果变差通常是数据集严重同质化并且过拟合Epoch了导致的灾难性遗忘(Catastrophic Forgetting)。 3.【修补应对】引入泛用指令混合进训练数据对齐；排查训练集中是否有脏数据(标签错乱毒化)；如果资源紧张优先打上一个 Prompt防腐墙 作为短期遮挡补救。",
        "key_points": ["冷静拉取坏案例进行盲测比较复现", "承认微调产生过拟合及灾难遗忘问题", "使用优质基准数据和多角度模板掺入对冲毒化风险"],
        "difficulty": "medium", "section": "跨部门模型扯皮定责化解"
    },
    {
        "id": "algo_bhv_2", "job_type": "python-algorithm", "category": "behavioral",
        "question": "产品经理（或领导）被市场大模型热潮洗脑，强制要求你们在一个毫秒级高并发、且只有普通服务器算力的线上检索流中使用百亿参数LLM去取代原来毫秒级的XGBoost判别模型，作为算法你是如何交涉的？",
        "reference_answer": "当场说不干或者硬上必定爆雷。策略是：以风险把控者身份提供“降解替代或阶段方案”。 1. 直接抛出实验压测数据：给PM看一张T4硬跑大模型的请求流时耗表格（如>2秒时延），证明其直接接入会直接导致目前服务全盘雪崩宕机违约。 2. 提供折中方案（如知识蒸馏与大带小）：可以下线用大模型针对庞大的无标注日志数据跑打标跑分析，形成高质量伪标签扩充数据规模后再重新拉去喂给那个XGBoost和LightGBM树模型实现“吸收大模型灵智”。 采用这种形式，既沾了边宣传也能实现毫无新增时耗风险的需求兼顾。",
        "key_points": ["用压力测试报告(TPS)击穿盲目崇拜幻想阻断灾难", "提出知识蒸馏或离线打标签大带小的安全思路", "不拒绝只兜售合理替代案"],
        "difficulty": "hard", "section": "伪需求降维拦截与向上处理"
    }
]

# ---- 写入操作 ----
def write_json(filename, data):
    with open(os.path.join(base_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

write_json('algorithm_technical.json', tech_data)
write_json('scenarios.json', scenarios_data)
write_json('projects.json', projects_data)
write_json('behavioral.json', behavioral_data)

# ==========================================
# 8. 扩展的技能评定 Markdown
# ==========================================
rubrics_content = """# Interview Evaluation Rubrics (Python算法工程师 / 大模型架构师)

本文档旨在统一规范基于 **Python基建、机器学习基础理论、大模型原理及应用实操** 等各个切面的考核深度与统一标尺。

## 一、 考核大盘拆分权重
整套定级打分采用以下 5个矩阵切块作为加权依据：
1. **Python 工程护城河 (15%)**
2. **机器学习与理论算法 (20%)**
3. **LLM与深度学习基建层 (25%)**
4. **大语言工程提效与RAG架构落地 (25%)**
5. **软素养、抗压与技术判断视野 (15%)**

---

## 二、 详细评分标准矩阵

### 2.1 Python底层与工程健壮度 (15%)
作为AI的地基，主要考察是否能应对高负荷部署时的数据流及防内存溢出：
- **专家 (4-5分)**：熟练剖析 CPython 中全局解释器锁 GIL 对于多核环境下的限制；针对OOM可以提出分代垃圾回收、通过追踪 `weakref` 或弱引用消除强环；Numpy 中通过修改 strids (步幅)零拷贝原理了如指掌。
- **合格 (2.5-3.5分)**：可用装饰器构建无感耗时埋点闭包栈；熟悉生成器应对GB级数据集不爆内存的运用；明白深浅拷贝机制导致的联动引用Bug。
- **不合格 (<2分)**：不知道迭代器与生成器的区别，认为Python开启内置的多线程就能处理海量并行的密集运算，基础数据结构时空复杂度乱判。

### 2.2 基础机器学习与演变能力 (20%)
算法基本功排查，考察应对小算力和结构化表单时候的数据挖掘与模型搭建：
- **专家 (4-5分)**：能深度剖析集成树如 Random Forest 和 XGBoost 的（Bagging 和 Boosting）底层数理差别（偏方差控制差异）；能手推交叉熵在反向更新时为什么完美越过了Sigmoid函数的激活死区（梯度消失）；深刻把控 Adam 如何平衡动量（一阶矩）与动态学习率（二阶矩）。
- **合格 (2.5-3.5分)**：可以用 L1菱形等高线正则化截断特征做稀疏解、用 L2平滑权重防过拟合；懂在反欺诈等畸形长尾分布中用 Focal loss 和重排 SMOTE 重采，不再盲目只刷准确率改信 AUC 。
- **不合格 (<2分)**：只懂`import sklearn`掉包跑分类；不能表述出交叉熵跟 MSE(均方误差) 的使用区别，无法讲清楚超参数之间的权衡。

### 2.3 LLM与深度构架体系 (25%)
不只是“调用 API 者”，要求彻底进入基座黑盒里面探察参数原理：
- **专家 (4-5分)**：可以复述并推导 Transformer 中 Attention 是如何用根号归一化压制方差保护梯度的；精通目前 Decoder-only 长序列生成；能透彻推演 RoPE(旋转位置编码) 的相对外推机制复平面运算。
- **合格 (2.5-3.5分)**：讲得出残差连接解决梯度消失的过程；知道 Pre-Norm 和 Post-Norm 以及 RMSNorm 在层迭代深度的防止发散保护；
- **不合格 (<2分)**：对于 QKV 是什么、怎么点积乘的一无所知；对词表切割（BPE / 分词）未登录词规避完全无概念。

### 2.4 大模型算力极限与部署工程 (25%)
在大规模微调耗时费钱的今日，考核成本降本控制和落地部署：
- **专家 (4-5分)**：熟透 DeepSpeed 的 ZeRO 切片分布（从切状态到完全去参数化的 3大阶段）机制；深刻熟知 KV-Cache 产生机制并利用 MQA \ GQA（组查询注意力解决空间问题）；vLLM中的 PagedAttention 的池页技术能全流打通。
- **合格 (2.5-3.5分)**：熟悉 LoRA (低秩低矩阵)等 PEFT 高参留效机制的微调原理并具备实践经历；深度调试过全套 RAG （结合 Chunk 修正，BGE微调，精重排机制）的系统去解决直接大模型幻觉瞎编乱造问题。
- **不合格 (<2分)**：只会在平台点训练。在碰到单张显存24G显卡不够部署的情况下，不能提出模型量化或任何减少显存支出的降维技术手段。

### 2.5 软素养、灾难回阻及向上管理 (15%)
评估候选人遭遇炼丹崩溃退货与不合理逼迫时的防爆破与替代能力：
- **专家 (4-5分)**：在面临微调出现大模型智力崩溃倒退时，能科学回滚到基座进行坏案例剥离并定位灾难性遗忘(Catastrophic Forgetting)进行对齐修复；面临“必须上AI”死命要求时可提出离线大带小的蒸馏降维兼容策略规避高风险并发。
- **合格 (2.5-3.5分)**：面对训练 Loss 跳出 `NaN`，懂得立刻抓监控数据（截断爆炸和混合浮点窄溢）。能够拉平技术要求避免和PM陷入盲目争执。
- **不合格 (<2分)**：对于业务方的效果质疑以模型玄学为由逃避推责定性为“没办法”。强行吞并要求搞挂线上系统。
"""

with open(os.path.join(knowledge_dir, 'interview_evaluation_rubrics.md'), 'w', encoding='utf-8') as f:
    f.write(rubrics_content)

tech_stack_content = """# 算法/大模型工程师必备核心技术栈 (Core Tech Stack)

在Python及AI大语言模型开发序列中，以下为主流通识要求的生态分布与使用切入点：

## 一、 语言底层与重型数据引擎 (Python Eco)
* **CPython解释器运行原理** (深入 GC, GIL 并行陷路与跨进程并发突破)。
* **Numpy底层阵列内存管控** (Ndarray, strids 步幅切割及无缝拷贝拉伸Broadcasting)。
* **Pandas / PyArrow / Polars** 数据清理重塑与极速转换分析矩阵。

## 二、 机器学习理论架构池 (ML Structure)
* **XGBoost & LightGBM** - 表格结构数据与反欺诈推荐场景中无视缺值、极值免疫的最强算力集成树结构。
* **Sklearn 全栈数据处理** - 对特征进行 Scaler, Encoder 及 SMOTE 插值采样处理。
* **推荐召回粗精排算法** - DeepFM，多门控混合专家网络（MMOE）的联合打分落地。

## 三、 大语言模型网络架构及演进 (LLM Foundations)
* **Transformer 架构系原生掌握** (Self-Attention 及缩放压制梯度逃逸，前置 RMSNorm 对深层梯度的强平滑)。
* **Decoder-Only 架构霸权** (GPT, LLaMA, Qwen系列主推原理)。
* **长视窗抗劫持对抗编码** (RoPE 旋转外推、ALiBi长度惩罚机制，解决长序列迷失)。
* **Token分词化工程** (BPE, BBPE 跨语种的生词 OOV 降本策略)。

## 四、 大语言工程实战栈与显存极致压榨 (LLM Engineering)
* **Parameter-Efficient 轻量化微调** - LoRA (低秩瓶颈拆分训练), QLoRA(NF4精细降维装载), P-tuning 等降低全参计算红线的微调主流策略。
* **Rerank & Embedding(检索增强)** - 掌握 Faiss / Milvus 等重度向量库的检索机制，利用 Chunk, 重排和 Hybrid 策略缓解模型海市蜃楼（幻觉）重伤。
* **ZeRO （显存剥离通信）** - Microsoft DeepSpeed 体系下的分布式冗余优化机制，打破 OOM 界限。
* **vLLM 推理框架集群** - 深刻介入运用 PagedAttention 按块投喂 KV-Cache 防并发碎块的极限承载调度。
* **模型对齐与奖励网络** - 理解 SFT，并在对齐层面了解 DPO 等新一代代替 PPO 强化学习极简人类偏好对齐手段。
"""

with open(os.path.join(knowledge_dir, 'core_tech_stack.md'), 'w', encoding='utf-8') as f:
    f.write(tech_stack_content)
