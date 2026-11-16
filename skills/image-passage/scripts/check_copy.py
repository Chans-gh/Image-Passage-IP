#!/usr/bin/env python3
"""发布文案与规格单「上图文字」检查：字数口径、平台上限、标签数、违规用语。

    python3 check_copy.py <项目>/copy.md [--platform xiaohongshu] [--tier S3]
        [--title-max 20] [--comment-max 150] [--no-comment] [--commercial] [--domain D10] [--profile image-passage-work/profile.md]
    python3 check_copy.py <项目>/copy.md --spec-dir <项目>/pages
    python3 check_copy.py --spec-dir <项目>/pages                 # 只查图上文字，不查 copy.md
    python3 check_copy.py --plan <项目>/plan.md                   # 第 ⑥ 阶段：从 plan.md 查图上文字
    python3 check_copy.py <项目>/copy.md --plan <项目>/plan.md --spec-dir <项目>/pages
    python3 check_copy.py --count "任意一段文字"

图上文字有两个来源，可任选或同时给：
  --plan <项目>/plan.md    读「## 逐页策划」里每个 ### PNN 页块的「上图文字：」条目；
  --spec-dir <项目>/pages  读每个 P*/spec.md 的「## 上图文字」小节。
同一页码在两个来源里都出现时分别报告、不合并——两者的差异本身就是「提取有没有出错」的信号。

检查项对两种来源完全一致：空文字、占位词、绝对化／功效／收益／诱导用语和账号禁用词。
提取到的逐条文字写进报告的 spec.sources[].pages，供人工照着逐字核对。
图上文字只统计字数、不与任何上限比较——本技能不设图上文字字数上限，字数仅供人工判断。
错别字与繁简混用无法用词表可靠检出，仍需看图或人工逐字核对。

字数口径（references/copywriting.md）：可见字符粗计，汉字、字母、数字、标点、表情各计 1，
不计空格和换行；标签、链接、交付说明另计。这是内部一致性口径，不代表平台的计数方式。
copy.md 的格式见 templates/copy.md（按「## 标题」「## 正文」「## 标签」等小节读取）；
spec.md、plan.md 的格式见 templates/spec.md、templates/plan.md。
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
          "一键三连", "评论区领取", "关注我领", "互粉", "互赞", "加微信", "加我微信", "加V", "加v", "+V", "+v"]
FIRST_PERSON = ["亲测", "我试过", "我用了", "我坚持", "我靠", "实测", "用了一个月", "真实体验"]
DISCLAIMER = ["不构成", "仅供参考", "请咨询", "以医生", "以专业", "以兽医", "个体差异"]
SENSITIVE_DOMAINS = {"D10", "D14", "D15", "D16", "D17", "D20", "D07"}

SPEC_SECTION = "上图文字"
SPEC_QUOTE_RE = re.compile(r"「(.*?)」")
# 占位词：对应 page-generation.md 第五节的硬规则——「待补素材」不能作为最终页面里的占位内容
SPEC_PLACEHOLDERS = ["待补", "待定", "待填", "TODO", "TBD", "占位", "稍后补", "XXXX", "×××"]
# 纯图页的显式声明：整行就是这些标记之一时，本页视为没有图上文字，不报空文字
NO_TEXT_MARKERS = {"无文字", "无图上文字", "不出现文字", "留白", "无"}


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


def level_of(line: str) -> str:
    """取一行「- 主标题：「文字」」里的层级名。没有可用的层级名时返回占位提示。"""
    head = line.split("「", 1)[0]
    head = head.strip().lstrip("-*·—").strip().rstrip("：:").strip()
    return head or "（未标层级）"


def declares_no_text(rows: list[str]) -> bool:
    """整行只是「无文字」这类声明时，本页视为没有图上文字。

    带「」的行不算，避免把主标题恰好是「无文字」的页误判成纯图页。
    """
    for row in rows:
        if "「" in row:
            continue
        value = re.sub(r"^[-*·—]\s*", "", row.strip())
        if "：" in value or ":" in value:
            value = re.split(r"[：:]", value)[-1]
        if value.strip() in NO_TEXT_MARKERS:
            return True
    return False


def spec_page_lines(path: Path) -> tuple[list[dict], list[dict], bool] | None:
    """读一页 spec.md 的「## 上图文字」小节。

    返回 (逐条清单, 未标注行, 是否声明无文字)；没有该小节时返回 None。
    逐条形如 {"level": "主标题", "text": "黄叶先别急着浇水", "count": 7}；
    未用「」标注的行形如 {"level": ..., "raw": ...}，无法检查，只作提示。
    纯图页在「上图文字」小节写「- 无文字」，此时不报空文字。
    """
    sec = sections(strip_comments(path.read_text(encoding="utf-8")))
    if SPEC_SECTION not in sec:
        return None
    rows = [line.strip() for line in sec[SPEC_SECTION].splitlines() if line.strip()]
    no_text = declares_no_text(rows)
    marked: list[dict] = []
    unmarked: list[dict] = []
    for line in rows:
        if declares_no_text([line]):
            continue
        level = level_of(line)
        quotes = SPEC_QUOTE_RE.findall(line)
        if not quotes:
            unmarked.append({"level": level, "raw": re.sub(r"^[-*·—]\s*", "", line)})
            continue
        for text in quotes:
            marked.append({"level": level, "text": text, "count": count_chars(text)})
    return marked, unmarked, no_text


def plan_text_area(body: str) -> tuple[list[str], bool]:
    """在一个 ### 页块里找「- 上图文字：」，返回 (文字区各行, 是否找到该条目)。

    文字区 = 该条目同一行的内容，加上它下面所有缩进更深的行，直到下一个同级或更浅缩进的条目。
    """
    lines = body.splitlines()
    start = None
    inline = ""
    indent = 0
    for idx, line in enumerate(lines):
        m = re.match(r"^(\s*)-\s*上图文字[：:]\s*(.*)$", line)
        if m:
            start, indent, inline = idx, len(m.group(1)), m.group(2).strip()
            break
    if start is None:
        return [], False
    area: list[str] = []
    if inline:
        # 同一行直接跟内容时，层级名按「上图文字」记
        area.append("- " + SPEC_SECTION + "：" + inline)
    for line in lines[start + 1:]:
        if not line.strip():
            continue
        if len(line) - len(line.lstrip()) <= indent:
            break
        area.append(line.strip())
    return area, True


def plan_pages(path: Path, add) -> list[dict]:
    """按 ### PNN 切分 plan.md「## 逐页策划」，取每页「上图文字」条目。"""
    pages: list[dict] = []
    text = strip_comments(path.read_text(encoding="utf-8"))
    parts = re.split(r"(?m)^###\s+(P\d{2})[^\n]*$", text)
    for i in range(1, len(parts), 2):
        page = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        area, found = plan_text_area(body)
        no_text = declares_no_text(area)
        lines: list[dict] = []
        unmarked: list[dict] = []
        for raw in area:
            if declares_no_text([raw]):
                continue
            level = level_of(raw)
            quotes = SPEC_QUOTE_RE.findall(raw)
            if not quotes:
                unmarked.append({"level": level, "raw": re.sub(r"^[-*·—]\s*", "", raw)})
                continue
            for item in quotes:
                lines.append({"level": level, "text": item, "count": count_chars(item)})
        if not found:
            add("warning", "plan", f"plan.md {page} 没有上图文字小节")
        elif not lines and not no_text:
            add("error", "plan-empty", f"plan.md {page} 的上图文字是空的")
        pages.append({"page": page, "lines": lines, "unmarked": unmarked,
                      "found": found, "no_text": no_text})
    return pages


def spec_dir_pages(spec_dir: Path, add) -> list[dict]:
    """扫描 <项目>/pages 下每个 P*/spec.md 的「## 上图文字」小节。"""
    pages: list[dict] = []
    paths = sorted(spec_dir.glob("P*/spec.md"))
    if not paths:
        add("warning", "spec", f"{spec_dir} 下没有找到 pages/P*/spec.md，未检查图上文字")
    for path in paths:
        page = path.parent.name
        parsed = spec_page_lines(path)
        if parsed is None:
            add("warning", "spec", f"spec.md {page} 缺少「{SPEC_SECTION}」小节，无法检查图上文字")
            pages.append({"page": page, "lines": [], "unmarked": [], "found": False, "no_text": False})
            continue
        marked, unmarked, no_text = parsed
        pages.append({"page": page, "lines": marked, "unmarked": unmarked,
                      "found": True, "no_text": no_text})
    return pages


def locate_hits(hits: list[str], located: list[tuple[str, dict]]) -> str:
    """把命中的词定位到「来源 页码 的「层级」：「整句」」。"""
    parts = []
    for hit in hits:
        where = [f"{label}：「{item['text']}」" for label, item in located if hit in item["text"]]
        parts.append(hit + ("（" + "、".join(where) + "）" if where else ""))
    return "、".join(parts)


def check_pages(kind: str, path: Path, pages: list[dict], add, commercial: bool, profile: Path | None) -> dict:
    """对一份来源的全部页做同一套图上文字检查，返回报告片段。

    空文字、占位词、合规词、字数清单四种检查对 plan.md 和 spec.md 完全一致，
    所以这几种 issue 的类型用来源中立的 text-* 前缀；来源由 detail 里的文件名区分。
    """
    prefix = "plan.md" if kind == "plan" else "spec.md"
    located: list[tuple[str, dict]] = []
    for pg in pages:
        head = f"{prefix} {pg['page']}"
        if pg.get("no_text"):
            add("info", "text-none", f"{head} 声明本页无图上文字")
            continue
        for item in pg["unmarked"]:
            add("info", "text-unmarked", f"{head} 的「{item['raw']}」未用「」标注，无法检查")
        for item in pg["lines"]:
            where = f"{head} 的「{item['level']}」"
            located.append((where, item))
            if not item["text"].strip():
                add("error", "text-empty", f"{where}是空的（模板初始状态或尚未填写）")
            hits = find(item["text"], SPEC_PLACEHOLDERS)
            if hits:
                add("error", "text-placeholder", f"{where}含占位词：" + "、".join(hits))
        if pg["lines"]:
            total = sum(item["count"] for item in pg["lines"])
            add("info", "text-count", f"{head} 上图文字共 {total} 字")

    joined = "\n".join(item["text"] for _, item in located)
    hits = find(joined, ABSOLUTE)
    if hits:
        add("error" if commercial else "warning", "text-absolute",
            "图上文字绝对化用语：" + locate_hits(hits, located))
    for words, issue_kind, label in [(EFFICACY, "text-efficacy", "功效宣称"),
                                     (FINANCE, "text-finance", "收益承诺"),
                                     (INDUCE, "text-induce", "诱导互动")]:
        hits = find(joined, words)
        if hits:
            add("error", issue_kind, "图上文字" + label + "：" + locate_hits(hits, located))
    hits = find(joined, profile_banned(profile))
    if hits:
        add("error", "text-banned", "图上文字账号禁用词：" + locate_hits(hits, located))

    return {"kind": kind, "path": str(path),
            "pages": [{"page": pg["page"], "lines": pg["lines"]} for pg in pages]}


def main() -> None:
    parser = argparse.ArgumentParser(description="发布文案与图上文字检查")
    parser.add_argument("copy", nargs="?", type=Path)
    parser.add_argument("--spec-dir", type=Path, help="项目 pages/ 目录；检查其中每个 P*/spec.md 的「上图文字」小节")
    parser.add_argument("--plan", type=Path, help="项目 plan.md；检查「逐页策划」里每页的「上图文字」")
    parser.add_argument("--count", help="只统计一段文字的字数")
    parser.add_argument("--platform", choices=["xiaohongshu", "wechat-tietu"])
    parser.add_argument("--tier", choices=list(TIERS))
    parser.add_argument("--title-max", type=int, default=20)
    parser.add_argument("--cover-max", type=int, default=14)
    parser.add_argument("--comment-max", type=int, default=150, help="首条评论的项目默认上限")
    parser.add_argument("--no-comment", action="store_true", help="本次不交付首条评论")
    parser.add_argument("--tags-min", type=int, default=3)
    parser.add_argument("--tags-max", type=int, default=6)
    parser.add_argument("--commercial", action="store_true", help="商业合作或推荐内容：绝对化用语记为错误")
    parser.add_argument("--domain", help="主题领域编号，如 D10；敏感领域检查提示语")
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()

    if args.count is not None:
        print(count_chars(args.count))
        return
    if args.copy is not None and not args.copy.is_file():
        parser.error(f"copy.md 路径不存在：{args.copy}")
    if args.plan is not None and not args.plan.is_file():
        parser.error(f"plan.md 路径不存在：{args.plan}")
    if args.spec_dir is not None and not args.spec_dir.is_dir():
        parser.error(f"--spec-dir 不是目录：{args.spec_dir}")
    if not args.copy and not args.plan and not args.spec_dir:
        parser.error("需要 copy.md 路径、--plan 或 --spec-dir 之一")

    issues: list[dict] = []

    def add(level: str, kind: str, detail: str) -> None:
        issues.append({"level": level, "type": kind, "detail": detail})

    file_field = None
    platform = args.platform
    tier = args.tier
    commercial = args.commercial
    n_title = n_body = n_comment = n_tags = 0

    if args.copy:
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
        comment = sec.get("首条评论", "")

        limits = load_json(ASSETS_DIR / "platforms.json").get(platform or "", {}) if platform else {}
        n_title, n_body = count_chars(title), count_chars(re.sub(r"https?://\S+", "", body))
        n_tags = len(tags)
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

        n_comment = count_chars(comment)
        if not comment and not args.no_comment:
            add("warning", "comment", "缺少首条评论（不需要时加 --no-comment）")
        elif n_comment > args.comment_max:
            add("warning", "comment", f"首条评论 {n_comment} 字，超过项目默认 {args.comment_max} 字")

        full = "\n".join([title, body, cover, comment])
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

        file_field = str(args.copy)

    sources = []
    if args.plan is not None:
        sources.append(check_pages("plan", args.plan, plan_pages(args.plan, add), add, commercial, args.profile))
    if args.spec_dir is not None:
        sources.append(check_pages("spec-dir", args.spec_dir, spec_dir_pages(args.spec_dir, add), add, commercial, args.profile))
    spec = None
    if sources:
        spec = {"sources": sources,
                "total_pages": len({pg["page"] for src in sources for pg in src["pages"]})}

    report = {"file": file_field, "platform": platform, "tier": tier,
              "counts": {"title": n_title, "body": n_body, "tags": n_tags, "comment": n_comment},
              "issues": issues,
              "errors": sum(i["level"] == "error" for i in issues),
              "warnings": sum(i["level"] == "warning" for i in issues),
              "spec": spec}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
