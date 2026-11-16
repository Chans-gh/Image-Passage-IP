# 文字前置与确认 SPEC

针对 **Image-Passage-IP** 的第二个改动，与 `docs/04_渲染路线精简SPEC.md` 同一分支（`feat/render-routes-g-only`）、同一个 PR。

## 一、问题

`docs/04` 把出图收敛为「两条路线、一种构成（整图生成）」之后，**文字仍然分两处产出，而且没有完整的确认过程**。核查出三处断点：

| 断点 | 现状 | 后果 |
|---|---|---|
| 1 | 图上文字在 `plan.md` 逐页策划里逐字列出，但对话里的策划精简版明确规定「**不写**上图文字全文」 | 用户确认的是「页面标题」，不是真正会画到图上的那句话；确认了一个自己没看全的版本 |
| 2 | 标题、正文、标签、首条评论在**第九阶段**（出图之后）才产出，第十阶段直接作为最终交付给出 | 全仓库只有「确认策划」「确认 P1」两个节点，**发布文案没有任何确认节点**。文案不合意时图已经做完，只能返工 |
| 3 | `workflow.md` 第六节的变更边界只列了四类改动（实测改资料、改核心结论、改主风格、增删页） | 「改图上文字」「改正文」不在其中，策划确认后改文案不需要重新确认，与「文字全量前置」的设计意图冲突 |

原设计把正文放在出图之后的理由是「正文要补充图片没展开的、不能与图片矛盾」（`copywriting.md` 第四节）。但这条理由在当前设计下已经不成立：每页的核心观点和上图文字在第六阶段就已定死，图文分工在策划阶段就能判断，保真素材也已经确定。而且 `templates/state.json` 本来就有 `copy.synced_with_pages` 字段，说明原设计留了「文案先出、出图后同步」的钩子，只是流程没接上。

## 二、决议（作者）

| 编号 | 决议 |
|---|---|
| D1 | **正文与首条评论一起前置到第六阶段**，与策划一并产出、一并确认 |
| D2 | **对话精简版给图上文字全文**：用「每页文字块」取代原来的「每页一行」 |
| D3 | **采纳 A 方案**：维持「文字全量前置」，用脚本补上内页文字此前没有检查的空档 |

## 三、新模型

确认 1 的产物从「策划」扩为「**策划 + 全部文字**」：

| 环节 | 旧 | 新 |
|---|---|---|
| ⑥ | 写 `plan.md`；只给策划方向 | 写 `plan.md` **＋ `copy.md` 成稿**；跑 `check_copy.py --plan` |
| ⑦ P1 与风格锁 | — | 不变 |
| ⑧ 逐页生成 | 规格单 → 生成 → 采用 | 不变；新增「规格单的图上文字必须逐字等于 `plan.md`」核对（`--spec-dir`） |
| ⑨ | 从零写发布文案 | **文案复核与同步**：按实际图片核对，无矛盾则 `copy.synced_with_pages = true` |

- 文案在确认 1 时就是**成稿**，不是提纲：确认后应当可以直接发布。
- 不再有「图片完成前的文案标为『文案版本』」这种默认中间态；只有「只写文案、不出图」的任务仍标「文案版本」。
- 第六节变更边界新增「改动图上文字或发布文案里的事实、数据、结论」。

## 四、文件级改动清单

| 文件 | 改动 |
|---|---|
| `references/workflow.md` | 第三节状态表与确认语义（确认策划**和同一版本的全部文字**）；第四节阶段流 ⑥ 改名「策划与全部文字」、新增第 8～10 步（写 `copy.md`、跑检查、置 `copy` 字段）、⑧ 补规格单逐字核对、⑨ 改写为「文案复核与同步」；第五节改名并新增「文字」小节、精简版改为「每页文字块」；第六节变更边界补文字类改动 |
| `SKILL.md` | 阶段表 ⑥ → 「策划与文字」、⑨ → 「文案复核」；确认节点说明改为「确认策划与全部文字」；脚本表补 `--plan` / `--spec-dir`；项目文件树注明 `copy.md` 的产出时机；快速路径「只写标题和正文」→ 走 ⑥ |
| `references/copywriting.md` | 第十二节：四项文案改为「第六阶段随策划产出并确认」，写明同步口径与「只写文案」时的「文案版本」标注；第十三节：补 `--plan` / `--spec-dir` 命令与检查项，并写明错别字无法用词表检出 |
| `references/page-generation.md` | 第四节「上图文字」字段补「本页没有文字时整行写『无文字』」 |
| `references/qa-checklist.md` | C 节新增「确认 1 交付时策划与全部文字一起给出」；I 节新增「正文与图片无矛盾、`copy.synced_with_pages` 已置 true」 |
| `templates/plan.md` | 「发布文案方向」加注释：这一节只写方向，成稿在 `copy.md`；页码行补 `off` 写法 |
| `templates/copy.md` | 头部注释补产出时机与新的检查命令 |
| `templates/spec.md` | 「上图文字」注释补「本页没有文字时整行写『- 无文字』」 |
| `scripts/check_copy.py` | 新增 `--plan <路径>` 与 `--spec-dir <目录>`；抽出 `declares_no_text()`、`spec_page_lines()`、`plan_text_area()`、`plan_pages()`、`spec_dir_pages()`、`check_pages()`、`compare_sources()`；`spec.sources[].pages[]` 增加 `unmarked` / `no_text` |
| `scripts/workspace.py` | 新增 `state <项目> <字段> <值> [--event]`：写 `state.json` 的一个字段并同步 `updated` 与 `log`，供 ⑥⑦⑨ 的确认、锁定、同步使用 |
| `references/page-generation.md` | §十 补「改 `state.json` 一律用 `workspace.py state`」与原因 |
| `AGENTS.md` | 镜像表补「逐页上图文字」行、更新「最终交付四项」行；Conventions 的交付四项补产出时机；Verifying changes 补三条命令 |
| `README.md` / `README.en.md` | 流程图一行改为「策划与文案 → 逐页出图 → 文案复核」；质检一条补图上文字检查 |
| `CHANGELOG.md` | 扩写 `[0.3.0]`：新增「确认 1 含全部文字」破坏性条目与 `--plan` / `--spec-dir` 新增条目 |
| `docs/04_渲染路线精简SPEC.md` | 修正两处受影响的表述（`templates/copy.md` 由「不改」改为指向本文档；双写表补 `workflow.md` §四 ⑥） |

## 五、检查脚本的能力与边界

```bash
# 第六阶段：读 plan.md 的逐页「上图文字」
python3 scripts/check_copy.py <项目>/copy.md --plan <项目>/plan.md

# 第八阶段起：读各页 spec.md（核对提取出来的文字与策划一致）
python3 scripts/check_copy.py --spec-dir <项目>/pages
```

**能做**：空 `「」`、占位词（`待补` / `TODO` 等）、绝对化用语 / 功效 / 收益承诺 / 诱导互动 / profile 禁用词、每页逐条字数清单（供人工核对，**不与任何阈值比较**）。

**不能做**：**错别字与繁简混用无法用词表可靠检出**。这几项仍要靠看图或人工逐字核对，不因为跑了脚本就算通过。

三个设计取舍：

- 第六阶段用 `--plan` 而不是 `--spec-dir`：`pages/PNN/spec.md` 要到第八阶段才由 `workspace.py page` 从 `plan.md` 提取生成，第六阶段跑 `--spec-dir` 是空的。
- 两个来源各自报告，同时给出**逐页比对**：两个都传时，同一页码的图上文字必须一致，不一致报 `text-mismatch`。只比文字，不比层级名——两边的层级命名本来就不一样。所以第八阶段可以只跑一条命令同时完成检查与核对。
- 纯图页在图上的文字处**整行**写「无文字」才算声明：带 `「」` 的行、或标记句之外还有别的内容，都按「本页有文字」处理。判定必须看整节而不是某一行——只看单行会让同页其他行的空文字、占位词和合规词一起被静默跳过。

`issues[].type` 分两类，看来源还是看内容：

| 类型 | 含义 |
|---|---|
| `plan` / `plan-empty` | `plan.md` 结构问题：没有「上图文字」小节 / 小节里没有任何内容 |
| `spec` | `spec.md` 结构问题：缺少该小节，或 `--spec-dir` 下一个 `P*/spec.md` 都没有 |
| `text-*` | 图上文字的内容问题，**两个来源共用**：`text-empty`（空「」）、`text-placeholder`（占位词）、`text-absolute` / `text-efficacy` / `text-finance` / `text-induce` / `text-banned`（合规）、`text-count` 与 `text-none`（清单，info 级）、`text-unmarked`（未用「」标注，无法检查） |
| `text-mismatch` | 两个来源同时给出时，同一页码的图上文字对不上（`spec.md` 提取出错） |

`text-*` 用来源中立的命名，是因为同一套内容检查对两个来源完全一致；**来源由 `detail` 里的文件名区分**，所以 `text-empty` 可能来自 `plan.md`，也可能来自 `spec.md`。

`spec.sources[].pages[]` 每页给四个字段：`page`、`lines`（逐条 `level` / `text` / `count`）、`unmarked`（未用「」标注的行）、`no_text`（本页是否声明无文字）。

## 六、验证

```bash
# 基线不变
python3 skills/image-passage/scripts/check_copy.py examples/copy-sample.md   # errors 0 / warnings 0

# 纯图页不误报
python3 skills/image-passage/scripts/check_copy.py --spec-dir <项目>/pages
#   info  text-none | spec.md P03 声明本页无图上文字

# 逐字清单可直接照抄核对
python3 skills/image-passage/scripts/check_copy.py --plan <项目>/plan.md

# 第八阶段：一个命令同时做内容检查与两个来源的逐页比对
python3 skills/image-passage/scripts/check_copy.py --plan <项目>/plan.md --spec-dir <项目>/pages
#   error  text-mismatch | P01 的图上文字在 plan.md 与 spec.md 里不一致：……
```

覆盖的分支：空 `「」`（模板初始态）报 error；填了两条、留一条空时报那一条；整节写「无文字」（同行内联 / 嵌套 / 独立行）只报 info；主标题恰好是「无文字」时按普通文字统计；两个来源对不上时报 `text-mismatch`。

**回归项（必须一直成立）**：同一页里既有正文又有一行裸「无」时，正文的合规检查**不能**被跳过。判定看整节而不是单行，就是为了这个。

## 七、明确不做的事

- **不新增任何字数上限**（`docs/04` 已裁决，本轮继续）。
- **不做自动错别字纠正**：需要词表或模型，且会把新的规则归属引入代码，与「每条规则只有一个定义文件」冲突。脚本只负责查出可疑项，判断留给人。
