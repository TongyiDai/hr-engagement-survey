#!/usr/bin/env python3
"""analyze_results.py 的单元测试。"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "analyze_results.py"
FIX = ROOT / "tests" / "fixtures"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True)


def test_basic_report():
    r = run("--input", str(FIX / "results-q12.json"), "--min-cell", "5", "--format", "json")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["overall"]["score"] == 3.4
    assert out["response"]["rate"] == 72.2


def test_small_cell_suppressed():
    r = run("--input", str(FIX / "results-q12.json"), "--min-cell", "5", "--format", "json")
    out = json.loads(r.stdout)
    # HR 部门 n=3 应被抑制
    assert any("HR" in s for s in out["suppressed"])
    dept_names = [row["name"] for row in out["segments"]["部门"]["rows"]]
    assert "HR" not in dept_names


def test_challenges_flagged():
    r = run("--input", str(FIX / "results-q12.json"), "--format", "json")
    out = json.loads(r.stdout)
    labels = [d["label"] for d in out["challenges"]]
    assert "成长与发展" in labels  # 2.9 < 3.4


def test_reject_pii_input():
    r = run("--input", str(FIX / "invalid-with-pii.json"))
    assert r.returncode == 2
    assert "个人标识" in r.stderr


def test_min_cell_threshold_adjustable():
    # 阈值调到 100，则大部分分组被抑制
    r = run("--input", str(FIX / "results-q12.json"), "--min-cell", "100", "--format", "json")
    out = json.loads(r.stdout)
    assert len(out["suppressed"]) >= 5


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} passed")
