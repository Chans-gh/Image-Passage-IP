# 渲染路线：按能力判断怎么出图

## 一、三项能力

判断依据是**当前环境的能力**，不是模型名。模型很难可靠地知道自己是谁，换名、套壳都会让名单失效；下面的环境说明只作参考。

1. **能不能生图**：当前环境里有没有可以调用的原生生图工具。
2. **能不能看图**：当前模型能不能读取图片内容。它决定能不能看懂用户的照片，以及能不能检查自己生成的图。
3. **能不能接收参考图**：生图工具能不能把一张图作为参考，要求原样保留其中的文字、数值与界面。它决定含真实截图或照片的页能不能出图。

出图只有两条路线：`native`（环境自带多模态生图能力，例如 GPT 系列、混元等自带 gen 的模型）和 `api`（第三方图片模型接口）。两者都不具备时是 `none`——**不是第三种路线**，是「不具备出图能力」的状态。

| | 能看图 | 不能看图 |
|---|---|---|
| **能生图**（native 或已配置 api） | ① 完整闭环：生成 → 看图逐字质检 → 修正 → 采用 | ② 能生成但无法视觉核对：只做 OCR 抽查，其余如实记「未经视觉检查」 |
| **不能生图** | ③ `none`：先完成策划和文案，说明怎样才能出图 | ④ `none`：同上 |

页面一律整图生成：一页的画面和全部文字由生图模型一次性画出。不再有「模型画底图、代码叠文字」的做法。

## 二、确定渲染模式

```
.env 的 RENDER_MODE
 ├─ native / api ─▶ 照写的执行（最高优先级；条件不满足时提示并请用户改）
 ├─ svg ─────────▶ 已停用：提示改用 native 或 api，本次不出图
 └─ auto（默认）
     ├─ 有原生生图工具 ───────────▶ native
     ├─ 已配置图片 API ───────────▶ api
     └─ 都没有 ───────────────────▶ none：先完成策划和文案，说明怎样才能出图
```

运行检查脚本，由你告诉它这三项能力：

```bash
python3 scripts/env_check.py --can-generate yes|no --can-see yes|no --reference-support yes|no|unknown
python3 scripts/env_check.py --can-generate no --can-see yes --json   # 机器可读
```

输出：

| 字段 | 含义 |
|---|---|
| `recommended_mode` | native / api / none |
| `reference_support` | 生图工具能否接收参考图（yes / no / unknown） |
| `qa_mode` | visual / script+ocr / unchecked |
| `checks` | Python 依赖、Pillow、ffmpeg、tesseract、文档库 |
| `env` | `.env` 路径和配置情况（KEY 只显示是否配置，不显示内容） |
| `notes` | 需要提醒用户的事项 |

把结论写进 `state.json` 的 `render`：`mode`、`capabilities`、`reference_support`、`qa_mode`、`tool`、`model`、`size`、`quality`、`seed`。

### 参考图支持

含真实截图、照片的页依赖参考图。它不支持时，这些页**不能出图**：

| `reference_support` | 处理 |
|---|---|
| `yes` | 正常出图，提示词写明原样嵌入、不重绘，生成后逐项核对 |
| `no` | 在策划阶段就说明：含素材的页无法承接，把素材承载的信息移到正文，或请用户换环境 |
| `unknown` | 先出 1 页含素材的样张验证；不通过则按 `no` 处理 |

`api` 路线由 `IMAGE_API_REFERENCE_MODE` 决定：为 `none` 时等同 `no`，并提示「一致性只靠提示词」。

### 锁定

- 渲染模式在 P1 采用时锁定（`render.locked = true`），同一套图中途不换。
- 确实需要换时，按「改变主风格」处理：重新生成并确认 P1，已完成的页按新风格重做。

## 三、各路线的做法

| 路线 | 出图方式 | 质检 | 关键点 |
|---|---|---|---|
| native | 调用环境自带的生图工具 | 能看图：visual；否则 OCR 抽查或 unchecked | 参考图每页都带；含保真素材的页要求原样嵌入 |
| api | `call_image_api.py` 调 OpenAI 兼容接口 | 同 native | 成本按次计算，先确认 P1 再批量 |

## 四、`.env`

复制仓库根目录的 `.env.example` 为 `.env`，放在运行 Agent 的目录或 `image-passage-work/` 下。脚本按这个顺序找：`$IMAGE_PASSAGE_ENV` → `./.env` → `image-passage-work/.env`。**不读技能目录里的 `.env`**，避免随技能一起被分享。

| 变量 | 说明 |
|---|---|
| `RENDER_MODE` | auto / native / api |
| `IMAGE_API_BASE_URL` | OpenAI 兼容地址，例如 `https://api.example.com/v1` |
| `IMAGE_API_KEY` | 只放在 `.env`；不写进任何文件、不打印、不提交 |
| `IMAGE_API_MODEL` | 模型名 |
| `IMAGE_API_SIZE` | 接口支持的尺寸，默认 `1024x1536`（2:3），生成后裁切适配为 3:4 |
| `IMAGE_API_REFERENCE_MODE` | `edits`：有参考图时调用 `/images/edits`（multipart `image[]`）；`none`：不传参考图。含保真素材的页必须为 `edits` |
| `IMAGE_API_QUALITY` | 可选 |
| `TRANSCRIBE_API_*` | 可选，语音转写（`/audio/transcriptions`） |
| `OUTPUT_WIDTH` / `OUTPUT_HEIGHT` | 默认 1242 / 1656 |
| `IMAGE_PASSAGE_WORKDIR` | 工作区目录 |

安全规则：

- 不要求用户把 KEY 发到对话里；请用户自己编辑 `.env`。
- 用户已经在对话里发了 KEY 时，提醒对方这样做有泄露风险，建议之后更换；不复述 KEY。
- `.env` 在仓库的 `.gitignore` 里；工作区 `image-passage-work/` 也不提交。

## 五、环境参考（不作为判断依据）

下面是写作时的观察，环境更新后可能变化。标「待实测」的项需要在对应环境里验证。

| 环境 | 生图 | 看图 | 通常路线 | 说明 |
|---|---|---|---|---|
| Codex | 有（内置生图技能，例如 `$imagegen`） | 能 | native，① | 参考图传入方式、输出路径、3:4 尺寸支持：待实测 |
| Claude Code | 通常没有 | 能 | 配置了图片 API 时 `api`；否则 `none` | 没有生图能力就不出图，只交付策划和文案 |
| WorkBuddy | 有（混元等，待实测） | 视模型而定 | native | 能否接收参考图：待实测 |
| 纯文本模型（例如部分开源文本模型） | 没有 | 不能 | `none` | 只交付策划和文案；报告里写「未经视觉检查」 |

### 待实测

| # | 事项 |
|---|---|
| 1 | Codex 生图：调用方式、参考图、局部编辑、3:4 尺寸、输出文件位置 |
| 2 | WorkBuddy 生图：同上 |
| 3 | 各生图模型的中文上图实际情况（只作提示词与重试策略的参考，不写进规则成为限制） |
| 4 | 提示词语言：中文 / 中英双语 |
| 5 | 参考图「原样嵌入」的实际保真度：截图文字与数字被改动的频率 |
| 6 | 局部编辑（inpainting）修单个错字的成功率 |

实测结论请写回本节，并在 `CHANGELOG.md` 记录。
