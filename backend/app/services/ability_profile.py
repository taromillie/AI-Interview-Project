"""能力画像聚合服务（Phase 2）。

将用户最近多场面试的复盘报告聚合为能力画像：
- dimensions：四维度加权平均
- skill_scores：从逐题反馈中匹配简历技能，取该技能相关题目的均分
- weak_points：按出现频次汇总弱点标签
聚合结果 upsert 到 ability_profiles 表。
"""
import logging
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.career import AbilityProfile
from app.models.interview import Interview, Report
from app.models.resume import Resume

logger = logging.getLogger(__name__)

DIM_KEYS = ["tech", "expression", "logic", "project"]


def _to_float(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


DIM_LABELS = {
    "tech": "技术深度",
    "expression": "表达清晰",
    "logic": "逻辑思维",
    "project": "项目颗粒度",
}

DIM_SUGGESTIONS = {
    "tech": "建议加强底层原理与架构设计类题目的练习，回答时结合源码与性能数据。",
    "expression": "建议用 STAR 法则（情境-任务-行动-结果）结构化组织回答，减少口头禅与冗余。",
    "logic": "建议先给出结论再逐步展开，强化分点作答与因果推导训练。",
    "project": "建议把项目亮点量化成指标，明确个人贡献与团队分工的边界。",
}


def _build_advice(dimensions: dict, skill_scores: dict, weak_points: list[str]) -> tuple[list[str], list[str]]:
    """基于聚合结果生成优势项与提升建议（模板规则，避免额外 LLM 调用）。"""
    strengths: list[str] = []
    suggestions: list[str] = []

    dim_sorted = sorted(DIM_KEYS, key=lambda k: _to_float(dimensions.get(k)), reverse=True)
    for k in dim_sorted[:2]:
        v = _to_float(dimensions.get(k))
        if v >= 70:
            strengths.append(f"{DIM_LABELS.get(k, k)}表现突出（{v:.0f} 分），面试中保持稳定。")

    skills_sorted = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)
    for name, v in skills_sorted[:2]:
        if v >= 75:
            strengths.append(f"技能「{name}」掌握扎实（{v:.0f} 分），相关追问应对自如。")

    lowest = dim_sorted[-1] if dim_sorted else None
    if lowest and _to_float(dimensions.get(lowest)) < 70:
        suggestions.append(
            f"{DIM_LABELS.get(lowest, lowest)}是当前短板（{_to_float(dimensions.get(lowest)):.0f} 分），"
            + DIM_SUGGESTIONS.get(lowest, "建议针对性复盘改进。")
        )
    for name, v in skills_sorted:
        if v < 65:
            suggestions.append(f"「{name}」相关题目得分偏低（{v:.0f} 分），建议补强后再实战检验。")
            if len(suggestions) >= 3:
                break
    for w in weak_points[:3]:
        if len(suggestions) >= 4:
            break
        suggestions.append(f"面试官多次提醒：{w}，复盘时作为重点改进项。")

    return strengths[:3], suggestions[:4]


def aggregate_ability_profile(db: Session, user_id: int, limit: int = 20) -> AbilityProfile | None:
    """聚合报告并写入能力画像表，无报告时返回 None。"""
    reports = db.scalars(
        select(Report)
        .join(Interview, Report.interview_id == Interview.id)
        .where(Interview.user_id == user_id)
        .order_by(Report.id.desc())
        .limit(limit)
    ).all()
    if not reports:
        return None

    dims: dict[str, list[float]] = {k: [] for k in DIM_KEYS}
    weak_counter: Counter[str] = Counter()
    for r in reports:
        d = r.dimensions or {}
        for k in DIM_KEYS:
            dims[k].append(_to_float(d.get(k, 0)))
        for w in r.weak_points or []:
            if isinstance(w, str) and w.strip():
                weak_counter[w.strip()] += 1

    dimensions = {k: round(sum(v) / len(v), 1) if v else 0.0 for k, v in dims.items()}
    weak_points = [w for w, _ in weak_counter.most_common(6)]

    # 技能分：最近简历技能 × 相关题目均分（无相关题则给中性分 70）
    latest = db.scalar(
        select(Resume).where(Resume.user_id == user_id).order_by(Resume.id.desc())
    )
    skill_scores: dict[str, float] = {}
    if latest and latest.skills:
        for skill in latest.skills:
            if not isinstance(skill, str) or not skill.strip():
                continue
            related: list[float] = []
            key = skill.strip().lower()
            for r in reports:
                for item in r.question_feedback or []:
                    if not isinstance(item, dict):
                        continue
                    # 题目与回答全文匹配，显著提高技能相关题的召回率
                    qa = (
                        f"{item.get('question') or ''} {item.get('answer') or ''} "
                        f"{item.get('comment') or ''}"
                    ).lower()
                    if key and key in qa:
                        related.append(_to_float(item.get("score"), 50.0))
            skill_scores[skill] = round(sum(related) / len(related), 1) if related else 70.0

    # 维度趋势：按时间升序取最近 10 场
    trend = []
    for r in sorted(reports[:10], key=lambda x: x.id):
        d = r.dimensions or {}
        trend.append(
            {
                "report_id": r.id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "dimensions": {k: _to_float(d.get(k)) for k in DIM_KEYS},
            }
        )

    strengths, suggestions = _build_advice(dimensions, skill_scores, weak_points)

    # upsert 缓存（仅落库模型已有的 dimensions / skill_scores 字段）
    profile = db.scalar(
        select(AbilityProfile).where(AbilityProfile.user_id == user_id)
    )
    if profile is None:
        profile = AbilityProfile(user_id=user_id)
        db.add(profile)
    profile.dimensions = dimensions
    profile.skill_scores = skill_scores
    db.commit()

    return {
        "dimensions": dimensions,
        "skill_scores": skill_scores,
        "weak_points": weak_points,
        "strengths": strengths,
        "suggestions": suggestions,
        "trend": trend,
        "report_count": len(reports),
        "updated_at": profile.updated_at,
    }
