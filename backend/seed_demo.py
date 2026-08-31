"""演示数据脚本：一键生成可讲解全流程的演示账号与数据。

用法（在 backend/ 目录下）：
    python seed_demo.py

生成内容：
1. demo 用户（demo / demo123）
2. 6 个带真实字段（公司/城市/薪资/福利/描述）的演示岗位
3. 每个岗位 3-4 条已发布的题库原子
4. 一份 Java 后端演示简历 + 一条 JD 历史
5. demo 用户对其中 2 个岗位的收藏与投递状态

脚本幂等：已存在的数据会自动跳过，可重复执行。
"""
import os
import sys

_BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(_BASE)
sys.path.insert(0, _BASE)

from app.core.db import SessionLocal, init_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.job_track import JobApplication, JobFavorite  # noqa: E402
from app.models.position import KnowledgeAtom, Position  # noqa: E402
from app.models.resume import JobDescription, Resume  # noqa: E402
from app.models.user import User  # noqa: E402

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"

# ── 演示岗位数据（company/city/salary/welfare/description 均为真实招聘字段）──
POSITIONS = [
    {
        "name": "Java 后端开发工程师",
        "direction": "backend",
        "difficulty": "mid",
        "skills": ["Java", "Spring Boot", "MySQL", "Redis"],
        "company": "云启科技",
        "city": "北京",
        "salary_min": 25,
        "salary_max": 40,
        "description": "负责核心交易系统的服务端研发，参与高并发场景下的架构设计与性能优化，保障系统稳定性与扩展性。",
        "welfare": ["双休", "六险一金", "弹性工作", "免费三餐"],
    },
    {
        "name": "前端开发工程师",
        "direction": "frontend",
        "difficulty": "mid",
        "skills": ["Vue", "React", "TypeScript", "Webpack"],
        "company": "星图网络",
        "city": "上海",
        "salary_min": 20,
        "salary_max": 35,
        "description": "负责数据可视化平台的 Web 前端研发，参与组件库建设与性能优化，提升产品交互体验。",
        "welfare": ["双休", "五险一金", "年度体检", "零食下午茶"],
    },
    {
        "name": "算法工程师",
        "direction": "algorithm",
        "difficulty": "senior",
        "skills": ["Python", "PyTorch", "机器学习", "NLP"],
        "company": "智算引擎",
        "city": "深圳",
        "salary_min": 30,
        "salary_max": 50,
        "description": "负责大模型应用层的算法研发，包括 RAG 检索增强、Prompt 工程与效果评估，推动业务落地。",
        "welfare": ["双休", "六险一金", "股票期权", "健身房"],
    },
    {
        "name": "数据分析师",
        "direction": "data",
        "difficulty": "junior",
        "skills": ["SQL", "Python", "Tableau", "AB测试"],
        "company": "数维科技",
        "city": "杭州",
        "salary_min": 15,
        "salary_max": 28,
        "description": "负责业务指标体系建设与报表自动化，通过 A/B 实验与归因分析支持运营与产品决策。",
        "welfare": ["双休", "五险一金", "租房补贴", "弹性工作"],
    },
    {
        "name": "Go 后端开发工程师",
        "direction": "backend",
        "difficulty": "senior",
        "skills": ["Go", "gRPC", "Redis", "Kafka"],
        "company": "极光云",
        "city": "成都",
        "salary_min": 20,
        "salary_max": 38,
        "description": "负责云原生中间件研发，参与消息队列与分布式缓存的稳定性治理，支撑大规模微服务架构。",
        "welfare": ["双休", "六险一金", "大牛带队", "交通补贴"],
    },
    {
        "name": "产品经理",
        "direction": "product",
        "difficulty": "mid",
        "skills": ["需求分析", "Axure", "数据分析", "项目管理"],
        "company": "青禾科技",
        "city": "广州",
        "salary_min": 18,
        "salary_max": 32,
        "description": "负责 B 端 SaaS 产品的需求调研与版本规划，协调设计与研发推进项目按期交付。",
        "welfare": ["双休", "五险一金", "项目奖金", "带薪年假"],
    },
]

# ── 题库原子（每个岗位 3-4 题，状态为 published 可被面试/刷题使用）──
ATOMS = {
    "Java 后端开发工程师": [
        ("谈谈你对 Java 内存模型（JMM）的理解，以及 volatile 的作用",
         ["JMM 定义了线程与主内存的抽象关系", "volatile 保证可见性与有序性，不保证原子性", "可举例双重检查锁中 volatile 的应用"],
         ["Java", "JVM"], "mid"),
        ("Spring Boot 的自动配置原理是什么",
         ["@EnableAutoConfiguration 与 spring.factories / AutoConfiguration.imports", "条件注解 @Conditional 系列", "自定义 starter 的实现思路"],
         ["Java", "Spring Boot"], "mid"),
        ("MySQL 索引失效的常见场景有哪些",
         ["最左前缀原则被破坏", "对索引列使用函数或隐式类型转换", "like 以通配符开头", "or 连接非索引列"],
         ["MySQL"], "mid"),
    ],
    "前端开发工程师": [
        ("Vue 3 中 ref 与 reactive 的区别及使用场景",
         ["ref 处理基础类型与对象，reactive 仅对象", "ref 通过 .value 访问，模板中自动解包", "reactive 的响应式基于 Proxy"],
         ["Vue"], "mid"),
        ("浏览器从输入 URL 到页面渲染发生了什么",
         ["DNS 解析与 TCP 连接", "HTTP 请求与响应", "HTML 解析构建 DOM/CSSOM", "合成与绘制"],
         ["HTTP", "浏览器"], "mid"),
        ("谈谈你对 TypeScript 泛型的理解",
         ["泛型可在类型安全的前提下实现复用", "接口泛型、函数泛型与默认类型参数", "泛型约束 extends"],
         ["TypeScript"], "junior"),
    ],
    "算法工程师": [
        ("如何评估一个 RAG 系统的检索质量",
         ["召回率/精确率等检索指标", "生成答案与上下文的忠实度评估", "可结合命中率与人工评测"],
         ["RAG", "机器学习"], "senior"),
        ("Transformer 自注意力机制的时间复杂度及其优化",
         ["标准注意力 O(n^2) 的复杂度推导", "FlashAttention 的 IO 优化", "稀疏注意力/线性注意力的思路"],
         ["NLP", "机器学习"], "senior"),
        ("简述你做过的一个特征工程案例，如何提升模型效果",
         ["业务理解到特征抽象的链路", "缺失值/异常值处理", "离线与线上效果对比的验证方式"],
         ["机器学习"], "mid"),
    ],
    "数据分析师": [
        ("如何设计一个增长实验并判断显著性",
         ["明确假设与核心指标", "样本量计算与分流机制", "显著性检验与陷阱（多重比较等）"],
         ["AB测试"], "mid"),
        ("SQL 中窗口函数与 GROUP BY 的区别",
         ["窗口函数不改变行数，GROUP BY 会聚合", "PARTITION BY 与 ORDER BY 的配合", "常见场景：排名、累计、同环比"],
         ["SQL"], "junior"),
        ("业务指标下跌，你会如何分析归因",
         ["先确认口径与数据准确性", "维度拆解：时间/渠道/人群", "结合漏斗与相关性定位根因"],
         ["数据分析"], "mid"),
    ],
    "Go 后端开发工程师": [
        ("Go 的 goroutine 与 channel 是如何协作的",
         ["goroutine 的调度模型 GMP", "channel 的同步与通信语义", "select 多路复用与超时控制"],
         ["Go"], "senior"),
        ("gRPC 相比 HTTP/1.1 的优势是什么",
         ["基于 HTTP/2 多路复用", "Protocol Buffers 二进制序列化更高效", "自带流式通信与双向流"],
         ["Go", "gRPC"], "mid"),
        ("如何保证 Redis 缓存与数据库的一致性",
         ["Cache Aside 的删除策略", "先更新库再删缓存", "延迟双删与消息队列兜底"],
         ["Redis"], "mid"),
    ],
    "产品经理": [
        ("如何做用户需求优先级排序",
         ["结合产品目标与资源约束", "RICE / 四象限等常见方法", "数据验证与用户反馈闭环"],
         ["需求分析"], "mid"),
        ("新产品冷启动，你会如何设计增长策略",
         ["明确北极星指标", "种子用户获取与口碑传播", "渠道分层与转化漏斗优化"],
         ["项目管理"], "mid"),
        ("如何与研发团队高效协作避免需求返工",
         ["需求文档与验收标准对齐", "原型评审提前暴露问题", "小步迭代快速反馈"],
         ["需求分析"], "junior"),
    ],
}

# ── 演示简历（Java 后端，3 年经验）──
DEMO_RESUME = {
    "name": "张三 - Java 后端（3 年）",
    "raw_text": (
        "张三，本科，计算机科学与技术专业，3 年 Java 后端开发经验。\n"
        "技能：Java、Spring Boot、MySQL、Redis、Kafka、微服务。\n"
        "项目：主导电商订单系统重构，支撑双 11 峰值 5k QPS；优化慢查询 30+ 处，接口 P99 降低 40%。\n"
        "教育背景：XX 大学，计算机科学与技术，2019-2023。"
    ),
    "parsed_json": {
        "basic": {"name": "张三", "education": "本科", "major": "计算机科学与技术", "experience_years": 3},
        "skills": [
            {"name": "Java", "level": "advanced"},
            {"name": "Spring Boot", "level": "advanced"},
            {"name": "MySQL", "level": "advanced"},
            {"name": "Redis", "level": "intermediate"},
            {"name": "Kafka", "level": "intermediate"},
        ],
        "projects": [
            {"name": "电商订单系统重构", "desc": "主导核心链路重构，支撑 5k QPS，P99 降低 40%"}
        ],
    },
    "skills": ["Java", "Spring Boot", "MySQL", "Redis", "Kafka"],
}

DEMO_JD = {
    "title": "Java 后端开发工程师（3-5 年）",
    "content": (
        "岗位职责：\n1. 负责核心交易系统的服务端研发；\n"
        "2. 参与高并发场景下的架构设计与性能优化。\n"
        "任职要求：\n1. 本科及以上，3 年以上 Java 开发经验；\n"
        "2. 熟悉 Spring Boot、MySQL、Redis；\n"
        "3. 有高并发、分布式系统经验者优先。"
    ),
}


def seed(db):
    # 1. 演示用户
    user = db.query(User).filter(User.username == DEMO_USERNAME).first()
    if user is None:
        user = User(
            username=DEMO_USERNAME,
            password_hash=hash_password(DEMO_PASSWORD),
            email="demo@example.com",
            target_position="Java 后端开发工程师",
            years_of_exp=3,
        )
        db.add(user)
        db.flush()
        print(f"[ok] 创建演示用户：{DEMO_USERNAME} / {DEMO_PASSWORD}")
    else:
        print(f"[skip] 演示用户已存在：{DEMO_USERNAME}")

    # 2. 演示岗位 + 题库
    created_positions = []
    for p in POSITIONS:
        pos = (
            db.query(Position)
            .filter(Position.name == p["name"], Position.company == p["company"])
            .first()
        )
        if pos is None:
            pos = Position(
                name=p["name"],
                direction=p["direction"],
                difficulty=p["difficulty"],
                skills=p["skills"],
                is_public=True,
                status="active",
                company=p["company"],
                city=p["city"],
                salary_min=p["salary_min"],
                salary_max=p["salary_max"],
                description=p["description"],
                welfare=p["welfare"],
                source="builtin",
            )
            db.add(pos)
            db.flush()
            print(f"[ok] 创建岗位：{p['company']} · {p['name']}（{p['city']} {p['salary_min']}-{p['salary_max']}K）")
        else:
            print(f"[skip] 岗位已存在：{p['name']} @ {p['company']}")
        created_positions.append(pos)

        # 题库原子（已发布）
        for question, points, tags, difficulty in ATOMS.get(p["name"], []):
            exists = (
                db.query(KnowledgeAtom)
                .filter(KnowledgeAtom.position_id == pos.id, KnowledgeAtom.question == question)
                .first()
            )
            if exists is None:
                db.add(
                    KnowledgeAtom(
                        position_id=pos.id,
                        question=question,
                        reference_points=points,
                        tags=tags,
                        difficulty=difficulty,
                        status="published",
                    )
                )
                print(f"[ok] 创建题目：{question[:24]}…")
    db.flush()

    # 3. 演示简历 + JD
    resume = (
        db.query(Resume).filter(Resume.user_id == user.id, Resume.name == DEMO_RESUME["name"]).first()
    )
    if resume is None:
        resume = Resume(
            user_id=user.id,
            name=DEMO_RESUME["name"],
            raw_text=DEMO_RESUME["raw_text"],
            parsed_json=DEMO_RESUME["parsed_json"],
            skills=DEMO_RESUME["skills"],
        )
        db.add(resume)
        print("[ok] 创建演示简历")
    else:
        print("[skip] 演示简历已存在")

    jd = db.query(JobDescription).filter(JobDescription.user_id == user.id).first()
    if jd is None:
        db.add(JobDescription(user_id=user.id, title=DEMO_JD["title"], content=DEMO_JD["content"]))
        print("[ok] 创建演示 JD")
    else:
        print("[skip] 演示 JD 已存在")

    # 4. 收藏 + 投递（用前两个岗位演示闭环：岗位广场 → 收藏 → 备战计划 → 投递）
    if created_positions:
        favs = [created_positions[0], created_positions[1]]
        for pos in favs:
            if db.query(JobFavorite).filter_by(user_id=user.id, position_id=pos.id).first() is None:
                db.add(JobFavorite(user_id=user.id, position_id=pos.id))
                print(f"[ok] 收藏岗位：{pos.name}")
            else:
                print(f"[skip] 已收藏：{pos.name}")

        first = created_positions[0]
        if db.query(JobApplication).filter_by(user_id=user.id, position_id=first.id).first() is None:
            db.add(
                JobApplication(
                    user_id=user.id, position_id=first.id, status="interviewing", note="已进入技术一面"
                )
            )
            print(f"[ok] 投递岗位：{first.name}（面试中）")
        else:
            print("[skip] 投递记录已存在")

    db.commit()
    print("\n✅ 演示数据就绪。用 demo / demo123 登录体验。")


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
