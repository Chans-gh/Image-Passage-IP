#!/usr/bin/env python3
"""检查当前环境能做什么，并给出渲染路线建议（references/render-routing.md）。

    python3 env_check.py --can-generate yes|no --can-see yes|no [--reference-support yes|no|unknown] [--json] [--quick]

--can-generate：当前环境里有没有原生生图工具（由模型根据自己可用的工具判断）
--can-see：当前模型能不能看图（能否读取图片内容）
--reference-support：当前生图工具能不能接收参考图（决定含保真素材的页能否出图）
--quick 跳过需要启动外部进程的检查（tesseract 语言包）
脚本本身检查：Python 依赖、Pillow、ffmpeg、tesseract、.env 配置。不会打印任何 KEY。

出图只有两条路线：native（环境自带多模态生图）与 api（第三方图片模型接口）。
两者都不具备时返回 none：先完成策划和文案，说明怎样才能出图。
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
from _common import load_env, mask_secret, workdir  # noqa: E402


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def tesseract_status() -> tuple[bool, str]:
    exe = shutil.which("tesseract")
    if not exe:
        return False, "未安装"
    out = subprocess.run([exe, "--list-langs"], capture_output=True, text=True)
    langs = out.stdout + out.stderr
    return ("chi_sim" in langs), ("可用（含中文）" if "chi_sim" in langs else "已安装，但缺少 chi_sim 中文包")


def main() -> None:
    parser = argparse.ArgumentParser(description="环境能力检查与渲染路线建议")
    parser.add_argument("--can-generate", choices=["yes", "no", "unknown"], default="unknown")
    parser.add_argument("--can-see", choices=["yes", "no", "unknown"], default="unknown")
    parser.add_argument("--reference-support", choices=["yes", "no", "unknown"], default="unknown")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    env, env_path = load_env()
    tess = (None, "跳过（--quick）") if args.quick else tesseract_status()
    api_ready = bool(env.get("IMAGE_API_BASE_URL") and env.get("IMAGE_API_KEY"))
    asr_ready = bool(env.get("TRANSCRIBE_API_BASE_URL") and env.get("TRANSCRIBE_API_KEY"))
    mode_cfg = (env.get("RENDER_MODE") or "auto").lower()
    pillow_ok = has_module("PIL")

    notes: list[str] = []
    gen = args.can_generate
    if mode_cfg == "svg":
        notes.append("RENDER_MODE=svg 已停用：出图只支持 native 与 api，请修改 .env 后重试；本次按 auto 判定")
        mode_cfg = "auto"
    if mode_cfg in ("native", "api"):
        mode = mode_cfg
        reason = f".env 指定 RENDER_MODE={mode_cfg}"
        if mode == "native" and gen == "no":
            notes.append("RENDER_MODE=native，但当前环境没有生图工具：请改用 api")
        if mode == "api" and not api_ready:
            notes.append("RENDER_MODE=api，但 IMAGE_API_BASE_URL / IMAGE_API_KEY 未配置")
    elif gen == "yes":
        mode, reason = "native", "环境有原生生图工具"
    elif api_ready:
        mode, reason = "api", "没有原生生图工具，但已配置图片 API"
    else:
        mode, reason = "none", "无法出图：既没有生图工具，也没有配置图片 API"
        notes.append("可以先完成策划和文案；出图需要在 .env 中配置图片 API，或换到有生图工具的环境")
    if gen == "unknown" and mode_cfg == "auto":
        notes.append("未说明是否有原生生图工具，请用 --can-generate 告知后再判断")

    # 参考图：含保真素材（真实截图、照片）的页依赖它
    ref = args.reference_support
    if ref == "unknown" and api_ready:
        ref_mode = (env.get("IMAGE_API_REFERENCE_MODE") or "edits").lower()
        ref = "no" if ref_mode == "none" else "unknown"
    if ref == "no" and mode != "none":
        notes.append("生图工具不支持参考图：含真实截图或照片的页无法出图，请提前告知用户，把素材承载的信息移到正文")
    elif ref == "unknown" and mode != "none":
        notes.append("尚未确认生图工具是否支持参考图：先出 1 页含素材的样张验证，再批量")

    if args.can_see == "yes":
        qa = "visual"
    elif tess[0]:
        qa = "script+ocr"
    else:
        qa = "unchecked"
    if args.can_see != "yes":
        notes.append("模型不能看图：无法逐字核对图上文字。建议先只出 1 页让用户确认，报告里注明「未经视觉检查」")
    if not pillow_ok:
        notes.append("未安装 Pillow：image_tools.py（fit / mask / sheet）不可用，画幅适配与打码需要它")

    report = {
        "recommended_mode": mode,
        "reason": reason,
        "reference_support": ref,
        "qa_mode": qa,
        "capabilities": {"generate": gen, "see": args.can_see},
        "checks": {
            "python": sys.version.split()[0],
            "pillow": pillow_ok,
            "requests": has_module("requests"),
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "tesseract": tess[1],
            "doc_libs": {m: has_module(m) for m in ["pdfplumber", "pypdf", "docx", "pptx", "openpyxl"]},
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
    print(f"参考图支持：{ref}    质检方式：{qa}")
    c = report["checks"]
    print(f"Pillow：{c['pillow']}  ffmpeg：{c['ffmpeg']}  tesseract：{c['tesseract']}")
    print(f".env：{report['env']['env_file'] or '未找到'}  RENDER_MODE={mode_cfg}  图片 API：{report['env']['IMAGE_API']['key']}"
          f"  语音转写：{report['env']['TRANSCRIBE_API']}")
    print(f"工作区：{report['env']['workdir']}")
    for n in notes:
        print("· " + n)


if __name__ == "__main__":
    main()
