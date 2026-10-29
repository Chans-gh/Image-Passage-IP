#!/usr/bin/env python3
"""下载开源中文字体（全部为 SIL OFL 协议，可免费商用）。

    python3 fetch_fonts.py              # 下载默认字体（思源黑体、霞鹜文楷）
    python3 fetch_fonts.py --all        # 下载 assets/fonts.json 里的全部字体
    python3 fetch_fonts.py --only noto-serif-sc long-cang
    python3 fetch_fonts.py --list

字体保存在 $IMAGE_PASSAGE_FONT_DIR，默认 ~/.cache/image-passage/fonts。
render_page.py 会自动注入已下载的字体。只依赖标准库。
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ASSETS_DIR, font_dir, load_json  # noqa: E402


def download(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "image-passage-font-fetcher"})
    with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as fh:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(1 << 16):
            fh.write(chunk)
            done += len(chunk)
            if total and sys.stderr.isatty():
                print(f"\r  {done / 1e6:5.1f} / {total / 1e6:.1f} MB", end="", file=sys.stderr)
    if sys.stderr.isatty():
        print(file=sys.stderr)
    print(f"  完成 {done / 1e6:.1f} MB")
    tmp.replace(dest)


def main() -> None:
    parser = argparse.ArgumentParser(description="下载开源中文字体")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--dir", type=Path)
    args = parser.parse_args()

    fonts = load_json(ASSETS_DIR / "fonts.json")["fonts"]
    target = args.dir or font_dir()
    if args.list:
        for f in fonts:
            mark = "✓" if (target / f["file"]).is_file() else " "
            print(f"[{mark}] {f['id']:<24} {f['zh']}（{f['family']}）  {f['role']}  {f['license']}"
                  f"{'  默认' if f.get('default') else ''}")
        print(f"目录：{target}")
        return
    if args.only:
        unknown = set(args.only) - {f["id"] for f in fonts}
        if unknown:
            print("未知字体：" + ", ".join(sorted(unknown)), file=sys.stderr)
            sys.exit(2)
        chosen = [f for f in fonts if f["id"] in args.only]
    elif args.all:
        chosen = fonts
    else:
        chosen = [f for f in fonts if f.get("default")]

    target.mkdir(parents=True, exist_ok=True)
    failed = []
    for f in chosen:
        dest = target / f["file"]
        if dest.is_file() and dest.stat().st_size > 10000:
            print(f"已存在：{f['zh']} → {dest}")
            continue
        print(f"下载：{f['zh']}（{f['license']}）")
        try:
            download(f["url"], dest)
        except Exception as exc:  # 网络不可用时给出清晰提示
            failed.append(f["id"])
            print(f"  失败：{exc}", file=sys.stderr)
    print(f"字体目录：{target}")
    if failed:
        print("以下字体下载失败，可稍后重试或手动下载到上述目录：" + ", ".join(failed), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
