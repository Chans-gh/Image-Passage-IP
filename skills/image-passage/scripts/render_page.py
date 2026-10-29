#!/usr/bin/env python3
"""把 HTML 页面渲染成 PNG，并做排版检查（S 纯排版页、H 底图＋叠加页）。

    python3 render_page.py pages/P03/page.html --out pages/P03/v1.png
    python3 render_page.py pages/P03/page.html --check-only          # 只检查不出图
    python3 render_page.py a.html b.html --out-dir out/              # 批量

检查项（结果打印为 JSON，有 error 时退出码为 1）：
  overflow     容器内容溢出（文字被截断）
  offpage      元素超出画布
  safe-area    文字进入四周安全边距
  font-size    文字角色低于最小字号（t-cover≥110，t-title≥72，t-sub≥48，t-body≥40，t-note≥30）
  font         字体没有加载成功，回退到了其他字体
  image        图片加载失败
  overlap      两段文字相互重叠
  highlight    强调处数量超过上限

依赖：playwright（Python 版）与 Chromium。字体由 fetch_fonts.py 下载后自动注入。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ASSETS_DIR, font_dir, load_env, load_json, output_size  # noqa: E402

MIN_SIZES = {"t-cover": 110, "t-title": 72, "t-sub": 48, "t-body": 40, "t-note": 30}

CHECK_JS = r"""
({minSizes, margin}) => {
  const issues = [];
  const page = document.querySelector('.page') || document.body;
  const pr = page.getBoundingClientRect();
  const W = pr.width, H = pr.height;
  const short = (el) => (el.innerText || el.alt || el.src || '').replace(/\s+/g, ' ').trim().slice(0, 40);
  const path = (el) => {
    const parts = [];
    while (el && el !== document.body && parts.length < 4) {
      let s = el.tagName.toLowerCase();
      if (el.classList.length) s += '.' + [...el.classList].slice(0, 2).join('.');
      parts.unshift(s); el = el.parentElement;
    }
    return parts.join(' > ');
  };
  const visible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };
  const hasOwnText = (el) => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 0);
  const all = [...page.querySelectorAll('*')].filter(visible);

  // overflow：设了 overflow 的容器、卡片、分区，以及页面本身
  for (const el of [page, ...all]) {
    const cs = getComputedStyle(el);
    const clips = cs.overflow !== 'visible' || el.matches('.card,.col,.zone,.option,.bubble,.cell,.photo,.shot');
    if (!clips || el.tagName === 'IMG') continue;
    if (el.scrollHeight > el.clientHeight + 3 || el.scrollWidth > el.clientWidth + 3) {
      issues.push({level: 'error', type: 'overflow', where: path(el), text: short(el),
        detail: `内容 ${el.scrollWidth}×${el.scrollHeight} 超出容器 ${el.clientWidth}×${el.clientHeight}`});
    }
  }

  const textEls = all.filter(hasOwnText);
  for (const el of textEls) {
    const r = el.getBoundingClientRect();
    const x = r.left - pr.left, y = r.top - pr.top;
    if (x < -1 || y < -1 || x + r.width > W + 1 || y + r.height > H + 1) {
      issues.push({level: 'error', type: 'offpage', where: path(el), text: short(el), detail: '文字超出画布'});
      continue;
    }
    const exempt = el.closest('.pagenum,.signature,.bleed,.allow-margin');
    if (!exempt && (x < margin - 2 || y < margin - 2 || x + r.width > W - margin + 2 || y + r.height > H - margin + 2)) {
      issues.push({level: 'warning', type: 'safe-area', where: path(el), text: short(el), detail: `文字进入安全边距（${margin}px）`});
    }
    const fs = parseFloat(getComputedStyle(el).fontSize);
    let role = null;
    for (const cls of Object.keys(minSizes)) { if (el.closest('.' + cls)) { role = cls; break; } }
    if (role && fs < minSizes[role] - 0.5) {
      issues.push({level: 'error', type: 'font-size', where: path(el), text: short(el), detail: `${role} 字号 ${fs}px，低于 ${minSizes[role]}px`});
    } else if (!el.closest('.allow-small') && fs < 30 - 0.5) {
      issues.push({level: 'warning', type: 'font-size', where: path(el), text: short(el), detail: `字号 ${fs}px，手机上可能看不清（建议 ≥30px）`});
    }
  }

  // font：检查实际用到的首选字体是否可用
  const families = new Set();
  for (const el of textEls) {
    const first = getComputedStyle(el).fontFamily.split(',')[0].trim().replace(/^["']|["']$/g, '');
    families.add(first);
  }
  const ctx = document.createElement('canvas').getContext('2d');
  const sample = '中文排版测试 Aa1';
  const width = (font) => { ctx.font = font; return ctx.measureText(sample).width; };
  const available = (fam) => ['monospace', 'serif'].some(base => width(`40px "${fam}", ${base}`) !== width(`40px ${base}`));
  for (const fam of families) {
    if (['serif', 'sans-serif', 'monospace', 'cursive', 'system-ui'].includes(fam)) continue;
    if (!available(fam)) {
      issues.push({level: 'warning', type: 'font', where: fam, text: '', detail: `字体「${fam}」不可用，已回退。运行 fetch_fonts.py 下载`});
    }
  }

  for (const img of page.querySelectorAll('img')) {
    if (!img.complete || img.naturalWidth === 0) {
      issues.push({level: 'error', type: 'image', where: path(img), text: img.getAttribute('src') || '', detail: '图片加载失败'});
    }
  }

  // overlap：两段互不包含的文字框相交超过较小者的 15%
  const boxes = textEls.map(el => ({el, r: el.getBoundingClientRect()}));
  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const w = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
      const h = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
      if (w <= 0 || h <= 0) continue;
      const small = Math.min(a.r.width * a.r.height, b.r.width * b.r.height);
      if (w * h > small * 0.15) {
        issues.push({level: 'warning', type: 'overlap', where: path(a.el) + ' ↔ ' + path(b.el),
          text: short(a.el) + ' ↔ ' + short(b.el), detail: '两段文字重叠'});
      }
    }
  }

  const hl = page.querySelectorAll('.hl,.circle').length;
  const limit = page.matches('.l-poster,.v11') ? 2 : 3;
  if (hl > limit) issues.push({level: 'warning', type: 'highlight', where: '.page', text: '', detail: `强调 ${hl} 处，超过上限 ${limit}`});

  return {issues, size: [Math.round(W), Math.round(H)], textBlocks: textEls.length};
}
"""


def font_face_css(fd: Path) -> tuple[str, list[str]]:
    meta = load_json(ASSETS_DIR / "fonts.json")
    rules, loaded = [], []
    for font in meta["fonts"]:
        path = fd / font["file"]
        if path.is_file():
            rules.append(
                f'@font-face {{ font-family: "{font["family"]}"; src: url("{path.resolve().as_uri()}"); '
                f'font-weight: {font.get("weight", "400")}; font-display: block; }}')
            loaded.append(font["family"])
    return "\n".join(rules), loaded


def render(html_paths: list[Path], outs: list[Path | None], width: int, height: int, scale: float) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("错误：需要 Python 版 playwright。安装：pip install playwright && python -m playwright install chromium",
              file=sys.stderr)
        sys.exit(2)
    env, _ = load_env()
    css, loaded = font_face_css(font_dir(env))
    results = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # 浏览器未安装或路径不同
            alt = Path("/opt/pw-browsers/chromium")
            if alt.exists():
                browser = p.chromium.launch(executable_path=str(alt))
            else:
                print(f"错误：无法启动 Chromium：{exc}\n运行：python -m playwright install chromium", file=sys.stderr)
                sys.exit(2)
        ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=scale)
        for html, out in zip(html_paths, outs):
            page = ctx.new_page()
            page.goto(html.resolve().as_uri(), wait_until="load")
            if css:
                page.add_style_tag(content=css)
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(150)
            margin = page.evaluate(
                "parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--margin')) || 64")
            report = page.evaluate(CHECK_JS, {"minSizes": MIN_SIZES, "margin": margin})
            if report["size"] != [width, height]:
                report["issues"].append({"level": "warning", "type": "size",
                                         "detail": f".page 尺寸为 {report['size']}，期望 {[width, height]}"})
            report["file"] = str(html)
            report["fonts_injected"] = loaded
            if out:
                out.parent.mkdir(parents=True, exist_ok=True)
                target = page.query_selector(".page")
                if target:
                    target.screenshot(path=str(out))
                else:
                    page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": width, "height": height})
                report["png"] = str(out)
            report["errors"] = sum(1 for i in report["issues"] if i["level"] == "error")
            report["warnings"] = sum(1 for i in report["issues"] if i["level"] == "warning")
            results.append(report)
            page.close()
        browser.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="HTML → PNG 渲染与排版检查")
    parser.add_argument("html", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, help="单个文件时的输出 PNG 路径")
    parser.add_argument("--out-dir", type=Path, help="批量输出目录（文件名沿用 HTML 所在目录名或文件名）")
    parser.add_argument("--check-only", action="store_true", help="只检查，不输出 PNG")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--scale", type=float, default=1.0, help="设备像素比，默认 1（输出 1242×1656）")
    parser.add_argument("--report", type=Path, help="把检查结果写入 JSON 文件")
    args = parser.parse_args()

    env, _ = load_env()
    w, h = output_size(env)
    width, height = args.width or w, args.height or h
    for path in args.html:
        if not path.is_file():
            print(f"错误：找不到 {path}", file=sys.stderr)
            sys.exit(2)
    if args.check_only:
        outs = [None] * len(args.html)
    elif args.out:
        if len(args.html) != 1:
            print("错误：--out 只能用于单个文件，批量请用 --out-dir", file=sys.stderr)
            sys.exit(2)
        outs = [args.out]
    elif args.out_dir:
        outs = [args.out_dir / ((p.parent.name if p.stem == "page" else p.stem) + ".png") for p in args.html]
    else:
        outs = [p.with_suffix(".png") for p in args.html]

    results = render(args.html, outs, width, height, args.scale)
    text = json.dumps(results if len(results) > 1 else results[0], ensure_ascii=False, indent=2)
    if args.report:
        args.report.write_text(text + "\n", encoding="utf-8")
    print(text)
    sys.exit(1 if any(r["errors"] for r in results) else 0)


if __name__ == "__main__":
    main()
