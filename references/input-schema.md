# 输入格式规范

两个脚本各有明确的输入契约。所有输入都应是**脱敏、聚合**的，不含任何个人标识。

## build_survey.py 的输入

无需外部输入文件，直接读 `references/dimension-templates.json`，按 `--template` 和 `--segments` 生成问卷。

```bash
python3 scripts/build_survey.py --template q12 --segments 部门,层级,司龄 --format markdown
python3 scripts/build_survey.py --template enps --format feishu-questions
python3 scripts/build_survey.py --template psych_safety --segments 部门 --format feishu-fields
```

`--format` 取值：
- `markdown`：给人看的问卷预览
- `json`：结构化问卷定义
- `feishu-questions`：可直接喂给 `form-questions-create --questions` 的 JSON 数组（自动按 10 题分批）
- `feishu-fields`：可直接喂给 `field-create --fields` 的字段定义

## analyze_results.py 的输入

输入是一份**聚合结果 JSON**，通常由 `data-query` 的分组均值整理而来，或从本地问卷导出汇总。结构：

```json
{
  "survey": {"template": "q12", "period": "2026-Q1", "prev_period": "2025-Q4"},
  "response": {"invited": 320, "responded": 231},
  "overall": {"score": 3.4, "prev_score": 3.2},
  "dimensions": [
    {"key": "expectation", "label": "角色与期待", "score": 3.8, "prev_score": 3.6},
    {"key": "development", "label": "成长与发展", "score": 2.9, "prev_score": 2.9}
  ],
  "segments": {
    "部门": [
      {"name": "研发", "count": 90, "score": 3.6},
      {"name": "销售", "count": 60, "score": 3.2},
      {"name": "HR", "count": 3, "score": 3.9}
    ],
    "层级": [
      {"name": "个人贡献者", "count": 180, "score": 3.3},
      {"name": "中层管理者", "count": 40, "score": 3.6}
    ]
  },
  "open_ended_themes": [
    {"theme": "职业发展", "mentions": 67, "sentiment": "negative"},
    {"theme": "远程灵活", "mentions": 47, "sentiment": "positive"}
  ]
}
```

字段说明：
- `overall.score` / `prev_score`：整体均值与上期均值，用于同比。
- `dimensions`：各维度均值，脚本据此排优势与短板。
- `segments`：分组结果，每组必须带 `count`。**count 低于 min-cell 阈值的组会被抑制，不展示分数。**
- `open_ended_themes`：可选，开放题主题归纳（已脱敏，不含原文引用）。
- eNPS 模板可额外带 `enps.promoters/passives/detractors` 计数，脚本据此算 eNPS。

## 禁止字段

输入 JSON 一旦出现下列字段（任意层级的 key 或 segment 名），脚本拒绝运行：

`姓名 / 工号 / 邮箱 / 手机号 / 身份证 / IP / 设备号 / 花名 / 座位号`

以及英文对应：`name / employee_id / email / phone / id_card / ip / device`（作为个人标识出现时）。

聚合维度名（部门/层级/司龄/地点/办公方式）不受影响。
