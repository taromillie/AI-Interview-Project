"""简历→岗位智能匹配服务（MVP 纯规则，可复现、零额外成本）。

综合分 = 技能覆盖率(80) + 方向匹配(12) + 经验匹配(8)，口径与简历×JD 诊断一致。
"""
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import Position
from app.models.resume import Resume
from app.services.job_crawler import infer_direction

logger = logging.getLogger(__name__)

SKILL_WEIGHT = 80.0   # 技能覆盖率权重
DIRECTION_WEIGHT = 12.0  # 方向匹配权重
EXP_WEIGHT = 8.0      # 经验匹配权重

_DIRECTION_LABEL = {
    "backend": "后端",
    "frontend": "前端",
    "algorithm": "算法",
    "product": "产品",
    "operations": "运营",
    "data": "数据",
    "tech": "通用技术",
}
_DIFFICULTY_LABEL = {"junior": "初级", "mid": "中级", "senior": "高级"}


# ---------------------------------------------------------------------------
# 单项打分
# ---------------------------------------------------------------------------
def _hit(resume_skills: list[str], skill: str) -> bool:
    """技能包含关系匹配：岗位技能词是简历技能词的子串即视为命中。"""
    target = skill.lower()
    return any(target in s.lower() for s in resume_skills)


def _skill_score(resume_skills: list[str], position_skills: list[str]) -> tuple[float, list[str], list[str]]:
    """技能覆盖率分（0-80）。岗位无技能标签时给中性分，避免误杀。"""
    required = [s for s in (position_skills or []) if s]
    if not required:
        return SKILL_WEIGHT * 0.5, [], []
    matched = [s for s in required if _hit(resume_skills, s)]
    missing = [s for s in required if s not in matched]
    score = len(matched) / len(required) * SKILL_WEIGHT
    return round(score, 1), matched, missing


def _parse_years(raw) -> float | None:
    """解析 '3年' / '3-5年' / '应届' / '5年以上' 等为年限数字，无法解析返回 None。"""
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if any(k in s for k in ("应届", "在校", "实习", "无经验")):
        return 0.0
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 1) if len(nums) > 1 else nums[0]


def _direction_score(resume_direction: str, position_direction: str) -> float:
    """方向匹配分（0-12）。任一方为 'tech' 时给中性分。"""
    if resume_direction == "tech" or position_direction == "tech":
        return DIRECTION_WEIGHT * 0.5
    return DIRECTION_WEIGHT if resume_direction == position_direction else 0.0


def _exp_score(years: float | None, difficulty: str) -> float:
    """经验匹配分（0-8）。无法解析经验时给中性分。"""
    if years is None:
        return EXP_WEIGHT * 0.5
    if difficulty == "junior":
        if years <= 2:
            return EXP_WEIGHT
        if years <= 5:
            return EXP_WEIGHT * 0.5
        return 0.0
    if difficulty == "mid":
        if 2 <= years <= 5:
            return EXP_WEIGHT
        if 1 <= years <= 7:
            return EXP_WEIGHT * 0.5
        return 0.0
    if difficulty == "senior":
        if years >= 5:
            return EXP_WEIGHT
        if years >= 2:
            return EXP_WEIGHT * 0.5
        return 0.0
    return EXP_WEIGHT * 0.5


# ---------------------------------------------------------------------------
# 规则推荐理由
# ---------------------------------------------------------------------------
def _build_reason(resume_direction: str, position: Position, matched: list[str],
                  missing: list[str], years: float | None, exp_score: float) -> str:
    parts: list[str] = []
    if matched:
        tips = "、".join(matched[:4])
        parts.append(f"你的技能中「{tips}」与岗位要求高度匹配")
    if missing:
        tips = "、".join(missing[:4])
        parts.append(f"目前缺少「{tips}」，建议补充相关经验")
    if not matched and not missing:
        parts.append("岗位技能标签不足，暂按中性评估")

    d_label = _DIRECTION_LABEL.get(position.direction, position.direction)
    if resume_direction != "tech" and position.direction != "tech" and resume_direction != position.direction:
        parts.append(f"岗位方向（{d_label}）与你的求职方向不一致，转岗需谨慎")

    diff_label = _DIFFICULTY_LABEL.get(position.difficulty, position.difficulty)
    if years is not None:
        if position.difficulty == "junior" and years > 2:
            parts.append(f"岗位偏{diff_label}，你已有 {years:.0f} 年经验，可重点关注中高级岗位")
        elif position.difficulty == "senior" and years < 5:
            parts.append(f"岗位偏{diff_label}，你的经验（{years:.0f} 年）可能不足")
        elif position.difficulty == "mid" and not (2 <= years <= 5):
            parts.append(f"岗位偏{diff_label}，你的经验（{years:.0f} 年）与之有偏差")
    return "；".join(parts)


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def _infer_resume_direction(resume: Resume) -> str:
    """从简历目标岗位 / 技能推断求职方向，无法推断返回 'tech'。"""
    parsed = resume.parsed_json or {}
    basic = parsed.get("basic") or {}
    target = str(basic.get("target_position") or "").strip()
    if target:
        d = infer_direction(target)
        if d != "tech":
            return d
    skills_text = " ".join(s for s in (resume.skills or []))
    if skills_text:
        d = infer_direction(skills_text)
        if d != "tech":
            return d
    return "tech"


def match_positions(db: Session, resume: Resume, limit: int = 10,
                    direction: str | None = None, city: str | None = None,
                    difficulty: str | None = None) -> list[dict]:
    """从岗位库召回并按综合分排序，返回 Top N 推荐。

    结果项: position 快照 + match_score + matched/missing_skills + reason + dimension_breakdown
    """
    resume_skills = [s for s in (resume.skills or [])]
    resume_direction = _infer_resume_direction(resume)
    parsed = resume.parsed_json or {}
    years = _parse_years((parsed.get("basic") or {}).get("years_of_exp"))

    stmt = select(Position).where(Position.status == "active")
    if direction:
        stmt = stmt.where(Position.direction == direction)
    if city:
        stmt = stmt.where(Position.city.contains(city))
    if difficulty:
        stmt = stmt.where(Position.difficulty == difficulty)

    results: list[dict] = []
    for p in db.scalars(stmt).all():
        skill_score, matched, missing = _skill_score(resume_skills, p.skills)
        direction_score = _direction_score(resume_direction, p.direction)
        exp_score = _exp_score(years, p.difficulty)
        total = round(skill_score + direction_score + exp_score, 1)
        reason = _build_reason(resume_direction, p, matched, missing, years, exp_score)
        results.append({
            "position": p,
            "match_score": total,
            "matched_skills": matched,
            "missing_skills": missing,
            "reason": reason,
            "dimension_breakdown": {
                "skill_score": skill_score,
                "direction_score": direction_score,
                "exp_score": exp_score,
            },
        })

    results.sort(key=lambda r: r["match_score"], reverse=True)
    return results[:limit]
