#!/usr/bin/env python3
"""从维度模板生成敬业度调研问卷。

输入唯一真源是 references/dimension-templates.json。
支持四种输出：markdown 预览、结构化 json、飞书问卷题目 JSON、飞书字段 JSON。
分组维度只允许粗粒度群体字段，出现个人标识即拒绝。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "references" / "dimension-templates.json"

LIKERT_OPTIONS = ["非常不同意", "不同意", "一般", "同意", "非常同意"]


def load_templates() -> dict:
    with TEMPLATES_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def resolve_segments(meta: dict, requested: list[str]) -> list[dict]:
    """把用户请求的分组维度名映射到 meta.segment_fields，拒绝个人标识。"""
    forbidden = set(meta.get("forbidden_fields", []))
    by_label = {f["label"]: f for f in meta["segment_fields"]}
    resolved = []
    for name in requested:
        name = name.strip()
        if not name:
            continue
        if name in forbidden:
            raise ValueError(f"分组维度 '{name}' 属于个人标识，禁止用于匿名调研。")
        if name not in by_label:
            raise ValueError(
                f"分组维度 '{name}' 不在允许列表中。允许：{', '.join(by_label)}。"
            )
        resolved.append(by_label[name])
    return resolved


def is_enps(template: dict) -> bool:
    return template.get("scale_override", {}).get("type") == "nps-0-10"


def iter_questions(template: dict):
    for dim in template["dimensions"]:
        for q in dim["questions"]:
            yield dim, q


def to_markdown(tpl_key: str, template: dict, segments: list[dict]) -> str:
    lines = [f"# {template['name']} 问卷预览", ""]
    lines.append(f"- 来源：{template['source']}")
    lines.append(f"- 适用：{template['scenario']}")
    total = sum(len(d["questions"]) for d in template["dimensions"])
    lines.append(f"- 题量：{total} 题")
    lines.append("")
    lines.append("> 本调研全程匿名，结果仅做群体聚合分析，不追溯到个人。")
    lines.append("")
    if segments:
        lines.append("## 分组信息（单选）")
        for seg in segments:
            opts = seg.get("options")
            opt_str = "：" + " / ".join(opts) if opts else "（按实际填写）"
            lines.append(f"- {seg['label']}{opt_str}")
        lines.append("")
    idx = 1
    for dim in template["dimensions"]:
        lines.append(f"## {dim['label']}")
        for q in dim["questions"]:
            if is_enps(template) and "0–10" in q:
                lines.append(f"{idx}. {q}")
            elif "（开放题）" in q:
                lines.append(f"{idx}. {q}")
            else:
                lines.append(f"{idx}. {q}")
                lines.append(f"   `{' / '.join(LIKERT_OPTIONS)}`")
            idx += 1
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def to_json(tpl_key: str, template: dict, segments: list[dict]) -> str:
    payload = {
        "template": tpl_key,
        "name": template["name"],
        "source": template["source"],
        "scale": "nps-0-10 + likert-5" if is_enps(template) else "likert-5",
        "segments": [{"key": s["key"], "label": s["label"], "options": s.get("options")} for s in segments],
        "dimensions": template["dimensions"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def question_type(template: dict, q: str) -> dict:
    if is_enps(template) and "0–10" in q:
        return {"type": "number", "title": q, "required": True,
                "style": {"type": "rating", "min": 0, "max": 10}}
    if "（开放题）" in q:
        return {"type": "text", "title": q.replace("（开放题）", ""), "required": False}
    return {
        "type": "select",
        "title": q,
        "required": True,
        "option_display_mode": 2,
        "options": [{"name": o} for o in LIKERT_OPTIONS],
    }


def to_feishu_questions(template: dict, segments: list[dict]) -> str:
    """飞书 form-questions-create 每次最多 10 题，自动分批。"""
    items: list[dict] = []
    for seg in segments:
        q: dict = {"type": "select", "title": seg["label"], "required": True, "option_display_mode": 0}
        if seg.get("options"):
            q["options"] = [{"name": o} for o in seg["options"]]
        items.append(q)
    for _dim, q in iter_questions(template):
        items.append(question_type(template, q))
    batches = [items[i:i + 10] for i in range(0, len(items), 10)]
    return json.dumps({"batches": batches}, ensure_ascii=False, indent=2) + "\n"


def to_feishu_fields(template: dict, segments: list[dict]) -> str:
    fields: list[dict] = []
    for seg in segments:
        f: dict = {"field_name": seg["label"], "type": 3}
        if seg.get("options"):
            f["property"] = {"options": [{"name": o} for o in seg["options"]]}
        fields.append(f)
    for _dim, q in iter_questions(template):
        if "（开放题）" in q:
            fields.append({"field_name": q.replace("（开放题）", ""), "type": 1})
        else:
            fields.append({"field_name": q, "type": 2})  # 数值：存 1–5 或 0–10
    return json.dumps(fields, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成敬业度调研问卷")
    parser.add_argument("--template", required=True, help="模板 key：q12 / engagement_experience / enps / belonging_inclusion / psych_safety")
    parser.add_argument("--segments", default="", help="分组维度，逗号分隔，如 部门,层级,司龄")
    parser.add_argument("--format", default="markdown",
                        choices=["markdown", "json", "feishu-questions", "feishu-fields"])
    args = parser.parse_args(argv)

    data = load_templates()
    templates = data["templates"]
    if args.template not in templates:
        parser.error(f"未知模板 '{args.template}'。可选：{', '.join(templates)}")
    template = templates[args.template]

    requested = [s for s in args.segments.split(",") if s.strip()]
    try:
        segments = resolve_segments(data["meta"], requested)
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    if args.format == "markdown":
        sys.stdout.write(to_markdown(args.template, template, segments))
    elif args.format == "json":
        sys.stdout.write(to_json(args.template, template, segments))
    elif args.format == "feishu-questions":
        sys.stdout.write(to_feishu_questions(template, segments))
    elif args.format == "feishu-fields":
        sys.stdout.write(to_feishu_fields(template, segments))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
