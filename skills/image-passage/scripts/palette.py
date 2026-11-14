#!/usr/bin/env python3
"""颜色名 → HEX（风格锁的精确版）。

    python3 palette.py resolve 鼠尾草绿 暖米白 炭灰
    python3 palette.py list

颜色参数可以写颜色名，也可以直接写 #RRGGBB。表里没有的颜色名会报错：
请由模型推导一个 HEX 直接传入，并把「颜色名 = HEX」写进 style-lock.md。只依赖标准库。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ASSETS_DIR, load_json  # noqa: E402

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def table() -> tuple[dict[str, str], dict[str, str]]:
    data = load_json(ASSETS_DIR / "colors.json")
    flat = {name: hexv for group in data["groups"].values() for name, hexv in group.items()}
    return flat, data.get("aliases", {})


def resolve(name: str) -> str | None:
    name = name.strip()
    if HEX_RE.match(name):
        return name.upper()
    flat, aliases = table()
    if name in flat:
        return flat[name]
    if name in aliases:
        return flat[aliases[name]]
    return None


def cmd_resolve(a: argparse.Namespace) -> None:
    missing = []
    for name in a.names:
        hexv = resolve(name)
        if hexv:
            print(f"{name} = {hexv}")
        else:
            missing.append(name)
            print(f"{name} = ?（表里没有，请推导 HEX 后写入 style-lock.md）")
    sys.exit(1 if missing else 0)


def cmd_list(_: argparse.Namespace) -> None:
    data = load_json(ASSETS_DIR / "colors.json")
    for group, colors in data["groups"].items():
        print(f"【{group}】 " + "  ".join(f"{n} {h}" for n, h in colors.items()))
    print("【别名】 " + "  ".join(f"{a}→{b}" for a, b in data.get("aliases", {}).items()))


def main() -> None:
    parser = argparse.ArgumentParser(description="颜色名 → HEX")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("resolve"); p.add_argument("names", nargs="+"); p.set_defaults(func=cmd_resolve)
    p = sub.add_parser("list"); p.set_defaults(func=cmd_list)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
