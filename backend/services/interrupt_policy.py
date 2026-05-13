"""打断触发策略（W3.2.7 / FT2.2.2.3）

职责：
给定一条候选人的最新回答 + 当前题目上下文，判定是否应该让 AI 面试官主动打断
（提示候选人聚焦、拉回主题或结束当前话题），并返回要拼到 system prompt
`force_next_instruction` 中的指令片段。

被以下位置调用：
- routers/interview.py :: process_message_logic

设计原则：
1. 规则优先，零外部依赖（不调 LLM），保证零成本、零延迟、可单测。
2. 失败必须降级：评估异常时上游 try/except 兜底，绝不阻塞主流程。
3. 与对话流接口契约：只输出"挂到现有 force_next_instruction 上的字符串"，
   不直接改写对话状态，保持职责单一。
"""

from dataclasses import dataclass
from typing import List, Optional
import re

# ===== 可调阈值 =====
DURATION_TIMEOUT_SEC = 90.0          # 单次回答语音时长超过此值判定超时
OFF_TOPIC_MIN_LEN = 150              # 离题判定的最小文本长度（避免对极短回答误伤）
RAMBLING_MIN_LEN = 400               # 赘述判定的最小文本长度
RAMBLING_TECH_TERM_MIN = 1           # 赘述场景下技术词命中阈值

# 通用技术名词词典（用于离题/赘述命中判定）
# 不追求完备，覆盖三大岗位的高频词即可
_TECH_TERMS = {
    # 通用
    "算法", "数据结构", "复杂度", "时间复杂度", "空间复杂度", "缓存", "数据库", "事务",
    "并发", "线程", "进程", "锁", "死锁", "队列", "栈", "哈希", "树", "图", "排序",
    "递归", "动态规划", "贪心", "回溯", "网络", "TCP", "UDP", "HTTP", "HTTPS",
    "DNS", "API", "REST", "gRPC", "消息队列", "MQ", "kafka", "rabbitmq",
    # Java 后端
    "Java", "Spring", "SpringBoot", "Spring Boot", "MyBatis", "JVM", "GC", "类加载",
    "Bean", "AOP", "IOC", "Redis", "MySQL", "Tomcat", "Maven", "Gradle", "Dubbo",
    "微服务", "分布式", "Zookeeper", "Nacos", "Sentinel", "Seata",
    # Web 前端
    "Vue", "React", "Angular", "TypeScript", "JavaScript", "ES6", "Webpack", "Vite",
    "Babel", "ESLint", "Pinia", "Vuex", "Redux", "组件", "虚拟DOM", "Diff", "响应式",
    "Hooks", "服务端渲染", "SSR", "CSR", "性能优化", "懒加载", "事件循环", "EventLoop",
    "Promise", "async", "await", "闭包",
    # Python 算法
    "Python", "NumPy", "Pandas", "Sklearn", "PyTorch", "TensorFlow", "Keras",
    "机器学习", "深度学习", "神经网络", "CNN", "RNN", "LSTM", "Transformer", "BERT",
    "GPT", "Attention", "梯度", "反向传播", "过拟合", "正则化", "Dropout", "BatchNorm",
    "特征工程", "交叉验证", "AUC", "F1", "精确率", "召回率", "推荐系统", "embedding",
    "NLP", "CV", "目标检测", "YOLO", "ResNet",
}


@dataclass
class InterruptDecision:
    """打断判定结果。

    triggered: 是否触发打断
    trigger_type: "" | "timeout" | "off_topic" | "rambling"
    prompt_addition: 要拼到 system prompt force_next_instruction 上的指令文本；
                    triggered=False 时为空串
    """
    triggered: bool
    trigger_type: str
    prompt_addition: str


_TECH_TERM_PATTERN = re.compile(
    "|".join(re.escape(t) for t in sorted(_TECH_TERMS, key=len, reverse=True)),
    re.IGNORECASE,
)


def _count_tech_terms(text: str) -> int:
    if not text:
        return 0
    return len(_TECH_TERM_PATTERN.findall(text))


def _keyword_overlap(text: str, key_points: List[str]) -> int:
    """返回 user_text 命中 key_points 中关键词的条数（部分匹配即算命中）。"""
    if not text or not key_points:
        return 0
    text_lower = text.lower()
    hits = 0
    for kp in key_points:
        if not kp:
            continue
        kp_str = str(kp).strip().lower()
        if not kp_str:
            continue
        # 关键词可能是"Spring AOP 原理"这种短语，取其前 4 字符做粗匹配
        token = kp_str[:4] if len(kp_str) >= 4 else kp_str
        if token in text_lower:
            hits += 1
    return hits


def evaluate_interrupt(
    user_text: str,
    duration_sec: Optional[float],
    current_question: str,
    current_question_key_points: Optional[List[str]] = None,
) -> InterruptDecision:
    """评估是否应该让 AI 打断。

    判定优先级（高到低）：
    1. timeout：duration_sec 超过 DURATION_TIMEOUT_SEC
    2. off_topic：文本足够长 + 与 key_points 零重叠 + 技术词命中 ≤ 1
    3. rambling：文本极长 + 技术词命中极少
    其他情况：不打断
    """
    text = (user_text or "").strip()
    key_points = current_question_key_points or []

    # 规则 1：超时
    if duration_sec is not None and duration_sec > DURATION_TIMEOUT_SEC:
        return InterruptDecision(
            triggered=True,
            trigger_type="timeout",
            prompt_addition=(
                f"【系统指令：打断 - 超时】候选人本轮回答时长 {duration_sec:.1f} 秒，"
                f"已超过建议时长（{int(DURATION_TIMEOUT_SEC)} 秒）。请礼貌地打断，"
                "用一句话肯定候选人的表达欲，然后明确要求其聚焦在【当前问题的核心点】上，"
                "用 30-60 秒补充关键结论，避免继续展开。"
            ),
        )

    # 规则 2：离题
    if len(text) >= OFF_TOPIC_MIN_LEN:
        overlap = _keyword_overlap(text, key_points)
        tech_hits = _count_tech_terms(text)
        if overlap == 0 and tech_hits <= 1:
            return InterruptDecision(
                triggered=True,
                trigger_type="off_topic",
                prompt_addition=(
                    "【系统指令：打断 - 离题】候选人最新回答与当前题目核心要点没有交集，"
                    "且几乎没有覆盖到关键技术词。请礼貌地打断，"
                    f"重申当前问题（\"{current_question[:60]}\"），"
                    "并引导候选人围绕题目要点重新作答。"
                ),
            )

    # 规则 3：赘述
    if len(text) >= RAMBLING_MIN_LEN:
        tech_hits = _count_tech_terms(text)
        if tech_hits < RAMBLING_TECH_TERM_MIN:
            return InterruptDecision(
                triggered=True,
                trigger_type="rambling",
                prompt_addition=(
                    "【系统指令：打断 - 赘述】候选人回答篇幅较长但技术含量较低，"
                    "信息密度不足。请礼貌地打断，"
                    "请候选人用 2-3 句话总结技术结论，再展开关键技术细节。"
                ),
            )

    return InterruptDecision(triggered=False, trigger_type="", prompt_addition="")
