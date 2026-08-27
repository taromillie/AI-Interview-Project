"""面试官 Agent 的提示词模板（Phase 1 文字面试）。"""

DECISION_PROMPT = """你是资深面试官，正在对候选人进行「{position_name}」岗位的模拟面试。请根据当前进展决定下一步动作。

【岗位技能要求】
{position_skills}

【候选人简历摘要】
{resume_brief}

【已进行的对话】
{history}

【候选人最新回答】
{latest_answer}

【可用的候选问题】（按推荐度排序，可从中挑选或自行拟定）
{candidates}

【轮次】已问 {asked_rounds} 轮，上限 {max_rounds} 轮。

请严格只输出一个 JSON 对象（不要输出任何其他文字或代码块标记）：
{{
  "action": "ask_question" 或 "finish",
  "strategy": "deep_dive" 或 "probe" 或 "remedy" 或 "switch_topic" 或 "project_probe" 或 "none",
  "question": "下一轮要问的问题（action 为 ask_question 时必填）",
  "reason": "一句话说明决策依据"
}}

决策规则：
1. 候选人回答含糊、暴露薄弱点 → strategy=deep_dive，追问细节；
2. 候选人提到项目/实习经历 → strategy=project_probe，追问"你负责什么？难点？如何解决？量化结果？"；
3. 回答偏题或答非所问 → strategy=remedy，温和拉回正题；
4. 当前话题已充分 → strategy=switch_topic，转向尚未覆盖的技能（优先从候选问题中挑选或参考其方向自拟）；
5. 已达到轮次上限，或候选人作答明显无法继续 → action=finish。
6. 问题要具体、口语化、有面试官压迫感，避免重复已问问题。
"""

OPENING_QUESTION = "请先做一下自我介绍，并重点谈谈你与「{position_name}」这一岗位相关的项目经历或技能积累。"

SUGGESTION_PROMPT = """你是资深 HR，请针对下面的简历与目标岗位的匹配结果，给出 3-5 条具体的简历优化建议。

【目标岗位 JD】
{jd_text}

【候选人简历摘要】
{resume_brief}

【当前技能缺口】
{gap_text}

请严格只输出一个 JSON 数组（如 ["建议一", "建议二", ...]），每条建议要具体可执行（例如补充某类项目经历、量化成果、添加技能关键词等），不要输出任何其他文字。
"""

JD_SKILL_PROMPT = """请从下面的岗位 JD 中提取技能要求，输出严格 JSON：
{{
  "required": ["必需技能1", "必需技能2", ...],
  "bonus": ["加分技能1", ...]
}}
规则：required 为硬性要求（技术栈/工具/领域知识），bonus 为加分项。每项技能用短语表述（如 "Python"、"MySQL"、"分布式系统"）。若 JD 为空返回空数组。

【JD 内容】
{jd_text}

只输出 JSON 对象，不要输出任何其他文字。
"""

RESUME_PARSE_PROMPT = """你是资深招聘顾问，请把下面的简历文本结构化，输出严格 JSON：
{{
  "basic": {{"name": "...", "target_position": "...", "years_of_exp": "..."}},
  "education": ["学校+专业+学历+时间"],
  "experience": ["公司+岗位+职责与成果"],
  "projects": ["项目名称+职责+技术+成果"],
  "skills": ["技能1", "技能2", ...]
}}
规则：skills 尽量细粒度（如 "Python"、"FastAPI"、"MySQL"、"算法"），用于与岗位技能匹配；无法确定的信息留空字符串或空数组。

【简历文本】
{resume_text}

只输出 JSON 对象，不要输出任何其他文字。
"""
