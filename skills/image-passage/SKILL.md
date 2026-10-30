---
name: image-passage
description: >-
  Plan and produce image-plus-text carousel posts (图文笔记) for Xiaohongshu 小红书
  and WeChat 贴图号 at 3:4: topic verification, template and visual style
  selection, page-by-page images via the environment's native image tool, HTML/SVG
  rendering, or a user-configured image API, optional reusable characters, and
  publish copy (title, body, tags, first comment) with QA. Use when the user wants a 小红书/贴图 post or carousel, only
  a plan, only the title and body copy, to edit or regenerate one page, to set up
  their account profile, or to build a reusable account character.
license: MIT
compatibility: >-
  Works in any agent that can read files. Rendering and checks need Python 3.9+;
  HTML rendering needs Playwright with Chromium; fonts are downloaded on demand.
  Optional: ffmpeg (video), tesseract with chi_sim (OCR), an OpenAI-compatible
  image or transcription API configured in .env.
metadata:
  version: "0.2.0"
  repository: "https://github.com/chans-gh/Image-Passage-IP"
  language: "zh-CN"
title: "图文策划与出图"
summary: "小红书 / 微信贴图号整套图文的策划、出图、文案与质检"
read_when:
  - 用户要做小红书或微信贴图号图文、套图、轮播图、单图笔记
  - 用户说「用 SOP 做」、只策划、只写标题正文、生成或修改某一页
  - 用户要设置账号配置，或建立、使用可复用的账号角色
---

# Image Passage：图文策划与出图

把一句话、一段经历或一堆素材，做成一套可以直接发布的 3:4 图文：**策划 → 逐页出图 → 标题正文标签与首条评论 → 质检 → 如实交付**。

最终交付四项，顺序固定：**标题、正文（末尾附标签）、图片、首条评论**。

本文件是总览。细则在 `references/`，按阶段**需要时再读**，不要一次全部读入。

## 不可覆盖的原则

任何配置、授权和用户要求都不能覆盖：

1. **不虚构**来源、亲测、经历、数据、官方结论、评论和用户反馈。明确标注的示例可以用，但不能改称真实证据。
2. **如实报告**：不把未完成说成已完成；免确认授权不说成用户看图确认过；无法检查的页写「未经视觉检查」。
3. **素材保真**：真实截图和照片的关键文字、数值、状态不被改变；需要保真的素材原样嵌入，不交给生图模型重画。
4. **一页一图**：每张正式图片只对应一页；不用多页拼版、合集裁切冒充单页。
5. **信息隔离**：生成某一页时，只把这一页的规格单、风格锁和参考图交给出图环节。
6. **密钥安全**：KEY 只放在用户自己的 `.env`；不要求用户在对话里发 KEY，不打印、不写进任何文件。
7. **权利与隐私**：截图中的个人信息先遮挡；他人肖像、作品、角色需要授权；不仿制知名 IP。
8. **平台上限**是外部硬约束（当前：标题 20 字、正文 800 字、图片 15 张、标签 8 个，见 `references/platforms/`），不能被配置覆盖。

## 路径约定

- `<skill>`：本技能目录（本文件所在目录）。脚本：`python3 <skill>/scripts/xxx.py`。
- 工作区：当前目录下的 `image-passage-work/`（`.env` 的 `IMAGE_PASSAGE_WORKDIR` 可改）。
  - `profile.md`：账号长期配置（可选）
  - `_assets/characters/`、`_assets/style-refs/`、`_assets/library/`：跨项目资产
  - `<项目名>/`：每个项目一个目录（见下文「项目文件」）
- `.env`：放在当前目录或工作区，模板是仓库根目录的 `.env.example`。

## 阶段总览

| 阶段 | 做什么 | 读 | 命令 |
|---|---|---|---|
| ⓪ 初始化 | 没有 profile 时给四个选择（直接开始 / 快速设置 / 完整设置 / 从已有内容提取）；用户直接提需求就跳过 | `onboarding.md` | `workspace.py init` |
| ① 接收输入 | 归一化进 `inputs.md`，标用途和可信度；文档、音视频先提取 | `inputs.md` | `workspace.py new <项目名>`、`extract_input.py` |
| ② 有效配置 | 逐字段取值：当次 ＞ 已确认 ＞ profile ＞ 项目默认 | `workflow.md` 第二节 | — |
| ③ 出图能力 | 判断能不能生图、能不能看图，确定路线和质检方式 | `render-routing.md` | `env_check.py --can-generate … --can-see …` |
| ④ 范围判断 | 完整套图 / 只策划 / 只文案 / 单页 / 修改 | `workflow.md` 第三节 | — |
| ⑤ 价值与核实 | 场景、问题、核心观点；R、I；核实事实；横切属性 | `content-templates.md` 第一、二节 | — |
| ⑥ 策划 | 选 T、F、H、V、C；每页 L、E、G/H/S；写 `plan.md`。**完整套图在此等待确认** | `content-templates.md`、`visual-system.md`、`workflow.md` 第五节 | — |
| ⑦ P1 与风格锁 | 生成封面；确认后写风格锁（13 项参数、描述版、精确版） | `page-generation.md`、`visual-system.md` 第五节 | `palette.py tokens` |
| ⑧ 逐页生成 | 规格单 → 编译 → 生成 → 质检 → 采用 / 阻塞 | `page-generation.md` 第六节 | `workspace.py page / adopt / block`、`render_page.py`、`call_image_api.py` |
| ⑨ 发布文案 | 标题、正文、标签、首条评论、来源、合规 | `copywriting.md` | `check_copy.py` |
| ⑩ 复核交付 | 发布前清单；状态一致性；交付报告 | `qa-checklist.md` 第 I 节、`workflow.md` 第七节 | `workspace.py status` |
| ⑪ 存为默认 | 问一次是否把本次选择存进 profile | `onboarding.md` 第四节 | — |

**默认的两个确认节点**（完整套图）：确认策划、确认 P1。F1 单图只确认策划。用户说「直接出」「不用确认」时按授权执行，并在报告里写「授权采用」。

## 按任务的快速路径

| 用户说 | 从哪开始 | 交付 |
|---|---|---|
| 「帮我做一套关于……的图文」 | ⓪ → ⑩ 全流程 | 标题、正文、图片、首条评论 |
| 「只策划」「先别出图」 | ① → ⑥ | `plan.md` |
| 「只写标题和正文」 | ① → ⑤ → ⑨ | 标题、正文、首条评论（标为「文案版本」） |
| 「做一张……」（单图） | F1：⑥ 策划确认后直接出图 | 标题、正文、1 张图、首条评论 |
| 「改第 3 页的……」 | 读 `state.json`，只改 P03 | 新版本 v(N+1) |
| 「继续」「接着做」 | 读 `state.json`，从未完成的页继续 | 剩余页 |
| 「看一下 P3 的提示词」 | 打开 `pages/P03/prompt.md` | — |
| 「设置账号」「以后都用……」 | `onboarding.md` | 更新 `profile.md` |
| 「做一个账号角色」 | `characters.md` | 角色资产包 |

## 出图：三条路线，三种构成

- **路线**（`render-routing.md`）：`native`（环境自带生图工具）/ `svg`（HTML＋CSS＋内联 SVG，用 Chromium 渲染为 PNG）/ `api`（`.env` 配置的 OpenAI 兼容图片接口）。按**能力**判断，不按模型名。P1 采用时锁定，中途不换。
- **构成方式**（`page-generation.md` 第二节），每页单独定：
  - **G 整图生成**：字少、以画面为主的页。
  - **H 底图＋叠加**：模型画留白底图，代码叠加准确文字、原样嵌入截图。字多、要保真的页。
  - **S 纯排版**：svg 路线的全部页，以及排版型风格。
- **白盒**：每页先写 `pages/PNN/spec.md`，再编译成 `prompt.md`（G/H）或 `page.html`（H/S）。默认不在对话里展示提示词，但文件始终保存。

## 项目文件

```
image-passage-work/<项目名>/
├── inputs/            用户素材副本、转写稿、关键帧
├── inputs.md          素材清单：用途、可信度、权利
├── plan.md            整篇策划与逐页策划
├── style-lock.md      风格锁：13 项参数、描述版、精确版
├── state.json         机器可读状态：配置、渲染、锚点、授权、每页进度
├── render/            base.css、tokens.css
├── pages/PNN/         spec.md、prompt.md、page.html、base.png、vN.png、qa.md
├── final/             采用版本 P01.png … PNN.png
└── copy.md            发布文案
```

继续或修改项目时，**先读 `state.json` 和 `plan.md`**，不依赖对话记忆。

## 脚本

全部在 `<skill>/scripts/`，依赖见 `requirements.txt`（`pip install -r requirements.txt`，再 `python -m playwright install chromium`）。

| 脚本 | 作用 |
|---|---|
| `env_check.py` | 环境能力检查，给出路线和质检方式建议 |
| `workspace.py` | `init` / `new` / `page` / `adopt` / `block` / `status` / `list` |
| `extract_input.py` | `doc`（pdf、docx、pptx、xlsx、csv、html…）/ `frames` / `audio` / `transcribe` |
| `fetch_fonts.py` | 下载开源中文字体（OFL），默认思源黑体、霞鹜文楷 |
| `palette.py` | 颜色名 → HEX；生成 `tokens.css` |
| `render_page.py` | HTML → 1242×1656 PNG，并检查溢出、边距、字号、字体、图片、重叠、高亮 |
| `call_image_api.py` | 调用图片 API（文生图 / 参考图编辑），适配为 3:4；`--dry-run` 预览请求 |
| `image_tools.py` | `fit` 适配画幅 / `mask` 遮挡隐私 / `sheet` 预览拼图 / `info` |
| `ocr_check.py` | OCR 核对图上文字与规格单（需要 tesseract＋chi_sim） |
| `check_copy.py` | 标题、字数档、标签、首条评论、封面文案、合规词检查；`--count` 统计字数 |

脚本不可用时（例如环境不能运行 Python），按 references 的规则手工完成，并在报告里说明哪些检查没有执行。

## 参考文件索引

| 文件 | 何时读 |
|---|---|
| `references/workflow.md` | 每个项目开始时；确认、授权、变更、交付格式 |
| `references/onboarding.md` | 首次使用、设置或更新账号配置 |
| `references/inputs.md` | 收到文件、图片、链接、音视频，或多种素材组合 |
| `references/content-templates.md` | 选 D、R、I、T、F、H，安排页面角色 |
| `references/visual-system.md` | 选 V、L、C、E；写风格锁；配色字体；素材保真 |
| `references/copywriting.md` | 写标题、正文、标签、首条评论；合规 |
| `references/page-generation.md` | 出图前；每页的流水线；修改与失败处理 |
| `references/render-routing.md` | 判断路线；配置 `.env` |
| `references/prompt-recipes.md` | native / api 路线写提示词 |
| `references/html-recipes.md` | svg 路线和 H 页写 HTML |
| `references/characters.md` | 启用或建立账号角色 |
| `references/qa-checklist.md` | 每页生成前后；发布前 |
| `references/platforms/*.md` | 平台上限和发布注意事项 |

## 交付报告（简版）

完成或中断时按 `workflow.md` 第七节：先按顺序给出标题、正文、图片、首条评论，再报告交付了什么（页数、文件位置）、确认与授权情况、质检方式（看图 / 脚本 / 未经视觉检查）、未完成和待补的项、需要用户核实的事（事实、素材权利）。最后问一次是否把本次选择存为账号默认。
