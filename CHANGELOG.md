# Changelog

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-11-14

### 变更（破坏性）

- 出图路线精简为两条：`native`（环境自带生图能力）与 `api`（OpenAI 兼容图片接口）。`svg` 路线及其依赖（Playwright／Chromium、系统字体、字体下载）全部移除；两条路线都不具备时为 `none`，只交付策划与文案并说明怎样才能出图。
- 每页只有一种构成方式：**整图生成**——一页的画面与全部文字由生图模型一次性生成。删除 `H`（底图＋HTML 叠加文字）与 `S`（纯 HTML/SVG 排版）。
- 新增能力项 `reference_support`（yes / no / unknown）：生图工具能否接收参考图。需要保真的截图和照片以参考图方式原样传入、不重绘；为 `no` 时含素材的页不能出图。
- `qa_mode` 改为 `visual` / `script+ocr` / `unchecked`；原 `script-only` 并入 `unchecked`（不再有渲染脚本可跑）。

### 移除

- 文件：`assets/css/base.css`、`assets/fonts.json`、`scripts/render_page.py`、`scripts/fetch_fonts.py`、`references/html-recipes.md`、`templates/page.html`、`templates/page-compose.html`、`templates/tokens.css`、`examples/demo/`。
- 依赖：`playwright`（`requirements.txt`）；`.env` 的 `IMAGE_PASSAGE_FONT_DIR`。
- 规则：`visual-system.md` 的「风格 × 渲染路线」「版式 × 渲染路线」两张适配表、L 表的 CSS 类列、E 表的实现列；`prompt-recipes.md` 的「H 页的底图提示词」整节。
- `palette.py` 的 `tokens` 子命令与字体／字号参数；`env_check.py` 的 Chromium 与字体检查。

### 变更

- 保真素材的打码时机明确为「交给生图模型之前」。
- 字体改为只写「字体感」，不再指定字体文件，避免要求复现商用字体字形。
- `examples/demo/copy.md` 改为 `examples/copy-sample.md`，只作 `check_copy.py` 的基线。

### 说明

- **未新增任何字数上限**。单页文字量仍只按 `visual-system.md` 第三节的 L 口径作参考，信息表达优先于迁就模型。

## [0.2.0] - 2026-10-30

### 新增

- 首条评论：每篇默认交付一条由账号自己发出的首条评论（`copywriting.md` 第十四节）；`copy.md` 模板新增小节；`check_copy.py` 检查是否填写、长度（默认 ≤150 字）和合规用语。
- 最终交付固定为四项：标题、正文（末尾附标签）、图片、首条评论（`copywriting.md` 第十二节、`workflow.md` 第七节）。
- `workspace.py status` 检查页数是否超过平台图片上限。
- `INSTALL.md`：写给 AI 的安装步骤（Claude Code、Codex、WorkBuddy、其他 Agent），含依赖、字体、自检和卸载；README 增加「让 AI 帮你装」。
- 专家头像改为作者提供的形象（不在 MIT 授权范围内）。

### 变更

- 平台上限由作者确认，小红书和微信贴图号统一：标题 20 字、正文 800 字、图片 15 张、标签 8 个（`assets/platforms.json`、`references/platforms/*.md`）。
- F5 长套改为 11～15 张。
- 诱导互动词表增加加微信类导流用语。
- 快捷提示改为直白说法：「帮我做一套小红书图文」「只策划，先不出图」「只写标题、正文和首条评论」。
- README 说明 G / H / S 三种构成方式的含义。

## [0.1.0] - 2026-10-29

首个版本：由 V3.1 SOP（`docs/source-v3.1/`）迁移重构。

### 新增

- Agent Skill `skills/image-passage/`：`SKILL.md` 总览，13 份 references，12 个项目模板。
- 三种使用方式：Claude Code 插件（`.claude-plugin/`）、Codex（`agents/openai.yaml`）、WorkBuddy 专家（`.codebuddy-plugin/`、`agents/image-passage.md`）。
- 按能力分流的出图路线：`native` / `svg` / `api`；每页构成方式 G / H / S。
- 页面规格单 → 提示词 / HTML 的白盒流程，全部存档。
- 可选的首次设置（四种开场）与 `profile.md`，结束时询问是否存为默认。
- 输入归一化 `inputs.md`：文档提取、音视频转写（可选接口）、ffmpeg 抽帧。
- 可选的账号角色：用户上传，或用提示词模板生成设定图、表情组、动作图。
- 脚本：`workspace.py`、`render_page.py`、`call_image_api.py`、`image_tools.py`、`palette.py`、`check_copy.py`、`extract_input.py`、`ocr_check.py`、`fetch_fonts.py`、`env_check.py`。
- 资产：75 个颜色名、8 款 OFL 中文字体、平台预设、`base.css` 版式与组件。
- 5 页演示 `examples/demo/`（svg 路线）。

### 移除

- 原 SOP 中创作者本人的 IP 角色信息。角色功能改为通用、默认不启用。

### 待核实

- 小红书、微信贴图号的标题、正文、标签、图片数上限（`assets/platforms.json` 标为未核实）。
