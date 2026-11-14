# SPEC：渲染路线精简为「整图生成」

> 状态：**待实施**（本文是实施前的唯一依据）
> 目标版本：`0.3.0`（破坏性变更）
> 建议分支：`feat/render-routes-g-only`
> 影响范围：`SKILL.md`、13 个 reference、11 个脚本、12 个模板、`assets/`、根文档、`examples/demo/`

---

## 1. 背景与目标

### 1.1 现状

当前出图有两套正交维度：

- **渲染路线 3 条**（`references/render-routing.md`）：`native`（环境自带生图）/ `svg`（HTML＋CSS＋内联 SVG，Playwright＋Chromium 渲染 PNG）/ `api`（OpenAI 兼容图片接口）。
- **构成方式 3 种**（`references/page-generation.md` §二）：`G` 整图生成 / `H` 底图＋叠加（模型画底图，代码叠加文字）/ `S` 纯排版。

`H` 和 `S` 的存在意义是「中文文字由代码保证准确、真实素材原样嵌入」。代价是：需要 Playwright、Chromium、字体下载、`base.css`＋`tokens.css` 两套样式源、36 个版式的 CSS 实现、以及一条独立的 HTML 质检链路。

### 1.2 已确认的决策（本次改动的输入）

| # | 决策 | 影响 |
|---|---|---|
| D1 | 只保留 **2 条路线**：多模态大模型自带生图能力（`native`）、第三方图片模型接口（`api`）。**移除 `svg`** | 删掉整条 HTML 渲染链路 |
| D2 | **取消「先出图，再往图上写文字」**，即移除构成方式 `H` 与 `S`，只剩 `G`：一页的全部内容（画面 ＋ 所有文字）由生图模型一次性生成 | 文字准确性从「代码保证」变为「模型保证」；**不因此新增任何字数限制或版式分级**（见 §3） |
| D3 | 真实截图／照片这类必须保真的素材：**要求模型原样嵌入参考图，不重绘**，不做任何代码合成 | 参考图能力成为硬门槛 |
| D4 | `svg` 相关文件**彻底删除**（不保留、不归档到 docs/） | 仓库变干净，依赖瘦身 |
| D5 | `examples/demo/` **删除** | 失去端到端样例，需另建文案回归基线 |

### 1.3 目标

1. 出图能力判断只剩「有没有生图能力」和「能不能看图」两件事，规则、脚本、文档三处一致。
2. 因为失去了「代码写字」这条退路，把原本分散在两条规则里的**兜底路径**收拢为一处（§3.2：换版式 → 拆页 → 正常重试 → 待处理），避免出现「无处可去」的死角。**不新增任何字数上限、也不对版式或风格做难度分级。**
3. 删除不再被任何流程引用的代码与资产，`requirements.txt` 只剩真正需要的依赖。

### 1.4 非目标

- **不改**平台上限（标题 20、正文 800、图片 15、标签 8）与画幅（3:4，1242×1656）。
- **不改**文案规则、字数档 S0–S4、口吻 K、模板 T01–T23、钩子 H01–H15、主题 D01–D20。
- **不改**输入归一化、profile、角色资产、首条评论、交付四项顺序。
- **不引入**新的渲染路线或新的第三方服务（如 SVG→PNG 转换器、HTML 截图服务）。
- **不删除**旧项目工作区里用户的数据文件（`page.html`、`tokens.css` 等只提示、不自动清理）。

---

## 2. 新决策模型

### 2.1 两条路线 ＋ 一个降级状态

| 路线 | 出图方式 | 前提 |
|---|---|---|
| `native` | 调用当前环境自带的多模态生图能力（例如 GPT 系列图像能力、混元等自带 gen 的模型） | 环境里存在可调用的生图工具 |
| `api` | 调用 `.env` 配置的 OpenAI 兼容图片接口 | 配置了 `IMAGE_API_BASE_URL` ＋ `IMAGE_API_KEY` |
| `none` | **不是第三种方式**，是「不具备出图能力」的降级状态 | 上面两者都不满足 → 只交付策划与文案 |

构成方式只有一种：**G 整图生成**。「构成方式」不再是一个需要选择的变量。

### 2.2 能力矩阵（替换现有的 2×2）

| | 能看图 | 不能看图 |
|---|---|---|
| **有生图能力**（`native` 或已配置 `api`） | ① 完整闭环：生成 → 看图逐字质检 → 修正 → 采用（`qa_mode = visual`） | ② 能出图但无法视觉核对：只做 OCR 抽查，其余记「未经视觉检查」（`qa_mode = script+ocr` / `unchecked`） |
| **无生图能力** | ③ `none`：只交付策划与文案，说明怎样才能出图 | ④ `none`：同上 |

与旧版的差别：`svg` 两格被 `none` 取代。**「不能生图」不再有替代出图路径。**

### 2.3 判定树（替换 `render-routing.md` 第二节）

```
.env 的 RENDER_MODE
 ├─ native / api ─▶ 照写的执行（最高优先级；条件不满足时提示并请用户改）
 ├─ svg ─────────▶ 已停用：提示改用 native 或 api，本次不出图
 └─ auto（默认）
     ├─ 有原生生图工具 ───────────▶ native
     ├─ 已配置图片 API ───────────▶ api
     └─ 都没有 ───────────────────▶ none：先完成策划和文案，说明怎样才能出图
```

`auto` 不再依赖 Chromium／Playwright／字体缓存。

### 2.4 新增门槛：参考图支持（`reference_support`）

因为 D3 要求「模型原样嵌入参考图」，**生图工具是否接受参考图**成为能否承接含保真素材页面的硬门槛。`env_check.py` 新增输出字段：

| 字段 | 取值 | 含义 |
|---|---|---|
| `reference_support` | `yes` / `no` / `unknown` | 当前生图工具能否接收参考图（由模型自述能力，`env_check.py` 只做记录，不能自动探测） |

规则：

- `no`：含保真素材的页**不能出图** → 在策划阶段就说明，把素材承载的信息移到正文，或请用户换环境。
- `unknown`：先出 1 页含素材的样张验证；不通过则按 `no` 处理。
- `api` 路线：由 `IMAGE_API_REFERENCE_MODE=edits` 决定；为 `none` 时等同 `no`，且必须提示「一致性只靠提示词」。

### 2.5 锁定与降级

- 渲染模式在 P1 采用时锁定（`render.locked = true`），同一套图中途不换。
- 需要换时按「改变主风格」处理：重新生成并确认 P1，已完成的页重做。
- 风格 × 路线的适配表（`visual-system.md` §二）与版式 × 路线的适配表（§三 末）**整表删除**，不做替代分级（见 3.3、3.4）。

---

## 3. 纯 G 下的文字与版式（不新增限制）

> **本节不新增长度限制。** 每页的文字量上限仍然只有一处定义：`visual-system.md` §三 版式 L 表的「文字量」列，以及 §四 的封面主文案表。原规则里「上图文字超过阈值 → 改用 H」的**自动改判规则**随 H 一并移除（`page-generation.md` §二 自动选择规则第 3 条），但阈值本身不再是分岔条件。文字多了怎么处理，见 3.2。

### 3.1 文字量口径不变

- 每页文字量按**所用版式 L** 的上限（`visual-system.md` §三），封面按 §四。
- 「文字量」是策划与质检的参考口径，**不是硬性字数立法**；信息没表达完就继续把话说完，不为凑数删内容，也不为压字数拆页。
- 版式与内容不匹配时，换一个更合适的版式 L，或按 3.2 处理。

### 3.2 文字不匹配版式时的处理（替换原「改用 H」）

原规则：文字超过阈值 → 改用 H（代码叠字）。H 移除后，按顺序：

1. **换版式**：选一个文字量上限更宽的 L（例如 L17 图文段落页、L23 多列对比表这类大方量版式）。
2. **拆页**：一个核心观点拆成两页，页序与页码同步更新（`page-generation.md` §三）。
3. **保留完整表达，接受重试**：内容就该这么说时，不改文案；按 `page-generation.md` §六 的正常重试流程走，仍不通过则 `block` 记待处理。

**不允许**为了让模型好写而删掉必要信息。影响判断的条件（来源、测试条件、适用人群）不能因为「字多」而丢失（`content-templates.md` §四）。

### 3.3 版式 L 表：不做难度分级，删除路线适配列

- 36 个版式 L **全部保留**，**不**按路线做推荐／可用／停用的分级。原来的「版式 × 渲染路线」适配表（`visual-system.md` §三 末）**整表删除**，不再出现「svg 很适合 / svg 依赖用户素材 / svg 需要角色资产 / native 风险较高」这类分类。
- 需要这类表述时，只在策划里按当次环境与素材情况说明，不写进规则文件，避免变成第二套判断标准。
- 原表最后一行的「L17、L18、L23、L30 文字多，中文容易出错」按 3.2 处理，不再单独标注。

### 3.4 风格 V 表：只删路线列，不做风险分级

- `visual-system.md` §二 的「风格 × 渲染路线」表**整表删除**。风格 V01–V12 的选择不再按路线判断。
- **不**新增「文字出错风险低／中／高」的分级——同样会变成第二套判断标准。
- 各风格原有的「控制」列要求（例如 V01「手写正文清楚」、V11「装饰最多 1～2 个」）**全部保留**。

### 3.5 表达元素 E：不做降级

- `E01`–`E39` **全部保留**。原拟把 `E27`–`E31`（图表类）标为「停用／降级为示意图」的处置**取消**——图表本身是正当表达元素。
- 原有的真实性要求不变：没有数据依据时不画看似精确的统计图（`visual-system.md` §三 末），引用要标来源（`copywriting.md` §十）。

### 3.6 修错流程

原「G 页文字反复出错 → 改为 H」的兜底随 H 移除，改为：

1. **局部编辑**：生图工具支持传入原图做局部修改时，只改错的那几个字，其余要求「完全不变」（`prompt-recipes.md` §五）。
2. **整页重新生成**：不支持局部编辑时，调整 `prompt.md` 后重出。
3. **`block`**：连续 2 次（profile 的「每页最多重试」）仍出错 → 记为待处理，不采用、不混入 `final/`。

### 3.7 页码、来源条、署名

这三类以前由代码保证正确，现在交给模型。**默认按原规则**：

- **页码**：仍按方案 B（封面与 F1 不显示、内页底部居中「X / N」），字号 ≥30px、与背景有对比（`visual-system.md` §五）。若某页页码反复写错，按 3.6 走；确实无法稳定时，可在该页或在 `state.json` 的 `config.pagenum` 关掉页码（`off`），并在报告里说明。
- **来源条**：按 `visual-system.md` §六 E09 与 `copywriting.md` §十执行（图上放简短来源，完整链接放正文、首条评论或交付说明），**不另设字数上限**。
- **署名／水印**：按 profile E 组与 `visual-system.md` §五 第 11 项「组件」执行，**不另设字数上限**。

---

## 4. 保真素材的处理（纯参考图路线）

按 D3，**不做任何代码合成**。真实截图／照片作为**参考图**传入，提示词要求原样保留。

### 4.1 流程

1. **先脱敏**：把截图里手机号、姓名、订单号、地址、头像等在**图片文件**上处理掉，再作为参考图传入：
   `python3 scripts/image_tools.py mask in.png inputs/in.masked.png --rect x,y,w,h --style blur`
   —— 这一步的时机从「嵌入页面时」提前到「交给模型前」，因为模型会重绘。
2. **写进规格单**：素材字段写明「原样嵌入，不重绘、不改变关键文字与数值」。
3. **提示词第 5 层**：写清每张素材的处理方式——
   `参考图 #2 是用户截图：保持其中的文字、数字、按钮状态与界面元素完全不变，只允许缩放与裁切；不要重绘、不要替换文字、不要补全看不清的部分。`
4. **提示词第 8 层**：按编号说明每张参考图的作用（风格参考 / 原样嵌入 / 角色一致）。
5. **质检查验**：逐项核对关键文字、数值、状态是否与素材一致；不一致即该页失败。

### 4.2 与不可覆盖原则的关系

`SKILL.md` 原则 3「素材保真」与 `visual-system.md` §八 保持**不变**，表述改为：

> 需要保真的截图和照片，以**参考图**方式交给生图模型，并明确要求原样保留关键文字、数值与状态。生成后逐项核对；出现证据内容变化时，该页判为失败，重新生成或记为待处理。不再使用代码叠加方式（本版本已移除）。

### 4.3 明确写入的已知限制

- 模型仍可能重绘。**必须**在质检中逐项核对，不能因为「提示词写了」就当作已保真。
- `native` 工具不支持参考图（`reference_support = no`）时，含素材的页无法承接，必须提前告知。

---

## 5. 质检与诚实状态

### 5.1 `qa_mode` 三档的新含义

| `qa_mode` | 能检查的 | 检查不了的 | 采用状态 |
|---|---|---|---|
| `visual` | 全部：结构、文字、数字、素材保真、人物、风格、页码 | — | `pass` |
| `script+ocr` | 只有图上文字（`ocr_check.py --expect-file spec.md` 抽查） | 画面、人物、风格、素材保真 | `pass-script-only` |
| `unchecked` | 无 | 全部 | `unchecked` |

**变化点**：原 `script-only` 档依赖 `render_page.py` 的排版检查，随本版本删除后该档失去检查手段，合并为 `unchecked`。

### 5.2 「不能看图」的处理

本方案下，看不到图就**无法核对文字**，交付可信度显著下降。规则：

- 仍然可以出图，但必须：
  1. 先只出 **1 页**让用户确认，通过后再继续；
  2. 报告里写明「未经视觉检查」，请用户抽查；
  3. 建议缩小页数，单页文字压到 3.1 上限的一半。
- `env_check.py` 的 `notes` 必须给出这条提示。

### 5.3 `ocr_check.py` 的地位上升

它从「S/H 页的辅助」变为**不能看图时唯一的文字核对手段**。规格单「上图文字」清单（用「」包住）因此成为强制字段，缺失即无法核对。

---

## 6. 文件级改动清单

### 6.1 删除（8 个文件 ＋ 2 个目录）

| 文件 | 行数 | 删除后需要同步的位置 |
|---|---|---|
| `skills/image-passage/assets/css/base.css` | 460 | `workspace.py`、`AGENTS.md`、`README*`、`llms.txt`、`INSTALL.md` |
| `skills/image-passage/assets/css/`（空目录） | — | — |
| `skills/image-passage/scripts/render_page.py` | 244 | `requirements.txt`、`env_check.py`、`SKILL.md`、`AGENTS.md`、`llms.txt`、`README*`、`INSTALL.md` |
| `skills/image-passage/scripts/fetch_fonts.py` | 88 | `fonts.json`、`env_check.py`、`_common.font_dir`、`INSTALL.md`、`README*`、`llms.txt` |
| `skills/image-passage/references/html-recipes.md` | 296 | `workflow.md` §一、`SKILL.md` 索引、`llms.txt`、`AGENTS.md` |
| `skills/image-passage/templates/page.html` | 31 | `workspace.py` |
| `skills/image-passage/templates/page-compose.html` | 28 | `workspace.py` |
| `skills/image-passage/templates/tokens.css` | 11 | `workspace.py`、`palette.py tokens` |
| `skills/image-passage/assets/fonts.json` | 94 | `AGENTS.md` 双写表、`llms.txt`、`visual-system.md` §七（字体表留在规则里） |
| `examples/demo/`（整个目录） | 476 KB | `README.md` / `README.en.md` 的演示行、`AGENTS.md`、`INSTALL.md`、`llms.txt`、`.gitignore` |

> `fonts.json` 的处置理由：删掉 `fetch_fonts.py` 与 HTML 渲染后，它没有任何脚本消费者；字体信息（8 款 OFL 字体的中文名与用途）已在 `visual-system.md` §七 的表里，保留双份违反单一归属。**已决议删除**（§14 Q1）。
>
> `examples/demo/` 目录整体删除，但其中的 `copy.md` **先移到 `examples/copy-sample.md`** 保留，作为 `check_copy.py` 的回归基线（§14 Q2）。

### 6.2 规则层

| 文件 | 改动 |
|---|---|
| `SKILL.md` | ① frontmatter `description` 删除 "HTML/SVG rendering"；`metadata.version` → `0.3.0`；② 阶段总览 ⑥/⑧ 行去掉 `G/H/S`；③「出图：三条路线，三种构成」整节改写为「两条路线，一种构成」（第 92–99 行）；④ 项目文件树删除 `render/`、`page.html`、`base.png`（第 104–114 行）；⑤ 脚本表删除 `fetch_fonts.py`、`render_page.py`，改写 `palette.py`（第 122–133 行）；⑥ 参考索引删除 `html-recipes.md`（第 150 行）；⑦ 依赖说明删除 `playwright install chromium`（第 120 行）；⑧ 保持 < 500 行 |
| `references/render-routing.md` | 几乎重写：§一 能力矩阵（§2.2）、§二 判定树（§2.3）、§三 各路线的做法（去掉 svg 行）、§五 环境参考表（Claude Code 从「svg，③」改为「`none`」；纯文本模型从「svg，④」改为「`none`」）、新增 `reference_support` 一节、`checks` 字段列表去掉 Chromium／字体 |
| `references/page-generation.md` | §二 改为「整图生成（唯一构成）」，删除自动选择规则 4 步与阈值、删除 `compose_H_available`；§三 删除「S / H 页改页码只需改 HTML」；§四 规格单表删除「构成方式」行、素材行加「原样嵌入」；§五 删除「S 页不需要参考图」、改写「不支持参考图时多用 H 页」→ 改为「无法承接含素材的页」；§六 删除 H / S 两条编译分支，只留 G（native / api），`qa_mode` 表按 §5.1 改写；§八 修改表只留 G 行，改写「文字反复出错 → 改为 H」为 §3.6 的流程；§十 文件清单删除 `base.png`、`page.html` |
| `references/visual-system.md` | §二 **删除「风格 × 渲染路线」整表**，不做替代分级（§3.4）；§三 末**删除「版式 × 渲染路线」整表**（§3.3），36 行 L 表的「文字量」「控制」「主元素」列**全部保留、不改数值**，仅删除「CSS 类」列（`base.css` 已删）；§四 缩略图检查删除 `render_page.py --scale` 的说法（保留 `image_tools.py sheet`）；§五 量化约束表的「`render_page.py` 检查」列改为「提示词表述 ＋ 目视核对」，删除依赖脚本的精确 px 行；13 项参数中第 2 项改为 `native / api`、第 3 项去掉「svg / H 补 HEX」、第 5 项去掉「svg / H 另记字体名和字号」；「精确版」改为「供提示词与风格锁使用的 HEX 表」（不再生成 `tokens.css`）；§六 E 表删除 CSS 实现列的 HTML 类名引用，`E01`–`E39` 保留、**不降级不停用**（§3.5）；§七 删除 `palette.py tokens` 命令与字体下载说明，字体一节改为「字体感词表」并新增「只写字体感，不指定具体商用字体的字形、不要求模仿字体品牌」；§八 按 §4.2 改写；§九 删除「svg 路线画不出一致的角色」 |
| `references/prompt-recipes.md` | 标题去掉「G、H 页」→「整图生成页」；§一 第 5 层加重「原样嵌入、不重绘」的写法；§二 中文上图文字**删除「超过时改用 H」的表述与 ≤14/≤30 字、≤4 条阈值**，改为指向 `visual-system.md` §三、§四 的**参考口径**，并声明「不是硬性字数上限，不要为了迁就模型删内容」（§3.1）；§五「H 页的底图提示词」**整节删除**（§14 Q4），其后各节**顺次重编号**（原 §六 → §五，原 §七 → §六，原 §八 → §七，原 §九 → §八），并同步改掉 `page-generation.md` 里「第六节」的引用；§五（原 §六）保留并强化为 §3.6 的第 1 步；§六（原 §七）参考图说明区分「风格参考 / 原样嵌入 / 角色一致」 |
| `references/qa-checklist.md` | §质检方式表按 §5.1 改写；E 节「构成方式 G / H / S 按规则选择」→「版式 L 与封面主文案符合 `visual-system.md` §三、§四 的口径」（不引入新阈值）；F 节删除「`tokens.css` 已按精确版生成」；G 节删除「G 页文字不超过阈值；超过时改 H」→ 改为 §3.2 的处理顺序；H 节删除「S / H 页：`render_page.py` 没有错误」→ 改为「文字逐字核对」「素材关键内容保真」；新增「页码反复出错时已按 §3.7 处理/关闭并说明」 |
| `references/workflow.md` | §一 归属表删除 `html-recipes.md` 行，`page-generation.md` 行去掉「构成方式 G/H/S」，`render-routing.md` 行改为「能力判断、渲染路线、参考图门槛」；§二 项目默认删除「排版底」行、页码行补 `off` 选项（仅在反复写错时使用）；§四 ③ 步骤改写（去掉 Chromium、加 `reference_support`）、⑦ 删除 `palette.py tokens`、⑧ 按新流水线；§五 策划格式「渲染路线与各页构成方式」→「渲染路线」；§六 变更边界「更换渲染模式」保留但去掉 svg 举例，**不新增**「改变文字上限策略需重新确认」 |
| `references/onboarding.md` | 影响表：C 组「`check_copy.py --profile`」不变；D 组字体倾向行删除「S / H 页使用的字体」；F 组删除「svg 嵌入角色 PNG」；G 组「展示提示词」保留；新增「参考图支持」相关提示（生图工具不支持参考图时，含截图/照片的页无法出图，需提前告知） |
| `references/characters.md` | §三 删除 `poses/*.png` 的「svg 路线直接嵌入」用途与透明背景要求（改为「可作为参考图，透明背景非必需」）；§五 删除 svg 的 `<img>` 嵌入一条，改为「native / api：参考图 + 第 6 层不可改变项」；§二 人物模式表述不变 |
| `references/inputs.md` | §七 打码时机提前：新增一句「素材要在作为参考图交给模型**之前**完成遮挡」；其余不变 |
| `references/content-templates.md` | **不改**（L34 目录页仍可用；原拟改动取消） |
| `references/copywriting.md` | **不改**（原拟加重「正文承担」的改动取消；§四 图文分工表原有内容已够用） |
| `references/platforms/*.md` | **不改** |

### 6.3 模板层

| 文件 | 改动 |
|---|---|
| `templates/spec.md` | 删除「构成方式」行；「上图文字」小节**不改数值**，仅保留原「逐字列出，每条标层级」的注释；「素材」小节加「原样嵌入，不重绘」；「参考图」小节区分作用 |
| `templates/plan.md` | 第 23 行「渲染路线 · 构成方式」→「渲染路线（native / api）」；第 43、57 行删除「构成方式」 |
| `templates/style-lock.md` | 第 5 行删除「写进 render/tokens.css」；第 2 项改为 `native / api`；「精确版」标题改为「精确版（HEX，供提示词与风格锁使用）」，删除「写进 tokens.css」；「生图参数」一节的字段按路线填 |
| `templates/state.json` | `config` 新增 `pagenum` 取值说明（`B` / `off`）；`pages.PNN` 不再写 `composition`；`render` 保留 `tool / model / size / quality / seed`，新增 `reference_support` |
| `templates/prompt.md` | 第 5 层注释补「原样嵌入」；第 7 层禁止项补「错字、别字、乱码、多余文字」；**不新增字数提示** |
| `templates/copy.md` | **不改** |
| `templates/profile.md` | G 组「每页最多重试：2」保留；F 组保留；新增一行可选「生图工具是否支持参考图」 |
| `templates/character.md` | 第 15 行「svg 时补 HEX」→「按需补 HEX」 |
| `templates/inputs.md` | **不改** |

### 6.4 资产与脚本

| 文件 | 改动 |
|---|---|
| `assets/colors.json` | `note` 去掉「svg / H 叠字」表述，改为「提示词与风格锁精确版使用」；75 个颜色名不变 |
| `assets/platforms.json` | **不改** |
| `assets/fonts.json` | **删除**（见 §6.1 与 §14） |
| `scripts/workspace.py` | 第 97–98 行删除 `render/` 目录创建（项目结构少一个目录）；第 107–110 行删除 `base.css` / `tokens.css` 复制；第 126–130 行删除 `page.html` 生成；`page` 子命令删除 `--composition` 参数（第 247–248 行）；`cmd_page` 不再写 `entry["composition"]` |
| `scripts/env_check.py` | 删除 `chromium_ok()`（第 29–44 行）、`cjk_system_fonts()`、`browser`、`scripts_ok`、`compose_h`、`fonts_downloaded`、`font_dir` 相关输出；判定树按 §2.3 重写（第 85–106 行）；`mode_cfg` 校验 `svg` → 提示已停用；`"native / svg / api"` → `"native / api"`；`report` 新增 `reference_support`、删除 `playwright_chromium` / `fonts_downloaded` / `system_cjk_fonts`；文本输出第 154 行删除 Chromium 与字体行，新增参考图一行 |
| `scripts/_common.py` | 删除 `font_dir()`（第 69–75 行）；`load_env` 的环境变量前缀 `RENDER_ / IMAGE_ / TRANSCRIBE_ / OUTPUT_` 保留；`output_size()`、`workdir()`、`mask_secret()` 不变 |
| `scripts/palette.py` | 删除 `fonts_by_id()`（第 46–48 行）、`cmd_tokens()`（第 69–114 行）、`tokens` 子命令（第 122–130 行）、`--font-*` 与 `--fs-*` 参数；docstring 去掉 tokens 示例；保留 `resolve` 与 `list` |
| `scripts/requirements.txt` | 删除 `playwright>=1.40`；注释从「渲染（svg 路线、H 底图＋叠加）」改为「图片处理与适配」；`pillow` 保留 |
| `scripts/image_tools.py` | 功能不变（`fit` / `mask` / `sheet` / `info` 全部保留）；docstring 强化 `mask` 的时机说明（交给模型前先打码） |
| `scripts/call_image_api.py` | docstring 说明参考图语义（原样嵌入，不重绘）；`--dry-run` 摘要保留 `references` / `references_dropped`；建议在原 `--ref` 帮助文本里写明「本页需要原样保真的素材」 |
| `scripts/ocr_check.py` | **不改**（地位上升，见 §5.3） |
| `scripts/check_copy.py` | **不改** |
| `scripts/extract_input.py` | **不改** |

### 6.5 根文档与元数据

| 文件 | 改动 |
|---|---|
| `AGENTS.md` | 第 7 行安装流程删除 Chromium 与字体；第 21 行 templates 清单删除 `page.html / page-compose.html / tokens.css`；第 23 行 assets 清单删除 `css/base.css`、`fonts.json`；第 28 行 demo 行删除；双写映射表（第 38–50 行）：删除「量化布局约束 ↔ render_page.py」「版式类 ↔ base.css」「字体 ↔ fonts.json / fetch_fonts.py」三行，「构成 G/H/S ↔ page-compose.html / base.css」整行删除（构成只剩 G，其结构不再镜像到代码）；第 57 行 HEX 说明去掉 `tokens.css`；验证小节（第 74–96 行）重写：删除 `playwright install`、`fetch_fonts.py`、`render_page.py` 三步，改为 `env_check` 判定树断言 ＋ `check_copy` 基线（样本路径改为 `examples/copy-sample.md`）；第 112–113 行 commit hygiene 删除 `examples/demo/render/base.css` 与 demo 体积约定 |
| `README.md` | 第 3 行版本徽章 → 0.3.0；第 17–19 行删除演示图片与说明；第 25 行删除「只能写文字 → svg」；第 27–32 行删除「每页三种构成方式」整块，改为「一页一图，整图生成」；第 34 行风格锁去掉 `tokens.css`；第 39 行质检描述改写（去掉渲染脚本）；第 40 行删除开源字体一条；第 88、92 行删除 `playwright install` 与 `fetch_fonts.py`；第 109 行 `RENDER_MODE` 去掉 `svg`；第 113 行删除 `IMAGE_PASSAGE_FONT_DIR`；第 130、150、151 行项目结构与 assets 清单修正；第 170 行「G / H 构成方式的自动阈值（30 字、4 个要点）」整条删除（不再有阈值）；第 177 行删除「下载的字体各自遵循 OFL」 |
| `README.en.md` | 同上对应位置：第 3、19、21、27、38、44、47、95、99、116、120、137、157、158、174 行 |
| `INSTALL.md` | 第 84、87 行删除 `playwright install` 与 `install-deps`；第 91、94 行删除字体下载；第 122、126、127 行自检说明与 demo 渲染命令改写；第 137 行 `native / svg / api` → `native / api` |
| `llms.txt` | 第 25 行删除 html-recipes 条目；第 33 行删除 render_page 条目；第 39 行删除 `fetch_fonts.py`；第 44 行 assets 清单去掉 `fonts.json`、`css/base.css`；第 45 行删除 demo 条目 |
| `CHANGELOG.md` | 新增 `## [0.3.0] - <日期>`，含「移除 / 变更 / 新增」三节（见 §11.3） |
| `.env.example` | `RENDER_MODE` 注释去掉 `svg`，改为只列 auto / native / api；删除 `IMAGE_PASSAGE_FONT_DIR` 两行；`IMAGE_API_REFERENCE_MODE` 说明强化（保真素材必需） |
| `.gitignore` | 第 13 行删除 `examples/demo/render/base.css`；第 7 行注释「字体缓存与渲染产物」改为「缓存与产物」，`.fonts/` 可保留 |
| `.claude-plugin/plugin.json` | `version` → 0.3.0 |
| `.codebuddy-plugin/plugin.json` | `version` → 0.3.0 |
| `docs/04_渲染路线精简SPEC.md` | 本文件（新增） |
| `docs/00–03` | **不改**（历史设计记录，见 §14） |

---

## 7. 编号与术语处置

遵循 AGENTS.md「编号稳定，废弃标停用，不删除、不重排」：

| 编号／术语 | 处置 |
|---|---|
| 渲染路线 `svg` | **停用**。字符串保留在文档中（带「已停用」标记），因为旧项目的 `state.json` 里存在该值 |
| 构成方式 `H`、`S` | **停用**。`G` 保留，但不再是「三选一」，而是唯一方式 |
| 构成方式字段 | `pages.PNN.composition` 不再写入新值；旧值读到时视为需重做 |
| 版式 `L01`–`L36` | **全部保留，不做分级、不标停用**（36 个版式都可用于整图生成）。原「版式 × 渲染路线」适配表整表删除（§3.3） |
| 风格 `V01`–`V12` | **全部保留，不做分级**。原「风格 × 渲染路线」表整表删除（§3.4） |
| 表达元素 `E01`–`E39` | **全部保留**，`E27`–`E31` 不标停用、不降级（§3.5） |
| 字数档 `S0`–`S4` | 保留不变。注意：`copywriting.md` 的「S 字数档」与 `page-generation.md` 的「S 纯排版」重名冲突，随构成方式 S 停用而**自然消除**，文档里可加一句说明 |
| 主题 `D01`–`D20`、模板 `T01`–`T23`、钩子 `H01`–`H15` | 全部不变（`H01`–`H15` 的「H 钩子」与构成方式 H 也是同名不同义，随本次改动一并消除歧义） |
| `compose_H_available` | 从 `env_check.py` 输出中移除；文档中标注「已停用」 |
| 项目目录 `render/` | 新项目不再创建 |

---

## 8. 双写映射与归属表更新

### 8.1 `workflow.md` §一 归属表

| 文件 | 新定义内容 |
|---|---|
| `render-routing.md` | 能力判断、两条渲染路线、参考图门槛（`reference_support`） |
| `page-generation.md` | 一页一图、规格单、整图生成流程、页码、失败与修改 |
| `visual-system.md` | 风格 V、版式 L、封面 C、表达元素 E、风格参数、量化约束、配色与字体感、素材保真 |
| ~~`html-recipes.md`~~ | **删除该行**（文件已删除） |

### 8.2 `AGENTS.md` 双写映射表（改动后应只剩 7 行）

| 规则（定义在） | 镜像在 |
|---|---|
| 颜色名（`visual-system.md` §七） | `assets/colors.json`、`scripts/palette.py` |
| 长度档 S0–S4、合规词表（`copywriting.md` §五、§九） | `scripts/check_copy.py` |
| 平台上限（`platforms/*.md`） | `assets/platforms.json`、`check_copy.py`、`workspace.py status`、SKILL.md 原则 8、两个 README |
| 最终交付四项与首条评论（`copywriting.md` §十二、§十四） | `templates/copy.md`、`check_copy.py`、`workflow.md` §七 |
| 渲染路线与参考图门槛（`render-routing.md`） | `.env.example`、`scripts/env_check.py`、`scripts/call_image_api.py` |
| 项目文件与状态（`page-generation.md` §十） | `scripts/workspace.py`、`templates/state.json` |
| profile 字段 A–H（`onboarding.md` §三） | `templates/profile.md` |

（删除的镜像行：量化布局约束 ↔ `render_page.py`；版式类 ↔ `base.css`；字体 ↔ `fonts.json` / `fetch_fonts.py`；构成 G/H/S ↔ `page-compose.html` / `base.css`）

---

## 9. 兼容与迁移

### 9.1 旧项目（用户工作区）

| 情况 | 处理 |
|---|---|
| `state.json` 的 `render.mode == "svg"` | 读到时提示「svg 路线已停用，需按 native / api 重新出图」，不自动改写 |
| `pages.PNN.composition` 为 `H` / `S` | 视为需重做；已 adopt 的 `final/PNN.png` 保留，但报告里标明「由已停用的路线生成」 |
| 工作区残留 `render/base.css`、`render/tokens.css`、`pages/PNN/page.html`、`base.png` | **不自动删除**（属于用户数据）；在交付报告里列一次，提示可自行清理 |
| `config.pagenum` 缺 `off` 分支 | 读取时按 `B` 处理 |

### 9.2 `.env`

- `RENDER_MODE=svg`：不报错退出，而是提示「已停用，请改为 native / api」，并按 §2.3 的结果继续。
- `IMAGE_PASSAGE_FONT_DIR`：不再读取；保留在用户 `.env` 里不报错（静默忽略）。

### 9.3 文案回归基线

`examples/demo/copy.md` 随 demo 删除，**移到 `examples/copy-sample.md`**（约 400 字节），继续作为 `check_copy.py` 的基线样本（基线不变：errors 0 / warnings 0）。作者已裁决：**保留基线**。

---

## 10. 验证方案

### 10.1 语法与静态检查

```bash
python3 - <<'PY'
import pathlib
bad = 0
for p in sorted(pathlib.Path("skills/image-passage/scripts").glob("*.py")):
    try: compile(p.read_text(encoding="utf-8"), str(p), "exec")
    except SyntaxError as e: bad += 1; print("FAIL", p.name, e)
print("语法错误数:", bad)
PY
```

（用内存 compile，避免 `py_compile` 写 `~/Library/Caches` 失败。）

### 10.2 `env_check.py` 判定树断言（本次最关键的回归点）

| 输入 | 期望 `recommended_mode` | 期望 `qa_mode` |
|---|---|---|
| `--can-generate yes --can-see yes` | `native` | `visual` |
| `--can-generate no --can-see yes`（无 api） | **`none`**（旧行为是 `svg`） | `script+ocr` 或 `script-only`→`unchecked` |
| `--can-generate no --can-see yes` ＋ 配置 api | `api` | 同上 |
| `--can-generate no --can-see no`（无 api） | `none` | `unchecked` |
| `RENDER_MODE=svg` | 提示已停用，回落到 auto 判定 | — |
| `RENDER_MODE=native --can-generate no` | `native` ＋ `notes` 提示条件不满足 | — |

同时断言输出中**不再出现** `compose_H_available`、`playwright_chromium`、`fonts_downloaded`、`system_cjk_fonts`，**新增** `reference_support`。

### 10.3 脚本冒烟（scratch 目录）

```bash
cd "$(mktemp -d)"
python3 <repo>/skills/image-passage/scripts/workspace.py init
python3 <repo>/skills/image-passage/scripts/workspace.py new demo
python3 <repo>/skills/image-passage/scripts/workspace.py page demo P01     # 不带 --composition
python3 <repo>/skills/image-passage/scripts/workspace.py status demo
python3 <repo>/skills/image-passage/scripts/env_check.py --quick
python3 <repo>/skills/image-passage/scripts/call_image_api.py --help
python3 <repo>/skills/image-passage/scripts/call_image_api.py --dry-run --prompt "test" --out /tmp/x.png
python3 <repo>/skills/image-passage/scripts/palette.py resolve 鼠尾草绿
python3 <repo>/skills/image-passage/scripts/palette.py list
python3 <repo>/skills/image-passage/scripts/image_tools.py info <任一 png>
python3 <repo>/skills/image-passage/scripts/ocr_check.py --help
```

断言：

- `new` 之后项目目录**不存在** `render/`，`pages/P01/` 里**没有** `page.html`。
- `workspace.py page` 没有 `--composition` 参数（`--help` 中不出现）。
- `palette.py tokens` 已不存在（`--help` 中不出现 `tokens`）。
- `env_check.py` 输出里没有 Chromium 与字体行。

### 10.4 文案基线

```bash
python3 skills/image-passage/scripts/check_copy.py examples/copy-sample.md
# 期望 errors 0 / warnings 0（标题 13、正文 328、标签 4、评论 73）
```

### 10.5 残留引用检查（必须只剩「已停用」说明）

```bash
grep -rn "svg\|render_page\|base\.css\|html-recipes\|fetch_fonts\|compose_H\|tokens\.css\|playwright\|Chromium" \
  skills/ *.md llms.txt .env.example .gitignore | grep -v "已停用" | grep -v CHANGELOG
```

期望：无输出（`docs/00–03` 与 `docs/source-v3.1/` 属历史归档，不在检查范围）。

### 10.6 无新增限制的检查

本次改动**净减少**两条上限（§3.1 撤销的「主标题 ≤14 字」「其他文字合计 ≤30 字」），不得新增任何一条。对比 `skills/` 下字数上限的出现次数：

```bash
diff <(git grep -oE "≤[0-9]+ 字" main -- skills/ | sed 's/.*://' | sort | uniq -c) \
     <(git grep -oE "≤[0-9]+ 字" -- skills/ | sed 's/.*://' | sort | uniq -c)
```

期望：只有下面两处减少，其余计数一律不变（`≤40 字` 是 L01 原有的，保持 1）：

```diff
3c3
<    3 ≤14 字
---
>    2 ≤14 字
9d8
<    1 ≤30 字
```

`visual-system.md` §三 L 表的「文字量」列数值必须与改动前**逐字一致**：

```bash
python3 - <<'PY'
import re, subprocess
old = subprocess.run(["git","show","main:skills/image-passage/references/visual-system.md"],
                     capture_output=True, text=True).stdout
new = open("skills/image-passage/references/visual-system.md", encoding="utf-8").read()
def rows(t):
    d = {}
    for line in t.splitlines():
        m = re.match(r"\|\s*(L\d{2})\s*\|(.+)", line)
        if m:
            d[m.group(1)] = [c.strip() for c in m.group(2).split("|")]
    return d
o, n = rows(old), rows(new)
# 旧表第 6 列是 CSS 类，新版已删；只比前 5 列（版式 / 适合 / 主元素 / 文字量 / 控制）
diff = [(k, o[k][:5], n[k][:5]) for k in sorted(o) if k not in n or o[k][:5] != n[k][:5]]
print("36 行齐全:", len(n) == 36, "· 前 5 列差异:", diff)
PY
```

期望：`36 行齐全: True · 前 5 列差异: []`——只删掉了 CSS 类列，版式、适合、主元素、**文字量**、控制五列逐字未动。

### 10.7 其他一致性

- 章节号交叉引用：`grep -rn "第.节\|§" skills/` 全量核对（`workflow.md` §一 归属表、`visual-system.md` §三/§五/§七 被多文件引用）。
- `SKILL.md` 行数 < 500，frontmatter `description` ≤ 1024 字符。
- 版本号四处一致：`.claude-plugin/plugin.json`、`.codebuddy-plugin/plugin.json`、`SKILL.md` metadata、README 与 README.en 徽章行。
- `llms.txt`、README、AGENTS.md 里出现的每个路径都指向真实存在的文件（无死链）。
- 端到端（人工）：用 `api` 路线出 1 页，验证「整图生成 ＋ 参考图原样嵌入 ＋ OCR 核对」。

---

## 11. 实施顺序与 PR 拆分

### 11.1 结论：**单个 PR**

中间态无法自洽——删掉 `base.css` 就必须同时改 `render_page.py`、`SKILL.md`、`AGENTS.md`、`workspace.py`、demo；拆开会造成「规则与代码不一致」的提交，违反 AGENTS.md 的双写约定。

### 11.2 建议 commit 顺序（同一 PR 内，便于审阅）

1. `feat!: 渲染路线精简为 native / api 两条`（`render-routing.md`、`env_check.py`、`.env.example`）
2. `feat!: 移除 H / S 构成方式，只保留整图生成`（`page-generation.md`、`prompt-recipes.md`、`spec.md`、`plan.md`、`style-lock.md`、`state.json`、`workspace.py`）
3. `feat!: 移除 H / S 构成方式，只保留整图生成`（`visual-system.md` 的路线适配表、`page-generation.md`、`prompt-recipes.md`、`qa-checklist.md`、`workflow.md`、`onboarding.md`、`characters.md`、`inputs.md`、`spec.md`、`plan.md`、`style-lock.md`、`state.json`、`workspace.py`）
4. `chore!: 删除 svg 链路与 demo`（8 个文件 ＋ demo ＋ `requirements.txt` ＋ `.gitignore` ＋ `palette.py` ＋ `_common.py` ＋ `image_tools.py` 注释）
5. `docs: 同步根文档与版本号 0.3.0`（`SKILL.md`、`AGENTS.md`、`README*`、`INSTALL.md`、`llms.txt`、`CHANGELOG.md`、两处 `plugin.json`、`docs/04`）

### 11.3 CHANGELOG 条目草稿

```markdown
## [0.3.0] - <日期>

### 移除（破坏性变更）

- 渲染路线 `svg`（HTML＋CSS＋内联 SVG 经 Chromium 渲染）与构成方式 `H` 底图＋叠加、`S` 纯排版。
  出图只保留 `native`（环境自带多模态生图）与 `api`（第三方图片模型接口）两条路线，页面一律整图生成。
- 随之删除：`assets/css/base.css`、`scripts/render_page.py`、`scripts/fetch_fonts.py`、
  `references/html-recipes.md`、`templates/page.html`、`templates/page-compose.html`、
  `templates/tokens.css`、`assets/fonts.json`、`examples/demo/`。
- `requirements.txt` 不再需要 Playwright／Chromium；安装流程不再需要下载字体。
- `env_check.py` 输出移除 `compose_H_available`，新增 `reference_support`。

### 变更

- 删除风格 × 渲染路线、版式 × 渲染路线的适配表，规则文件里不再保留「哪种路线适合哪个风格／版式」的分类；`L01–L36`、`V01–V12`、`E01–E39` 编号全部保留，不做停用或分级。
- 原文「上图文字超过阈值 → 改用 H」的自动改判规则移除；文字与版式不匹配时按「换版式 → 拆页 → 正常重试 → 待处理」处理（`visual-system.md` §三、`page-generation.md` §二）。
- 保真素材改为以参考图方式交给模型并明确要求原样保留；生成后逐项核对，不做代码合成。
- `qa_mode` 的 `script-only` 档合并为 `unchecked`（渲染脚本已删除）。
- 页码默认仍按原规则显示；反复写错时可在该页或整套关闭并说明。

### 新增

- `docs/04_渲染路线精简SPEC.md`：本次改造的实施说明。
- 生图工具不支持参考图（`reference_support = no`）时含素材页面的处理规则。
- `examples/copy-sample.md`：`check_copy.py` 的回归基线（原 `examples/demo/copy.md`）。
```

### 11.4 提交与 PR

```bash
git switch -c feat/render-routes-g-only
# ... 按 11.2 的 5 个 commit 提交 ...
git add -A && git status --porcelain     # 确认没混入 .env / 缓存
git push -u origin feat/render-routes-g-only
gh pr create --repo Chans-gh/Image-Passage-IP --base main --head feat/render-routes-g-only \
  --title "feat!: 渲染路线精简为 native / api 两条，移除 svg 与文字叠加层" \
  --body "<引用本 SPEC 的目标、决策、验证结果>"
```

---

## 12. 风险与待实测

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| R1 | **中文文字准确率不稳定**：字数越多、错字与漏字越容易出现 | 高 | 提示词逐字列出（`prompt-recipes.md` §四）；局部编辑修单字；正常重试；仍不通过则 `block`（§3.6）。**不通过限制内容表达来规避** |
| R2 | **模型重绘保真素材**，与不可覆盖原则 3 冲突 | 高 | §4 流程；质检查验设为必查；失败即 `block` |
| R3 | **`native` 生图工具是否支持参考图待实测** | 高 | `reference_support` 字段；`unknown` 时先出 1 页验证 |
| R4 | 失去代码排版后，**精细对齐类版式**（表格、图表、排行榜、目录）的实际效果依赖模型 | 中 | 策划阶段按当次环境说明；效果不达预期时换版式或拆页，不改动规则里的版式清单 |
| R5 | 不能看图的环境**无法核对文字** | 中 | §5.2：先出 1 页、报告标注「未经视觉检查」 |
| R6 | api 路线**成本上升**（重试与试错次数增加） | 中 | 先确认 P1 再批量；P1 确认后锁定参数 |
| R7 | 旧项目工作区残留 HTML 文件造成困惑 | 低 | §9.1 报告里提示一次，不自动删 |

### 待实测（写回 `render-routing.md` 第五节）

| # | 事项 |
|---|---|
| 1 | 各生图模型（GPT 系列、混元、第三方接口）**中文上图的实际情况**：单页多少字开始出错、哪些字型容易错（仅作为提示词与重试策略的参考，**不写进规则成为限制**） |
| 2 | 各工具**是否支持参考图**、支持几张、如何传入（决定 `reference_support` 的实际取值） |
| 3 | 参考图「原样嵌入」的**实际保真度**：截图文字与数字被改动的频率 |
| 4 | 局部编辑（inpainting）修单个错字的**成功率** |
| 5 | 3:4 尺寸支持情况与裁切适配的实际效果 |
| 6 | 提示词语言：中文 / 中英双语对文字正确率的影响 |

---

## 13. 验收标准（DoD）

- [ ] `env_check.py` 的 6 组判定树断言全部通过，输出不再含 Chromium／字体字段，新增 `reference_support`。
- [ ] `RENDER_MODE=svg` 只提示「已停用」，不误判为可用路线。
- [ ] 8 个文件 ＋ `examples/demo/` ＋ `assets/css/` 已删除；`requirements.txt` 无 `playwright`。
- [ ] `workspace.py` 不再创建 `render/` 与 `page.html`，`page` 子命令无 `--composition`。
- [ ] `palette.py` 只剩 `resolve` / `list`。
- [ ] 11 个脚本语法检查通过；`env_check.py --quick`、`call_image_api.py --dry-run`、`image_tools.py` 冒烟通过。
- [ ] `check_copy.py` 对基线样本仍为 errors 0 / warnings 0。
- [ ] §10.5 的残留引用 grep 无输出（历史归档除外）。
- [ ] §10.6 通过：`skills/` 下没有新增任何字数上限或版式／风格分级；`visual-system.md` 的 L 表「文字量」列与改动前逐字一致。
- [ ] `SKILL.md` < 500 行，`description` ≤ 1024 字符，且不再提 HTML/SVG。
- [ ] 版本号四处（两个 plugin.json、SKILL.md、README 徽章）统一为 0.3.0，CHANGELOG 有对应条目。
- [ ] `workflow.md` §一 归属表与 `AGENTS.md` 双写映射表已按 §8 更新。
- [ ] `L01–L36`、`V01–V12`、`E01–E39` 全部保留，未标停用、未分级、未重排。
- [ ] `llms.txt`、README、AGENTS.md、INSTALL.md 中的路径无死链。
- [ ] §14 的六项决议已全部落地。

---

## 14. 决议（已由作者裁决）

| # | 待确认 | **决议** | 落地位置 |
|---|---|---|---|
| Q1 | `assets/fonts.json` 是否删除 | **删除** | §6.1、§6.4 |
| Q2 | `examples/demo/copy.md` 是否保留为 `check_copy.py` 基线 | **保留**，移到 `examples/copy-sample.md` | §6.1、§9.3、§10.4 |
| Q3 | 规则里的「版式 × 渲染路线」适配表 | **清空**：整表删除，不做替代分级，不再出现任何路线适配分类 | §3.3、§6.2 |
| Q4 | `prompt-recipes.md` §五「H 页的底图提示词」 | **删除** | §6.2 |
| Q5 | 页码默认 | **默认按原规则显示**（方案 B）；反复写错时再关闭 | §3.7 |
| Q6 | 「构成方式」术语 | **保留术语**，只留 G 一个取值 | §7 |

> 另：本 SPEC 早先版本中的「每页文字硬上限（≤40 字等）」「版式 L 三级分类」「风格 V 风险分级」「E 图表降级」四项**已全部撤销**——它们是撰写 SPEC 时的自造规则，仓库原有规则中没有，且会与「图文排版」的核心能力冲突。§3 已改写为「不新增限制」。
