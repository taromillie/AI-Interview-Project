"""谈薪评估服务（Phase 2）。

LLM 结合市场行情给出薪资区间与谈薪策略；失败时用城市×年限×岗位基数
规则表兜底，保证接口总能返回合理区间。
"""
import json
import logging

from sqlalchemy.orm import Session

from app.agents.prompts import SALARY_EVAL_PROMPT
from app.llm.base import ChatMessage, LLMProvider
from app.models.career import SalaryEval
from app.models.resume import Resume
from app.schemas.career import SalaryEvalRequest

logger = logging.getLogger(__name__)

# 城市薪酬系数（基准 1.0 = 一线）
CITY_COEFF = {
    "北京": 1.0, "上海": 1.0, "深圳": 1.0, "广州": 0.9,
    "杭州": 0.95, "南京": 0.8, "苏州": 0.8, "成都": 0.75,
    "武汉": 0.75, "西安": 0.7, "重庆": 0.7, "长沙": 0.7,
    "天津": 0.75, "郑州": 0.65, "合肥": 0.7,
}
# 岗位月薪基数（3 年经验、一线城市中位，元）
POS_BASE = {
    "架构": 30000, "算法": 26000, "数据": 24000, "后端": 22000,
    "前端": 20000, "产品": 20000, "运维": 18000, "测试": 17000,
    "运营": 15000, "销售": 14000,
}
DEFAULT_BASE = 18000


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


def _resume_brief(resume: Resume | None) -> str:
    """把简历解析成结构化摘要，供 LLM 评估薪资时结合。"""
    if resume is None:
        return "（未提供简历，仅按市场行情估算）"
    parsed = resume.parsed_json or {}
    basic = parsed.get("basic") or {}
    parts = []
    name = str(basic.get("name") or "").strip()
    if name:
        parts.append(f"姓名：{name}")
    exp = str(basic.get("years_of_exp") or "").strip()
    if exp:
        parts.append(f"经验：{exp}")
    skills = resume.skills or []
    if skills:
        parts.append("技能：" + "、".join(str(s) for s in skills[:25]))
    exps = parsed.get("experience") or []
    if exps:
        parts.append(f"工作经历 {len(exps)} 段，最新：{str(exps[0])[:120]}")
    projs = parsed.get("projects") or []
    if projs:
        parts.append(f"项目 {len(projs)} 个，代表：{str(projs[0])[:120]}")
    edu = parsed.get("education") or []
    if edu:
        parts.append("教育：" + str(edu[0])[:80])
    brief = "\n".join(parts)
    return brief or "（简历已上传但内容为空）"


def _rule_fallback(payload: SalaryEvalRequest, resume: Resume | None = None) -> dict:
    """规则表：中位 = 基数 × 城市系数 × (1 + 年限×0.10) × 简历因子。"""
    coeff = next((v for k, v in CITY_COEFF.items() if k in payload.city), 0.8)
    base = next((v for k, v in POS_BASE.items() if k in payload.target_position), DEFAULT_BASE)
    years = max(0, min(int(payload.years or 0), 15))
    # 结合简历修正：技能密度 + 项目密度
    skill_n = proj_n = 0
    resume_note = None
    if resume is not None:
        skill_n = len(resume.skills or [])
        parsed = resume.parsed_json or {}
        proj_n = len(parsed.get("projects") or [])
        skill_bonus = min(skill_n // 6, 3) * 0.03   # 每 6 项技能 +3%，上限 +9%
        proj_bonus = min(proj_n, 3) * 0.02          # 每个项目 +2%，上限 +6%
        resume_factor = 1 + skill_bonus + proj_bonus
        if resume_factor > 1:
            resume_note = f"结合简历：{skill_n} 项技能、{proj_n} 个项目，薪资水平上浮约 {round((resume_factor - 1) * 100)}%"
    else:
        resume_factor = 1.0
    mid = int(base * coeff * (1 + years * 0.10) * resume_factor)
    lo, hi = int(mid * 0.8), int(mid * 1.3)
    city_tier = "一线" if coeff >= 0.9 else "新一线" if coeff >= 0.75 else "二线"
    factors = [
        f"城市系数：{payload.city} 按{city_tier}水平测算（参考系数 {coeff}）",
        f"工作年限 {payload.years} 年，每满 1 年薪资上浮约 10%",
        f"目标岗位「{payload.target_position}」市场基数为 {base} 元/月",
    ]
    if resume_note:
        factors.append(resume_note)
    return {
        "salary_range": [lo, mid, hi],
        "factors": factors,
        "strategy": [
            f"期望薪资报区间（{lo}-{mid} 元）而非单一数字，留谈判余地",
            "先让对方报价，再基于区间回应，避免先亮底线",
            f"谈判底线建议设定为 {lo} 元，低于此值可争取期权/福利补偿",
        ],
    }


async def run_salary_eval(
    db: Session,
    llm: LLMProvider,
    *,
    user_id: int,
    payload: SalaryEvalRequest,
    resume: Resume | None,
) -> SalaryEval:
    """执行谈薪评估并落库，返回 SalaryEval。"""
    brief = _resume_brief(resume)
    prompt = SALARY_EVAL_PROMPT.format(
        target_position=payload.target_position,
        city=payload.city,
        years=payload.years,
        skill_stack="、".join(payload.skill_stack) or "（未提供技能栈）",
        resume_brief=brief,
    )
    try:
        raw = await llm.achat([ChatMessage("user", prompt)], temperature=0.3, max_tokens=1200)
        data = _extract_json(raw)
        rng = data.get("salary_range") or []
        if not isinstance(rng, list) or len(rng) < 3:
            raise ValueError("salary_range 格式错误")
        salary_range = [int(rng[0]), int(rng[1]), int(rng[2])]
        factors = [str(f)[:200] for f in (data.get("factors") or []) if str(f).strip()][:6]
        strategy = [str(s)[:300] for s in (data.get("strategy") or []) if str(s).strip()][:6]
        if salary_range[1] <= 0:
            raise ValueError("salary_range 非法")
    except Exception:
        logger.warning("salary eval LLM 失败，使用规则回退", exc_info=True)
        fallback = _rule_fallback(payload, resume)
        salary_range, factors, strategy = (
            fallback["salary_range"], fallback["factors"], fallback["strategy"],
        )

    ev = SalaryEval(
        user_id=user_id,
        skill_stack=payload.skill_stack,
        years=payload.years,
        city=payload.city,
        target_position=payload.target_position,
        result={"salary_range": salary_range, "factors": factors, "strategy": strategy},
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev
