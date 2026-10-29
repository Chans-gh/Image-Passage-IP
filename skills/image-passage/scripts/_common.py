"""Image-Passage 脚本公共函数：路径、.env 读取、输出规格。

只依赖 Python 标准库。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
TEMPLATES_DIR = SKILL_DIR / "templates"

DEFAULT_WIDTH = 1242
DEFAULT_HEIGHT = 1656


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def env_file_candidates() -> list[Path]:
    """.env 的查找顺序：IMAGE_PASSAGE_ENV → 当前目录 → 工作区目录。不读取技能目录。"""
    paths = []
    if os.environ.get("IMAGE_PASSAGE_ENV"):
        paths.append(Path(os.environ["IMAGE_PASSAGE_ENV"]).expanduser())
    paths.append(Path.cwd() / ".env")
    wd = os.environ.get("IMAGE_PASSAGE_WORKDIR")
    paths.append((Path(wd).expanduser() if wd else Path.cwd() / "image-passage-work") / ".env")
    return paths


def load_env() -> tuple[dict[str, str], Path | None]:
    """合并 .env 与进程环境变量；进程环境变量优先。返回 (值, 使用的 .env 路径)。"""
    merged: dict[str, str] = {}
    used = None
    for path in env_file_candidates():
        if path.is_file():
            merged.update(_parse_env_file(path))
            used = path
            break
    for key, value in os.environ.items():
        if key.startswith(("RENDER_", "IMAGE_", "TRANSCRIBE_", "OUTPUT_")) and value:
            merged[key] = value
    return merged, used


def workdir(env: dict[str, str] | None = None) -> Path:
    env = env if env is not None else load_env()[0]
    wd = env.get("IMAGE_PASSAGE_WORKDIR") or os.environ.get("IMAGE_PASSAGE_WORKDIR")
    return Path(wd).expanduser().resolve() if wd else (Path.cwd() / "image-passage-work").resolve()


def font_dir(env: dict[str, str] | None = None) -> Path:
    env = env if env is not None else load_env()[0]
    fd = env.get("IMAGE_PASSAGE_FONT_DIR") or os.environ.get("IMAGE_PASSAGE_FONT_DIR")
    if fd:
        return Path(fd).expanduser()
    return Path.home() / ".cache" / "image-passage" / "fonts"


def output_size(env: dict[str, str] | None = None) -> tuple[int, int]:
    env = env if env is not None else load_env()[0]
    try:
        return int(env.get("OUTPUT_WIDTH") or DEFAULT_WIDTH), int(env.get("OUTPUT_HEIGHT") or DEFAULT_HEIGHT)
    except ValueError:
        return DEFAULT_WIDTH, DEFAULT_HEIGHT


def mask_secret(value: str | None) -> str:
    if not value:
        return "(未设置)"
    return "已设置（" + str(len(value)) + " 位，已隐藏）"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def die(message: str, code: int = 1) -> None:
    print("错误：" + message, file=sys.stderr)
    sys.exit(code)
