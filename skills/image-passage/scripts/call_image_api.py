#!/usr/bin/env python3
"""调用外部图片 API（api 路线）。默认按 OpenAI 兼容格式：

    无参考图：POST {IMAGE_API_BASE_URL}/images/generations   JSON
    有参考图：POST {IMAGE_API_BASE_URL}/images/edits         multipart，字段 image[]

    python3 call_image_api.py --prompt-file pages/P03/prompt.md --out pages/P03/v1.png \
        [--ref final/P01.png --ref pages/P02/v1.png] [--dry-run]

读取 .env：IMAGE_API_BASE_URL / IMAGE_API_KEY / IMAGE_API_MODEL / IMAGE_API_SIZE /
IMAGE_API_REFERENCE_MODE / IMAGE_API_QUALITY。结果自动适配为 3:4（1242×1656），
原始返回图另存为 <out>.raw.png。KEY 不会被打印。

依赖：requests、Pillow。
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import die, load_env, mask_secret  # noqa: E402


def extract_prompt(text: str) -> str:
    """prompt.md 里如果有 ```text 代码块，只取第一个代码块；否则取全文。"""
    m = re.search(r"```(?:text)?\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="调用 OpenAI 兼容图片 API")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt")
    src.add_argument("--prompt-file", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ref", action="append", type=Path, default=[], help="参考图，可多次")
    parser.add_argument("--size")
    parser.add_argument("--model")
    parser.add_argument("--fit", default="cover", choices=["cover", "contain", "none"])
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env, env_path = load_env()
    base = (env.get("IMAGE_API_BASE_URL") or "").rstrip("/")
    key = env.get("IMAGE_API_KEY") or ""
    model = args.model or env.get("IMAGE_API_MODEL") or ""
    size = args.size or env.get("IMAGE_API_SIZE") or "1024x1536"
    ref_mode = (env.get("IMAGE_API_REFERENCE_MODE") or "edits").lower()
    quality = env.get("IMAGE_API_QUALITY") or ""
    prompt = args.prompt if args.prompt else extract_prompt(args.prompt_file.read_text(encoding="utf-8"))

    for ref in args.ref:
        if not ref.is_file():
            die(f"参考图不存在：{ref}")
    use_edits = bool(args.ref) and ref_mode == "edits"
    endpoint = f"{base}/images/{'edits' if use_edits else 'generations'}"
    summary = {
        "env_file": str(env_path) if env_path else None,
        "endpoint": endpoint if base else "(IMAGE_API_BASE_URL 未设置)",
        "model": model or "(未设置)",
        "key": mask_secret(key),
        "size": size,
        "references": [str(r) for r in args.ref] if use_edits else [],
        "references_dropped": [str(r) for r in args.ref] if args.ref and not use_edits else [],
        "prompt_chars": len(prompt),
    }
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return
    if not base or not key:
        die("api 模式需要在 .env 中设置 IMAGE_API_BASE_URL 和 IMAGE_API_KEY（见 .env.example）")
    if summary["references_dropped"]:
        print("提示：IMAGE_API_REFERENCE_MODE=none，参考图不会传给接口，一致性只靠提示词。", file=sys.stderr)

    try:
        import requests
    except ImportError:
        die("需要 requests：pip install requests", 2)

    headers = {"Authorization": f"Bearer {key}"}
    payload: dict[str, str] = {"prompt": prompt, "size": size, "n": "1"}
    if model:
        payload["model"] = model
    if quality:
        payload["quality"] = quality
    try:
        if use_edits:
            files = [("image[]", (r.name, r.open("rb"), "image/png")) for r in args.ref]
            resp = requests.post(endpoint, headers=headers, data=payload, files=files, timeout=args.timeout)
        else:
            body = dict(payload, n=1)
            resp = requests.post(endpoint, headers=headers, json=body, timeout=args.timeout)
    except requests.RequestException as exc:
        die(f"请求失败：{exc}")
    if resp.status_code >= 400:
        die(f"接口返回 {resp.status_code}：{resp.text[:500]}")
    data = resp.json()
    try:
        item = data["data"][0]
    except (KeyError, IndexError, TypeError):
        die(f"无法解析返回结果：{json.dumps(data, ensure_ascii=False)[:500]}")

    raw = args.out.with_suffix(".raw.png")
    raw.parent.mkdir(parents=True, exist_ok=True)
    if item.get("b64_json"):
        raw.write_bytes(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        img = requests.get(item["url"], timeout=args.timeout)
        img.raise_for_status()
        raw.write_bytes(img.content)
    else:
        die("返回结果里没有 b64_json 或 url")

    if args.fit == "none":
        raw.replace(args.out)
        print(f"已保存 {args.out}")
    else:
        from image_tools import fit_image
        w, h = fit_image(raw, args.out, args.fit)
        print(f"已保存 {args.out}（{w}×{h}，原图 {raw}）")
    if item.get("revised_prompt"):
        print("接口改写后的提示词：" + item["revised_prompt"][:300])


if __name__ == "__main__":
    main()
