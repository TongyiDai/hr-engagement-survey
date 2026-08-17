# 飞书集成命令契约

本 Skill 与飞书的集成基于 `lark-cli`。飞书是**可选**外部系统：没有它时，用本地问卷导出和聚合结果一样能完成分析。所有写入操作遵循「先确认身份 → 只读探测 → 用户确认 → 窄范围写入 → 回读校验」。

外部系统 ID、租户、凭证都由运行环境提供，Skill 不保存任何令牌。

## 1. 身份核验（写入前必做）

```bash
lark-cli auth status --json --verify
```

确认 `identity=user`、`verified=true`。当前构建没有 `auth` 子命令时，退回只读探测：

```bash
lark-cli contact +get-user --as user
```

任何 Agent 都必须尊重当前账号与租户边界，不混用机器人身份做匿名调研的收集。

## 2. 建匿名收集表

在目标 Base 下建一张收集表。字段只包含：分组维度（单选）+ 各题目（数值/单选）。**不建**任何个人标识字段。

```bash
lark-cli base +field-create --as user \
  --base-token <BASE_TOKEN> --table-id <TABLE_ID> \
  --fields '[{"field_name":"部门","type":3,"property":{"options":[{"name":"研发"},{"name":"销售"},{"name":"HR"}]}},
             {"field_name":"层级","type":3,"property":{"options":[{"name":"个人贡献者"},{"name":"基层管理者"},{"name":"中层管理者"},{"name":"高层"}]}},
             {"field_name":"司龄","type":3,"property":{"options":[{"name":"0–6 个月"},{"name":"6–12 个月"},{"name":"1–3 年"},{"name":"3 年以上"}]}}]'
```

题目字段可用脚本 `build_survey.py --format feishu-fields` 生成，避免手写。

## 3. 建问卷与题目

```bash
lark-cli base +form-create --as user \
  --base-token <BASE_TOKEN> --table-id <TABLE_ID> \
  --name "2026 Q1 员工敬业度匿名调研" \
  --description "本调研全程匿名，结果仅做聚合分析，不追溯到个人。"
```

拿到 `form-id` 后批量建题（每次最多 10 题，`build_survey.py --format feishu-questions` 生成 JSON）：

```bash
lark-cli base +form-questions-create --as user \
  --base-token <BASE_TOKEN> --form-id <FORM_ID> \
  --questions '[{"type":"select","title":"我知道工作中对我的期待是什么。","required":true,
                 "option_display_mode":2,
                 "options":[{"name":"非常不同意"},{"name":"不同意"},{"name":"一般"},{"name":"同意"},{"name":"非常同意"}]}]'
```

评分题也可用 `"type":"number","style":{"type":"rating","icon":"star","min":1,"max":5}` 做星级评分。分组单选题放在问卷开头，粒度保持粗。

## 4. 发布与回读

发布后回读问卷与题目，确认题量、量表、匿名说明都对：

```bash
lark-cli base +form-detail --base-token <BASE_TOKEN> --form-id <FORM_ID>
lark-cli base +form-questions-list --base-token <BASE_TOKEN> --form-id <FORM_ID>
```

分享链接从 `form-detail` 拿。提醒用户：飞书表单本身可设为匿名收集，问卷题目里不要再加任何个人标识题。

## 5. 回收后取聚合数据

调研关闭后，用服务端聚合直接拿分组均值，避免把逐条原始作答拉到本地：

```bash
lark-cli base +data-query --as user --base-token <BASE_TOKEN> \
  --dsl '{"table_id":"<TABLE_ID>",
          "dimensions":[{"field":"部门"}],
          "measures":[{"field":"我对自己的工作充满投入和热情。","method":"AVERAGE"}]}'
```

用 `data-query` 做分组均值、计数、Top N。把结果整理成 `analyze_results.py` 的输入格式（见 [input-schema.md](input-schema.md)），再做完整诊断。**任何分组的 count 低于 min-cell 阈值时不取该组明细。**

## 6. 搭建趋势看板

```bash
lark-cli base +dashboard-create --as user --base-token <BASE_TOKEN> --name "敬业度趋势看板"
lark-cli base +dashboard-block-create --as user --base-token <BASE_TOKEN> \
  --dashboard-id <DASHBOARD_ID> --name "分维度得分" \
  --data-config '<见 dashboard-block-data-config.md>'
lark-cli base +dashboard-arrange --as user --base-token <BASE_TOKEN> --dashboard-id <DASHBOARD_ID>
```

看板建议图表：总分同比折线、分维度柱状、分组（部门/层级/司龄）对比、eNPS 趋势。图表数据源指向同一张收集表，随脉冲调研自动刷新。看板同样遵守小样本抑制——过滤掉样本过小的分组。

## 边界

- 写入（建表/建问卷/建看板）前一律先向用户确认，写入后回读。
- 不采集、不展示任何个人标识；分组维度保持粗粒度。
- 数据不可用或样本过小时停止并说明，不用默认值硬凑。
