#!/usr/bin/env python3
"""对敬业度调研的聚合结果做诊断分析。

输入是脱敏、聚合的结果 JSON（见 references/input-schema.md）。
输出总分与同比、分维度优势与短板、分组差异（带小样本抑制）、开放题主题。
含个人标识字段的输入一律拒绝。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 明确的个人标识字段。不含泛化的 "name"：分组行里的 name 是群体标签（如"研发"），非个人。
FORBIDDEN = {
    "姓名", "工号", "邮箱", "手机号", "身份证", "设备号", "花名", "座位号",
    "employee_id", "email", "phone", "id_card", "device", "full_name",
}
NOISE = 0.5  # 同比波动小于该值视为噪声


def scan_forbidden(obj, path: str = "") -> list[str]:
    """递归检查 JSON 里是否出现个人标识字段（key 或 segment 名）。"""
    hits: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN:
                hits.append(f"{path}.{k}" if path else k)
            hits.extend(scan_forbidden(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(scan_forbidden(v, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if obj in FORBIDDEN:
            hits.append(f"{path}={obj}")
    return hits


def delta_mark(cur: float, prev) -> str:
    if prev is None:
        return "—"
    d = round(cur - prev, 2)
    if abs(d) < NOISE:
        return f"{d:+.2f}（波动）"
    arrow = "↑" if d > 0 else "↓"
    return f"{d:+.2f} {arrow}"


def analyze(data: dict, min_cell: int) -> dict:
    result: dict = {"suppressed": [], "min_cell": min_cell}

    resp = data.get("response", {})
    invited = resp.get("invited")
    responded = resp.get("responded")
    if invited and responded:
        rate = responded / invited
        band = ("强" if rate >= 0.75 else "良好" if rate >= 0.60
                else "可接受" if rate >= 0.50 else "偏弱")
        result["response"] = {"invited": invited, "responded": responded,
                              "rate": round(rate * 100, 1), "band": band}

    overall = data.get("overall", {})
    if "score" in overall:
        result["overall"] = {
            "score": overall["score"],
            "delta": delta_mark(overall["score"], overall.get("prev_score")),
        }

    if "enps" in data:
        e = data["enps"]
        p, pa, d = e.get("promoters", 0), e.get("passives", 0), e.get("detractors", 0)
        total = p + pa + d
        if total:
            result["enps"] = round((p - d) / total * 100, 1)

    dims = data.get("dimensions", [])
    ranked = sorted(dims, key=lambda x: x["score"])
    result["strengths"] = [d for d in reversed(ranked) if d["score"] >= 4.0][:5]
    result["challenges"] = [d for d in ranked if d["score"] < 3.4][:5]
    result["dimensions"] = [
        {"label": d["label"], "score": d["score"], "delta": delta_mark(d["score"], d.get("prev_score"))}
        for d in dims
    ]

    seg_out: dict = {}
    for seg_name, groups in data.get("segments", {}).items():
        rows = []
        for g in groups:
            if g.get("count", 0) < min_cell:
                result["suppressed"].append(f"{seg_name}·{g['name']}（n={g.get('count', 0)}）")
                continue
            rows.append({"name": g["name"], "count": g["count"], "score": g["score"]})
        if len(rows) >= 2:
            rows.sort(key=lambda x: x["score"])
            seg_out[seg_name] = {
                "rows": rows,
                "gap": round(rows[-1]["score"] - rows[0]["score"], 2),
                "low": rows[0]["name"],
                "high": rows[-1]["name"],
            }
        elif rows:
            seg_out[seg_name] = {"rows": rows, "gap": 0.0, "low": None, "high": None}
    result["segments"] = seg_out

    themes = data.get("open_ended_themes", [])
    result["themes"] = sorted(themes, key=lambda x: -x.get("mentions", 0))
    return result


def to_markdown(data: dict, r: dict) -> str:
    survey = data.get("survey", {})
    L = [f"# 敬业度调研诊断报告 · {survey.get('period', '')}", ""]
    L.append(f"> 匿名聚合分析。小样本抑制阈值：{r['min_cell']} 人。")
    L.append("")

    if "response" in r:
        rp = r["response"]
        L.append(f"**参与率**：{rp['rate']}%（{rp['responded']}/{rp['invited']}，{rp['band']}）")
    if "overall" in r:
        L.append(f"**整体敬业度**：{r['overall']['score']} / 5.0　同比 {r['overall']['delta']}")
    if "enps" in r:
        L.append(f"**eNPS**：{r['enps']}")
    L.append("")

    if r["strengths"]:
        L.append("## 优势（≥ 4.0）")
        for d in r["strengths"]:
            L.append(f"- {d['label']}：{d['score']}")
        L.append("")
    if r["challenges"]:
        L.append("## 短板（< 3.4）")
        for d in r["challenges"]:
            L.append(f"- {d['label']}：{d['score']}　→ 建议纳入行动计划")
        L.append("")

    L.append("## 分维度得分")
    for d in r["dimensions"]:
        L.append(f"- {d['label']}：{d['score']}（同比 {d['delta']}）")
    L.append("")

    if r["segments"]:
        L.append("## 分组差异")
        for seg_name, s in r["segments"].items():
            L.append(f"### {seg_name}")
            for row in s["rows"]:
                L.append(f"- {row['name']}（n={row['count']}）：{row['score']}")
            if s["gap"] >= NOISE and s["low"]:
                L.append(f"- 差距：{s['high']} 与 {s['low']} 相差 {s['gap']}，值得关注。")
            L.append("")

    if r["themes"]:
        L.append("## 开放题主题")
        for t in r["themes"]:
            senti = {"positive": "正面", "negative": "负面", "neutral": "中性"}.get(t.get("sentiment", ""), "")
            L.append(f"- {t['theme']}（提及 {t.get('mentions', 0)} 次，{senti}）")
        L.append("")

    if r["suppressed"]:
        L.append("## 已抑制的小样本分组")
        L.append("为保护匿名，以下分组样本过小，未展示分数：")
        for s in r["suppressed"]:
            L.append(f"- {s}")
        L.append("")

    L.append("## 下一步")
    L.append("把短板落成有负责人、时间线、衡量指标的行动计划，见 references/action-planning.md。")
    L.append("宣布结果时同时宣布要做什么——只收集不行动会让下次回收率崩盘。")
    return "\n".join(L).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="敬业度调研结果分析")
    parser.add_argument("--input", required=True, help="聚合结果 JSON 路径")
    parser.add_argument("--min-cell", type=int, default=5, help="小样本抑制阈值，默认 5")
    parser.add_argument("--format", default="markdown", choices=["markdown", "json"])
    args = parser.parse_args(argv)

    with open(args.input, encoding="utf-8") as fh:
        data = json.load(fh)

    hits = scan_forbidden(data)
    if hits:
        print("错误：输入包含个人标识字段，拒绝分析（匿名边界）。命中：" + "; ".join(hits[:8]),
              file=sys.stderr)
        return 2

    r = analyze(data, args.min_cell)
    if args.format == "json":
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(to_markdown(data, r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
