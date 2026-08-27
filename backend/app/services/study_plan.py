"""备战计划服务（Phase 3，FR-B-06）。

LLM 基于能力画像缺口生成 N 天冲刺计划；失败时用规则模板兜底，
保证接口总能返回一份可执行的计划。
"""
import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.prompts import STUDY_PLAN_PROMPT
from app.llm.base import ChatMessage, LLMProvider
from app.models.career import AbilityProfile
from app.models.resume import Resume
from app.models.study import StudyPlan

logger = logging.getLogger(__name__)


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


def _rule_plan(days: int, target_position: str, gaps: list[str]) -> dict:
    """规则兜底：按阶段分配天数。"""
    gaps = gaps or ["岗位核心技能", "项目实战", "面试表达"]
    tasks = []
    day = 0
    phases = [
        ("基础补强", max(1, int(days * 0.3)), gaps[:3]),
        ("实战刷题", max(1, int(days * 0.4)), ["真题练习", "项目复盘", "深度追问模拟"]),
        ("面试冲刺", max(1, days - max(1, int(days * 0.3)) - max(1, int(days * 0.4))), ["模拟面试", "复盘总结", "表达打磨"]),
    ]
    for name, count, topics in phases:
        for i in range(count):
            day += 1
            tasks.append({
                "day": day,
                "title": f"{name}：{'、'.join(topics[:2])}",
                "description": f"完成「{topics[i % len(topics)]}」的集中学习与练习，记录收获与卡点。",
                "topics": [topics[i % len(topics)]],
                "done": False,
            })
    title = f"{target_position} {days} 天冲刺计划" if target_position else f"{days} 天冲刺备战计划"
    return {
        "title": title,
        "summary": f"按「基础补强 → 实战刷题 → 面试冲刺」三阶段完成 {days} 天备战，每天一个主题、渐进加压。",
        "tasks": tasks,
    }


async def generate_study_plan(
    db: Session,
    llm: LLMProvider,
    *,
    user_id: int,
    target_position: str,
    days: int,
    resume: Resume | None,
) -> StudyPlan:
    """生成备战计划并落库。"""
    days = max(3, min(int(days), 60))

    # 收集能力画像缺口
    profile = db.scalar(
        select(AbilityProfile)
        .where(AbilityProfile.user_id == user_id)
        .order_by(AbilityProfile.id.desc())
    )
    skill_scores = profile.skill_scores if profile else {}
    weak_points: list[str] = []
    dims = profile.dimensions if profile else {}
    for k, v in (dims or {}).items():
        if isinstance(v, (int, float)) and v < 60:
            weak_points.append(f"{k}维度得分 {v:.0f}")
    if skill_scores:
        low = sorted(skill_scores.items(), key=lambda x: x[1])[:3]
        for k, v in low:
            if isinstance(v, (int, float)) and v < 70:
                weak_points.append(f"技能「{k}」得分 {v:.0f}")

    skills = resume.skills if resume else []
    brief = (resume.raw_text or "")[:300] if resume else "（未提供简历）"

    prompt = STUDY_PLAN_PROMPT.format(
        days=days,
        target_position=target_position or "目标岗位",
        skill_scores=json.dumps(skill_scores, ensure_ascii=False)[:500],
        weak_points="、".join(weak_points) or "（暂无画像数据，按通用备战规划）",
        skills="、".join(skills) or "（未提供）",
        resume_brief=brief,
    )
    try:
        raw = await llm.achat([ChatMessage("user", prompt)], temperature=0.3, max_tokens=2600)
        data = _extract_json(raw)
        tasks = []
        for it in data.get("tasks") or []:
            if isinstance(it, dict) and it.get("day") is not None:
                day = max(1, int(it["day"]))
                topics = [str(t)[:60] for t in (it.get("topics") or []) if str(t).strip()][:4]
                tasks.append({
                    "day": day,
                    "title": str(it.get("title") or f"第 {day} 天")[:100],
                    "description": str(it.get("description") or "")[:300],
                    "topics": topics,
                    "done": False,
                })
        tasks = sorted(tasks, key=lambda x: x["day"])[:days]
        if len(tasks) < days:  # 不足补足
            for i in range(1, days + 1):
                if i not in {t["day"] for t in tasks}:
                    tasks.append({
                        "day": i,
                        "title": f"第 {i} 天：查漏补缺与复习",
                        "description": "复习前几日知识点，整理错题与薄弱环节。",
                        "topics": ["复习巩固"],
                        "done": False,
                    })
            tasks = sorted(tasks, key=lambda x: x["day"])[:days]
        title = str(data.get("title") or f"{target_position} {days} 天冲刺计划")[:120]
        summary = str(data.get("summary") or "")[:200]
        if not tasks:
            raise ValueError("LLM 输出无任务")
    except Exception:
        logger.warning("study plan LLM 失败，使用规则回退", exc_info=True)
        fallback = _rule_plan(days, target_position, weak_points)
        title, summary, tasks = fallback["title"], fallback["summary"], fallback["tasks"]

    plan = StudyPlan(
        user_id=user_id,
        title=title,
        target_position=target_position,
        days=days,
        tasks=tasks,
        summary=summary,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
