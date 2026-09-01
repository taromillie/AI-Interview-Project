"""复盘报告生成服务（Phase 1）。

LLM 对整场面试做四维度评分 + 逐题反馈；失败时用规则评分兜底，
保证面试结束一定产出报告。
"""
import json
import logging

from app.llm.base import ChatMessage, LLMProvider
from app.models.interview import InterviewMessage

logger = logging.getLogger(__name__)

REPORT_PROMPT = """你是资深面试官兼职业顾问，请对下面这场模拟面试进行复盘，输出严格 JSON：
{{
  "overall_score": 0到100的整数,
  "dimensions": {{
    "tech": 0到100,
    "expression": 0到100,
    "logic": 0到100,
    "project": 0到100
  }},
  "question_feedback": [
    {{"question": "题目", "answer": "候选回答(截断100字)", "score": 0到100, "comment": "点评", "suggestion": "该回答的优化建议(100字以内)"}}
  ],
  "weak_points": ["弱点1", "弱点2", ...],
  "coverage": {{
    "covered": ["已考察且表现较好的知识点"],
    "uncovered": ["岗位要求但本次未覆盖/表现薄弱的知识点"]
  }},
  "learning_path": [
    {{"phase": "阶段名称", "action": "具体学习行动", "duration": "预计时长"}}
  ],
  "summary": "100字以内的整体评价与改进建议"
}}

维度说明：
- tech：技术深度与正确性
- expression：表达清晰度与条理性
- logic：逻辑性与回答结构
- project：项目经历的真实性与颗粒度

【目标岗位】{position_name}（技能：{position_skills}）
【候选人简历摘要】
{resume_brief}

【面试记录】
{transcript}

规则：
1. coverage 基于岗位技能清单判断：covered 为已考察且回答达标的技能，uncovered 为岗位要求但未考察或表现薄弱的技能；
2. learning_path 3-5 个阶段，针对 weak_points 与 uncovered 给出可执行的学习路线；
3. suggestion 为该回答的具体优化建议，须可执行：指出回答的不足与具体改进方法，可给出示范话术或回答框架（如 STAR 法则、先结论后展开、补充量化数据），不要空泛评价；
4. 只输出 JSON 对象，不要输出任何其他文字。
"""


def _extract_json(raw: str) -> dict:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("未找到 JSON")
    data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("JSON 不是对象")
    return data


def _transcript(messages: list[InterviewMessage]) -> str:
    lines = []
    for m in messages:
        role = "面试官" if m.role == "assistant" else "候选人"
        lines.append(f"{role}：{m.content[:300]}")
    return "\n".join(lines)


def _clamp(value, lo=0.0, hi=100.0) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return 50.0


async def generate_report(
    llm: LLMProvider,
    *,
    position_name: str,
    position_skills: list[str],
    resume_brief: str,
    messages: list[InterviewMessage],
) -> dict:
    """LLM 生成复盘报告数据。"""
    prompt = REPORT_PROMPT.format(
        position_name=position_name,
        position_skills="、".join(position_skills[:12]) or "（未提供）",
        resume_brief=(resume_brief or "")[:800],
        transcript=_transcript(messages),
    )
    raw = await llm.achat(
        [ChatMessage("user", prompt)],
        temperature=0.2,
        max_tokens=1600,
    )
    data = _extract_json(raw)

    # 归一化数据，防止 LLM 输出越界
    dims = data.get("dimensions") or {}
    dimensions = {
        "tech": _clamp(dims.get("tech")),
        "expression": _clamp(dims.get("expression")),
        "logic": _clamp(dims.get("logic")),
        "project": _clamp(dims.get("project")),
    }
    qf = []
    for item in data.get("question_feedback", []) or []:
        if isinstance(item, dict):
            qf.append(
                {
                    "question": str(item.get("question", ""))[:300],
                    "answer": str(item.get("answer", ""))[:150],
                    "score": _clamp(item.get("score")),
                    "comment": str(item.get("comment", ""))[:300],
                    "suggestion": str(item.get("suggestion", ""))[:300],
                }
            )
    weak_points = [str(w) for w in (data.get("weak_points") or []) if str(w).strip()][:6]
    overall = sum(dimensions.values()) / len(dimensions) if dimensions else 0.0

    # 知识覆盖统计（FR-G-04）
    cov = data.get("coverage") or {}
    covered = [str(c)[:100] for c in (cov.get("covered") or []) if str(c).strip()][:12]
    uncovered = [str(u)[:100] for u in (cov.get("uncovered") or []) if str(u).strip()][:12]
    # 学习路线（FR-G-05）
    learning_path = []
    for item in data.get("learning_path", []) or []:
        if isinstance(item, dict) and str(item.get("phase") or "").strip():
            learning_path.append({
                "phase": str(item.get("phase"))[:60],
                "action": str(item.get("action"))[:200],
                "duration": str(item.get("duration") or "")[:30],
            })
    if not learning_path:
        learning_path = _rule_learning_path(position_skills, weak_points)

    return {
        "overall_score": round(_clamp(data.get("overall_score", overall)), 1),
        "dimensions": dimensions,
        "question_feedback": qf,
        "weak_points": weak_points,
        "coverage": {"covered": covered, "uncovered": uncovered},
        "learning_path": learning_path,
        "summary": str(data.get("summary") or "")[:200],
    }


def _rule_learning_path(position_skills: list[str], weak_points: list[str]) -> list[dict]:
    """规则兜底：基于岗位技能与弱点生成学习路线。"""
    target = position_skills[:3] if position_skills else ["岗位核心技能"]
    return [
        {"phase": "基础夯实", "action": f"系统复习「{'、'.join(target)}」，补齐知识盲区", "duration": "1 周"},
        {"phase": "实战演练", "action": f"针对{'、'.join(weak_points[:2]) or '薄弱点'}做专项练习与项目复盘", "duration": "1-2 周"},
        {"phase": "面试冲刺", "action": "每天 1 场模拟面试，复盘表达与逻辑，沉淀高频问题回答模板", "duration": "1 周"},
    ]


def fallback_report(messages: list[InterviewMessage]) -> dict:
    """规则降级：基于回答长度与轮数的粗略评分。"""
    user_msgs = [m for m in messages if m.role == "user"]
    if not user_msgs:
        return {
            "overall_score": 0.0,
            "dimensions": {"tech": 0, "expression": 0, "logic": 0, "project": 0},
            "question_feedback": [],
            "weak_points": ["面试未产生有效作答"],
            "coverage": {"covered": [], "uncovered": []},
            "learning_path": [],
            "summary": "本次面试未产生有效回答，请重新开始一场模拟面试。",
        }
    avg_len = sum(len(m.content) for m in user_msgs) / len(user_msgs)
    base = min(85.0, 45.0 + avg_len / 20.0)
    tech = base
    expression = min(90.0, base + 3)
    logic = min(85.0, base - 2)
    project = min(80.0, base - 5)

    qf = []
    for m in user_msgs:
        qf.append(
            {
                "question": "（规则降级评分）",
                "answer": m.content[:100],
                "score": round(base, 1),
                "comment": "LLM 复盘暂不可用，已按回答完整度粗略评分，请稍后重新生成。",
                "suggestion": "AI 复盘暂不可用，建议补充量化指标与项目细节后重新生成，以获取逐题优化建议。",
            }
        )
    return {
        "overall_score": round((tech + expression + logic + project) / 4, 1),
        "dimensions": {
            "tech": round(tech, 1),
            "expression": round(expression, 1),
            "logic": round(logic, 1),
            "project": round(project, 1),
        },
        "question_feedback": qf,
        "weak_points": ["回答颗粒度不足，建议补充量化指标"],
        "coverage": {"covered": [], "uncovered": []},
        "learning_path": _rule_learning_path([], ["回答颗粒度不足"]),
        "summary": "本次复盘由规则引擎生成（LLM 调用失败），建议补充细节后重新评估。",
    }
