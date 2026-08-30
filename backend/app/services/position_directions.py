"""岗位方向分组与聚合（岗位广场：从「雷同岗位卡」到「岗位方向卡」）。

方向键 = 岗位名归一（幂等，不修改原始数据；完整清洗见 services/job_quality.py）：
- 剥离括号说明（产品经理（北京）→ 产品经理）
- 取第一个 "/" 前部分（产品经理/高级产品经理 → 产品经理）
- 去空格 / 全角空格（Java 开发工程师 → Java开发工程师）
- 剥离职级前缀（资深/高级/中级/初级/助理/实习/应届/专家）
- 常见职位后缀清洗（开发工程师/架构工程师/分析师/工程师/专员）

展示名取组内多数派原始岗位名；聚合公司数、平均薪资、Top 技能。
"""
import collections
import re

_SUFFIX_RULES = (
    ("开发工程师", "开发"),   # Java 开发工程师 → Java开发
    ("架构工程师", "架构"),   # 前端架构工程师 → 前端架构
    ("分析师", "分析"),       # 数据分析师 → 数据分析
    ("工程师", ""),           # 算法工程师 → 算法；测试开发工程师 → 测试开发
    ("专员", ""),             # 运营专员 → 运营
)

_PREFIX_STRIP = ("资深", "高级", "中级", "初级", "助理", "实习", "应届", "专家", "顾问")
_PAREN_RE = re.compile(r"[（(].*?[)）]")


def normalize_position_name(name: str) -> str:
    """岗位名 → 方向键（归一，幂等）。"""
    n = _PAREN_RE.sub("", name)
    n = n.split("/")[0].strip().replace(" ", "").replace("\u3000", "")
    # 职级前缀剥离（循环处理：高级资深产品经理 → 产品经理）
    while n:
        hit = False
        for p in _PREFIX_STRIP:
            if n.startswith(p) and len(n) > len(p):
                n = n[len(p):]
                hit = True
                break
        if not hit:
            break
    for suffix, repl in _SUFFIX_RULES:
        if n.endswith(suffix) and len(n) > len(suffix):
            return n[: -len(suffix)] + repl
    return n


def _position_summary(p) -> dict:
    """岗位 → 前端可用的摘要字典（嵌套在方向卡中，避免依赖 ORM 序列化）。"""
    return {
        "id": p.id,
        "name": p.name,
        "direction": p.direction,
        "difficulty": p.difficulty,
        "skills": p.skills or [],
        "company": p.company,
        "city": p.city,
        "salary_min": p.salary_min,
        "salary_max": p.salary_max,
        "description": p.description,
        "welfare": p.welfare,
        "source": p.source,
        "source_url": p.source_url,
        "published_at": p.published_at.isoformat() if p.published_at else None,
        "synced_at": p.synced_at.isoformat() if p.synced_at else None,
    }


def build_directions(positions, top_skills: int = 6) -> list[dict]:
    """把岗位列表聚合为方向卡数组。

    每张方向卡：
    - key：方向键（归一岗位名，用于前端筛选）
    - name：展示名（组内多数派原始岗位名）
    - count：岗位数（≈ 公司数）
    - skills：Top 技能 chips
    - salary_min / salary_max：平均薪资（可能为空）
    - first_position_id：该方向首个岗位 id（供「面试该方向」使用）
    - positions：该方向下的岗位摘要列表
    按 count 降序。
    """
    groups: dict[str, list] = collections.defaultdict(list)
    for p in positions:
        groups[normalize_position_name(p.name)].append(p)

    result = []
    for key, items in groups.items():
        display_name = collections.Counter(i.name for i in items).most_common(1)[0][0]
        # 技能聚合（大小写不敏感合并：java + Java → 计数更多者）
        skill_counts: dict[str, int] = collections.Counter()
        skill_names: dict[str, dict] = {}
        for it in items:
            for s in (it.skills or []):
                sk = str(s).strip()
                if not sk:
                    continue
                k = sk.lower()
                skill_counts[k] += 1
                prev = skill_names.get(k)
                if prev is None or prev["count"] < skill_counts[k]:
                    skill_names[k] = {"name": sk, "count": skill_counts[k]}
        ordered = sorted(skill_counts, key=skill_counts.get, reverse=True)
        top = [skill_names[k]["name"] for k in ordered[:top_skills]]
        smins = [i.salary_min for i in items if i.salary_min]
        smaxs = [i.salary_max for i in items if i.salary_max]
        positions_out = [_position_summary(i) for i in items]
        result.append(
            {
                "key": key,
                "name": display_name,
                "count": len(items),
                "skills": top,
                "salary_min": round(sum(smins) / len(smins)) if smins else None,
                "salary_max": round(sum(smaxs) / len(smaxs)) if smaxs else None,
                "first_position_id": positions_out[0]["id"] if positions_out else None,
                "positions": positions_out,
            }
        )
    result.sort(key=lambda d: -d["count"])
    return result
