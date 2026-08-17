# 上游与先例

## 上游来源

- 上游项目：[w95/awesome-claude-corporate-skills](https://github.com/w95/awesome-claude-corporate-skills)
- 上游 Skill：[03-human-resources/employee-engagement-survey](https://github.com/w95/awesome-claude-corporate-skills/tree/78dbc7c719920610d5b1c60bd13d9bb52d711c7a/03-human-resources/employee-engagement-survey)
- 固定版本：`78dbc7c719920610d5b1c60bd13d9bb52d711c7a`
- 上游许可证：MIT
- 核验时间：2026-08-17（Asia/Shanghai）

## 保留与扩展

上游 Skill 的核心是敬业度调研的完整方法论：调研设计、题目原则、回收率、数据分析、行动计划、结果沟通和脉冲调研。本包保留这套闭环思路，并做了实质扩展：

- **五套经典权威维度模板**（Q12 / 敬业度×员工体验 / eNPS / 归属与包容 / 心理安全感与团队协作），供用户按目的选型，而不是照搬一份美式问卷。
- **中文语境重写**：题目、量表、沟通模板、行动计划全部按中国职场语境改写，不是逐字翻译。
- **飞书深度集成**：从维度模板自动生成飞书问卷（字段与题目）、匿名收集、Base 服务端聚合分析、趋势看板搭建的完整命令契约。
- **本地脚本**：问卷生成器（多格式输出）、聚合结果分析器（同比、优势短板、分组差异、开放题主题）。
- **匿名硬约束**：不采集个人标识、粗粒度分组、小样本抑制（默认阈值 5）、拒绝含个人标识的输入、只聚合不检索个人。
- **假数据回放与单元测试**：11 项测试覆盖模板渲染、分批、PII 拒绝、小样本抑制。
- **跨 Agent 使用须知、停止规则与人工决策边界**。

## 公开先例

- Gallup Q12：员工敬业度 12 问，业界最广泛使用的敬业度基线量表。
- Employee Net Promoter Score（eNPS）：源自 Net Promoter Score，迁移到员工推荐意愿测量。
- Amy C. Edmondson, "Psychological Safety and Learning Behavior in Work Teams" (Administrative Science Quarterly, 1999)：团队心理安全感量表的学术源头；Google 亚里士多德计划验证其为高效团队的关键因素。
- 员工体验、归属与包容维度综合自公开的员工体验与 DEI 调研实践，非任何单一厂商专有问卷的照搬。

题目为中文语境重写，不是任何专有问卷的逐字复制；商用前请自行确认所选框架的授权要求。
