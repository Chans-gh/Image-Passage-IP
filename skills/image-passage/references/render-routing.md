# 渲染路线：按能力判断怎么出图

## 一、两项能力

判断依据是**当前环境的能力**，不是模型名。模型很难可靠地知道自己是谁，换名、套壳都会让名单失效；下面的环境说明只作参考。

1. **能不能生图**：当前环境里有没有可以调用的原生生图工具。
2. **能不能看图**：当前模型能不能读取图片内容。它决定能不能看懂用户的照片，以及能不能检查自己生成的图。

| | 能看图 | 不能看图 |
|---|---|---|
| **能生图** | ① 完整闭环：生成 → 看图质检 → 修正 | ② 能生成但无法自查：用 OCR 或请用户检查 |
| **不能生图** | ③ svg 路线，渲染后看图质检 | ④ svg 路线，只能脚本检查；用户的照片要附文字说明 |

任何一类在 `.env` 配置了图片 API 后都可以走 api 路线；质检能力仍然取决于能不能看图。

## 二、确定渲染模式

```
.env 的 RENDER_MODE
 ├─ native / svg / api ─▶ 照写的执行（最高优先级；条件不满足时提示并请用户改）
 └─ auto（默认）
     ├─ 能生图 ─────────────────────▶ native
     ├─ 能运行渲染脚本 ─────────────▶ svg
     │     （已配置图片 API 时，插画、实景类风格可以提议改用 api，需用户同意，按次计费）
     ├─ 配置了图片 API ─────────────▶ api
     └─ 都不满足 ───────────────────▶ none：先完成策划和文案，说明怎样才能出图
```

运行检查脚本，由你告诉它前两项能力：

```bash
python3 scripts/env_check.py --can-generate yes|no --can-see yes|no
python3 scripts/env_check.py --can-generate no --can-see yes --json   # 机器可读
```

输出：

| 字段 | 含义 |
|---|---|
| `recommended_mode` | native / svg / api / none |
| `compose_H_available` | 能否使用 H 底图＋叠加（需要生图能力＋渲染脚本） |
| `qa_mode` | visual / script+ocr / script-only |
| `checks` | Python 依赖、Chromium、ffmpeg、tesseract、字体、系统中文字体 |
| `env` | `.env` 路径和配置情况（KEY 只显示是否配置，不显示内容） |
| `notes` | 需要提醒用户的事项 |

把结论写进 `state.json` 的 `render`：`mode`、`capabilities`、`qa_mode`、`tool`、`model`、`size`、`quality`、`seed`。

### 锁定

- 渲染模式在 P1 采用时锁定（`render.locked = true`），同一套图中途不换。
- 确实需要换时，按「改变主风格」处理：重新生成并确认 P1，已完成的页按新风格重做。
- 风格 × 路线、版式 × 路线的适配见 `visual-system.md` 第二、三节。路线会让风格降级时，在策划里写明。

## 三、各路线的做法

| 路线 | 页面构成 | 质检 | 关键点 |
|---|---|---|---|
| native | G / H（H 需要渲染脚本） | 能看图：visual；否则 OCR | 字多的页用 H；参考图每页都带 |
| svg | S | 能看图：visual；否则 script-only | 全部页面都是 HTML；照片和截图原样嵌入；角色只能嵌入 PNG |
| api | G / H | 同 native | `call_image_api.py`；成本按次计算，先确认 P1 再批量 |

## 四、`.env`

复制仓库根目录的 `.env.example` 为 `.env`，放在运行 Agent 的目录或 `image-passage-work/` 下。脚本按这个顺序找：`$IMAGE_PASSAGE_ENV` → `./.env` → `image-passage-work/.env`。**不读技能目录里的 `.env`**，避免随技能一起被分享。

| 变量 | 说明 |
|---|---|
| `RENDER_MODE` | auto / native / svg / api |
| `IMAGE_API_BASE_URL` | OpenAI 兼容地址，例如 `https://api.example.com/v1` |
| `IMAGE_API_KEY` | 只放在 `.env`；不写进任何文件、不打印、不提交 |
| `IMAGE_API_MODEL` | 模型名 |
| `IMAGE_API_SIZE` | 接口支持的尺寸，默认 `1024x1536`（2:3），生成后裁切适配为 3:4 |
| `IMAGE_API_REFERENCE_MODE` | `edits`：有参考图时调用 `/images/edits`（multipart `image[]`）；`none`：不传参考图 |
| `IMAGE_API_QUALITY` | 可选 |
| `TRANSCRIBE_API_*` | 可选，语音转写（`/audio/transcriptions`） |
| `OUTPUT_WIDTH` / `OUTPUT_HEIGHT` | 默认 1242 / 1656 |
| `IMAGE_PASSAGE_WORKDIR` | 工作区目录 |
| `IMAGE_PASSAGE_FONT_DIR` | 字体缓存目录 |

安全规则：

- 不要求用户把 KEY 发到对话里；请用户自己编辑 `.env`。
- 用户已经在对话里发了 KEY 时，提醒对方这样做有泄露风险，建议之后更换；不复述 KEY。
- `.env` 在仓库的 `.gitignore` 里；工作区 `image-passage-work/` 也不提交。

## 五、环境参考（不作为判断依据）

下面是写作时的观察，环境更新后可能变化。标「待实测」的项需要在对应环境里验证。

| 环境 | 生图 | 看图 | 通常路线 | 说明 |
|---|---|---|---|---|
| Codex | 有（内置生图技能，例如 `$imagegen`） | 能 | native，① | 参考图传入方式、输出路径、3:4 尺寸支持：待实测。能运行脚本，H 可用 |
| Claude Code | 通常没有 | 能 | svg，③ | 渲染后看图质检；配置了图片 API 时插画类可提议 api |
| WorkBuddy | 有（混元等，待实测） | 视模型而定 | native | 能否运行 Playwright 脚本（决定 H 是否可用）：待实测 |
| 纯文本模型（例如部分开源文本模型） | 没有 | 不能 | svg，④ | 只能脚本检查；用户照片要附文字说明；报告里写「未经视觉检查」 |

### 待实测

| # | 事项 |
|---|---|
| 1 | Codex 生图：调用方式、参考图、局部编辑、3:4 尺寸、输出文件位置 |
| 2 | WorkBuddy 生图：同上；能否运行 Playwright |
| 3 | 各生图模型的中文上图上限（决定 G / H 阈值） |
| 4 | 提示词语言：中文 / 中英双语 |
| 5 | 不支持参考图时，只靠描述版的一致性程度 |

实测结论请写回本节，并在 `CHANGELOG.md` 记录。
