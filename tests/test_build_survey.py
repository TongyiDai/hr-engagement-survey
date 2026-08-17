#!/usr/bin/env python3
"""build_survey.py 的单元测试。"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_survey.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def test_all_templates_render():
    tpls = json.load(open(ROOT / "references" / "dimension-templates.json", encoding="utf-8"))["templates"]
    for key in tpls:
        r = run("--template", key, "--format", "markdown")
        assert r.returncode == 0, f"{key} 渲染失败：{r.stderr}"
        assert tpls[key]["name"] in r.stdout


def test_reject_pii_segment():
    r = run("--template", "q12", "--segments", "部门,姓名", "--format", "markdown")
    assert r.returncode == 2
    assert "个人标识" in r.stderr


def test_reject_unknown_segment():
    r = run("--template", "q12", "--segments", "血型", "--format", "markdown")
    assert r.returncode == 2
    assert "不在允许列表" in r.stderr


def test_feishu_questions_batched_by_ten():
    r = run("--template", "engagement_experience", "--segments", "部门", "--format", "feishu-questions")
    assert r.returncode == 0
    batches = json.loads(r.stdout)["batches"]
    assert all(len(b) <= 10 for b in batches)
    total = sum(len(b) for b in batches)
    assert total == 25  # 24 题 + 1 个分组题


def test_feishu_fields_valid_json():
    r = run("--template", "psych_safety", "--segments", "部门,层级", "--format", "feishu-fields")
    assert r.returncode == 0
    fields = json.loads(r.stdout)
    assert fields[0]["field_name"] == "部门"
    assert any(f["type"] == 2 for f in fields)  # 有数值题


def test_enps_uses_rating_scale():
    r = run("--template", "enps", "--format", "feishu-questions")
    assert r.returncode == 0
    flat = [q for b in json.loads(r.stdout)["batches"] for q in b]
    assert any(q.get("style", {}).get("max") == 10 for q in flat)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} passed")
