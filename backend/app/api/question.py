"""题库管理接口（知识原子 CRUD，ADMIN 发布）。"""
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.db import get_db
from app.models.position import KnowledgeAtom, Position
from app.models.user import User
from app.services.skill_catalog import SKILL_SYNONYMS as TAG_SYNONYMS

router = APIRouter(prefix="/questions", tags=["题库管理"])

# 内置岗位库（is_public=True，ADMIN 可维护；首次访问时自动初始化）
BUILTIN_POSITIONS = [
    {
        "name": "后端开发工程师",
        "direction": "backend",
        "difficulty": "mid",
        "skills": ["Python", "Java", "MySQL", "Redis", "消息队列", "分布式"],
    },
    {
        "name": "Java 开发工程师",
        "direction": "backend",
        "difficulty": "mid",
        "skills": ["Java", "Spring Boot", "MyBatis", "MySQL", "JVM", "微服务"],
    },
    {
        "name": "全栈开发工程师",
        "direction": "backend",
        "difficulty": "senior",
        "skills": ["Vue", "React", "Node.js", "Go", "系统设计", "Docker"],
    },
    {
        "name": "测试开发工程师",
        "direction": "backend",
        "difficulty": "junior",
        "skills": ["pytest", "接口测试", "自动化测试", "Selenium", "Linux"],
    },
    {
        "name": "前端开发工程师",
        "direction": "frontend",
        "difficulty": "mid",
        "skills": ["HTML/CSS", "JavaScript", "TypeScript", "Vue", "工程化", "性能优化"],
    },
    {
        "name": "前端架构工程师",
        "direction": "frontend",
        "difficulty": "senior",
        "skills": ["React", "架构设计", "微前端", "Node.js", "性能优化", "工程化"],
    },
    {
        "name": "算法工程师",
        "direction": "algorithm",
        "difficulty": "senior",
        "skills": ["机器学习", "深度学习", "Python", "PyTorch", "数据结构", "数学基础"],
    },
    {
        "name": "推荐算法工程师",
        "direction": "algorithm",
        "difficulty": "senior",
        "skills": ["推荐系统", "召回排序", "特征工程", "A/B 测试", "Python"],
    },
    {
        "name": "产品经理",
        "direction": "product",
        "difficulty": "mid",
        "skills": ["需求分析", "PRD", "数据分析", "项目管理", "用户研究"],
    },
    {
        "name": "AI 产品经理",
        "direction": "product",
        "difficulty": "senior",
        "skills": ["大模型应用", "需求分析", "数据分析", "Prompt 设计", "商业化"],
    },
    {
        "name": "数据分析师",
        "direction": "data",
        "difficulty": "junior",
        "skills": ["SQL", "Python", "Excel", "数据可视化", "A/B 测试"],
    },
    {
        "name": "数据仓库工程师",
        "direction": "data",
        "difficulty": "senior",
        "skills": ["数仓建模", "ETL", "Hive", "Spark", "Flink", "Doris"],
    },
    {
        "name": "运营专员",
        "direction": "operations",
        "difficulty": "junior",
        "skills": ["内容运营", "活动策划", "用户增长", "数据分析", "文案"],
    },
    {
        "name": "用户增长运营",
        "direction": "operations",
        "difficulty": "mid",
        "skills": ["增长黑客", "渠道投放", "用户运营", "数据分析", "私域运营"],
    },
]


# 内置示例题库（status=published，随内置岗位初始化注入；幂等，岗位已有题目则跳过）。
# key 为 BUILTIN_POSITIONS 中的岗位名。
BUILTIN_ATOMS = {
    "后端开发工程师": [
        {
            "question": "请说明 Python 中 GIL 是什么，对多线程程序有什么影响？",
            "reference_points": [
                "GIL 是全局解释器锁，同一时刻仅允许一个线程执行字节码",
                "CPU 密集型任务受 GIL 限制难以并行，IO 密集型可用多线程",
                "可改用多进程、asyncio 或释放 GIL 的 C 扩展来规避",
            ],
            "tags": ["Python", "GIL", "多线程"],
            "difficulty": "mid",
        },
        {
            "question": "MySQL 索引失效的常见场景有哪些？如何排查？",
            "reference_points": [
                "对索引列使用函数、隐式类型转换或前导模糊查询会导致失效",
                "联合索引不满足最左前缀原则时部分失效",
                "通过 EXPLAIN 查看 type/key 判断是否走索引",
            ],
            "tags": ["MySQL", "索引"],
            "difficulty": "mid",
        },
        {
            "question": "Redis 缓存穿透、击穿、雪崩分别是什么？如何解决？",
            "reference_points": [
                "穿透：查询不存在数据，用布隆过滤器或缓存空值",
                "击穿：热点 key 过期瞬间高并发，用互斥锁或逻辑过期",
                "雪崩：大量 key 同时过期，过期时间加随机值或集群降级",
            ],
            "tags": ["Redis", "缓存"],
            "difficulty": "mid",
        },
    ],
    "Java 开发工程师": [
        {
            "question": "JVM 内存区域如何划分？垃圾回收的主要算法有哪些？",
            "reference_points": [
                "堆、虚拟机栈、本地方法栈、方法区、程序计数器",
                "标记-清除、标记-复制、标记-整理三种基础算法",
                "分代收集：新生代复制算法、老年代标记-整理",
            ],
            "tags": ["JVM", "垃圾回收"],
            "difficulty": "mid",
        },
        {
            "question": "Spring Boot 的自动配置原理是什么？",
            "reference_points": [
                "基于 @EnableAutoConfiguration 与 META-INF/spring.factories",
                "通过条件注解（@ConditionalOnClass 等）按需装配 Bean",
                "用户自定义配置优先于自动配置",
            ],
            "tags": ["Spring Boot", "自动配置"],
            "difficulty": "mid",
        },
        {
            "question": "如何设计一个幂等的下单接口？",
            "reference_points": [
                "客户端生成唯一请求 ID，服务端以该 ID 做去重",
                "数据库唯一约束 + 事务保证只写入一次",
                "重复请求直接返回首次结果，避免重复扣款",
            ],
            "tags": ["Java", "分布式", "接口设计"],
            "difficulty": "senior",
        },
    ],
    "全栈开发工程师": [
        {
            "question": "从输入 URL 到页面渲染完成，中间经历了哪些过程？",
            "reference_points": [
                "DNS 解析、TCP 建连、TLS 握手、HTTP 请求",
                "服务端处理与响应，浏览器解析 HTML/CSS/JS",
                "构建 DOM/CSSOM、合成渲染树、布局与绘制",
            ],
            "tags": ["浏览器", "网络", "渲染"],
            "difficulty": "mid",
        },
        {
            "question": "前后端如何做接口鉴权？JWT 与 Session 方案如何选择？",
            "reference_points": [
                "Session 服务端存储、JWT 无状态自包含",
                "JWT 适合分布式与移动端，注意过期与注销问题",
                "敏感场景可结合刷新令牌与黑名单机制",
            ],
            "tags": ["鉴权", "JWT", "系统设计"],
            "difficulty": "mid",
        },
        {
            "question": "你会如何设计一个支持高并发的短链接服务？",
            "reference_points": [
                "发号器生成短码，Redis 缓存热点映射降低 DB 压力",
                "读写分离 + 缓存过期与预热策略",
                "重定向 302/301 的选择与监控埋点",
            ],
            "tags": ["系统设计", "Go", "Redis"],
            "difficulty": "senior",
        },
    ],
    "测试开发工程师": [
        {
            "question": "如何设计一份接口自动化测试用例？覆盖率如何衡量？",
            "reference_points": [
                "按接口、参数、异常与边界设计用例矩阵",
                "结合 pytest + requests 组织用例与断言",
                "用代码覆盖率和接口覆盖率共同评估",
            ],
            "tags": ["接口测试", "pytest"],
            "difficulty": "mid",
        },
        {
            "question": "App 兼容性测试需要考虑哪些维度？",
            "reference_points": [
                "系统版本、屏幕尺寸与分辨率、厂商定制 ROM",
                "网络环境：弱网、断网、切换网络",
                "通过真机云测与自动化框架组合覆盖",
            ],
            "tags": ["兼容性测试", "移动端"],
            "difficulty": "junior",
        },
        {
            "question": "如何让 UI 自动化测试用例稳定不 flaky？",
            "reference_points": [
                "使用显式等待替代固定 sleep",
                "测试数据与用例隔离，避免相互依赖",
                "失败自动重试与截图留证辅助定位",
            ],
            "tags": ["Selenium", "自动化测试"],
            "difficulty": "mid",
        },
    ],
    "前端开发工程师": [
        {
            "question": "Vue 的响应式原理是什么？ref 和 reactive 有何区别？",
            "reference_points": [
                "Vue3 基于 Proxy 拦截读写，收集依赖并触发更新",
                "ref 用于基本类型与对象，reactive 仅支持对象",
                "模板编译后依赖 track 与 trigger 驱动视图更新",
            ],
            "tags": ["Vue", "响应式"],
            "difficulty": "mid",
        },
        {
            "question": "JavaScript 的事件循环机制是怎样的？宏任务和微任务有何区别？",
            "reference_points": [
                "单线程模型，同步任务先执行，异步进入任务队列",
                "微任务优先于宏任务执行，如 Promise.then 先于 setTimeout",
                "浏览器每轮事件循环先清空微任务队列再取一个宏任务",
            ],
            "tags": ["JavaScript", "事件循环"],
            "difficulty": "mid",
        },
        {
            "question": "首屏性能优化有哪些手段？如何量化收益？",
            "reference_points": [
                "代码分割、按需加载、CDN 与资源压缩",
                "图片懒加载、骨架屏、减少重排重绘",
                "用 Lighthouse 的 FCP/LCP 指标对比优化前后",
            ],
            "tags": ["性能优化", "工程化"],
            "difficulty": "mid",
        },
    ],
    "前端架构工程师": [
        {
            "question": "微前端方案的几种实现方式与适用场景是什么？",
            "reference_points": [
                "iframe、single-spa 路由劫持、module federation",
                "按团队自治、技术栈隔离、渐进迁移等诉求选择",
                "关注应用间通信、样式隔离与公共依赖管理",
            ],
            "tags": ["微前端", "架构设计"],
            "difficulty": "senior",
        },
        {
            "question": "如何设计一套可维护的前端组件规范与设计系统？",
            "reference_points": [
                "分层：基础组件、业务组件、页面模板",
                "用设计令牌统一颜色、字号、间距",
                "文档沉淀 + 视觉回归测试保障一致性",
            ],
            "tags": ["组件设计", "设计系统"],
            "difficulty": "senior",
        },
        {
            "question": "大型 React 应用中如何做状态管理？何时引入 Redux？",
            "reference_points": [
                "优先本地状态与 Context，避免过度全局化",
                "跨模块共享、缓存、复杂派生数据再考虑 Redux/Zustand",
                "配合 selector 做精细化订阅避免无效渲染",
            ],
            "tags": ["React", "状态管理"],
            "difficulty": "mid",
        },
    ],
    "算法工程师": [
        {
            "question": "训练集与测试集分布不一致时如何处理？",
            "reference_points": [
                "通过分布统计与可视化定位偏移来源",
                "数据增强、重采样、域自适应等缓解手段",
                "线上指标验证与持续监控防漂移",
            ],
            "tags": ["机器学习", "数据分布"],
            "difficulty": "senior",
        },
        {
            "question": "请解释梯度消失问题及常用缓解手段。",
            "reference_points": [
                "深层网络反向传播梯度连乘导致消失",
                "ReLU 等激活函数与残差连接缓解",
                "BatchNorm、合理初始化与梯度裁剪",
            ],
            "tags": ["深度学习", "神经网络"],
            "difficulty": "mid",
        },
        {
            "question": "如何判断一个模型是否过拟合？如何降低过拟合？",
            "reference_points": [
                "训练集与验证集指标差距显著扩大即过拟合",
                "正则化、Dropout、早停、数据增强",
                "减少模型容量与特征维度",
            ],
            "tags": ["机器学习", "过拟合"],
            "difficulty": "mid",
        },
    ],
    "推荐算法工程师": [
        {
            "question": "推荐系统冷启动问题如何解决？",
            "reference_points": [
                "用户冷启动：用注册信息、热门内容与探索策略",
                "物品冷启动：内容特征 + 相似物品联动推荐",
                "利用多臂老虎机等在线探索平衡收益",
            ],
            "tags": ["推荐系统", "冷启动"],
            "difficulty": "senior",
        },
        {
            "question": "召回与排序阶段各有什么常见算法？",
            "reference_points": [
                "召回：协同过滤、双塔向量、规则与热门兜底",
                "排序：LR/GBDT、DeepFM 等 CTR 模型",
                "重排：多样性、打散与商业规则约束",
            ],
            "tags": ["推荐系统", "召回排序"],
            "difficulty": "senior",
        },
        {
            "question": "如何设计并评估一个 A/B 实验？",
            "reference_points": [
                "明确假设、指标与样本量计算",
                "随机分流保证组间无显著差异",
                "关注显著性检验与长期效果跟踪",
            ],
            "tags": ["A/B 测试", "数据分析"],
            "difficulty": "mid",
        },
    ],
    "产品经理": [
        {
            "question": "如何从用户反馈中提炼真实需求并排优先级？",
            "reference_points": [
                "区分真实诉求与表面抱怨，访谈还原使用场景",
                "用 RICE 或 KANO 模型量化影响与成本",
                "需求池管理并与业务目标对齐",
            ],
            "tags": ["需求分析", "优先级"],
            "difficulty": "mid",
        },
        {
            "question": "写 PRD 时如何把需求描述得清晰可执行？",
            "reference_points": [
                "包含背景、目标、用户故事与验收标准",
                "用流程图、原型与边界用例覆盖异常场景",
                "明确版本范围与上线指标",
            ],
            "tags": ["PRD", "文档"],
            "difficulty": "junior",
        },
        {
            "question": "一个功能上线后数据不达预期，你会怎么排查？",
            "reference_points": [
                "先确认数据口径与埋点是否准确",
                "拆解漏斗定位流失环节，结合用户反馈归因",
                "输出假设并设计下一个迭代实验验证",
            ],
            "tags": ["数据分析", "复盘"],
            "difficulty": "mid",
        },
    ],
    "AI 产品经理": [
        {
            "question": "如何评估一个大模型应用场景是否值得落地？",
            "reference_points": [
                "确认任务是否适合 LLM 且价值明确",
                "评估数据质量、成本、延迟与合规风险",
                "通过小范围试点指标验证后再规模化",
            ],
            "tags": ["大模型应用", "商业化"],
            "difficulty": "senior",
        },
        {
            "question": "Prompt 设计有哪些常见技巧？如何评测效果？",
            "reference_points": [
                "明确角色、任务、约束与输出格式",
                "Few-shot 示例与思维链提升复杂任务表现",
                "建立评测集与指标持续回归对比",
            ],
            "tags": ["Prompt 设计", "评测"],
            "difficulty": "mid",
        },
        {
            "question": "RAG 方案中检索质量差如何优化？",
            "reference_points": [
                "优化切分策略与元数据过滤",
                "混合检索、重排序提升召回精度",
                "引入查询改写与结果后处理",
            ],
            "tags": ["RAG", "大模型应用"],
            "difficulty": "senior",
        },
    ],
    "数据分析师": [
        {
            "question": "SQL 中窗口函数的作用是什么？举例说明。",
            "reference_points": [
                "在结果集内按分区排序计算排名、累计值等",
                "ROW_NUMBER、RANK、SUM OVER 等常见用法",
                "适合分组 TopN、同比环比等分析场景",
            ],
            "tags": ["SQL", "窗口函数"],
            "difficulty": "mid",
        },
        {
            "question": "如何评估一个 A/B 实验的显著性与可信度？",
            "reference_points": [
                "明确原假设与核心指标，预先计算样本量",
                "关注 p 值与置信区间，警惕多重比较",
                "检查分组均衡与实验期间环境变化",
            ],
            "tags": ["A/B 测试", "统计分析"],
            "difficulty": "mid",
        },
        {
            "question": "一份分析报告如何做到让业务方真正落地行动？",
            "reference_points": [
                "结论先行，用数据讲故事并给出可执行建议",
                "可视化突出重点，避免信息过载",
                "与业务方对齐指标口径并跟踪落地效果",
            ],
            "tags": ["数据可视化", "报告"],
            "difficulty": "junior",
        },
    ],
    "数据仓库工程师": [
        {
            "question": "数仓建模中星型模型与雪花模型如何选择？",
            "reference_points": [
                "星型模型表结构简单、查询性能好",
                "雪花模型规范化程度高、冗余少但关联多",
                "大多数场景优先星型，必要时适度冗余",
            ],
            "tags": ["数仓建模", "维度建模"],
            "difficulty": "senior",
        },
        {
            "question": "如何处理数据同步中的脏数据与重复数据？",
            "reference_points": [
                "同步前做完整性校验与格式清洗",
                "按业务主键去重并保留最新记录",
                "异常数据落库标记并监控告警",
            ],
            "tags": ["ETL", "数据质量"],
            "difficulty": "mid",
        },
        {
            "question": "离线数仓与实时数仓如何协同？",
            "reference_points": [
                "离线处理批量高延迟场景，实时处理时效性场景",
                "统一指标体系与口径，避免两套数据打架",
                "基于 Lambda/Kappa 架构权衡复杂度与成本",
            ],
            "tags": ["Hive", "Spark", "Flink"],
            "difficulty": "senior",
        },
    ],
    "运营专员": [
        {
            "question": "如何策划一场拉新活动并评估效果？",
            "reference_points": [
                "明确目标人群、激励设计与传播链路",
                "设定活动北极星指标与过程指标",
                "复盘投入产出比与留存质量",
            ],
            "tags": ["活动策划", "用户增长"],
            "difficulty": "junior",
        },
        {
            "question": "内容运营如何判断选题是否有效？",
            "reference_points": [
                "结合用户画像与搜索热词预判需求",
                "用阅读、互动、转化等指标验证选题",
                "建立选题库与数据反馈循环持续优化",
            ],
            "tags": ["内容运营", "数据分析"],
            "difficulty": "junior",
        },
        {
            "question": "用户复购率持续下滑，你会从哪些维度排查？",
            "reference_points": [
                "按用户分层与生命周期拆解流失群体",
                "检查商品、价格、体验与服务链路变化",
                "结合调研与竞品对比制定挽回策略",
            ],
            "tags": ["用户运营", "数据分析"],
            "difficulty": "mid",
        },
    ],
    "用户增长运营": [
        {
            "question": "如何搭建一个用户的增长漏斗并定位流失环节？",
            "reference_points": [
                "定义从曝光到转化的关键节点与指标",
                "分渠道、分人群对比漏斗转化率",
                "针对瓶颈环节设计实验并验证",
            ],
            "tags": ["增长黑客", "漏斗分析"],
            "difficulty": "mid",
        },
        {
            "question": "渠道投放如何做归因与预算分配？",
            "reference_points": [
                "按渠道建立统一归因口径（首触/末触/线性）",
                "用 LTV/CAC 对比渠道质量而非只看获客量",
                "结合边际效应动态调整预算",
            ],
            "tags": ["渠道投放", "数据分析"],
            "difficulty": "mid",
        },
        {
            "question": "私域运营的核心指标有哪些？如何提升转化？",
            "reference_points": [
                "关注好友通过率、活跃率与转化率",
                "通过分层运营与 SOP 触达提升粘性",
                "用内容与权益设计缩短转化路径",
            ],
            "tags": ["私域运营", "用户运营"],
            "difficulty": "mid",
        },
    ],
}


def _norm(s: str) -> str:
    """规范化：小写并去掉全部空白，用于同义词/子串匹配。"""
    return "".join(str(s).lower().split())


def _atom_matches(atom: KnowledgeAtom, kw_norm: str) -> bool:
    """宽松匹配：题面/参考要点/标签包含关键词，或标签命中同义词表。"""
    if kw_norm in _norm(atom.question):
        return True
    for rp in atom.reference_points or []:
        if kw_norm in _norm(rp):
            return True
    for t in atom.tags or []:
        tn = _norm(t)
        if kw_norm == tn or kw_norm in tn:
            return True
        canon = TAG_SYNONYMS.get(tn, tn)
        if kw_norm == canon or kw_norm in canon or canon in kw_norm:
            return True
    return False


def _atom_has_tag(atom: KnowledgeAtom, tag_norm: str) -> bool:
    """标签参数过滤：规范化精确匹配标签或其同义词。"""
    for t in atom.tags or []:
        tn = _norm(t)
        if tag_norm == tn or tag_norm == TAG_SYNONYMS.get(tn, tn):
            return True
    return False


def _seed_builtin_positions(db: Session) -> None:
    """确保内置示例岗位存在（幂等），并连带注入内置示例题库。

    内置岗位（BUILTIN_POSITIONS）作为开箱即用的公共示例岗位按 name 幂等创建，
    与 jobui 等真实岗位共存，用户可随时归档；首次创建后为其注入示例题库。
    """
    names = {row[0] for row in db.execute(select(Position.name)).all()}
    created = False
    for item in BUILTIN_POSITIONS:
        if item["name"] not in names:
            db.add(Position(is_public=True, creator_id=None, **item))
            created = True
    if created:
        db.commit()
    _seed_builtin_atoms(db)


def _seed_builtin_atoms(db: Session) -> None:
    """为内置岗位注入示例题库（published，幂等）。

    仅当某内置岗位当前没有任何题目时才注入，不覆盖、不重复用户已维护的题目。
    """
    for name, items in BUILTIN_ATOMS.items():
        pos = db.scalar(select(Position).where(Position.name == name).limit(1))
        if pos is None:
            continue
        has_atom = db.scalar(
            select(KnowledgeAtom.id).where(KnowledgeAtom.position_id == pos.id).limit(1)
        )
        if has_atom is not None:
            continue
        for item in items:
            db.add(
                KnowledgeAtom(
                    position_id=pos.id,
                    question=item["question"],
                    reference_points=item["reference_points"],
                    tags=item["tags"],
                    difficulty=item["difficulty"],
                    status="published",
                    created_by=None,
                )
            )
    db.commit()


@router.get("")
def list_atoms(
    position_id: int | None = None,
    status: str | None = Query(default=None, pattern="^(draft|published|archived)$"),
    keyword: str | None = None,
    tag: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """题库列表：管理员可见全部；普通用户仅可见已发布公共题 + 本人草稿。

    - position_id：展示该岗位直属题目 + 该岗位技能标签命中的题目（标签驱动筛选，
      使 skills 稀疏的真实岗位也能筛出相关题目）。
    - keyword：宽松匹配（题面/参考要点/标签包含，含技能同义词归一，如 java→Java）。
    - tag：规范化精确匹配标签或其同义词。
    """
    _seed_builtin_positions(db)
    stmt = select(KnowledgeAtom)
    if position_id:
        pos = db.get(Position, position_id)
        if pos is not None and (pos.skills or []):
            skill_conds = [
                func.cast(KnowledgeAtom.tags, String).like(f'%"{skill}"%')
                for skill in pos.skills
                if str(skill).strip()
            ]
            if skill_conds:
                stmt = stmt.where(
                    or_(KnowledgeAtom.position_id == position_id, *skill_conds)
                )
            else:
                stmt = stmt.where(KnowledgeAtom.position_id == position_id)
        else:
            stmt = stmt.where(KnowledgeAtom.position_id == position_id)
    if user.role == "admin":
        if status:
            stmt = stmt.where(KnowledgeAtom.status == status)
        atoms = list(db.scalars(stmt).all())
    elif status == "draft":
        stmt = stmt.where(
            KnowledgeAtom.status == "draft",
            KnowledgeAtom.created_by == user.id,
        )
        atoms = list(db.scalars(stmt).all())
    elif status == "archived":
        stmt = stmt.where(
            KnowledgeAtom.status == "archived",
            KnowledgeAtom.created_by == user.id,
        )
        atoms = list(db.scalars(stmt).all())
    else:
        stmt = stmt.where(
            or_(
                KnowledgeAtom.status == "published",
                and_(KnowledgeAtom.status == "draft", KnowledgeAtom.created_by == user.id),
            )
        )
        atoms = list(db.scalars(stmt).all())
    if tag:
        tag_norm = _norm(tag)
        atoms = [a for a in atoms if _atom_has_tag(a, tag_norm)]
    if keyword:
        kw_norm = _norm(keyword)
        atoms = [a for a in atoms if _atom_matches(a, kw_norm)]
    return atoms


@router.get("/positions")
def list_positions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """岗位列表：内置岗位库为空时自动初始化。"""
    _seed_builtin_positions(db)
    return db.scalars(select(Position).where(Position.status == "active").order_by(Position.id)).all()


@router.get("/positions/directions")
def list_position_directions(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """岗位方向聚合（岗位广场两级视图的方向卡）。

    把岗位列表按「归一岗位名」聚合成方向卡：方向名 + 公司数 + Top 技能 +
    平均薪资 + 该方向岗位列表。归一逻辑见 services/position_directions。
    """
    from app.services.position_directions import build_directions

    _seed_builtin_positions(db)
    positions = db.scalars(
        select(Position).where(Position.status == "active").order_by(Position.id)
    ).all()
    return build_directions(positions)


class ImportRequest(BaseModel):
    position_id: int
    format: str = "auto"  # auto / json / markdown
    text: str


@router.post("/import", status_code=201)
def import_atoms_api(
    payload: ImportRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量导入题目（JSON / Markdown，自动识别或显式指定）。

    结果：created 新建条数；skipped 同岗位重复跳过；errors 逐行错误明细。
    """
    from app.services.question_import import import_atoms, parse_auto, parse_json, parse_markdown

    try:
        if payload.format == "json":
            items = parse_json(payload.text)
        elif payload.format == "markdown":
            items = parse_markdown(payload.text)
        else:
            items = parse_auto(payload.text)
        result = import_atoms(db, user, payload.position_id, items)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=f"解析失败：{exc}")
    return result


@router.post("/positions/sync")
def trigger_position_sync(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """手动触发一次岗位采集同步（真实数据源）。"""
    from app.services.job_crawler import sync_jobs

    stats = sync_jobs(db=db)
    if stats.get("skipped"):
        return {"ok": False, "reason": stats.get("reason", "已有同步任务进行中"), "stats": stats}
    return {"ok": True, "stats": stats}


@router.get("/positions/sync-config")
def get_sync_config(user: User = Depends(get_current_user)):
    """获取岗位自动同步配置与最近同步时间。"""
    from app.services.sync_state import get_sync_state

    return get_sync_state()


@router.post("/positions/sync-config")
def set_sync_config(
    auto_enabled: bool | None = None,
    interval_minutes: int | None = None,
    user: User = Depends(get_current_user),
):
    """调整岗位自动同步频率（分钟）。interval_minutes 最短 5 分钟。"""
    from app.services.sync_state import update_sync_config

    return update_sync_config(auto_enabled=auto_enabled, interval_minutes=interval_minutes)


class GenerateRequest(BaseModel):
    topic: str
    position_id: int | None = None
    count: int = 3


class GeneratedAtomItem(BaseModel):
    question: str
    reference_points: list[str] = []
    tags: list[str] = []
    difficulty: str = "mid"


class SaveGeneratedRequest(BaseModel):
    position_id: int
    items: list[GeneratedAtomItem]


def _extract_json_array(text: str) -> list:
    """从 LLM 输出中提取 JSON 数组（容忍 markdown 代码块与前后杂质文本）。"""
    s = str(text or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:]
    start = s.find("[")
    end = s.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        data = json.loads(s[start : end + 1])
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


@router.post("/generate", status_code=200)
async def generate_atoms(
    payload: GenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """AI 一键生成题目（仅预览，不入库）：输入知识点/薄弱点，LLM 出题。

    需先在「模型配置」页配置并启用 LLM；生成结果可编辑后调 /generate/save 入库。
    """
    from app.llm.base import ChatMessage
    from app.services.llm_utils import require_llm

    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="请填写要生成的知识点")
    count = max(1, min(payload.count, 5))
    llm = require_llm(db, user)

    position_hint = ""
    if payload.position_id:
        pos = db.get(Position, payload.position_id)
        if pos is not None:
            skills = "、".join(pos.skills or [])
            position_hint = f"目标岗位：{pos.name}。"
            if skills:
                position_hint += f"该岗位关键技能：{skills}，题目应尽量贴合这些技能。"

    prompt = (
        "你是一名资深技术面试官，负责为候选人准备面试题库。\n"
        f"请围绕知识点「{topic}」生成 {count} 道高质量面试题。\n"
        f"{position_hint}\n"
        "要求：\n"
        "1. 题目覆盖「概念理解、场景应用、深挖追问」等层次，题干具体、可独立回答（20~60 字）。\n"
        "2. 每题包含字段：question（题干）、reference_points（3~5 个面试官追问/评分要点）、"
        "tags（2~4 个技能标签，第一个标签必须是最贴合该知识点的名称）、"
        "difficulty（junior/mid/senior 三选一）。\n"
        "3. 只输出一个 JSON 数组，不要 markdown 代码块、不要任何解释。格式示例：\n"
        '[{"question":"...","reference_points":["...","..."],"tags":["..."],"difficulty":"mid"}]'
    )
    resp = await llm.achat(
        [
            ChatMessage("system", "你只输出合法 JSON 数组，不输出任何多余文字。"),
            ChatMessage("user", prompt),
        ],
        temperature=0.6,
        max_tokens=3000,
    )
    items = _extract_json_array(resp)
    valid = []
    for it in items:
        if not isinstance(it, dict) or not str(it.get("question", "")).strip():
            continue
        valid.append(
            GeneratedAtomItem(
                question=str(it["question"]).strip(),
                reference_points=[
                    str(x).strip() for x in (it.get("reference_points") or []) if str(x).strip()
                ],
                tags=[str(x).strip() for x in (it.get("tags") or []) if str(x).strip()],
                difficulty=(
                    it["difficulty"]
                    if it.get("difficulty") in ("junior", "mid", "senior")
                    else "mid"
                ),
            )
        )
    if not valid:
        raise HTTPException(status_code=502, detail="AI 返回内容无法解析，请重试")
    return {"items": valid}


@router.post("/generate/save", status_code=201)
def save_generated_atoms(
    payload: SaveGeneratedRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """将 AI 生成的题目批量保存为私有草稿。"""
    position = db.get(Position, payload.position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    created = []
    for item in payload.items:
        question = item.question.strip()
        if not question:
            continue
        atom = KnowledgeAtom(
            position_id=payload.position_id,
            question=question,
            reference_points=item.reference_points,
            tags=item.tags,
            difficulty=item.difficulty,
            status="draft",
            created_by=user.id,
        )
        db.add(atom)
        created.append(atom)
    db.commit()
    for a in created:
        db.refresh(a)
    return {"count": len(created), "created": created}


@router.post("", status_code=201)
def create_atom(
    position_id: int,
    question: str,
    reference_points: list[str] | None = None,
    tags: list[str] | None = None,
    difficulty: str = "mid",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = db.get(Position, position_id)
    if position is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    atom = KnowledgeAtom(
        position_id=position_id,
        question=question,
        reference_points=reference_points or [],
        tags=tags or [],
        difficulty=difficulty,
        status="draft",
        created_by=user.id,
    )
    db.add(atom)
    db.commit()
    db.refresh(atom)
    return atom


@router.post("/{atom_id}/publish")
def publish_atom(
    atom_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """仅管理员可发布知识原子（约束：仅 published 进入面试追问链路）。"""
    atom = db.get(KnowledgeAtom, atom_id)
    if atom is None:
        raise HTTPException(status_code=404, detail="知识原子不存在")
    atom.status = "published"
    db.commit()
    db.refresh(atom)
    return atom
