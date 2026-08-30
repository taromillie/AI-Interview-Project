"""动态 RAG 四信号决策（设计 AD-03，工作包 A）。

将面试推进决策从 Agent prompt 中抽出为独立、可测试的规则模块。
四类信号：
1. low_information  —— 回答信息量低（过短/空洞），疑似不会或敷衍；
2. weak_recall      —— 检索召回弱：候选题目与最新回答命中度低，疑似偏题；
3. avoid_streak     —— 连续回避：多轮低信息/避而不答；
4. exhausted_topic  —— 当前话题已连续追问过深（probe_streak 超限），须换方向。

策略映射（优先级从高到低）：
exhausted_topic → switch_topic
weak_recall + low_information → remedy（拉回正题）
weak_recall     → remedy
avoid_streak≥2  → switch_topic（换更基础方向）
low_information → 依难度：easy→remedy / normal→probe / hard→deep_dive
has_project_hint→ project_probe
其余           → none（交给 Agent 自主判断）

难度加权（FR-I-04）：hard 提升 deep_dive 压测倾向，easy 提升 remedy 引导倾向。
"""
import re
from dataclasses import dataclass, field

# 判断"低信息回答"的最小有效长度（去除空白后）
LOW_INFO_MIN_LEN = 15
# 话题连续追问上限（超过视为已挖尽）
MAX_PROBE_STREAK = 2
# 触发"连续回避"的轮数
AVOID_STREAK_THRESHOLD = 2

# 回答中出现这些词视为"提到了项目经历"，倾向 project_probe
_PROJECT_HINT_KEYWORDS = (
    "项目", "实习", "系统", "模块", "负责", "实现", "开发", "搭建",
    "设计", "上线", "重构", "优化", "接口", "数据库", "部署", "性能",
)


@dataclass
class DecisionSignals:
    """四信号快照 + 供 prompt 注入的人类可读摘要。"""

    low_information: bool = False
    weak_recall: bool = False
    avoid_streak: int = 0
    exhausted_topic: bool = False
    has_project_hint: bool = False
    summary: str = ""

    @property
    def is_clear(self) -> bool:
        """是否有任何明确信号（否则策略交给 Agent 自主判断）。"""
        return any(
            (self.low_information, self.weak_recall, self.avoid_streak >= AVOID_STREAK_THRESHOLD,
             self.exhausted_topic, self.has_project_hint)
        )


def is_low_information(answer: str) -> bool:
    """判断回答是否信息量过低（去空白后过短）。"""
    compact = re.sub(r"\s+", "", answer or "").strip()
    return len(compact) < LOW_INFO_MIN_LEN


def has_project_hint(answer: str) -> bool:
    """判断回答是否提及项目/实战经历。"""
    text = answer or ""
    return any(kw in text for kw in _PROJECT_HINT_KEYWORDS)


def analyze_signals(
    latest_answer: str,
    *,
    hit_score: int = 0,
    probe_streak: int = 0,
    avoid_streak: int = 0,
    max_probe_streak: int = MAX_PROBE_STREAK,
    enable_recall: bool = True,
) -> DecisionSignals:
    """分析四类信号。

    Args:
        latest_answer: 候选人最新回答文本。
        hit_score: 候选题目与回答的关键词命中分（0 表示完全没有命中）。
        probe_streak: 当前话题已连续追问轮数。
        avoid_streak: 已连续低信息/回避的回答轮数。
        max_probe_streak: 话题追问上限。
        enable_recall: 是否启用"弱召回"信号（v1.2）。
            谈薪等模式候选来自内置问题库而非题库原子，无标签可命中，
            关闭后可避免"答非所问"误判导致的频繁 remedy 拉回。
    """
    text = latest_answer or ""
    low_info = is_low_information(text)
    # 弱召回：回答有实质内容，但候选题目命中为 0 —— 大概率答非所问/偏题
    weak_recall = enable_recall and (not low_info) and hit_score <= 0
    exhausted = probe_streak >= max_probe_streak
    project_hint = has_project_hint(text)

    summary_parts = []
    if low_info:
        summary_parts.append("回答信息量低")
    if weak_recall:
        summary_parts.append("回答与当前话题候选命中弱（疑似偏题）")
    if avoid_streak >= AVOID_STREAK_THRESHOLD:
        summary_parts.append(f"已连续 {avoid_streak} 轮低信息/回避")
    if exhausted:
        summary_parts.append("当前话题已追问过深，应换方向")
    if project_hint:
        summary_parts.append("回答提到项目/实战经历")

    return DecisionSignals(
        low_information=low_info,
        weak_recall=weak_recall,
        avoid_streak=avoid_streak,
        exhausted_topic=exhausted,
        has_project_hint=project_hint,
        summary="；".join(summary_parts) or "未检测到显著信号，正常推进",
    )


def decide_strategy(signals: DecisionSignals, difficulty: str = "normal") -> str:
    """四信号 → 策略映射（优先级从高到低，可测试的纯函数）。"""
    if signals.exhausted_topic:
        return "switch_topic"
    if signals.weak_recall and signals.low_information:
        return "remedy"
    if signals.weak_recall:
        return "remedy"
    if signals.avoid_streak >= AVOID_STREAK_THRESHOLD:
        return "switch_topic"
    if signals.low_information:
        return _low_info_strategy(difficulty)
    if signals.has_project_hint:
        return "project_probe"
    return "none"


def _low_info_strategy(difficulty: str) -> str:
    """低信息回答按难度加权：hard 压测 deep_dive，easy 引导 remedy，normal 一般追问。"""
    if difficulty == "hard":
        return "deep_dive"
    if difficulty == "easy":
        return "remedy"
    return "probe"


def build_signal_section(signals: DecisionSignals) -> str:
    """生成供 Agent prompt 注入的信号摘要段。"""
    if not signals.is_clear:
        return ""
    return (
        f"【信号检测】\n{signals.summary}。\n"
        "提示：请优先参考上述信号调整策略（如：信号为偏题则用 remedy 拉回正题并给提示，"
        "信号为话题过深则必须 switch_topic 换方向，避免死磕）。\n"
    )
