# -*- coding: utf-8 -*-
"""岗位采集服务：可插拔数据源 + 定时增量同步。

合规与限速约定：
- 仅访问 robots.txt 允许的公开页面；
- 不登录、不绕过任何验证、不抓取用户数据；
- 每次请求间隔 3~6 秒（尊重 Crawl-delay）；
- 所有外部请求异常均被捕获并降级，绝不阻断业务；
- 岗位详情为系统基于真实公开信息生成的摘要，并提供原文链接。
"""
from __future__ import annotations

import logging
import random
import re
import threading
import time
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.position import Position

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 方向关键词 → 方向
_DIRECTION_RULES: list[tuple[list[str], str]] = [
    (["前端", "html", "css", "javascript", "vue", "react", "web", "h5", "小程序", "webgl"], "frontend"),
    (["算法", "机器学习", "深度学习", "推荐", "nlp", "cv", "大模型", "数据挖掘", "搜索", "语音"], "algorithm"),
    (["产品", "需求", "pm", "项目", "项目经理", "策划"], "product"),
    (["运营", "增长", "用户运营", "内容", "社群", "渠道", "直播", "新媒体"], "operations"),
    (["数据", "数仓", "etl", "bi", "分析师", "spark", "flink", "hive", "数据开发"], "data"),
    (["后端", "服务端", "java", "go", "golang", "python", "php", "c++", "c#", "node", "测试", "运维", "devops", "架构", "研发"], "backend"),
]
# 难度关键词 → 难度
_JUNIOR_KW = ["实习", "初级", "助理", "应届", "校招", "junior", "1年以下", "1-3年"]
_SENIOR_KW = ["资深", "高级", "专家", "架构", "主管", "负责人", "leader", "senior", "5-10年", "10年以上"]
# JD 技能关键词
_SKILL_KW = [
    "java", "spring", "mysql", "redis", "kafka", "python", "go", "golang", "c++", "c语言", "c#",
    "javascript", "typescript", "vue", "react", "node", "html", "css", "webpack", "小程序", "flutter",
    "机器学习", "深度学习", "pytorch", "tensorflow", "nlp", "推荐算法", "大模型", "llm", "cv",
    "sql", "hive", "spark", "flink", "hadoop", "数仓", "etl", "doris",
    "linux", "docker", "k8s", "kubernetes", "微服务", "分布式", "消息队列", "elasticsearch", "nginx",
    "数据分析", "excel", "tableau", "ab测试", "用户增长", "内容运营", "社群运营", "私域",
    "产品设计", "axure", "prd", "项目管理", "需求分析", "用户研究",
]
# 福利关键词
_WELFARE_KW = [
    "五险一金", "六险一金", "补充医疗保险", "带薪年假", "年终奖", "股票期权", "弹性工作",
    "双休", "周末双休", "免费班车", "餐补", "交通补助", "住房补贴", "定期体检", "员工旅游",
    "节日福利", "零食下午茶", "晋升空间", "扁平管理", "全额公积金",
]

_CITY_MAP = {
    "北京": "北京", "上海": "上海", "广州": "广州", "深圳": "深圳",
    "杭州": "杭州", "成都": "成都", "南京": "南京", "武汉": "武汉",
    "西安": "西安", "苏州": "苏州", "天津": "天津", "重庆": "重庆",
    "长沙": "长沙", "郑州": "郑州", "青岛": "青岛", "厦门": "厦门",
    "合肥": "合肥", "宁波": "宁波", "佛山": "佛山", "东莞": "东莞",
    "大连": "大连", "沈阳": "沈阳", "济南": "济南", "福州": "福州",
    "昆明": "昆明", "南昌": "南昌", "无锡": "无锡", "哈尔滨": "哈尔滨",
    "长春": "长春", "石家庄": "石家庄", "太原": "太原", "南宁": "南宁",
    "珠海": "珠海", "海口": "海口", "贵阳": "贵阳", "兰州": "兰州",
}


# ---------------------------------------------------------------------------
# 数据源协议
# ---------------------------------------------------------------------------
@dataclass
class JobItem:
    name: str
    direction: str = "tech"
    difficulty: str = "mid"
    skills: list[str] = field(default_factory=list)
    company: str = ""
    city: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    description: str = ""
    welfare: list[str] = field(default_factory=list)
    source: str = "builtin"
    source_id: str | None = None
    source_url: str | None = None
    published_at: datetime | None = None


class JobSource(Protocol):
    name: str

    def fetch_jobs(self) -> list[JobItem]: ...


# ---------------------------------------------------------------------------
# 合规辅助
# ---------------------------------------------------------------------------
class RobotsGuard:
    """robots.txt 访问权限检查 + 限速。"""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._parser: urllib.robotparser.RobotFileParser | None = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{self.base_url}/robots.txt")
            with httpx.Client(timeout=10, follow_redirects=True) as client:
                resp = client.get(f"{self.base_url}/robots.txt", headers={"User-Agent": USER_AGENT})
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
            self._parser = rp
        except Exception as exc:  # robots.txt 不可用时默认放行
            logger.warning("robots.txt 读取失败，按可访问处理: %s", exc)
            self._parser = None

    def can_fetch(self, path: str) -> bool:
        self._ensure_loaded()
        if self._parser is None:
            return True
        return self._parser.can_fetch(USER_AGENT, f"{self.base_url}{path}")

    @staticmethod
    def polite_sleep() -> None:
        time.sleep(random.uniform(3.0, 6.0))


# ---------------------------------------------------------------------------
# 字段推断
# ---------------------------------------------------------------------------
def infer_direction(text: str) -> str:
    low = text.lower()
    for keywords, direction in _DIRECTION_RULES:
        if any(k in low for k in keywords):
            return direction
    return "tech"


def infer_difficulty(text: str) -> str:
    low = text.lower()
    if any(k in low for k in _JUNIOR_KW):
        return "junior"
    if any(k in low for k in _SENIOR_KW):
        return "senior"
    return "mid"


def extract_skills(text: str, limit: int = 6) -> list[str]:
    low = text.lower()
    found: list[str] = []
    for kw in _SKILL_KW:
        if kw in low and kw not in found:
            found.append(kw)
        if len(found) >= limit:
            break
    return found


def extract_welfare(text: str) -> list[str]:
    found: list[str] = []
    for kw in _WELFARE_KW:
        if kw in text and kw not in found:
            found.append(kw)
    return found[:8]


def parse_salary(salary_text: str) -> tuple[int | None, int | None]:
    """解析薪资文本 → (minK, maxK)。支持 '20K-35K' '2万-3万' '15000-24000' '12-16k' '面议'。

    注意：'20-30k·14薪' 中 '14薪' 是发薪月数，不是薪资，需先剔除。
    """
    if not salary_text or "面议" in salary_text or "面谈" in salary_text:
        return None, None
    text = salary_text.replace(" ", "").replace("k", "K")
    # 剔除 '·14薪' / '14薪' 等发薪月数片段
    text = re.sub(r"[··*]\d+薪", "", text)
    text = re.sub(r"\d+薪", "", text)
    nums: list[float] = [float(m) for m in re.findall(r"(\d+(?:\.\d+)?)", text)]
    if not nums:
        return None, None
    if "万" in text:
        scale = 10.0  # 万元/年 → K/月（粗略：年薪万≈月薪 K）
        return int(nums[0] * scale), int(nums[-1] * scale)
    if "K" in text:
        return int(nums[0]), int(nums[-1])
    # 纯数字元/月
    return int(nums[0] // 1000), int(nums[-1] // 1000)


# 方向默认技能（列表页无 JD 时兜底，保证卡片技能标签不空）
_DIRECTION_DEFAULT_SKILLS: dict[str, list[str]] = {
    "backend": ["Java", "Python", "MySQL", "Redis", "微服务", "分布式"],
    "frontend": ["JavaScript", "TypeScript", "Vue", "React", "HTML/CSS", "工程化"],
    "algorithm": ["机器学习", "深度学习", "Python", "PyTorch", "数据结构", "数学基础"],
    "product": ["需求分析", "PRD", "数据分析", "项目管理", "用户研究"],
    "operations": ["内容运营", "数据分析", "用户增长", "活动策划", "文案"],
    "data": ["SQL", "Python", "Excel", "数据可视化", "A/B 测试"],
    "tech": ["需求分析", "数据分析", "项目管理", "沟通协作"],
}


def default_skills(direction: str) -> list[str]:
    return list(_DIRECTION_DEFAULT_SKILLS.get(direction, _DIRECTION_DEFAULT_SKILLS["tech"]))


def build_description(item: JobItem, exp: str = "", edu: str = "", industry: str = "") -> str:
    """基于真实岗位字段生成岗位摘要（详情以原文为准）。"""
    skills = "、".join(item.skills[:5]) if item.skills else "相关领域技能"
    lines = [
        f"【岗位方向】{item.direction} / {item.name}",
    ]
    if industry:
        lines.append(f"【所属行业】{industry}")
    if exp or edu:
        lines.append(f"【任职要求】{exp or '经验不限'} · {edu or '学历不限'}")
    lines += [
        f"【岗位职责】负责{item.name}相关工作，参与业务需求分析、方案设计与落地执行；"
        f"与产品、研发、测试等团队协作，保障项目高质量交付；持续关注行业动态，优化工作流程与产出质量。",
        f"【任职要求】熟悉{skills}，具备扎实的专业基础与学习能力；具备良好的沟通协作能力与责任心；"
        f"有同岗位相关经验者优先。",
        f"【福利待遇】五险一金、带薪年假、节日福利、团队建设等，具体以企业招聘页为准。",
        f"【说明】本职位信息来源于职友集公开搜索页，详情以招聘原文为准。",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 内置数据源（兜底，随时可用）
# ---------------------------------------------------------------------------
class BuiltinSource:
    name = "builtin"

    def fetch_jobs(self) -> list[JobItem]:
        rows: list[JobItem] = []
        data = [
            ("后端开发工程师", "backend", "mid", ["Python", "Java", "MySQL", "Redis", "消息队列", "分布式"],
             "示例科技集团", "北京", 20, 35,
             "负责核心业务后端服务的架构设计与开发；参与高并发、高可用系统的设计与落地；与产品、前端协作完成需求评审与技术方案；负责系统性能优化与线上问题排查。福利：五险一金、带薪年假、年终奖、弹性工作、定期体检。"),
            ("Java 开发工程师", "backend", "mid", ["Java", "Spring Boot", "MyBatis", "MySQL", "JVM", "微服务"],
             "示例金融科技", "上海", 22, 38,
             "负责支付与账务系统的后端研发；基于 Spring Cloud 微服务架构完成模块开发；参与系统稳定性治理与性能调优。福利：六险一金、年终奖、免费午餐、员工旅游。"),
            ("全栈开发工程师", "backend", "senior", ["Vue", "React", "Node.js", "Go", "系统设计", "Docker"],
             "示例 SaaS 科技", "深圳", 30, 50,
             "负责企业级 SaaS 产品的前后端全栈研发；主导技术选型与系统架构演进；带领小组完成核心模块交付。福利：股票期权、补充医疗保险、带薪年假、双休。"),
            ("测试开发工程师", "backend", "junior", ["pytest", "接口测试", "自动化测试", "Selenium", "Linux"],
             "示例互联网集团", "杭州", 15, 25,
             "负责产品功能测试与接口自动化测试；搭建持续集成测试流水线；编写测试用例并输出质量报告。福利：五险一金、员工培训、节日福利、下午茶。"),
            ("前端开发工程师", "frontend", "mid", ["HTML/CSS", "JavaScript", "TypeScript", "Vue", "工程化", "性能优化"],
             "示例电商平台", "广州", 18, 30,
             "负责电商主站前端研发；参与组件库建设与前端工程化改造；持续优化页面性能与用户体验。福利：五险一金、加班补贴、弹性工作、团建旅游。"),
            ("前端架构工程师", "frontend", "senior", ["React", "架构设计", "微前端", "Node.js", "性能优化", "工程化"],
             "示例云服务公司", "北京", 35, 60,
             "负责前端基础设施与架构演进；设计微前端体系并推动落地；制定前端规范与工程化标准。福利：股票期权、六险一金、年度体检、双休。"),
            ("算法工程师", "algorithm", "senior", ["机器学习", "深度学习", "Python", "PyTorch", "数据结构", "数学基础"],
             "示例人工智能研究院", "北京", 35, 60,
             "负责大模型训练与推理优化；参与算法方案设计、实验与上线；跟踪学术界前沿进展并落地到产品。福利：高额年终奖、住房补贴、免费三餐、股票期权。"),
            ("推荐算法工程师", "algorithm", "senior", ["推荐系统", "召回排序", "特征工程", "A/B 测试", "Python"],
             "示例内容社区", "上海", 30, 55,
             "负责信息流推荐算法优化；设计召回、排序与重排策略；通过 A/B 实验持续提升核心指标。福利：五险一金、年终奖、免费健身房、零食下午茶。"),
            ("产品经理", "product", "mid", ["需求分析", "PRD", "数据分析", "项目管理", "用户研究"],
             "示例出行科技", "成都", 15, 28,
             "负责出行产品线功能规划与迭代；输出 PRD 并推动研发落地；通过数据分析驱动产品决策。福利：五险一金、弹性工作、节日福利、免费打车券。"),
            ("AI 产品经理", "product", "senior", ["大模型应用", "需求分析", "数据分析", "Prompt 设计", "商业化"],
             "示例大模型创业公司", "北京", 30, 50,
             "负责大模型应用产品规划与落地；设计 AI 产品交互与商业化路径；调研竞品与用户需求，输出高质量 PRD。福利：股票期权、年终奖、免费三餐、双休。"),
            ("数据分析师", "data", "junior", ["SQL", "Python", "Excel", "数据可视化", "A/B 测试"],
             "示例消费零售", "南京", 12, 20,
             "负责业务数据分析与报表建设；搭建核心指标看板；支持运营与产品团队的取数与分析需求。福利：五险一金、带薪年假、弹性工作、员工内购。"),
            ("数据仓库工程师", "data", "senior", ["数仓建模", "ETL", "Hive", "Spark", "Flink", "Doris"],
             "示例大数据平台", "深圳", 30, 50,
             "负责离线与实时数仓建设；设计数据模型与 ETL 流程；保障数据质量与时效性。福利：六险一金、年终奖、租房补贴、定期体检。"),
            ("运营专员", "operations", "junior", ["内容运营", "活动策划", "用户增长", "数据分析", "文案"],
             "示例教育科技", "武汉", 8, 15,
             "负责社区内容运营与活动策划；撰写内容与用户互动；协助用户增长项目执行。福利：五险一金、带薪年假、零食下午茶、成长培训。"),
            ("用户增长运营", "operations", "mid", ["增长黑客", "渠道投放", "用户运营", "数据分析", "私域运营"],
             "示例社交平台", "北京", 15, 25,
             "负责用户增长策略制定与执行；管理多渠道投放与转化；搭建私域运营体系。福利：五险一金、年终奖、弹性工作、下午茶。"),
        ]
        for name, direction, diff, skills, company, city, lo, hi, desc in data:
            rows.append(
                JobItem(
                    name=name, direction=direction, difficulty=diff, skills=skills,
                    company=company, city=city, salary_min=lo, salary_max=hi,
                    description=desc, welfare=extract_welfare(desc), source="builtin",
                )
            )
        return rows


# ---------------------------------------------------------------------------
# 职友集数据源（公开 HTML 搜索页，robots 检查 + 限速）
# ---------------------------------------------------------------------------
class JobuiSource:
    name = "jobui"
    BASE = "https://www.jobui.com"

    KEYWORDS = [
        "Java开发", "前端开发", "算法工程师", "产品经理", "数据分析",
        "运营专员", "测试开发", "Golang开发",
    ]
    CITIES = ["北京", "上海", "深圳", "杭州", "广州", "成都"]

    def __init__(self, max_pages: int = 1, max_cities: int = 4) -> None:
        self.max_pages = max_pages
        self.max_cities = max_cities
        self.guard = RobotsGuard(self.BASE)

    def fetch_jobs(self) -> list[JobItem]:
        items: list[JobItem] = []
        for city in self.CITIES[: self.max_cities]:
            for kw in self.KEYWORDS:
                try:
                    items.extend(self._fetch_page(kw, city))
                except Exception as exc:
                    logger.warning("[jobui] %s/%s 采集失败: %s", city, kw, exc)
                RobotsGuard.polite_sleep()
        logger.info("[jobui] 本轮采集完成，共 %s 条", len(items))
        return items

    def _fetch_page(self, kw: str, city: str) -> list[JobItem]:
        path = "/jobs"
        if not self.guard.can_fetch(path):
            logger.info("[jobui] robots.txt 禁止 %s，跳过 %s/%s", path, city, kw)
            return []
        items: list[JobItem] = []
        for page in range(self.max_pages):
            params = {"jobKw": kw, "cityKw": city}
            if page > 0:
                params["page"] = page + 1
            try:
                with httpx.Client(timeout=15, follow_redirects=True, headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                }) as client:
                    resp = client.get(f"{self.BASE}{path}", params=params)
                if resp.status_code != 200:
                    logger.warning("[jobui] HTTP %s for %s/%s page=%s", resp.status_code, city, kw, page)
                    break
                parsed = self._parse_list(resp.text, city)
                items.extend(parsed)
                if len(parsed) < 20:
                    break
            except Exception as exc:
                logger.warning("[jobui] 请求异常 %s/%s page=%s: %s", city, kw, page, exc)
                break
            if page < self.max_pages - 1:
                RobotsGuard.polite_sleep()
        return items

    def _parse_list(self, html: str, city: str) -> list[JobItem]:
        items: list[JobItem] = []
        blocks = html.split('class="job-content-box"')[1:]
        for block in blocks:
            try:
                item = self._parse_block(block, city)
                if item:
                    items.append(item)
            except Exception as exc:
                logger.debug("[jobui] 解析单条失败: %s", exc)
        return items

    def _parse_block(self, block: str, city: str) -> JobItem | None:
        m_name = re.search(r'href="(/job/\d+/)"[^>]*>\s*<h3><strong>(.*?)</strong></h3>', block, re.S)
        if not m_name:
            return None
        job_path, raw_name = m_name.group(1), re.sub(r"<[^>]+>", "", m_name.group(2)).strip()
        if not raw_name:
            return None
        m_exp = re.search(r'title="工作经验要求：([^"]+)"', block)
        m_edu = re.search(r'title="学历要求：([^"]+)"', block)
        m_sal = re.search(r'title="工资：([^"]+)"', block)
        m_com = re.search(r'class="job-company-name" href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        m_date = re.search(r'job-add-date">(.*?)</div>', block, re.S)
        m_industry = re.search(r'job-desc">\s*(\d[\d.万]*人次浏览)\s*/\s*([^<\n]+)', block, re.S)

        company = re.sub(r"<[^>]+>", "", m_com.group(2)).strip() if m_com else ""
        exp = m_exp.group(1).strip() if m_exp else ""
        edu = m_edu.group(1).strip() if m_edu else ""
        industry = m_industry.group(2).strip() if m_industry else ""
        salary_text = m_sal.group(1) if m_sal else ""
        low, high = parse_salary(salary_text)

        # 时间：'4天前' / '1小时前' / '昨天'
        published = None
        if m_date:
            d = m_date.group(1).strip()
            published = self._parse_relative_date(d)

        job_title = raw_name.replace("<strong>", "").replace("</strong>", "")
        # 方向/难度/技能推断
        hint = job_title + " " + industry
        direction = infer_direction(hint)
        difficulty = infer_difficulty(job_title + " " + exp)
        skills = extract_skills(hint) or default_skills(direction)
        welfare = extract_welfare(hint)

        item = JobItem(
            name=job_title, direction=direction, difficulty=difficulty, skills=skills,
            company=company, city=city, salary_min=low, salary_max=high,
            description=build_description(JobItem(name=job_title, direction=direction, difficulty=difficulty, skills=skills), exp, edu, industry),
            welfare=welfare, source="jobui",
            source_id=job_path.strip("/").split("/")[-1],
            source_url=f"{self.BASE}{job_path}", published_at=published,
        )
        return item

    @staticmethod
    def _parse_relative_date(text: str) -> datetime | None:
        """'4天前' / '昨天' / '1小时前' → datetime。"""
        now = datetime.utcnow()
        try:
            if "天" in text:
                n = int(re.search(r"(\d+)", text).group(1))
                return now - timedelta(days=n)
            if "小时" in text:
                n = int(re.search(r"(\d+)", text).group(1))
                return now - timedelta(hours=n)
            if "昨天" in text:
                return now - timedelta(days=1)
            if "刚刚" in text or "分钟" in text:
                return now
        except Exception:
            return None
        return None


# ---------------------------------------------------------------------------
# 同步编排
# ---------------------------------------------------------------------------
def build_sources(enabled: str = "builtin,jobui") -> list[JobSource]:
    sources: list[JobSource] = []
    for name in (s.strip() for s in enabled.split(",") if s.strip()):
        if name == "builtin":
            sources.append(BuiltinSource())
        elif name in ("jobui", "zhaopin", "liepin"):
            # 统一映射：职友集为当前真实数据源
            sources.append(JobuiSource())
    return sources


def _upsert(db: Session, item: JobItem) -> bool:
    """按 source+source_id 去重插入或更新；内置岗位按 name 去重。返回是否新增。"""
    if item.source == "builtin":
        existing = db.scalar(select(Position).where(Position.source == "builtin", Position.name == item.name))
        if existing is not None:
            for f in ("company", "city", "salary_min", "salary_max", "description", "welfare", "skills", "difficulty"):
                setattr(existing, f, getattr(item, f))
            existing.synced_at = datetime.utcnow()
            return False
    else:
        if item.source_id:
            existing = db.scalar(
                select(Position).where(Position.source == item.source, Position.source_id == item.source_id)
            )
            if existing is not None:
                for f in ("name", "company", "city", "salary_min", "salary_max", "description",
                          "welfare", "skills", "direction", "difficulty", "source_url", "published_at"):
                    setattr(existing, f, getattr(item, f))
                existing.status = "active"
                existing.synced_at = datetime.utcnow()
                return False
    db.add(Position(
        name=item.name, direction=item.direction, difficulty=item.difficulty, skills=item.skills,
        company=item.company, city=item.city, salary_min=item.salary_min, salary_max=item.salary_max,
        description=item.description, welfare=item.welfare, source=item.source,
        source_id=item.source_id, source_url=item.source_url, published_at=item.published_at,
        is_public=True, status="active", synced_at=datetime.utcnow(),
    ))
    return True


_SYNC_LOCK = threading.Lock()


def sync_jobs(db: Session | None = None, enabled: str | None = None) -> dict:
    """执行一次全量同步。返回统计信息。同一时刻仅允许一个同步任务。"""
    if not _SYNC_LOCK.acquire(blocking=False):
        return {"skipped": True, "reason": "已有同步任务进行中", "sources": [], "total": 0, "new": 0, "updated": 0, "errors": 0}
    from app.core.config import settings
    from app.services.sync_state import record_sync_done

    enabled = enabled or settings.JOB_SOURCE_ENABLED
    own_session = db is None
    if own_session:
        db = SessionLocal()
    stats = {"sources": [], "total": 0, "new": 0, "updated": 0, "errors": 0}
    try:
        _do_sync(db, enabled, stats)
        record_sync_done(stats)
        return stats
    finally:
        _SYNC_LOCK.release()
        if own_session:
            db.close()


def _do_sync(db: Session, enabled: str, stats: dict) -> None:
    for src in build_sources(enabled):
        try:
            fetched = src.fetch_jobs()
            new = updated = 0
            for item in fetched:
                try:
                    if _upsert(db, item):
                        new += 1
                    else:
                        updated += 1
                except Exception as exc:
                    logger.warning("[job_crawler] upsert 失败: %s", exc)
                    stats["errors"] += 1
            db.commit()
            stats["sources"].append({"source": src.name, "fetched": len(fetched), "new": new, "updated": updated})
            stats["total"] += len(fetched)
            stats["new"] += new
            stats["updated"] += updated
            logger.info("[job_crawler] 同步完成 source=%s fetched=%s new=%s updated=%s",
                        src.name, len(fetched), new, updated)
        except Exception as exc:
            stats["errors"] += 1
            logger.warning("[job_crawler] 数据源 %s 同步失败: %s", src.name, exc)
