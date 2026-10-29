#!/usr/bin/env python3
"""图片小工具（依赖 Pillow）。

    python3 image_tools.py fit in.png out.png [--mode cover|contain] [--bg "#FFFFFF"]
        把任意尺寸的图适配为 3:4 输出规格（默认 1242×1656）。cover 居中裁切，contain 留边。
    python3 image_tools.py mask in.png out.png --rect x,y,w,h [--rect ...] [--style blur|fill]
        遮挡隐私信息（手机号、姓名、订单号、头像等）。坐标为像素，也可写百分比如 10%,20%,30%,5%。
    python3 image_tools.py sheet out.jpg a.png b.png ... [--cols 3] [--label]
        拼一张预览图（只用于内部查看或用户明确要求的整套预览，不能当作正式页面）。
    python3 image_tools.py info a.png b.png ...
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_env, output_size  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError:
    print("错误：需要 Pillow。安装：pip install pillow", file=sys.stderr)
    sys.exit(2)


def fit_image(src: Path, dst: Path, mode: str = "cover", bg: str = "#FFFFFF",
              size: tuple[int, int] | None = None) -> tuple[int, int]:
    width, height = size or output_size(load_env()[0])
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if mode == "cover":
        out = ImageOps.fit(img, (width, height), method=Image.LANCZOS, centering=(0.5, 0.5))
    else:
        img.thumbnail((width, height), Image.LANCZOS)
        out = Image.new("RGB", (width, height), bg)
        out.paste(img, ((width - img.width) // 2, (height - img.height) // 2))
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    return out.size


def parse_rect(text: str, w: int, h: int) -> tuple[int, int, int, int]:
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError(f"矩形格式应为 x,y,w,h：{text}")
    vals = []
    for i, part in enumerate(parts):
        base = w if i % 2 == 0 else h
        vals.append(int(float(part[:-1]) / 100 * base) if part.endswith("%") else int(float(part)))
    x, y, rw, rh = vals
    return x, y, x + rw, y + rh


def cmd_fit(a: argparse.Namespace) -> None:
    size = fit_image(a.src, a.dst, a.mode, a.bg)
    print(f"已输出 {a.dst}（{size[0]}×{size[1]}，{a.mode}）")


def cmd_mask(a: argparse.Namespace) -> None:
    img = ImageOps.exif_transpose(Image.open(a.src)).convert("RGB")
    for rect in a.rect:
        box = parse_rect(rect, img.width, img.height)
        if a.style == "blur":
            region = img.crop(box).filter(ImageFilter.GaussianBlur(radius=max(8, (box[3] - box[1]) // 3)))
            img.paste(region, box)
        else:
            ImageDraw.Draw(img).rounded_rectangle(box, radius=8, fill=a.color)
    a.dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(a.dst)
    print(f"已遮挡 {len(a.rect)} 处 → {a.dst}")


def cmd_sheet(a: argparse.Namespace) -> None:
    imgs = [ImageOps.exif_transpose(Image.open(p)).convert("RGB") for p in a.files]
    cell_w = a.cell
    cell_h = int(cell_w * 4 / 3)
    cols = max(1, a.cols)
    rows = (len(imgs) + cols - 1) // cols
    gap = 16
    sheet = Image.new("RGB", (cols * cell_w + (cols + 1) * gap, rows * cell_h + (rows + 1) * gap), "#EDEDED")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=28)
    except TypeError:
        font = ImageFont.load_default()
    for i, (img, path) in enumerate(zip(imgs, a.files)):
        thumb = ImageOps.fit(img, (cell_w, cell_h), method=Image.LANCZOS) if a.crop else ImageOps.pad(img, (cell_w, cell_h), color="#FFFFFF")
        x = gap + (i % cols) * (cell_w + gap)
        y = gap + (i // cols) * (cell_h + gap)
        sheet.paste(thumb, (x, y))
        if a.label:
            draw.rectangle((x, y, x + 120, y + 40), fill="#000000")
            draw.text((x + 10, y + 6), Path(path).stem[:8], fill="#FFFFFF", font=font)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out, quality=88)
    print(f"预览图 → {a.out}（{len(imgs)} 张，{cols} 列）")


def cmd_info(a: argparse.Namespace) -> None:
    for path in a.files:
        img = Image.open(path)
        w, h = img.size
        print(f"{path}  {w}×{h}  比例 {w / h:.3f}（3:4 = 0.750）  {img.mode}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Image-Passage 图片工具")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fit"); p.add_argument("src", type=Path); p.add_argument("dst", type=Path)
    p.add_argument("--mode", default="cover", choices=["cover", "contain"]); p.add_argument("--bg", default="#FFFFFF")
    p.set_defaults(func=cmd_fit)
    p = sub.add_parser("mask"); p.add_argument("src", type=Path); p.add_argument("dst", type=Path)
    p.add_argument("--rect", action="append", required=True); p.add_argument("--style", default="fill", choices=["fill", "blur"])
    p.add_argument("--color", default="#9A9A9A"); p.set_defaults(func=cmd_mask)
    p = sub.add_parser("sheet"); p.add_argument("out", type=Path); p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--cols", type=int, default=3); p.add_argument("--cell", type=int, default=360)
    p.add_argument("--label", action="store_true"); p.add_argument("--crop", action="store_true")
    p.set_defaults(func=cmd_sheet)
    p = sub.add_parser("info"); p.add_argument("files", nargs="+", type=Path); p.set_defaults(func=cmd_info)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
