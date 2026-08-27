"""简历×JD 匹配诊断服务（Phase 1）。

实现思路（MVP，不依赖向量库，保证可复现）：
1. LLM 从 JD 提取 required / bonus 技能清单；
2. 与简历技能做集合匹配（大小写不敏感、包含关系），按权重计算匹配分；
3. 对缺失的必需技能生成缺口（GapItem）；
4. LLM 生成简历优化建议，失败时基于缺口生成规则建议。
"""
import json
import logging

from sqlalchemy.orm import Session

from app.agents.prompts import JD_SKILL_PROMPT, SUGGESTION_PROMPT
from app.llm.base import ChatMessage, LLMProvider
from app.models.resume import MatchDiagnostic, Resume

logger = logging.getLogger(__name__)

REQUIRED_WEIGHT = 85.0
BONUS_WEIGHT = 15.0


def _extract_json(raw: str):
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


async def extract_jd_skills(llm: LLMProvider, jd_text: str) -> dict:
    """从 JD 提取 required / bonus 技能。"""
    try:
        raw = await llm.achat(
            [ChatMessage("user", JD_SKILL_PROMPT.format(jd_text=jd_text[:6000]))],
            temperature=0,
            max_tokens=800,
        )
        data = json.loads(raw) if isinstance(json.loads(raw), dict) else {}
        # 兼容外层对象或数组
        if isinstance(data, dict):
            return {
                "required": [str(s) for s in data.get("required", []) if str(s).strip()],
                "bonus": [str(s) for s in data.get("bonus", []) if str(s).strip()],
            }
        return {"required": [], "bonus": []}
    except Exception as exc:  # noqa: BLE001
        logger.warning("JD 技能提取失败: %s", exc)
        return {"required": [], "bonus": []}


def _hit(resume_skills: list[str], skill: str) -> bool:
    """判断简历技能是否命中 JD 技能（包含关系，大小写不敏感）。"""
    target = skill.lower()
    return any(target in s.lower() for s in resume_skills)


def compute_match(resume_skills: list[str], jd_skills: dict) -> tuple[float, list[dict]]:
    """计算匹配分与缺口列表。返回 (score 0-100, gaps)。"""
    required = [s for s in jd_skills.get("required", []) if s]
    bonus = [s for s in jd_skills.get("bonus", []) if s]

    matched_req = [s for s in required if _hit(resume_skills, s)]
    matched_bonus = [s for s in bonus if _hit(resume_skills, s)]

    req_ratio = len(matched_req) / len(required) if required else 0.0
    bonus_ratio = len(matched_bonus) / len(bonus) if bonus else 0.0
    score = round(req_ratio * REQUIRED_WEIGHT + bonus_ratio * BONUS_WEIGHT, 1)
    score = max(0.0, min(100.0, score))

    gaps: list[dict] = []
    for skill in required:
        if not _hit(resume_skills, skill):
            gaps.append(
                {
                    "skill": skill,
                    "required_level": "熟练",
                    "current_level": "简历未体现",
                    "suggestion": f"补充「{skill}」相关项目经历或技能关键词，并给出可量化的使用场景",
                }
            )
    return score, gaps


async def generate_suggestions(
    llm: LLMProvider,
    jd_text: str,
    resume_brief: str,
    gaps: list[dict],
) -> list[str]:
    """生成简历优化建议；失败时基于缺口生成规则建议。"""
    gap_text = "；".join(f"缺口 {g['skill']}" for g in gaps) or "无明显硬缺口"
    try:
        raw = await llm.achat(
            [
                ChatMessage(
                    "user",
                    SUGGESTION_PROMPT.format(
                        jd_text=jd_text[:4000],
                        resume_brief=(resume_brief or "")[:1500],
                        gap_text=gap_text,
                    ),
                )
            ],
            temperature=0.3,
            max_tokens=600,
        )
        items = _extract_json(raw)
        if isinstance(items, list):
            return [str(i) for i in items if str(i).strip()][:6]
    except Exception as exc:  # noqa: BLE001
        logger.warning("简历建议生成失败，使用规则建议: %s", exc)
    return [
        f"在简历中突出与目标岗位相关的技能关键词：{g['skill']}（写在技能清单与技术栈段落）"
        for g in gaps[:3]
    ] or ["补充更多量化成果（数据、指标），增强说服力"]


async def run_diagnostic(
    db: Session,
    llm: LLMProvider,
    resume: Resume,
    jd_text: str,
) -> MatchDiagnostic:
    """执行一次完整诊断并落库。"""
    jd_skills = await extract_jd_skills(llm, jd_text)
    resume_skills = resume.skills or []
    score, gaps = compute_match(resume_skills, jd_skills)
    brief = resume.parsed_json.get("brief", "") or resume.raw_text[:300] or ""
    suggestions = await generate_suggestions(llm, jd_text, brief, gaps)

    diagnostic = MatchDiagnostic(
        user_id=resume.user_id,
        resume_id=resume.id,
        jd_text=jd_text,
        match_score=score,
        gaps=gaps,
        suggestions=suggestions,
    )
    db.add(diagnostic)
    db.commit()
    db.refresh(diagnostic)
    return diagnostic
