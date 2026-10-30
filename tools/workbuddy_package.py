#!/usr/bin/env python3
"""检查 WorkBuddy 专家清单，并打包上传用的 zip。

    python3 tools/workbuddy_package.py check
    python3 tools/workbuddy_package.py zip [--out dist/image-passage-workbuddy.zip] [--flat] [--force]

规则来自 https://open.workbuddy.cn/docs/expert （整理见 docs/workbuddy-submission.md）。
只打包 git 已跟踪的文件，所以 .env、工作区和缓存不会进包。只依赖标准库；头像尺寸检查需要 Pillow。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / ".codebuddy-plugin" / "plugin.json"
INCLUDE = [".codebuddy-plugin", "agents", "avatars", "skills", "README.md", "LICENSE", ".env.example"]
CATEGORIES = {"01-ProductDesign", "02-Engineering", "03-GameSpatial", "04-DataAI", "05-MarketingGrowth",
              "06-ContentCreative", "07-SalesCommerce", "08-FinanceInvestment", "09-OperationsHR",
              "10-ProjectQuality", "11-SecurityCompliance", "12-IndustryConsultant", "13-TencentZone",
              "14-WorldWise", "15-Education"}
REQUIRED = ["name", "expertType", "version", "description", "author", "agents", "agentName", "displayName",
            "profession", "displayDescription", "avatar", "categoryId", "defaultInitPrompt", "plugin",
            "tags", "quickPrompts"]
SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{20,}|AKID[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{30,})")


def bilingual(value) -> bool:
    return isinstance(value, dict) and bool(value.get("zh")) and bool(value.get("en"))


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    return dict(re.findall(r"^([A-Za-z_]+):\s*(.*)$", m.group(1), re.M))


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--", *INCLUDE], cwd=ROOT, check=True,
                         capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line]


def check() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for key in REQUIRED:
        if key not in m or m[key] in ("", None, [], {}):
            errors.append(f"plugin.json 缺少必填字段 {key}")
    if not re.fullmatch(r"[a-z]+(-[a-z]+)*", m.get("name", "")):
        errors.append("name 只能用小写字母和连字符")
    if m.get("plugin") != m.get("name"):
        errors.append("plugin 必须等于 name")
    if m.get("expertType") not in ("agent", "team"):
        errors.append("expertType 只能是 agent 或 team")
    if not re.fullmatch(r"\d+\.\d+\.\d+", m.get("version", "")):
        errors.append("version 需要语义化版本，例如 1.0.0")
    author = m.get("author") or {}
    if not author.get("name"):
        errors.append("author.name 必填")
    if not author.get("email"):
        errors.append("author.email 必填：上传前在 plugin.json 里补上联系邮箱")
    for key in ["displayName", "profession", "displayDescription", "defaultInitPrompt"]:
        if key in m and not bilingual(m[key]):
            errors.append(f"{key} 需要同时有 zh 和 en")
    zh_desc = (m.get("displayDescription") or {}).get("zh", "")
    if zh_desc and not 40 <= len(zh_desc) <= 50:
        errors.append(f"displayDescription.zh 需要 40～50 字，当前 {len(zh_desc)} 字")
    for key in ["tags", "quickPrompts"]:
        items = m.get(key) or []
        if len(items) != 3:
            errors.append(f"{key} 必须恰好 3 个，当前 {len(items)} 个")
        if not all(bilingual(i) for i in items):
            errors.append(f"{key} 的每一项都需要 zh 和 en")
    if m.get("quickPrompts") and m.get("defaultInitPrompt") != m["quickPrompts"][0]:
        errors.append("defaultInitPrompt 必须等于 quickPrompts 的第一项")
    if m.get("categoryId") not in CATEGORIES:
        errors.append(f"categoryId 不在官方列表中：{m.get('categoryId')}")
    if m.get("categoryId") == "13-TencentZone":
        errors.append("13-TencentZone 仅限腾讯内部专家")

    agent_files = [ROOT / a for a in m.get("agents", [])]
    for path in agent_files:
        if not path.is_file():
            errors.append(f"agent 文件不存在：{path.relative_to(ROOT)}")
            continue
        fm = frontmatter(path)
        if fm.get("name") != path.stem:
            errors.append(f"{path.name}：frontmatter 的 name 必须等于文件名")
        for key in ["description", "displayName", "profession"]:
            if not fm.get(key):
                errors.append(f"{path.name}：frontmatter 缺少 {key}")
        if "tools" in fm:
            errors.append(f"{path.name}：不能声明 tools，权限由系统分配")
    if m.get("agentName") not in [p.stem for p in agent_files]:
        errors.append("agentName 必须对应 agents 里某个文件名（不含 .md）")
    for skill in m.get("skills", []):
        if not (ROOT / skill / "SKILL.md").is_file():
            errors.append(f"技能目录缺少 SKILL.md：{skill}")

    avatar = ROOT / m.get("avatar", "")
    if not avatar.is_file():
        errors.append(f"头像不存在：{m.get('avatar')}")
    else:
        size_kb = avatar.stat().st_size / 1024
        if size_kb > 500:
            errors.append(f"头像 {size_kb:.0f}KB，超过 500KB")
        try:
            from PIL import Image
            with Image.open(avatar) as im:
                if im.size != (512, 512):
                    errors.append(f"头像需要 512×512，当前 {im.size[0]}×{im.size[1]}")
        except ImportError:
            warnings.append("未安装 Pillow，跳过头像尺寸检查")

    files = tracked_files()
    for rel in files:
        path = ROOT / rel
        if path.name == ".env" or rel.startswith("image-passage-work/"):
            errors.append(f"不应打包：{rel}")
        if path.suffix in {".md", ".json", ".py", ".yaml", ".txt", ".html", ".css", ".example"}:
            if SECRET_RE.search(path.read_text(encoding="utf-8", errors="ignore")):
                errors.append(f"疑似真实密钥：{rel}")
    untracked = subprocess.run(["git", "status", "--porcelain", "--", *INCLUDE], cwd=ROOT,
                               capture_output=True, text=True).stdout.strip()
    if untracked:
        warnings.append("有未提交的改动，zip 只包含已跟踪文件的当前内容：\n    " + untracked.replace("\n", "\n    "))
    return errors, warnings


def build_zip(out: Path, flat: bool) -> int:
    name = json.loads(MANIFEST.read_text(encoding="utf-8"))["name"]
    out.parent.mkdir(parents=True, exist_ok=True)
    files = [f for f in tracked_files() if "__pycache__" not in f]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in files:
            zf.write(ROOT / rel, rel if flat else f"{name}/{rel}")
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description="WorkBuddy 专家清单检查与打包")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    p = sub.add_parser("zip")
    p.add_argument("--out", type=Path, default=ROOT / "dist" / "image-passage-workbuddy.zip")
    p.add_argument("--flat", action="store_true", help="文件直接放在 zip 根目录，不套一层 image-passage/")
    p.add_argument("--force", action="store_true", help="检查有错误时仍然打包")
    args = parser.parse_args()

    errors, warnings = check()
    for w in warnings:
        print("提醒：" + w)
    for e in errors:
        print("错误：" + e)
    if args.cmd == "check":
        print("检查通过" if not errors else f"共 {len(errors)} 个错误")
        sys.exit(1 if errors else 0)
    if errors and not args.force:
        print("有错误，未打包（确认要打包时加 --force）")
        sys.exit(1)
    n = build_zip(args.out, args.flat)
    print(f"已打包 {n} 个文件：{args.out}（{args.out.stat().st_size / 1024:.0f}KB）")


if __name__ == "__main__":
    main()
