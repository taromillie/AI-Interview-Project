"""简历解析服务：文本提取 + LLM 结构化抽取。

- PDF 用 PyMuPDF 提取文本，支持 txt/md 等纯文本；
- 用 LLM 抽取基本信息/教育/经历/技能（JSON），失败或超时时降级为纯文本摘要。
"""
import asyncio
import json
import logging

import fitz  # PyMuPDF

from app.agents.prompts import RESUME_PARSE_PROMPT
from app.llm.base import ChatMessage, LLMProvider

logger = logging.getLogger(__name__)

MAX_RESUME_SIZE = 2 * 1024 * 1024  # 2MB
# 单次 LLM 解析最长等待时间；超时直接降级，避免保存长时间卡住
PARSE_TIMEOUT = 45.0


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """按文件类型提取简历纯文本。"""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)
    # 其余按纯文本处理（txt/md）
    return file_bytes.decode("utf-8", errors="ignore")


def _parse_json(raw: str) -> dict:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("未找到 JSON 对象")
    data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("JSON 不是对象")
    return data


async def parse_resume(llm: LLMProvider, raw_text: str) -> dict:
    """LLM 结构化抽取简历；失败返回降级结果。"""
    if not raw_text or not raw_text.strip():
        return {"structured": {}, "skills": [], "brief": ""}

    try:
        raw = await asyncio.wait_for(
            llm.achat(
                [ChatMessage("user", RESUME_PARSE_PROMPT.format(resume_text=raw_text[:6000]))],
                temperature=0,
                max_tokens=1200,
            ),
            timeout=PARSE_TIMEOUT,
        )
        structured = _parse_json(raw)
        skills = [
            str(s).strip()
            for s in structured.get("skills", [])
            if str(s).strip()
        ]
        brief = build_brief(structured, raw_text)
        return {"structured": structured, "skills": skills, "brief": brief}
    except asyncio.TimeoutError:
        logger.warning("简历结构化解析超时（%.0fs），使用降级结果", PARSE_TIMEOUT)
        return {"structured": {}, "skills": [], "brief": raw_text[:500]}
    except Exception as exc:  # noqa: BLE001 - 解析失败不阻断上传
        logger.warning("简历结构化解析失败，使用降级结果: %s", exc)
        return {"structured": {}, "skills": [], "brief": raw_text[:500]}


def build_brief(structured: dict, raw_text: str) -> str:
    """生成简历摘要（用于面试 Agent 上下文）。"""
    parts: list[str] = []
    basic = structured.get("basic") or {}
    if basic.get("name"):
        parts.append(f"姓名：{basic['name']}")
    if basic.get("target_position"):
        parts.append(f"目标岗位：{basic['target_position']}")
    if basic.get("years_of_exp"):
        parts.append(f"经验年限：{basic['years_of_exp']}")
    for item in structured.get("education", []):
        if item:
            parts.append(f"教育：{item}")
    for item in structured.get("experience", [])[:3]:
        if item:
            parts.append(f"经历：{item}")
    for item in structured.get("projects", [])[:3]:
        if item:
            parts.append(f"项目：{item}")
    skills = structured.get("skills") or []
    if skills:
        parts.append(f"技能：{'、'.join(str(s) for s in skills[:20])}")
    return "\n".join(parts) if parts else raw_text[:500]
