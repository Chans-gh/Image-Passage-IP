#!/usr/bin/env python3
"""检查当前环境能做什么，并给出渲染路线建议（references/render-routing.md）。

    python3 env_check.py --can-generate yes|no --can-see yes|no [--json] [--quick]

--can-generate：当前环境里有没有原生生图工具（由模型根据自己可用的工具判断）
--can-see：当前模型能不能看图（能否读取图片内容）
脚本本身检查：Python 依赖、Chromium、ffmpeg、tesseract、字体、.env 配置。
--quick 跳过启动浏览器的测试。不会打印任何 KEY。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ASSETS_DIR, font_dir, load_env, load_json, mask_secret, workdir  # noqa: E402


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def chromium_ok() -> tuple[bool, str]:
    if not has_module("playwright"):
        return False, "未安装 playwright（pip install playwright && python -m playwright install chromium）"
    code = ("from playwright.sync_api import sync_playwright\n"
            "from pathlib import Path\n"
            "with sync_playwright() as p:\n"
            "    try:\n        b = p.chromium.launch()\n"
            "    except Exception:\n        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')\n"
            "    b.close()\n")
    try:
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return False, "启动 Chromium 超时"
    if out.returncode == 0:
        return True, "可用"
    return False, "Chromium 无法启动：" + (out.stderr.strip().splitlines() or ["未知错误"])[-1][:200]


def tesseract_status() -> tuple[bool, str]:
    exe = shutil.which("tesseract")
    if not exe:
        return False, "未安装"
    out = subprocess.run([exe, "--list-langs"], capture_output=True, text=True)
    langs = out.stdout + out.stderr
    return ("chi_sim" in langs), ("可用（含中文）" if "chi_sim" in langs else "已安装，但缺少 chi_sim 中文包")


def cjk_system_fonts() -> list[str]:
    exe = shutil.which("fc-list")
    if not exe:
        return []
    out = subprocess.run([exe, ":lang=zh", "family"], capture_output=True, text=True)
    return sorted({line.split(",")[0].strip() for line in out.stdout.splitlines() if line.strip()})[:8]


def main() -> None:
    parser = argparse.ArgumentParser(description="环境能力检查与渲染路线建议")
    parser.add_argument("--can-generate", choices=["yes", "no", "unknown"], default="unknown")
    parser.add_argument("--can-see", choices=["yes", "no", "unknown"], default="unknown")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    env, env_path = load_env()
    fd = font_dir(env)
    fonts = load_json(ASSETS_DIR / "fonts.json")["fonts"]
    fonts_have = [f["id"] for f in fonts if (fd / f["file"]).is_file()]
    browser = (None, "跳过（--quick）") if args.quick else chromium_ok()
    tess = tesseract_status()
    api_ready = bool(env.get("IMAGE_API_BASE_URL") and env.get("IMAGE_API_KEY"))
    asr_ready = bool(env.get("TRANSCRIBE_API_BASE_URL") and env.get("TRANSCRIBE_API_KEY"))
    mode_cfg = (env.get("RENDER_MODE") or "auto").lower()
    scripts_ok = browser[0] is not False and has_module("PIL")

    notes: list[str] = []
    gen = args.can_generate
    if mode_cfg in ("native", "svg", "api"):
        mode = mode_cfg
        reason = f".env 指定 RENDER_MODE={mode_cfg}"
        if mode == "native" and gen == "no":
            notes.append("RENDER_MODE=native，但当前环境没有生图工具：请改用 svg 或 api")
        if mode == "svg" and browser[0] is False:
            notes.append("RENDER_MODE=svg，但 Chromium 不可用：" + browser[1])
        if mode == "api" and not api_ready:
            notes.append("RENDER_MODE=api，但 IMAGE_API_BASE_URL / IMAGE_API_KEY 未配置")
    elif gen == "yes":
        mode, reason = "native", "环境有原生生图工具"
    elif browser[0] is not False and has_module("PIL"):
        mode, reason = "svg", "没有原生生图工具；可以用 HTML/SVG 排版渲染"
        if api_ready:
            notes.append("已配置图片 API：插画、实景类风格可以改用 api（需用户同意，按次计费）")
    elif api_ready:
        mode, reason = "api", "没有原生生图工具，也无法运行渲染脚本，但已配置图片 API"
    else:
        mode, reason = "none", "无法出图：没有生图工具，渲染脚本不可用，也没有配置图片 API"
        notes.append("可以先完成策划和文案；出图需要安装 playwright，或在 .env 中配置图片 API")
    if gen == "unknown" and mode_cfg == "auto":
        notes.append("未说明是否有原生生图工具，请用 --can-generate 告知后再判断")

    compose_h = mode in ("native", "api") and browser[0] is not False and has_module("PIL")
    if args.can_see == "yes":
        qa = "visual"
    elif tess[0]:
        qa = "script+ocr"
    else:
        qa = "script-only"
    if args.can_see != "yes":
        notes.append("模型不能看图：用户的照片需要附一句文字说明；无法视觉检查的页面在报告中注明「未经视觉检查」")
    if not fonts_have:
        notes.append("尚未下载开源字体：运行 fetch_fonts.py（否则使用系统字体，效果和授权都不可控）")

    report = {
        "recommended_mode": mode,
        "reason": reason,
        "compose_H_available": compose_h,
        "qa_mode": qa,
        "capabilities": {"generate": gen, "see": args.can_see, "scripts": scripts_ok},
        "checks": {
            "python": sys.version.split()[0],
            "playwright_chromium": browser[1],
            "pillow": has_module("PIL"),
            "requests": has_module("requests"),
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "tesseract": tess[1],
            "doc_libs": {m: has_module(m) for m in ["pdfplumber", "pypdf", "docx", "pptx", "openpyxl"]},
            "fonts_downloaded": fonts_have,
            "font_dir": str(fd),
            "system_cjk_fonts": cjk_system_fonts(),
        },
        "env": {
            "env_file": str(env_path) if env_path else None,
            "RENDER_MODE": mode_cfg,
            "IMAGE_API": {"base_url": env.get("IMAGE_API_BASE_URL") or None, "key": mask_secret(env.get("IMAGE_API_KEY")),
                          "model": env.get("IMAGE_API_MODEL") or None, "reference_mode": env.get("IMAGE_API_REFERENCE_MODE") or "edits"},
            "TRANSCRIBE_API": "已配置" if asr_ready else "未配置",
            "workdir": str(workdir(env)),
        },
        "notes": notes,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print(f"建议渲染路线：{mode}（{reason}）")
    print(f"H 底图＋叠加：{'可用' if compose_h else '不可用'}    质检方式：{qa}")
    c = report["checks"]
    print(f"Chromium：{c['playwright_chromium']}  Pillow：{c['pillow']}  ffmpeg：{c['ffmpeg']}  tesseract：{c['tesseract']}")
    print(f"字体：{', '.join(fonts_have) or '未下载'}（{fd}）  系统中文字体：{', '.join(c['system_cjk_fonts']) or '无'}")
    print(f".env：{report['env']['env_file'] or '未找到'}  RENDER_MODE={mode_cfg}  图片 API：{report['env']['IMAGE_API']['key']}"
          f"  语音转写：{report['env']['TRANSCRIBE_API']}")
    print(f"工作区：{report['env']['workdir']}")
    for n in notes:
        print("· " + n)


if __name__ == "__main__":
    main()
