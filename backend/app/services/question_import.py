"""题库批量导入：JSON / Markdown 解析与落库（P2，FR-C-01）。

支持的输入格式：
- JSON：顶层数组，或 {"questions": [...]}；每条含 question/title、reference_points/reference、tags、difficulty
- Markdown：以 `## 题目`（或 ### / ####）分隔题目；body 内 `- 要点xxx`、`- 标签: a, b`、`- 难度: senior` 可选项
"""
import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import KnowledgeAtom, Position

logger = logging.getLogger(__name__)

DIFFICULTIES = {"junior", "mid", "senior"}


def normalize_difficulty(value) -> str:
    """归一化难度，非法值回退 mid。"""
    v = str(value or "").strip().lower()
    return v if v in DIFFICULTIES else "mid"


def _to_str_list(value) -> list[str]:
    """把标量/列表/逗号字符串统一转成字符串列表。"""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in re.split(r"[,，;；]", value) if x.strip()]
    return [str(value).strip()]


def parse_json(text: str) -> list[dict]:
    """解析 JSON 题库。语法错误抛 json.JSONDecodeError，结构错误抛 ValueError。"""
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("questions") or data.get("items") or []
    if not isinstance(data, list):
        raise ValueError("JSON 应为题目数组或含 questions 字段的对象")
    items = []
    for i, raw in enumerate(data, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"第 {i} 条不是对象")
        question = str(raw.get("question") or raw.get("title") or "").strip()
        if not question:
            raise ValueError(f"第 {i} 条缺少 question/title 字段")
        items.append({
            "question": question,
            "reference_points": _to_str_list(raw.get("reference_points") or raw.get("reference")),
            "tags": _to_str_list(raw.get("tags")),
            "difficulty": normalize_difficulty(raw.get("difficulty")),
        })
    return items


def parse_markdown(text: str) -> list[dict]:
    """解析 Markdown 题库：`## 题目` 分隔，子项 `- 内容` 视为参考要点。"""
    items = []
    parts = re.split(r"^#{1,4}\s+(.+?)\s*$", text, flags=re.MULTILINE)
    # parts = [前导, 标题1, 正文1, 标题2, 正文2, ...]
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        if not title:
            continue
        item: dict = {"question": title, "reference_points": [], "tags": [], "difficulty": "mid"}
        for raw_line in body.splitlines():
            s = raw_line.strip().lstrip("-*•").strip()
            if not s:
                continue
            low = s.lower()
            if low.startswith("标签:") or low.startswith("tag:"):
                item["tags"] = _to_str_list(s.split(":", 1)[1])
            elif low.startswith("难度:"):
                item["difficulty"] = normalize_difficulty(s.split(":", 1)[1])
            elif low.startswith("要点:") or low.startswith("参考:"):
                item["reference_points"].append(s.split(":", 1)[1].strip())
            else:
                item["reference_points"].append(s)
        items.append(item)
    return items


def parse_auto(text: str) -> list[dict]:
    """自动识别：优先 JSON，失败则按 Markdown。"""
    try:
        return parse_json(text)
    except json.JSONDecodeError:
        return parse_markdown(text)
    except ValueError as exc:
        # JSON 结构错误：若看起来像 Markdown（含 ## 标题）则回退，否则抛出
        if re.search(r"^#{1,4}\s+\S", text, flags=re.MULTILINE):
            return parse_markdown(text)
        raise exc


def import_atoms(
    db: Session,
    user,
    position_id: int,
    items: list[dict],
) -> dict:
    """批量导入知识原子（去重：同岗位下题目重复则跳过），返回统计。"""
    position = db.get(Position, position_id)
    if position is None:
        raise ValueError("岗位不存在")
    created = 0
    skipped = 0
    errors: list[dict] = []
    existing: set[str] = set()
    for (q,) in db.execute(
        select(KnowledgeAtom.question).where(KnowledgeAtom.position_id == position_id)
    ):
        existing.add(str(q).strip())

    for i, it in enumerate(items, start=1):
        q = str(it.get("question") or "").strip()
        if not q:
            errors.append({"row": i, "reason": "题目为空"})
            continue
        if q in existing:
            skipped += 1
            continue
        db.add(KnowledgeAtom(
            position_id=position_id,
            question=q,
            reference_points=it.get("reference_points") or [],
            tags=it.get("tags") or [],
            difficulty=it.get("difficulty") or "mid",
            status="draft",
            created_by=user.id,
        ))
        existing.add(q)
        created += 1
    db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
