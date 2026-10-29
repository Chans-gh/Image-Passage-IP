#!/usr/bin/env python3
"""颜色名 → HEX，并生成项目的 tokens.css（风格锁的精确版）。

    python3 palette.py resolve 鼠尾草绿 暖米白 炭灰
    python3 palette.py list
    python3 palette.py tokens --out <项目>/render/tokens.css \
        --bg 暖米白 --surface 纯白 --text 炭灰 --muted 冷灰 --line 炭灰 \
        --primary 鼠尾草绿 --accent 珊瑚橙 --highlight 奶油黄 \
        --font-title noto-sans-sc --font-body noto-sans-sc --font-hand lxgw-wenkai \
        [--radius 24] [--stroke 3] [--margin 64] [--fs-cover 132 --fs-title 80 --fs-body 42]

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


def fonts_by_id() -> dict[str, dict]:
    return {f["id"]: f for f in load_json(ASSETS_DIR / "fonts.json")["fonts"]}


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


def cmd_tokens(a: argparse.Namespace) -> None:
    colors = {}
    for key in ["bg", "surface", "text", "muted", "line", "primary", "accent", "highlight", "good", "bad"]:
        value = getattr(a, key)
        if value is None:
            continue
        hexv = resolve(value)
        if not hexv:
            print(f"错误：颜色「{value}」不在参考表中，请直接传入 HEX（例如 --{key} '#9CAF88'）", file=sys.stderr)
            sys.exit(1)
        colors[key] = (value, hexv)
    fonts = fonts_by_id()
    font_vars = {}
    for key in ["title", "body", "hand", "serif"]:
        fid = getattr(a, f"font_{key}")
        if fid is None:
            continue
        if fid not in fonts:
            print(f"错误：未知字体 id「{fid}」，可选：{', '.join(fonts)}", file=sys.stderr)
            sys.exit(1)
        font_vars[key] = fonts[fid]

    lines = ["/* 由 palette.py 生成：风格锁的精确版。同一套图内不要逐页修改。 */", ":root {"]
    var_names = {"bg": "--c-bg", "surface": "--c-surface", "text": "--c-text", "muted": "--c-muted",
                 "line": "--c-line", "primary": "--c-primary", "accent": "--c-accent",
                 "highlight": "--c-highlight", "good": "--c-good", "bad": "--c-bad"}
    for key, (name, hexv) in colors.items():
        lines.append(f"  {var_names[key]}: {hexv}; /* {name} */")
    for key, font in font_vars.items():
        stack = [f'"{font["family"]}"'] + [f for f in ['"Noto Sans SC"', '"WenQuanYi Zen Hei"'] if f.strip('"') != font["family"]]
        generic = "serif" if key == "serif" else "sans-serif"
        lines.append(f'  --f-{key}: {", ".join(stack)}, {generic}; /* {font["zh"]} */')
    for key in ["radius", "stroke", "margin", "fs_cover", "fs_title", "fs_sub", "fs_body", "fs_note"]:
        value = getattr(a, key)
        if value is not None:
            lines.append(f"  --{key.replace('_', '-')}: {value:g}px;")
    if a.fw_title:
        lines.append(f"  --fw-title: {a.fw_title};")
    lines.append("}")
    text = "\n".join(lines) + "\n"
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8")
        print(f"已写入 {a.out}")
    else:
        print(text, end="")


def main() -> None:
    parser = argparse.ArgumentParser(description="颜色名 → HEX，生成 tokens.css")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("resolve"); p.add_argument("names", nargs="+"); p.set_defaults(func=cmd_resolve)
    p = sub.add_parser("list"); p.set_defaults(func=cmd_list)
    p = sub.add_parser("tokens"); p.add_argument("--out", type=Path)
    for key in ["bg", "surface", "text", "muted", "line", "primary", "accent", "highlight", "good", "bad"]:
        p.add_argument(f"--{key}")
    for key in ["title", "body", "hand", "serif"]:
        p.add_argument(f"--font-{key}")
    for key in ["radius", "stroke", "margin", "fs-cover", "fs-title", "fs-sub", "fs-body", "fs-note"]:
        p.add_argument(f"--{key}", type=float)
    p.add_argument("--fw-title", type=int)
    p.set_defaults(func=cmd_tokens)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
