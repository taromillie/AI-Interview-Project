"""真实面试复盘服务（Phase 3，FR-D-03）。

LLM 对录入的真实面试问答逐题批改；失败时规则兜底评分。
"""
import json
import logging

from sqlalchemy.orm import Session

from app.agents.prompts import REAL_INTERVIEW_REVIEW_PROMPT
from app.llm.base import ChatMessage, LLMProvider
from app.models.real_interview import RealInterview, RealInterviewItem

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


def _clamp(value, lo=0.0, hi=100.0) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return 50.0


def _rule_review(items: list[RealInterviewItem]) -> dict:
    """规则兜底：按回答长度粗评分。"""
    reviews = []
    for it in items:
        score = min(85.0, 40.0 + len(it.answer) / 25.0)
        reviews.append({
            "question": it.question[:200],
            "score": round(_clamp(score), 1),
            "comment": "LLM 复盘暂不可用，已按回答完整度粗略评分；建议补充细节后重新生成。",
        })
    return {
        "overall_score": round(sum(r["score"] for r in reviews) / len(reviews), 1) if reviews else 0.0,
        "dimensions": {"tech": 0, "expression": 0, "logic": 0, "project": 0},
        "item_reviews": reviews,
        "suggestions": ["重新生成复盘以获得更精准建议"],
        "summary": "本次复盘由规则引擎生成（LLM 调用失败）。",
    }


async def review_real_interview(
    db: Session,
    llm: LLMProvider,
    interview: RealInterview,
) -> dict:
    """对真实面试逐题批改，结果写回 interview.review。"""
    items = db.query(RealInterviewItem).filter_by(interview_id=interview.id).order_by(RealInterviewItem.id).all()

    items_text = "\n".join(
        f"Q{i+1}: {it.question[:300]}\nA{i+1}: {it.answer[:300]}" for i, it in enumerate(items)
    ) or "（无问答记录）"

    prompt = REAL_INTERVIEW_REVIEW_PROMPT.format(
        company=interview.company,
        position=interview.position or "未填写",
        round_type=interview.round_type or "未填写",
        interview_date=interview.interview_date or "未填写",
        notes=(interview.notes or "")[:300] or "（无）",
        items_text=items_text,
    )
    try:
        raw = await llm.achat([ChatMessage("user", prompt)], temperature=0.2, max_tokens=2200)
        data = _extract_json(raw)

        dims = data.get("dimensions") or {}
        item_reviews = []
        for i, it in enumerate(items):
            found = None
            for ir in data.get("item_reviews") or []:
                if isinstance(ir, dict) and i < len(items) and (
                    str(ir.get("question") or "").strip() == it.question.strip()
                    or str(ir.get("question") or "").strip() == f"Q{i+1}"
                ):
                    found = ir
                    break
            if found is None:
                ir_list = [x for x in (data.get("item_reviews") or []) if isinstance(x, dict)]
                found = ir_list[i] if i < len(ir_list) else {}
            score = _clamp(found.get("score"))
            comment = str(found.get("comment") or "")[:400]
            item_reviews.append({
                "question": it.question[:300],
                "score": round(score, 1),
                "comment": comment,
            })
            it.score = score
            it.comment = comment

        review = {
            "overall_score": round(_clamp(data.get("overall_score", sum(r["score"] for r in item_reviews) / max(len(item_reviews), 1))), 1),
            "dimensions": {
                "tech": _clamp(dims.get("tech")),
                "expression": _clamp(dims.get("expression")),
                "logic": _clamp(dims.get("logic")),
                "project": _clamp(dims.get("project")),
            },
            "item_reviews": item_reviews,
            "suggestions": [str(s)[:200] for s in (data.get("suggestions") or []) if str(s).strip()][:5],
            "summary": str(data.get("summary") or "")[:300],
        }
    except Exception:
        logger.warning("real interview review LLM 失败，使用规则回退", exc_info=True)
        review = _rule_review(items)
        for it, ir in zip(items, review["item_reviews"]):
            it.score = ir["score"]
            it.comment = ir["comment"]

    interview.review = review
    db.commit()
    db.refresh(interview)
    return review
