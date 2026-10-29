#!/usr/bin/env python3
"""发布文案检查：字数口径、平台上限、标签数、违规用语。

    python3 check_copy.py <项目>/copy.md [--platform xiaohongshu] [--tier S3]
        [--title-max 20] [--commercial] [--domain D10] [--profile image-passage-work/profile.md]
    python3 check_copy.py --count "任意一段文字"

字数口径（references/copywriting.md）：可见字符粗计，汉字、字母、数字、标点、表情各计 1，
不计空格和换行；标签、链接、交付说明另计。这是内部一致性口径，不代表平台的计数方式。
copy.md 的格式见 templates/copy.md（按「## 标题」「## 正文」「## 标签」等小节读取）。
只依赖标准库。退出码：有 error 时为 1。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ASSETS_DIR, load_json  # noqa: E402

TIERS = {"S0": (0, 50), "S1": (50, 150), "S2": (150, 300), "S3": (300, 500), "S4": (500, 800)}
# 支持正则：「第一」排除「第一步、第一次」等序数用法
ABSOLUTE = ["最好", "最强", "最佳", "最优", "最便宜", "最有效", "最安全", "最低价", r"第一(?![步次天页张周月年遍眼口轮期章节条点组印阶反时个件课季集篇])",
            "唯一", "顶级", "极致",
            "100%", "百分百", "绝对", "万能", "永久", "零风险", "国家级", "世界级", "史上", "全网最"]
EFFICACY = ["治疗", "根治", "治愈", "药到病除", "立竿见影", "包治", "疗效", "消炎", "祛斑", "减肥神器", "七天瘦"]
FINANCE = ["稳赚", "保本", "必涨", "躺赚", "翻倍", "收益保证", "无风险收益"]
INDUCE = ["点赞过", "赞过百", "评论扣", "扣1", "扣 1", "关注后私信", "私信领取", "私信领", "求关注", "转发给",
          "一键三连", "评论区领取", "关注我领", "互粉", "互赞"]
FIRST_PERSON = ["亲测", "我试过", "我用了", "我坚持", "我靠", "实测", "用了一个月", "真实体验"]
DISCLAIMER = ["不构成", "仅供参考", "请咨询", "以医生", "以专业", "以兽医", "个体差异"]
SENSITIVE_DOMAINS = {"D10", "D14", "D15", "D16", "D17", "D20", "D07"}


def count_chars(text: str) -> int:
    n = 0
    zwj = 0
    for ch in text:
        if ch.isspace():
            continue
        cp = ord(ch)
        if ch == "‍":
            zwj += 1
            continue
        if cp in (0xFE0E, 0xFE0F) or 0x1F3FB <= cp <= 0x1F3FF or unicodedata.combining(ch):
            continue
        n += 1
    return max(0, n - zwj)


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def sections(md: str) -> dict[str, str]:
    out: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current:
                out[current] = "\n".join(buf).strip()
            current, buf = m.group(1), []
        elif current:
            buf.append(line)
    if current:
        out[current] = "\n".join(buf).strip()
    return out


def find(text: str, words: list[str]) -> list[str]:
    hits = set()
    for word in words:
        m = re.search(word, text) if any(c in word for c in "(?[") else (word if word in text else None)
        if m:
            hits.add(m.group(0) if hasattr(m, "group") else word)
    return sorted(hits)


def profile_banned(path: Path | None) -> list[str]:
    if not path or not path.is_file():
        return []
    m = re.search(r"禁用词[：:]\s*(.+)", path.read_text(encoding="utf-8"))
    if not m:
        return []
    return [w.strip() for w in re.split(r"[、,，/\s]+", m.group(1)) if w.strip() and "(" not in w and "（" not in w]


def main() -> None:
    parser = argparse.ArgumentParser(description="发布文案检查")
    parser.add_argument("copy", nargs="?", type=Path)
    parser.add_argument("--count", help="只统计一段文字的字数")
    parser.add_argument("--platform", choices=["xiaohongshu", "wechat-tietu"])
    parser.add_argument("--tier", choices=list(TIERS))
    parser.add_argument("--title-max", type=int, default=20)
    parser.add_argument("--cover-max", type=int, default=14)
    parser.add_argument("--tags-min", type=int, default=3)
    parser.add_argument("--tags-max", type=int, default=6)
    parser.add_argument("--commercial", action="store_true", help="商业合作或推荐内容：绝对化用语记为错误")
    parser.add_argument("--domain", help="主题领域编号，如 D10；敏感领域检查提示语")
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()

    if args.count is not None:
        print(count_chars(args.count))
        return
    if not args.copy or not args.copy.is_file():
        parser.error("需要 copy.md 路径")

    raw = args.copy.read_text(encoding="utf-8")
    meta = dict(re.findall(r"(平台|字数档|主模板|领域|商业)[：:]\s*([A-Za-z0-9\-]+|是|否)", raw))
    platform = args.platform or {"xiaohongshu": "xiaohongshu", "wechat-tietu": "wechat-tietu"}.get(meta.get("平台", ""), None)
    tier = args.tier or (meta.get("字数档") if meta.get("字数档") in TIERS else None)
    domain = args.domain or meta.get("领域")
    commercial = args.commercial or meta.get("商业") == "是"
    sec = {k: strip_comments(v).strip() for k, v in sections(raw).items()}

    title = sec.get("标题", "").splitlines()[0].strip() if sec.get("标题") else ""
    body = sec.get("正文", "")
    tags = re.findall(r"#[^\s#]+", sec.get("标签", ""))
    cover = sec.get("封面主文案", "")
    issues: list[dict] = []

    def add(level: str, kind: str, detail: str) -> None:
        issues.append({"level": level, "type": kind, "detail": detail})

    limits = load_json(ASSETS_DIR / "platforms.json").get(platform or "", {}) if platform else {}
    n_title, n_body = count_chars(title), count_chars(re.sub(r"https?://\S+", "", body))
    if not title:
        add("error", "title", "缺少标题")
    elif n_title > args.title_max:
        add("warning", "title", f"标题 {n_title} 字，超过项目默认 {args.title_max} 字")
    if limits.get("title_max") and n_title > limits["title_max"]:
        add("error", "title", f"标题 {n_title} 字，超过{limits['name']}上限 {limits['title_max']} 字")
    if not body:
        add("error", "body", "缺少正文")
    if tier:
        lo, hi = TIERS[tier]
        if not lo <= n_body <= hi:
            add("warning", "body", f"正文 {n_body} 字，不在 {tier}（{lo}～{hi} 字）范围内")
    if limits.get("body_max") and n_body > limits["body_max"]:
        add("error", "body", f"正文 {n_body} 字，超过{limits['name']}上限 {limits['body_max']} 字")
    if tags and not args.tags_min <= len(tags) <= args.tags_max:
        add("warning", "tags", f"标签 {len(tags)} 个，建议 {args.tags_min}～{args.tags_max} 个")
    if limits.get("tags_max") and len(tags) > limits["tags_max"]:
        add("error", "tags", f"标签 {len(tags)} 个，超过{limits['name']}上限 {limits['tags_max']} 个")
    if cover:
        first = cover.splitlines()[0].strip()
        if count_chars(first) > args.cover_max:
            add("warning", "cover", f"封面主标题 {count_chars(first)} 字，超过 {args.cover_max} 字（大字报可放宽到 20）")

    full = "\n".join([title, body, cover])
    hits = find(full, ABSOLUTE)
    if hits:
        add("error" if commercial else "warning", "absolute", "绝对化用语：" + "、".join(hits))
    for words, kind, label in [(EFFICACY, "efficacy", "功效宣称"), (FINANCE, "finance", "收益承诺"),
                               (INDUCE, "induce", "诱导互动")]:
        hits = find(full, words)
        if hits:
            add("error", kind, f"{label}：" + "、".join(hits))
    hits = find(full, profile_banned(args.profile))
    if hits:
        add("error", "banned", "账号禁用词：" + "、".join(hits))
    hits = find(full, FIRST_PERSON)
    if hits:
        add("info", "first-person", "第一人称体验表述（需有用户提供的真实依据）：" + "、".join(hits))
    if domain in SENSITIVE_DOMAINS and not find(full + sec.get("合规标注", ""), DISCLAIMER):
        add("warning", "disclaimer", f"{domain} 属于敏感领域，正文或合规标注里没有找到边界提示语")
    if commercial and "合作" not in (sec.get("合规标注", "") + body):
        add("error", "commercial", "商业内容未标注合作关系")
    if not platform:
        add("info", "platform", "未指定平台，未检查平台上限")
    elif not limits.get("verified"):
        add("info", "platform", f"{limits.get('name', platform)}的上限尚未核实，发布前以 App 实际限制为准")

    report = {"file": str(args.copy), "platform": platform, "tier": tier,
              "counts": {"title": n_title, "body": n_body, "tags": len(tags)},
              "issues": issues,
              "errors": sum(i["level"] == "error" for i in issues),
              "warnings": sum(i["level"] == "warning" for i in issues)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
