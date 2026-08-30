# -*- coding: utf-8 -*-
"""技能词表：同义词规范、岗位类型标准技能集、技能规范与补全。

数据质量治理（方案③）的核心词表：
- SKILL_SYNONYMS：别名 → 规范标签（与题库管理页 TAG_SYNONYMS 同源，供技能规范）。
- ROLE_SKILLS：归一岗位名 → 该岗位类型的标准技能集（对齐内置岗位库 BUILTIN_POSITIONS）。
- _DIRECTION_FALLBACK：方向级兜底技能（无岗位类型命中时使用）。
"""
from __future__ import annotations


def canonical_key(skill: str) -> str:
    """规范化键：小写并去掉全部空白，用于同义词匹配。"""
    return "".join(str(skill).strip().lower().split())


# 技能同义词表：key 为规范化键（小写去空白），value 为规范标签。
SKILL_SYNONYMS = {
    "java": "Java",
    "jvm": "JVM",
    "spring": "Spring Boot",
    "springboot": "Spring Boot",
    "springmvc": "Spring MVC",
    "springcloud": "Spring Cloud",
    "mybatis": "MyBatis",
    "mysql": "MySQL",
    "sql": "SQL",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "redis": "Redis",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "kafka": "Kafka",
    "mq": "消息队列",
    "消息队列": "消息队列",
    "rabbitmq": "RabbitMQ",
    "python": "Python",
    "python3": "Python",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "golang": "Go",
    "go语言": "Go",
    "go": "Go",
    "c++": "C++",
    "c语言": "C++",
    "c#": "C#",
    "react": "React",
    "reactjs": "React",
    "vue": "Vue",
    "vuejs": "Vue",
    "vue2": "Vue",
    "vue3": "Vue",
    "angular": "Angular",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "html": "HTML/CSS",
    "css": "HTML/CSS",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "linux": "Linux",
    "git": "Git",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "spark": "Spark",
    "flink": "Flink",
    "hive": "Hive",
    "hadoop": "Hadoop",
    "etl": "ETL",
    "elasticsearch": "Elasticsearch",
    "es": "Elasticsearch",
    "nginx": "Nginx",
    "grpc": "gRPC",
    "jwt": "JWT",
    "http": "HTTP",
    "tcp": "TCP",
    "websocket": "WebSocket",
    "ab测试": "A/B 测试",
    "next.js": "Next.js",
    "设计模式": "设计模式",
    "高并发": "高并发",
    "并发": "高并发",
    "分布式": "分布式",
    "微服务": "微服务",
    "缓存": "缓存",
    "数据库": "数据库",
    "索引": "索引",
    "性能优化": "性能优化",
    "网络安全": "网络安全",
    "操作系统": "操作系统",
    "计算机网络": "计算机网络",
    "数据结构": "数据结构",
    "算法": "算法",
    "机器学习": "机器学习",
    "深度学习": "深度学习",
    "推荐系统": "推荐系统",
    "prompt": "Prompt 设计",
    "rag": "RAG",
    "大模型": "大模型应用",
    "llm": "大模型应用",
}

# 归一岗位名 → 标准技能集（对齐内置岗位库 BUILTIN_POSITIONS 的技能设计）
ROLE_SKILLS: dict[str, list[str]] = {
    "Java开发": ["Java", "Spring Boot", "MyBatis", "MySQL", "JVM", "微服务"],
    "Golang开发": ["Go", "gRPC", "Docker", "Kubernetes", "MySQL", "消息队列"],
    "前端开发": ["JavaScript", "TypeScript", "Vue", "React", "HTML/CSS", "工程化"],
    "前端架构": ["React", "架构设计", "微前端", "Node.js", "性能优化", "工程化"],
    "全栈开发": ["Vue", "React", "Node.js", "Go", "系统设计", "Docker"],
    "测试开发": ["pytest", "接口测试", "自动化测试", "Selenium", "Linux"],
    "算法": ["机器学习", "深度学习", "Python", "PyTorch", "数据结构", "数学基础"],
    "推荐算法": ["推荐系统", "召回排序", "特征工程", "A/B 测试", "Python"],
    "产品经理": ["需求分析", "PRD", "数据分析", "项目管理", "用户研究"],
    "AI产品经理": ["大模型应用", "需求分析", "数据分析", "Prompt 设计", "商业化"],
    "数据分析": ["SQL", "Python", "Excel", "数据可视化", "A/B 测试"],
    "数据仓库": ["数仓建模", "ETL", "Hive", "Spark", "Flink", "Doris"],
    "运营": ["内容运营", "活动策划", "用户增长", "数据分析", "文案"],
    "用户增长运营": ["增长黑客", "渠道投放", "用户运营", "数据分析", "私域运营"],
    "后端开发": ["Python", "Java", "MySQL", "Redis", "消息队列", "分布式"],
}

# 方向级兜底技能（岗位类型未命中时，按方向补全）
_DIRECTION_FALLBACK: dict[str, list[str]] = {
    "backend": ["Java", "Python", "MySQL", "Redis", "微服务", "分布式"],
    "frontend": ["JavaScript", "TypeScript", "Vue", "React", "HTML/CSS", "工程化"],
    "algorithm": ["机器学习", "深度学习", "Python", "PyTorch", "数据结构", "数学基础"],
    "product": ["需求分析", "PRD", "数据分析", "项目管理", "用户研究"],
    "operations": ["内容运营", "数据分析", "用户增长", "活动策划", "文案"],
    "data": ["SQL", "Python", "Excel", "数据可视化", "A/B 测试"],
    "tech": ["需求分析", "数据分析", "项目管理", "沟通协作"],
}


def canonicalize_skill(skill: str) -> str:
    """单技能规范化：别名 → 规范标签；无法识别时原样返回（去掉首尾空白）。"""
    return SKILL_SYNONYMS.get(canonical_key(skill), str(skill).strip())


def complete_skills(
    name: str,
    direction: str,
    skills: list[str],
    min_count: int = 3,
    max_count: int = 6,
) -> list[str]:
    """技能补全：技能稀疏（< min_count）时，按岗位类型标准技能集补齐（去重、不覆盖已有）。

    目的：让 skills 稀疏的真实岗位（如 Java 岗只有 [java]）也能命中题库标签，
    提升面试检索（position_scope / select_candidates 标签驱动召回）的质量。
    """
    if len(skills) >= min_count:
        return list(skills)
    from app.services.position_directions import normalize_position_name

    norm = normalize_position_name(name)
    base = ROLE_SKILLS.get(norm) or _DIRECTION_FALLBACK.get(direction)
    if not base:
        return list(skills)
    seen = {canonical_key(s) for s in skills}
    merged = list(skills)
    for s in base:
        if canonical_key(s) not in seen:
            merged.append(s)
    return merged[:max_count]
