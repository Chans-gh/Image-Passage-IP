#!/usr/bin/env python3
"""素材提取：把文档、音频、视频转成模型能读的文字和图片（输入归一化用）。

    python3 extract_input.py doc <文件> [--out 文字.txt]
        支持 .pdf .docx .pptx .xlsx .csv .txt .md .html。需要的库缺失时会提示安装。
    python3 extract_input.py frames <视频> --out-dir inputs/frames [--max 12]
        按场景变化抽关键帧（不够时均匀补齐），并生成 sheet.jpg 预览图。需要 ffmpeg。
    python3 extract_input.py audio <视频> --out inputs/audio.mp3
        抽出音轨。需要 ffmpeg。
    python3 extract_input.py transcribe <音频> --out inputs/transcript.txt [--language zh]
        调用 .env 中的 TRANSCRIBE_API_*（OpenAI 兼容 /audio/transcriptions）。需要 requests。
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import die, load_env  # noqa: E402


def need(module: str, pip_name: str):
    try:
        return __import__(module)
    except ImportError:
        die(f"读取这种文件需要 {pip_name}：pip install {pip_name}", 2)


def doc_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".txt", ".md", ".markdown"):
        return path.read_text(encoding="utf-8", errors="replace")
    if ext in (".html", ".htm"):
        raw = path.read_text(encoding="utf-8", errors="replace")
        raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)
        text = re.sub(r"<br\s*/?>|</p>|</div>|</h\d>|</li>", "\n", raw, flags=re.I)
        return html.unescape(re.sub(r"<[^>]+>", "", text))
    if ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                return "\n\n".join(f"[第 {i + 1} 页]\n" + (p.extract_text() or "") for i, p in enumerate(pdf.pages))
        except ImportError:
            pypdf = need("pypdf", "pypdf")
            reader = pypdf.PdfReader(str(path))
            return "\n\n".join(f"[第 {i + 1} 页]\n" + (p.extract_text() or "") for i, p in enumerate(reader.pages))
    if ext == ".docx":
        docx = need("docx", "python-docx")
        d = docx.Document(str(path))
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                parts.append(" | ".join(c.text.strip() for c in row.cells))
        return "\n".join(parts)
    if ext == ".pptx":
        pptx = need("pptx", "python-pptx")
        prs = pptx.Presentation(str(path))
        out = []
        for i, slide in enumerate(prs.slides, 1):
            texts = [sh.text_frame.text for sh in slide.shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()]
            out.append(f"[第 {i} 页]\n" + "\n".join(texts))
        return "\n\n".join(out)
    if ext in (".xlsx", ".xlsm"):
        openpyxl = need("openpyxl", "openpyxl")
        wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
        out = []
        for ws in wb.worksheets:
            out.append(f"[工作表 {ws.title}]")
            for row in ws.iter_rows(values_only=True):
                if any(v is not None for v in row):
                    out.append(" | ".join("" if v is None else str(v) for v in row))
        return "\n".join(out)
    if ext == ".csv":
        with path.open(encoding="utf-8-sig", errors="replace", newline="") as fh:
            return "\n".join(" | ".join(r) for r in csv.reader(fh))
    die(f"暂不支持的文件类型：{ext}。可以让用户粘贴文字或截图。", 2)
    return ""


def cmd_doc(a: argparse.Namespace) -> None:
    text = doc_text(a.file).strip()
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text + "\n", encoding="utf-8")
        print(f"已提取 {len(text)} 字 → {a.out}")
    else:
        print(text)


def ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        die("需要 ffmpeg。没有时请用户截几张关键画面，并提供文字稿。", 2)
    return exe


def duration(video: Path) -> float:
    probe = shutil.which("ffprobe")
    if not probe:
        return 0.0
    out = subprocess.run([probe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)],
                         capture_output=True, text=True)
    try:
        return float(json.loads(out.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0


def cmd_frames(a: argparse.Namespace) -> None:
    exe = ffmpeg()
    a.out_dir.mkdir(parents=True, exist_ok=True)
    for old in a.out_dir.glob("frame_*.jpg"):
        old.unlink()
    subprocess.run([exe, "-v", "error", "-i", str(a.video), "-vf", f"select='gt(scene,{a.scene})',scale=1080:-2",
                    "-vsync", "vfr", "-frames:v", str(a.max), str(a.out_dir / "frame_%03d.jpg")], check=False)
    frames = sorted(a.out_dir.glob("frame_*.jpg"))
    if len(frames) < min(6, a.max):
        dur = duration(a.video) or 60.0
        need_n = a.max - len(frames)
        for i in range(need_n):
            t = dur * (i + 0.5) / need_n
            subprocess.run([exe, "-v", "error", "-ss", f"{t:.2f}", "-i", str(a.video), "-frames:v", "1",
                            "-vf", "scale=1080:-2", str(a.out_dir / f"frame_u{i:03d}.jpg")], check=False)
        frames = sorted(a.out_dir.glob("frame_*.jpg"))
    if not frames:
        die("没有抽到画面，请确认视频文件可以播放")
    try:
        from image_tools import cmd_sheet
        cmd_sheet(argparse.Namespace(out=a.out_dir / "sheet.jpg", files=frames, cols=4, cell=300, label=True, crop=False))
    except SystemExit:
        pass
    print(f"抽取 {len(frames)} 帧 → {a.out_dir}（预览：sheet.jpg）")


def cmd_audio(a: argparse.Namespace) -> None:
    exe = ffmpeg()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([exe, "-v", "error", "-y", "-i", str(a.video), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
                    str(a.out)], check=True)
    print(f"音轨 → {a.out}")


def cmd_transcribe(a: argparse.Namespace) -> None:
    env, _ = load_env()
    base = (env.get("TRANSCRIBE_API_BASE_URL") or "").rstrip("/")
    key = env.get("TRANSCRIBE_API_KEY") or ""
    model = env.get("TRANSCRIBE_API_MODEL") or "whisper-1"
    if not base or not key:
        die("没有配置语音转写（.env 中的 TRANSCRIBE_API_BASE_URL / TRANSCRIBE_API_KEY）。"
            "请用户用手机或会议软件自带的转文字功能，把文字稿粘贴过来。", 3)
    requests = need("requests", "requests")
    with a.audio.open("rb") as fh:
        resp = requests.post(f"{base}/audio/transcriptions", headers={"Authorization": f"Bearer {key}"},
                             data={"model": model, "language": a.language, "response_format": "text"},
                             files={"file": (a.audio.name, fh)}, timeout=600)
    if resp.status_code >= 400:
        die(f"转写接口返回 {resp.status_code}：{resp.text[:300]}")
    text = resp.text.strip()
    if text.startswith("{"):
        try:
            text = json.loads(text).get("text", text)
        except json.JSONDecodeError:
            pass
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text + "\n", encoding="utf-8")
    print(f"转写 {len(text)} 字 → {a.out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="素材提取")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("doc"); p.add_argument("file", type=Path); p.add_argument("--out", type=Path)
    p.set_defaults(func=cmd_doc)
    p = sub.add_parser("frames"); p.add_argument("video", type=Path); p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--max", type=int, default=12); p.add_argument("--scene", type=float, default=0.3)
    p.set_defaults(func=cmd_frames)
    p = sub.add_parser("audio"); p.add_argument("video", type=Path); p.add_argument("--out", type=Path, required=True)
    p.set_defaults(func=cmd_audio)
    p = sub.add_parser("transcribe"); p.add_argument("audio", type=Path); p.add_argument("--out", type=Path, required=True)
    p.add_argument("--language", default="zh"); p.set_defaults(func=cmd_transcribe)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
