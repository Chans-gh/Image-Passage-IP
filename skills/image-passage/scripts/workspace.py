#!/usr/bin/env python3
"""工作区与项目管理。

    python3 workspace.py init                     # 建立 image-passage-work/ 和 profile.md
    python3 workspace.py new <项目名> [--platform xiaohongshu|wechat-tietu|both]
    python3 workspace.py page <项目名> P03 [--composition G|H|S]
    python3 workspace.py adopt <项目名> P03 v2     # 记录采用版本并复制到 final/
    python3 workspace.py block <项目名> P03 "原因"  # 记为待处理
    python3 workspace.py status <项目名>           # 进度与一致性检查
    python3 workspace.py list

只依赖 Python 标准库。工作区位置：$IMAGE_PASSAGE_WORKDIR 或 ./image-passage-work
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ASSETS_DIR, TEMPLATES_DIR, die, workdir  # noqa: E402

PAGE_RE = re.compile(r"^P(\d{1,3})$", re.I)


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def norm_page(page: str) -> str:
    m = PAGE_RE.match(page.strip())
    if not m:
        die(f"页码格式应为 P01、P2 这样的形式：{page}")
    return f"P{int(m.group(1)):02d}"


def safe_name(name: str) -> str:
    name = name.strip()
    if not name or any(c in name for c in '/\\:*?"<>|') or name.startswith("."):
        die(f"项目名不能为空，也不能包含 / \\ : * ? \" < > | 或以 . 开头：{name}")
    return name


def fill(text: str, **values: str) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def read_state(project: Path) -> dict:
    path = project / "state.json"
    if not path.is_file():
        die(f"找不到 {path}，请先运行 new")
    return json.loads(path.read_text(encoding="utf-8"))


def write_state(project: Path, state: dict, event: str | None = None) -> None:
    state["updated"] = now()
    if event:
        state.setdefault("log", []).append({"at": state["updated"], "event": event})
    (project / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def project_dir(name: str) -> Path:
    path = workdir() / safe_name(name)
    if not path.is_dir():
        die(f"项目不存在：{path}")
    return path


def cmd_init(args: argparse.Namespace) -> None:
    wd = workdir()
    for sub in ["_assets/characters", "_assets/style-refs", "_assets/library"]:
        (wd / sub).mkdir(parents=True, exist_ok=True)
    profile = wd / "profile.md"
    if profile.exists() and not args.force:
        print(f"已存在，未覆盖：{profile}")
    else:
        text = fill((TEMPLATES_DIR / "profile.md").read_text(encoding="utf-8"), DATE=now()[:10])
        profile.write_text(text, encoding="utf-8")
        print(f"已创建：{profile}")
    print(f"工作区：{wd}")


def cmd_new(args: argparse.Namespace) -> None:
    wd = workdir()
    if not (wd / "profile.md").exists():
        cmd_init(argparse.Namespace(force=False))
    name = safe_name(args.name)
    project = wd / name
    if project.exists() and not args.force:
        die(f"项目已存在：{project}（继续已有项目请用 status）")
    for sub in ["inputs", "pages", "final", "render"]:
        (project / sub).mkdir(parents=True, exist_ok=True)
    values = dict(PROJECT=name, DATE=now()[:10], PLATFORM=args.platform)
    for tpl in ["plan.md", "inputs.md", "copy.md", "style-lock.md"]:
        target = project / tpl
        if not target.exists() or args.force:
            target.write_text(fill((TEMPLATES_DIR / tpl).read_text(encoding="utf-8"), **values), encoding="utf-8")
    state = json.loads(fill((TEMPLATES_DIR / "state.json").read_text(encoding="utf-8"), **values))
    state["created"] = now()
    write_state(project, state, "项目创建")
    shutil.copy(ASSETS_DIR / "css" / "base.css", project / "render" / "base.css")
    tokens = project / "render" / "tokens.css"
    if not tokens.exists():
        shutil.copy(TEMPLATES_DIR / "tokens.css", tokens)
    print(f"已创建项目：{project}")


def cmd_page(args: argparse.Namespace) -> None:
    project = project_dir(args.name)
    page = norm_page(args.page)
    pdir = project / "pages" / page
    pdir.mkdir(parents=True, exist_ok=True)
    state = read_state(project)
    total = state.get("config", {}).get("pages_total") or "N"
    spec = pdir / "spec.md"
    if not spec.exists():
        spec.write_text(fill((TEMPLATES_DIR / "spec.md").read_text(encoding="utf-8"),
                             PAGE=page, NUM=str(int(page[1:])), TOTAL=str(total),
                             COMPOSITION=args.composition), encoding="utf-8")
    if args.composition in ("H", "S") and not (pdir / "page.html").exists():
        tpl = "page-compose.html" if args.composition == "H" else "page.html"
        (pdir / "page.html").write_text(fill((TEMPLATES_DIR / tpl).read_text(encoding="utf-8"),
                                             PAGE=page, NUM=str(int(page[1:])), TOTAL=str(total)),
                                        encoding="utf-8")
    entry = state.setdefault("pages", {}).setdefault(page, {})
    entry.setdefault("status", "todo")
    entry.setdefault("versions", [])
    entry.setdefault("adopted", None)
    entry.setdefault("attempts", 0)
    entry["composition"] = args.composition
    write_state(project, state, f"{page} 建立规格单（{args.composition}）")
    print(f"已准备：{pdir}")


def cmd_adopt(args: argparse.Namespace) -> None:
    project = project_dir(args.name)
    page = norm_page(args.page)
    version = args.version if args.version.startswith("v") else "v" + args.version
    src = project / "pages" / page / f"{version}.png"
    if not src.is_file():
        die(f"找不到 {src}")
    state = read_state(project)
    entry = state.setdefault("pages", {}).setdefault(page, {"versions": []})
    if version not in entry.setdefault("versions", []):
        entry["versions"].append(version)
    entry["adopted"] = version
    entry["status"] = "done"
    entry["qa"] = args.qa
    entry.pop("blocked_reason", None)
    shutil.copy(src, project / "final" / f"{page}.png")
    write_state(project, state, f"{page} 采用 {version}（质检：{args.qa}）")
    print(f"{page} 采用 {version} → final/{page}.png")


def cmd_block(args: argparse.Namespace) -> None:
    project = project_dir(args.name)
    page = norm_page(args.page)
    state = read_state(project)
    entry = state.setdefault("pages", {}).setdefault(page, {"versions": []})
    entry["status"] = "blocked"
    entry["blocked_reason"] = args.reason
    write_state(project, state, f"{page} 待处理：{args.reason}")
    print(f"{page} 已记为待处理：{args.reason}")


def cmd_status(args: argparse.Namespace) -> None:
    project = project_dir(args.name)
    state = read_state(project)
    cfg = state.get("config", {})
    render = state.get("render", {})
    plan = state.get("plan", {})
    total = cfg.get("pages_total")
    pages = state.get("pages", {})
    issues: list[str] = []

    print(f"项目：{state.get('project')}  平台：{state.get('platform')}  范围：{state.get('scope')}")
    print(f"渲染：{render.get('mode') or '未定'}{'（已锁定）' if render.get('locked') else ''}"
          f"  生图：{render.get('capabilities', {}).get('generate')}  看图：{render.get('capabilities', {}).get('see')}")
    print(f"策划：v{plan.get('version', 0)}  确认：{plan.get('confirmed_version') or '未确认'}"
          f"（{plan.get('confirmed_by') or '-'}）")
    p1 = state.get("anchors", {}).get("P1", {})
    print(f"P1：{p1.get('version') or '未采用'}（{p1.get('status') or '-'}）  共 {total or '?'} 页")

    expected = [f"P{i:02d}" for i in range(1, int(total) + 1)] if isinstance(total, int) and total > 0 else sorted(pages)
    counts = {"done": 0, "blocked": 0, "todo": 0}
    for page in expected:
        entry = pages.get(page)
        if not entry:
            print(f"  {page}  未开始")
            counts["todo"] += 1
            continue
        status = entry.get("status", "todo")
        adopted = entry.get("adopted")
        extra = f"  原因：{entry['blocked_reason']}" if status == "blocked" else ""
        print(f"  {page}  {status:<8} {entry.get('composition', '?')}  采用：{adopted or '-'}"
              f"  版本：{','.join(entry.get('versions', [])) or '-'}{extra}")
        counts["done" if status == "done" else "blocked" if status == "blocked" else "todo"] += 1
        if status == "done":
            if not adopted or not (project / "pages" / page / f"{adopted}.png").is_file():
                issues.append(f"{page} 标为完成，但采用版本文件不存在")
            if not (project / "final" / f"{page}.png").is_file():
                issues.append(f"{page} 标为完成，但 final/{page}.png 不存在")
    extra_final = sorted(p.stem for p in (project / "final").glob("P*.png") if p.stem not in expected)
    if extra_final:
        issues.append("final/ 中有策划之外的页：" + ", ".join(extra_final))
    copy = (project / "copy.md").read_text(encoding="utf-8") if (project / "copy.md").exists() else ""
    if "{{" in copy or not re.search(r"^## 标题\s*\n\s*\S", copy, re.M):
        issues.append("copy.md 尚未填写标题")
    print(f"完成 {counts['done']} · 待处理 {counts['blocked']} · 未完成 {counts['todo']}")
    if issues:
        print("需要注意：")
        for item in issues:
            print("  - " + item)
    sys.exit(0)


def cmd_list(_: argparse.Namespace) -> None:
    wd = workdir()
    if not wd.is_dir():
        print(f"工作区不存在：{wd}")
        return
    for state_file in sorted(wd.glob("*/state.json")):
        state = json.loads(state_file.read_text(encoding="utf-8"))
        done = sum(1 for p in state.get("pages", {}).values() if p.get("status") == "done")
        print(f"{state_file.parent.name}  {done}/{state.get('config', {}).get('pages_total') or '?'} 页  "
              f"更新于 {state.get('updated', '')[:16]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Image-Passage 工作区管理")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_init)
    p = sub.add_parser("new"); p.add_argument("name")
    p.add_argument("--platform", default="xiaohongshu", choices=["xiaohongshu", "wechat-tietu", "both"])
    p.add_argument("--force", action="store_true"); p.set_defaults(func=cmd_new)
    p = sub.add_parser("page"); p.add_argument("name"); p.add_argument("page")
    p.add_argument("--composition", default="G", choices=["G", "H", "S"]); p.set_defaults(func=cmd_page)
    p = sub.add_parser("adopt"); p.add_argument("name"); p.add_argument("page"); p.add_argument("version")
    p.add_argument("--qa", default="pass", choices=["pass", "pass-script-only", "unchecked"])
    p.set_defaults(func=cmd_adopt)
    p = sub.add_parser("block"); p.add_argument("name"); p.add_argument("page"); p.add_argument("reason")
    p.set_defaults(func=cmd_block)
    p = sub.add_parser("status"); p.add_argument("name"); p.set_defaults(func=cmd_status)
    p = sub.add_parser("list"); p.set_defaults(func=cmd_list)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
