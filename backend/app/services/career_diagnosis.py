"""转行诊断服务（Phase 2）。

LLM 对比当前岗位与目标岗位，产出可迁移技能 / 技能缺口 / 学习路径；
失败时用岗位知识规则兜底，保证接口总能返回结果。
"""
import json
import logging

from sqlalchemy.orm import Session

from app.agents.prompts import CAREER_DIAGNOSIS_PROMPT
from app.llm.base import ChatMessage, LLMProvider
from app.models.career import CareerPlan
from app.models.resume import Resume

logger = logging.getLogger(__name__)

# 目标岗位 → 常见技能清单（规则兜底用）
POSITION_SKILLS = {
    "前端": ["JavaScript", "HTML", "CSS", "Vue", "React", "TypeScript"],
    "后端": ["Python", "Java", "Go", "MySQL", "Redis", "FastAPI"],
    "数据": ["Python", "SQL", "Pandas", "Spark", "机器学习"],
    "算法": ["Python", "数据结构", "机器学习", "深度学习"],
    "产品": ["需求分析", "Axure", "数据分析", "用户调研"],
    "测试": ["测试用例设计", "Selenium", "接口测试", "Linux"],
    "运维": ["Linux", "Docker", "Kubernetes", "Shell"],
}


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


def _rule_fallback(from_position: str, to_position: str, skills: list[str]) -> dict:
    """LLM 不可用时按目标岗位关键字生成基础转型建议。"""
    gap_skills: list[str] = []
    for key, items in POSITION_SKILLS.items():
        if key in to_position:
            gap_skills = [s for s in items if s not in (skills or [])]
            break
    if not gap_skills:
        gap_skills = ["岗位核心技能", "项目实战", "面试准备"]
    gaps = [
        {"skill": s, "level": "入门", "suggestion": f"系统学习并完成 1-2 个使用 {s} 的实战项目"}
        for s in gap_skills[:6]
    ]
    roadmap = [
        {"stage": "打基础", "action": f"系统学习目标岗位核心技能：{'、'.join(gap_skills[:3])}", "duration": "1-2 个月"},
        {"stage": "项目实战", "action": "完成 2-3 个对标岗位的实战项目并沉淀到简历", "duration": "2-3 个月"},
        {"stage": "求职准备", "action": "更新简历并参与模拟面试打磨表达", "duration": "1 个月"},
    ]
    return {
        "transferable": [
            {"skill": "学习能力", "evidence": "已有跨领域学习经验，可快速掌握新技能栈"},
            {"skill": "沟通协作", "evidence": "当前岗位的跨职能协作经验可直接复用"},
        ],
        "gaps": gaps,
        "roadmap": roadmap,
        "summary": f"从「{from_position}」转型「{to_position}」具备一定基础，建议按路线图补齐技能缺口后切入。",
    }


async def run_career_diagnosis(
    db: Session,
    llm: LLMProvider,
    *,
    user_id: int,
    from_position: str,
    to_position: str,
    resume: Resume | None,
) -> CareerPlan:
    """执行转行诊断并落库，返回 CareerPlan。"""
    skills = resume.skills if resume else []
    brief = (resume.raw_text or "")[:300] if resume else "（未提供简历）"

    prompt = CAREER_DIAGNOSIS_PROMPT.format(
        from_position=from_position,
        to_position=to_position,
        skills="、".join(skills) or "（未提供简历）",
        resume_brief=brief,
    )
    try:
        raw = await llm.achat([ChatMessage("user", prompt)], temperature=0.3, max_tokens=1600)
        data = _extract_json(raw)

        def clean_list(key: str, fields: tuple[str, ...]) -> list[dict]:
            out = []
            for it in data.get(key, []) or []:
                if isinstance(it, dict):
                    item = {f: str(it.get(f) or "")[:100] for f in fields}
                    if item[fields[0]].strip():
                        out.append(item)
            return out

        transferable = clean_list("transferable", ("skill", "evidence"))
        gaps = clean_list("gaps", ("skill", "level", "suggestion"))
        roadmap = clean_list("roadmap", ("stage", "action", "duration"))
        summary = str(data.get("summary") or "")[:200]
        if not gaps and not roadmap:
            raise ValueError("LLM 输出为空结构")
    except Exception:
        logger.warning("career diagnosis LLM 失败，使用规则回退", exc_info=True)
        fallback = _rule_fallback(from_position, to_position, skills)
        transferable, gaps = fallback["transferable"], fallback["gaps"]
        roadmap, summary = fallback["roadmap"], fallback["summary"]

    plan = CareerPlan(
        user_id=user_id,
        from_position=from_position,
        to_position=to_position,
        transferable=transferable,
        gaps=gaps,
        roadmap=roadmap,
        summary=summary,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
