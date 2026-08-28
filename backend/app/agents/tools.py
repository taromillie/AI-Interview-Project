"""有边界 Agent 工具层（设计 AD-02，工作包 A）。

提供三个只读工具，供面试编排器在 Agent 决策前装配上下文：
1. search_knowledge —— 检索候选题目（向量增强 + 关键词降级）；
2. get_resume_evidence —— 读取简历中的证据（技能/项目/经历摘要）；
3. get_coverage —— 统计岗位技能覆盖度与已问知识点，辅助换话题。

边界约束（FR-C-04）：
- 三个工具均为只读，无任何写副作用；
- 每次面试决策最多允许调用 MAX_TOOL_CALLS=3 次，超出即拒绝；
- 工具调用异常不阻断主流程：失败返回 ToolResult(ok=False)，由调用方降级。
"""
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from app.rag.embedding import EmbeddingProvider
from app.rag.retriever import aselect_candidates

logger = logging.getLogger(__name__)

MAX_TOOL_CALLS = 3
RESUME_EVIDENCE_MAX_CHARS = 800
COVERAGE_MAX_SKILLS = 16


@dataclass
class ToolResult:
    """工具调用结果：统一携带 name/ok/data/error。"""

    name: str
    ok: bool
    data: Any = None
    error: str = ""


@dataclass
class ToolCallGuard:
    """单轮工具调用计数器：超过 MAX_TOOL_CALLS 后拒绝后续调用。"""

    limit: int = MAX_TOOL_CALLS
    calls: list[str] = field(default_factory=list)

    def can_call(self, name: str) -> bool:
        return len(self.calls) < self.limit

    def record(self, name: str, ok: bool) -> None:
        self.calls.append(f"{name}:{'ok' if ok else 'fail'}")

    @property
    def used(self) -> int:
        return len(self.calls)

    @property
    def transcript(self) -> str:
        return ", ".join(self.calls) or "（本轮未调用工具）"


async def search_knowledge(
    db,
    position_id: int | None,
    asked_ids: set[int],
    answer_text: str | None = None,
    top_n: int = 6,
    embedder: EmbeddingProvider | None = None,
    guard: ToolCallGuard | None = None,
) -> ToolResult:
    """工具①：检索候选题目（向量优先 + 关键词降级）。"""
    if guard and not guard.can_call("search_knowledge"):
        return ToolResult("search_knowledge", ok=False, error="工具调用超限")
    try:
        atoms = await aselect_candidates(
            db, position_id, asked_ids,
            answer_text=answer_text, top_n=top_n, embedder=embedder,
        )
        if guard:
            guard.record("search_knowledge", True)
        return ToolResult("search_knowledge", ok=True, data=atoms)
    except Exception as exc:  # noqa: BLE001 - 工具失败不阻断流程
        logger.warning("search_knowledge 调用失败: %s", exc)
        if guard:
            guard.record("search_knowledge", False)
        return ToolResult("search_knowledge", ok=False, error=str(exc))


def get_resume_evidence(
    resume: Any | None,
    guard: ToolCallGuard | None = None,
) -> ToolResult:
    """工具②：读取简历证据摘要（技能/项目/经历，只读）。"""
    if guard and not guard.can_call("get_resume_evidence"):
        return ToolResult("get_resume_evidence", ok=False, error="工具调用超限")
    try:
        evidence = _extract_resume_evidence(resume)
        if guard:
            guard.record("get_resume_evidence", True)
        return ToolResult("get_resume_evidence", ok=True, data=evidence)
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_resume_evidence 调用失败: %s", exc)
        if guard:
            guard.record("get_resume_evidence", False)
        return ToolResult("get_resume_evidence", ok=False, error=str(exc))


def get_coverage(
    position_skills: list[str],
    asked_questions: list[str],
    guard: ToolCallGuard | None = None,
) -> ToolResult:
    """工具③：统计岗位技能覆盖度（已问 vs 未覆盖），辅助换话题。"""
    if guard and not guard.can_call("get_coverage"):
        return ToolResult("get_coverage", ok=False, error="工具调用超限")
    try:
        coverage = _compute_coverage(position_skills, asked_questions)
        if guard:
            guard.record("get_coverage", True)
        return ToolResult("get_coverage", ok=True, data=coverage)
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_coverage 调用失败: %s", exc)
        if guard:
            guard.record("get_coverage", False)
        return ToolResult("get_coverage", ok=False, error=str(exc))


def _extract_resume_evidence(resume: Any | None) -> str:
    """从简历对象/字典提取可读证据摘要。"""
    if resume is None:
        return "（未提供简历，可基于岗位要求发问）"
    if isinstance(resume, dict):
        raw = resume
    elif hasattr(resume, "parsed_json"):
        raw = resume.parsed_json
        if isinstance(raw, str):
            try:
                raw = json.loads(raw or "{}")
            except (TypeError, json.JSONDecodeError):
                raw = {}
        if not isinstance(raw, dict):
            raw = {}
    else:
        raw = {}

    skills = raw.get("skills") or []
    projects = raw.get("projects") or []
    experience = raw.get("experience") or []
    parts = []
    if skills:
        parts.append("技能：" + "、".join(skills[:12]))
    if projects:
        parts.append("项目：" + " | ".join(str(p)[:80] for p in projects[:3]))
    if experience:
        parts.append("经历：" + " | ".join(str(e)[:80] for e in experience[:2]))
    text = "\n".join(parts)
    return text[:RESUME_EVIDENCE_MAX_CHARS] or "（简历信息较少，可基于岗位要求发问）"


def _compute_coverage(position_skills: list[str], asked_questions: list[str]) -> dict:
    """计算技能覆盖：返回 {covered, uncovered, ratio, hint}。"""
    asked_text = " ".join(asked_questions) or ""
    covered: list[str] = []
    uncovered: list[str] = []
    for skill in position_skills[:COVERAGE_MAX_SKILLS]:
        if not skill:
            continue
        if skill.lower() in asked_text.lower():
            covered.append(skill)
        else:
            uncovered.append(skill)
    total = len(covered) + len(uncovered)
    ratio = round(len(covered) / total, 2) if total else 0.0
    hint = "建议优先转向尚未覆盖的技能方向：" + "、".join(uncovered[:6]) if uncovered else "岗位技能已基本覆盖"
    return {"covered": covered, "uncovered": uncovered, "ratio": ratio, "hint": hint}
