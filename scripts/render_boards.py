#!/usr/bin/env python3
"""渲染员工敬业度匿名调研的四张 Geometry Blue 画板。

风格：白底、黑线、单一蓝色强调（#2F6BFF）、几何极简、16:9。
每张对应 assets/scenes 下的一个场景 JSON，内容与本 Skill 绑定。
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

W, H = 1200, 675
BLACK = "#111111"
LINE = "#222222"
GRAY = "#666666"
GUIDE = "#B8B8B8"
LIGHT = "#E8E8E8"
FILL = "#F5F5F5"
BLUE = "#2F6BFF"
FONT = "-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans CJK SC',sans-serif"


def esc(v: object) -> str:
    return html.escape(str(v), quote=True)


def txt(x, y, v, size=16, fill=BLACK, anchor="middle", weight=400, letter=0):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{FONT}" '
            f'font-size="{size}px" font-weight="{weight}" letter-spacing="{letter}px" fill="{fill}">{esc(v)}</text>')


def two_lines(x, y, a, b, size=16, fill=BLACK, gap=20, weight=600):
    return txt(x, y - gap / 2 + 5, a, size, fill, weight=weight) + txt(x, y + gap / 2 + 5, b, size, fill, weight=weight)


def line(x1, y1, x2, y2, color=LINE, width=1.5, arrow=False, dashed=False):
    marker = ' marker-end="url(#arrow)"' if arrow else ""
    dash = ' stroke-dasharray="5 7"' if dashed else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{dash}{marker} />'


def path(d, color=LINE, width=1.5, arrow=False, dashed=False):
    marker = ' marker-end="url(#arrow)"' if arrow else ""
    dash = ' stroke-dasharray="5 7"' if dashed else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash}{marker} />'


def rect(x, y, w, h, fill="none", stroke=LINE, width=1.5):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" />'


def circle(cx, cy, r, fill="none", stroke=LINE, width=1.5):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" />'


def title(scene):
    intent = scene["intent"]
    sub = intent.get("subtitle", "员工敬业度匿名调研")
    return "".join([
        txt(96, 78, intent["core_message"], 32, BLACK, "start", 650),
        txt(96, 108, sub, 14, GRAY, "start"),
        line(96, 136, 1104, 136, LIGHT, 1),
    ])


def paper(x, y, lines=3):
    """一张问卷/文档小图标。"""
    body = [rect(x, y, 90, 108, "#FFFFFF", LINE, 1.5)]
    for i in range(lines):
        body.append(line(x + 14, y + 26 + i * 22, x + 76, y + 26 + i * 22, GUIDE, 1))
    return "".join(body)


# ---------- 画板 1：闭环流程 ----------
def render_flow(scene):
    body = [title(scene)]
    y = 330
    steps = [
        (150, "选模板", "5 套经典维度"),
        (368, "生成问卷", "本地 / 飞书"),
        (586, "匿名收集", "无个人标识"),
        (804, "聚合分析", "分维度 · 分组"),
        (1020, "行动计划", "可追责"),
    ]
    # 连接线
    for x0, x1 in ((240, 288), (458, 506), (676, 724), (894, 942)):
        body.append(line(x0, y, x1, y, LINE, 1.5, arrow=True))
    # 节点
    body.append(paper(105, y - 54, 3))
    body.append(paper(323, y - 54, 4))
    # 匿名收集：汇聚到中心（去标识）
    body.append(circle(586, y, 48, BLUE))
    body.append(two_lines(586, y - 2, "匿名", "聚合", 17, "#FFFFFF", 21, 650))
    # 分析：条形
    for i, hh in enumerate((30, 46, 22, 38)):
        bx = 776 + i * 20
        body.append(f'<rect x="{bx}" y="{y + 26 - hh}" width="12" height="{hh}" fill="none" stroke="{LINE}" stroke-width="1.5" />')
    # 行动：清单勾选
    body.append(rect(982, y - 42, 84, 96, "#FFFFFF", LINE, 1.5))
    for i in range(3):
        cy = y - 20 + i * 26
        body.append(f'<circle cx="1000" cy="{cy}" r="7" fill="{BLUE}" /><path d="M 996 {cy} l 3 3 l 6 -7" fill="none" stroke="#FFFFFF" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />')
        body.append(line(1014, cy, 1052, cy, GUIDE, 1))
    # 标签
    for x, label, sub in steps:
        body.append(txt(x, y + 92, label, 16, BLACK, weight=600))
        body.append(txt(x, y + 116, sub, 12, GRAY))
    # 底部回环：脉冲追踪
    body.append(path("M 1020 448 C 1020 556 150 556 150 448", GUIDE, 1.2, True, dashed=True))
    body.append(txt(585, 590, "脉冲调研持续追踪，验证改进是否见效", 12, GRAY))
    return "".join(body)


# ---------- 画板 2：五套模板选型 ----------
def render_templates(scene):
    body = [title(scene)]
    cx, cy = 300, 366
    body.append(circle(cx, cy, 40, BLUE))
    body.append(two_lines(cx, cy - 2, "按目的", "选型", 15, "#FFFFFF", 19, 650))
    items = [
        ("Q12 敬业度", "12 题 · 快速基线"),
        ("敬业度 × 体验", "24 题 · 年度全面"),
        ("eNPS 脉冲", "7 题 · 月度追踪"),
        ("归属与包容", "11 题 · 文化公平"),
        ("心理安全感", "10 题 · 团队协作"),
    ]
    top, gap, bx = 214, 66, 620
    for i, (name, sub) in enumerate(items):
        y = top + i * gap
        body.append(path(f"M {cx + 42} {cy} C 480 {cy} 500 {y + 16} {bx - 16} {y + 16}", LINE, 1.3, True))
        body.append(rect(bx, y, 400, 46, "#FFFFFF", LINE, 1.4))
        body.append(f'<rect x="{bx}" y="{y}" width="6" height="46" fill="{BLUE}" />')
        body.append(txt(bx + 24, y + 20, name, 16, BLACK, "start", 600))
        body.append(txt(bx + 24, y + 38, sub, 12, GRAY, "start"))
    body.append(txt(300, 470, "可单选，也可组合", 13, GRAY))
    body.append(txt(300, 494, "量表统一 1–5", 13, GRAY))
    return "".join(body)


# ---------- 画板 3：匿名与小样本抑制 ----------
def render_anonymity(scene):
    body = [title(scene)]
    # 左：许多个人作答（点阵）汇入
    body.append(txt(220, 214, "员工作答", 14, GRAY, weight=600))
    import math
    for r in range(4):
        for c in range(5):
            x = 150 + c * 34
            y = 250 + r * 34
            body.append(circle(x, y, 6, "#FFFFFF", GUIDE, 1.2))
    # 去标识闸门
    body.append(line(340, 236, 340, 420, LINE, 1.5, dashed=True))
    body.append(txt(340, 450, "去个人标识", 12, GRAY))
    body.append(path("M 316 328 C 390 328 410 340 470 340", LINE, 1.5, True))
    # 中：聚合圆
    body.append(circle(560, 336, 66, BLUE))
    body.append(two_lines(560, 333, "群体", "聚合", 18, "#FFFFFF", 22, 650))
    body.append(txt(560, 430, "只看分组，不看个人", 13, GRAY))
    # 右：小样本抑制
    body.append(line(628, 336, 720, 336, LINE, 1.5, arrow=True))
    body.append(rect(742, 276, 330, 122, "#F5F5F5", LIGHT, 1))
    body.append(txt(762, 306, "分组展示", 14, BLACK, "start", 600))
    body.append(txt(762, 336, "研发 n=90　✓", 14, GRAY, "start"))
    body.append(txt(762, 362, "销售 n=60　✓", 14, GRAY, "start"))
    body.append(txt(762, 388, "HR   n=3 　✕ 已抑制", 14, BLUE, "start", 600))
    body.append(txt(604, 470, "样本 < 阈值（默认 5）的分组不展示分数，防止反向识别", 12, GRAY))
    return "".join(body)


# ---------- 画板 4：系统出洞察 / 人做决定 ----------
def render_boundary(scene):
    body = [title(scene)]
    body.append(rect(112, 196, 476, 340, FILL, "none", 0))
    body.append(rect(706, 196, 382, 340, "#FFFFFF", LIGHT, 1))
    body.append(line(647, 190, 647, 548, GUIDE, 1, dashed=True))
    body.append(txt(350, 228, "系统可以做", 15, GRAY, weight=600))
    body.append(txt(897, 228, "人负责", 15, GRAY, weight=600))
    # 左：数据→洞察
    body.append(paper(168, 288, 3))
    body.append(txt(213, 420, "聚合数据", 15, BLACK, weight=600))
    body.append(line(300, 336, 388, 336, LINE, 1.5, arrow=True))
    for i, hh in enumerate((26, 40, 20)):
        bx = 410 + i * 22
        body.append(f'<rect x="{bx}" y="{336 - hh}" width="14" height="{hh}" fill="none" stroke="{LINE}" stroke-width="1.5" />')
    body.append(txt(444, 420, "洞察与短板", 15, BLACK, weight=600))
    body.append(path("M 500 336 C 560 336 574 360 616 360", LINE, 1.5, True))
    # 复核点
    body.append(circle(647, 360, 18, BLUE))
    body.append(txt(647, 408, "交接点", 13, BLUE, weight=650))
    body.append(line(669, 360, 752, 360, LINE, 1.5, arrow=True))
    # 右：人做决定
    body.append(circle(884, 350, 74, "#FFFFFF", LINE, 1.5))
    body.append(circle(884, 350, 50, "none", LIGHT, 1))
    body.append(circle(884, 350, 8, BLUE))
    body.append(txt(884, 432, "管理者与 HR", 16, BLACK, weight=650))
    body.append(txt(884, 460, "决定改进什么、谁来负责", 12, GRAY))
    body.append(txt(350, 500, "整理事实、生成行动模板", 13, GRAY))
    body.append(txt(897, 500, "改进决策与资源投入", 13, GRAY))
    return "".join(body)


RENDERERS = {
    "flow": render_flow,
    "templates": render_templates,
    "anonymity": render_anonymity,
    "boundary": render_boundary,
}


def render(scene):
    kind = scene["intent"]["composition"]
    fn = RENDERERS.get(kind)
    if fn is None:
        raise ValueError(f"unsupported composition: {kind}")
    body = fn(scene)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <title>{esc(scene["intent"]["core_message"])}</title>
  <desc>Geometry Board for the 员工敬业度匿名调研 skill.</desc>
  <defs>
    <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 8 4 L 0 8 z" fill="{LINE}" />
    </marker>
  </defs>
  <rect width="{W}" height="{H}" fill="#FFFFFF" />
  {body}
</svg>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for scene_path in sorted(args.scene_dir.glob("*.json")):
        scene = json.loads(scene_path.read_text(encoding="utf-8"))
        out = args.output_dir / f"{scene_path.stem}.svg"
        out.write_text(render(scene), encoding="utf-8")
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
