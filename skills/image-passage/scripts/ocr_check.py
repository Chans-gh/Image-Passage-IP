#!/usr/bin/env python3
"""用 OCR 核对图上文字（给不能看图的模型用，或作为 G 页的辅助检查）。

    python3 ocr_check.py pages/P03/v1.png --expect "三步救回黄叶绿萝" --expect "剪掉黄叶"
    python3 ocr_check.py pages/P03/v1.png --expect-file pages/P03/spec.md

--expect-file 会读取规格单「上图文字」小节里每行「」中的文字。
每条期望文字给出匹配度：≥0.9 视为写对，0.6～0.9 可能有错字，<0.6 视为缺失或错误。
OCR 对艺术字、手写字的识别率有限：低分只说明需要人工确认，不等于一定写错。

依赖：tesseract（含 chi_sim 语言包）与 Pillow。
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def expected_from_spec(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"##\s*上图文字(.*?)(\n##\s|\Z)", text, re.S)
    block = m.group(1) if m else text
    return [s for s in re.findall(r"「([^」]+)」", block) if s.strip()]


def norm(s: str) -> str:
    return re.sub(r"[\s\W_]+", "", s, flags=re.U).lower()


def best_ratio(needle: str, hay: str) -> float:
    n, h = norm(needle), norm(hay)
    if not n:
        return 1.0
    if n in h:
        return 1.0
    best = 0.0
    win = len(n)
    for i in range(0, max(1, len(h) - win + 1)):
        r = difflib.SequenceMatcher(None, n, h[i:i + win + 2]).ratio()
        best = max(best, r)
    return round(best, 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR 核对图上文字")
    parser.add_argument("image", type=Path)
    parser.add_argument("--expect", action="append", default=[])
    parser.add_argument("--expect-file", type=Path)
    parser.add_argument("--lang", default="chi_sim+eng")
    args = parser.parse_args()

    exe = shutil.which("tesseract")
    if not exe:
        print(json.dumps({"available": False, "detail": "未安装 tesseract（需要 chi_sim 语言包）。无法自动核对，"
                          "请在状态报告中注明「未经视觉检查」，并请用户抽查。"}, ensure_ascii=False))
        sys.exit(2)
    expected = list(args.expect)
    if args.expect_file:
        expected += expected_from_spec(args.expect_file)
    if not expected:
        parser.error("需要 --expect 或 --expect-file")
    out = subprocess.run([exe, str(args.image), "stdout", "-l", args.lang, "--psm", "11"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        print(json.dumps({"available": False, "detail": out.stderr.strip()[:300]}, ensure_ascii=False))
        sys.exit(2)
    ocr = out.stdout
    results = []
    for item in expected:
        r = best_ratio(item, ocr)
        results.append({"expect": item, "score": r,
                        "verdict": "ok" if r >= 0.9 else "check" if r >= 0.6 else "missing"})
    report = {"available": True, "image": str(args.image), "results": results,
              "ocr_excerpt": re.sub(r"\s+", " ", ocr)[:400]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if any(x["verdict"] == "missing" for x in results) else 0)


if __name__ == "__main__":
    main()
