# Image Passage

[中文](README.md) · MIT License · v0.2.0

Image Passage plans and produces 3:4 image-plus-text carousel posts for **Xiaohongshu (小红书)** and **WeChat 贴图号**. It turns a sentence, an experience or a pile of material into a full set of post images plus a title, body and tags, ready to publish.

**Plan → page-by-page images → publish copy → QA → honest delivery report**

The final delivery has four parts: **title, body (tags at the end), images, and a first comment**. Default limits: title 20 characters, body 800, up to 15 images and 8 tags.

One rule set, three ways to use it:

- a **WorkBuddy expert** called 「图文策划师」;
- an **Agent Skill** for Claude Code, Codex and any other agent that supports `SKILL.md`;
- a **plain repository**: any AI that can read files can follow `skills/image-passage/SKILL.md`.

The skill's working language is Simplified Chinese, because the target platforms are Chinese. The rule files are written in Chinese.

![Demo: 5 pages rendered on the svg route](examples/demo/preview.jpg)

<sub>Demo project in `examples/demo/`. It uses the svg route, which needs no image-generation ability: HTML+CSS is rendered to 1242×1656 PNG.</sub>

## Features

- **The image route follows capability, not model names.**
  - The environment has an image tool → `native`.
  - Text-only model → `svg`: the model writes HTML+CSS with inline SVG, and a script renders it with Chromium.
  - An OpenAI-compatible image API is configured in `.env` → `api`.
- **Each page is built one of three ways.**
  - **G (Generate)**: the image model draws the whole page. For pages with little text, such as a picture cover.
  - **H (Hybrid)**: the image model draws a background with blank zones, and code overlays exact text and screenshots.
  - **S (Static)**: pure HTML+CSS layout, no image model.
  - Text-heavy pages, and pages that must reproduce screenshots faithfully, automatically use H or S. This keeps image models from garbling text.
- **White box.** Every page gets a spec (`spec.md`) that is compiled into `prompt.md` or `page.html`. Everything is archived. Prompts are hidden from the chat by default but can always be opened and edited.
- **A structured planning library:**
  - content: 20 topic domains, 18 reader values, 23 content templates, 5 length formats, 15 hooks;
  - visual: 12 visual styles, 36 layouts, 13 cover types, 39 expressive elements.
- **Style lock.** After the cover (P1) is approved, 13 visual parameters are locked. Colours are written as names, and a script derives the HEX values into `tokens.css`.
- **Optional account profile.** Start right away, or set up an account profile three ways: a quick setup, a full setup, or extracting your style from screenshots of past posts. At the end of each run, the skill asks once whether to save your choices as defaults.
- **Many input types.** Text, screenshots, photos, documents (pdf / docx / pptx / xlsx / csv / html), links, audio and video. Audio and video use an optional transcription API, and ffmpeg extracts video frames.
- **Optional account character, off by default.** Upload your own character art, or use the built-in prompt templates to generate a reference sheet, expressions and poses.
- **First comment.** Each post comes with a first comment the account posts itself: extra details, conditions, or a discussion question. It does not repeat the body and contains no engagement bait or off-platform links.
- **QA.**
  - The render script checks for overflow, off-page elements, font size, fonts, images, overlap and the number of highlights.
  - The copy script checks title, length tier, tags, first comment, absolute claims, efficacy or return promises, and engagement bait.
  - Pages that cannot be visually inspected are reported as such.
- **Open fonts.** 8 OFL Chinese fonts, including Noto Sans SC and LXGW WenKai, are downloaded on demand.

## Install

**Let your AI install it.** Send this to the agent you use (Claude Code, Codex, …). It will follow [INSTALL.md](INSTALL.md) to install the skill and dependencies and run a self-check:

```text
Please install Image Passage following https://github.com/chans-gh/Image-Passage-IP/blob/main/INSTALL.md
```

Manual install:

### Claude Code

```text
/plugin marketplace add chans-gh/Image-Passage-IP
/plugin install image-passage@image-passage-ip
```

Or install only the skill: copy or symlink `skills/image-passage` into `~/.claude/skills/` (global) or a project's `.claude/skills/`.

### Codex

```bash
git clone https://github.com/chans-gh/Image-Passage-IP.git
mkdir -p ~/.agents/skills
ln -s "$PWD/Image-Passage-IP/skills/image-passage" ~/.agents/skills/image-passage
```

For a single project, link it into that project's `.agents/skills/` instead. `skills/image-passage/agents/openai.yaml` provides the display name and default prompt.

### WorkBuddy

The repository root is a WorkBuddy expert package: `.codebuddy-plugin/plugin.json` (manifest), `agents/image-passage.md` (identity and opening), `avatars/expert.png` (avatar) and `skills/image-passage/` (preloaded skill). Import the repository in the WorkBuddy client under 专家市场 → 我的专家 → 创建专家.

### Other agents

Point the agent at `skills/image-passage/SKILL.md`. The rules only need file access. If the scripts cannot run, the steps can be done by hand, and the delivery report states which checks were skipped.

## Dependencies

The render and check scripts need Python 3.9+. Run these from the repository root:

```bash
pip install -r skills/image-passage/scripts/requirements.txt
```

```bash
python -m playwright install chromium
```

```bash
python3 skills/image-passage/scripts/fetch_fonts.py
```

Optional: `ffmpeg` for video frames and audio extraction, and `tesseract` with `chi_sim` for OCR checks.

To check which route the current environment supports:

```bash
python3 skills/image-passage/scripts/env_check.py
```

## `.env` (optional)

You only need `.env` for the `api` route and for audio or video transcription. Copy `.env.example` to `.env` in the directory where the agent runs, or in `image-passage-work/`.

| Variable | Purpose |
|---|---|
| `RENDER_MODE` | `auto` (default) / `native` / `svg` / `api` |
| `IMAGE_API_BASE_URL`, `IMAGE_API_KEY`, `IMAGE_API_MODEL` | OpenAI-compatible image API (`/images/generations`, `/images/edits`) |
| `IMAGE_API_SIZE`, `IMAGE_API_REFERENCE_MODE`, `IMAGE_API_QUALITY` | Size, how reference images are passed, quality parameter |
| `TRANSCRIBE_API_*` | OpenAI-compatible transcription API (`/audio/transcriptions`) |
| `IMAGE_PASSAGE_WORKDIR`, `IMAGE_PASSAGE_FONT_DIR` | Workspace and font cache directories |

`.env` is gitignored. **Never paste keys into the chat.** The scripts never print keys, and `--dry-run` masks them.

## Usage

Things you can say to the agent:

- "帮我做一套关于……的图文" runs the full workflow. By default it stops for your approval twice: on the **plan** and on the **P1 cover**.
- "只策划" (plan only), "只写标题、正文和首条评论" (copy only), "做一张……" (single image).
- "改第 3 页的标题" (edit page 3), "继续" (continue), "看一下 P3 的提示词" (show P3's prompt).
- "设置账号" (set up profile), "做一个账号角色" (build a character).

Work files go to `image-passage-work/<project>/` in the current directory:

```
inputs/  inputs.md  plan.md  style-lock.md  state.json
render/{base.css, tokens.css}
pages/PNN/{spec.md, prompt.md, page.html, base.png, vN.png, qa.md}
final/PNN.png  copy.md
```

Work can resume in a new session: the agent reads `state.json` and `plan.md` rather than relying on chat memory.

## Repository layout

```
.claude-plugin/          Claude Code plugin and marketplace manifests
.codebuddy-plugin/       WorkBuddy expert manifest
agents/image-passage.md  Expert identity and opening (WorkBuddy / Claude Code subagent)
avatars/expert.png       Expert avatar
skills/image-passage/    The skill
├── SKILL.md             Overview: principles, stages, routes, scripts, reference index
├── agents/openai.yaml   Codex display metadata
├── references/          Detailed rules, read per stage on demand
├── templates/           Project file templates
├── scripts/             Python scripts (render, QA, API, input extraction)
└── assets/              Colour table, font table, platform presets, base.css
examples/demo/           5-page demo (svg route)
docs/                    Design docs (Chinese) and the archived V3.1 source rules
```

Maintainer notes for AI agents are in [AGENTS.md](AGENTS.md). A file index is in [llms.txt](llms.txt).

## Open items

- Native image and vision capabilities in Codex and WorkBuddy will be added after the author tests them.
- The thresholds for automatically choosing between G and H (30 characters, 4 points) are initial defaults.
- Platform limits (title 20, body 800, 15 images, 8 tags) were set by the author. Update `references/platforms/*.md` if platform rules change.

Issues and PRs are welcome. Please read [AGENTS.md](AGENTS.md) before changing rules.

## License

Code and rule files are under [MIT](LICENSE). The expert avatar `avatars/expert.png` is the author's own character and is not covered by the MIT license; do not reuse it without permission. Downloaded fonts are under the SIL Open Font License. When you publish generated content, follow platform rules and make sure you have the rights to the material, likenesses and characters you use.
