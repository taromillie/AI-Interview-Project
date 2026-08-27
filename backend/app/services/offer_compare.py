"""Offer 对比服务（Phase 3，FR-F-03）。

LLM 基于多个 offer 的年化总包与综合因素给出对比分析；失败时规则兜底。
"""
import json
import logging

from app.agents.prompts import OFFER_COMPARE_PROMPT
from app.llm.base import ChatMessage, LLMProvider
from app.models.offer import Offer

logger = logging.getLogger(__name__)


def annual_package(o: Offer) -> int:
    """年化总包：月薪 × (12 + 年终月数) + 股票年化。"""
    return o.monthly_salary * (12 + o.bonus_months) + o.stock_value


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


def _rule_analysis(offers: list[Offer]) -> str:
    """规则兜底：按年化总包排序给出建议。"""
    ranked = sorted(offers, key=annual_package, reverse=True)
    lines = [f"当前 {len(offers)} 个 Offer 中年化总包从高到低为："]
    for o in ranked:
        lines.append(
            f"· {o.company}（{o.position or '未填'}）：{annual_package(o)} 元/年"
            + (f"，生活平衡评分 {o.work_balance}/10" if o.work_balance else "")
        )
    best = ranked[0]
    lines.append(
        f"按总包优先建议选择 {best.company}；若更看重生活平衡，可结合各 Offer 的评分与城市生活成本综合决策。"
    )
    return "\n".join(lines)


def build_compare_table(offers: list[Offer]) -> list[dict]:
    """结构化对比表（行=字段，列=各 offer）。"""
    fields = [
        ("公司", [o.company for o in offers]),
        ("岗位", [o.position for o in offers]),
        ("城市", [o.city for o in offers]),
        ("月薪（元）", [f"{o.monthly_salary}" for o in offers]),
        ("年终奖（月）", [f"{o.bonus_months}" for o in offers]),
        ("股票年化（元/年）", [f"{o.stock_value}" for o in offers]),
        ("年化总包（元/年）", [f"{annual_package(o)}" for o in offers]),
        ("生活平衡（1-10）", [f"{o.work_balance}" for o in offers]),
        ("福利", [o.benefits or "—" for o in offers]),
        ("备注", [o.notes or "—" for o in offers]),
    ]
    return [{"field": f, "values": vs} for f, vs in fields]


async def compare_offers(llm: LLMProvider, offers: list[Offer]) -> tuple[list[dict], str]:
    """返回（对比表, AI 分析建议）。"""
    table = build_compare_table(offers)
    offers_text = "\n".join(
        f"{i+1}. {o.company}｜{o.position or '-'}｜{o.city or '-'}｜月薪{o.monthly_salary}元×{12 + o.bonus_months}薪｜"
        f"股票年化{o.stock_value}元/年｜年化总包{annual_package(o)}元｜生活平衡{o.work_balance}/10｜"
        f"福利：{o.benefits or '-'}｜备注：{o.notes or '-'}"
        for i, o in enumerate(offers)
    )
    prompt = OFFER_COMPARE_PROMPT.format(offers_text=offers_text)
    try:
        raw = await llm.achat([ChatMessage("user", prompt)], temperature=0.3, max_tokens=800)
        data = _extract_json(raw)
        analysis = str(data.get("analysis") or "")[:800]
        if not analysis.strip():
            raise ValueError("analysis 为空")
    except Exception:
        logger.warning("offer compare LLM 失败，使用规则兜底", exc_info=True)
        analysis = _rule_analysis(offers)
    return table, analysis
