# HTML 排版写法（S 纯排版页、H 页的文字层）

S 页和 H 页用 HTML＋CSS 排版，`scripts/render_page.py` 用 Chromium 渲染成 1242×1656 的 PNG，并做排版检查。HTML 的排版能力（自动换行、flex、grid、中文字体）比手写 SVG 稳定得多；图表、图标、连线用**内联 SVG**。

## 一、准备

```bash
python3 scripts/fetch_fonts.py                  # 第一次：下载默认字体（思源黑体、霞鹜文楷）
python3 scripts/fetch_fonts.py --only noto-serif-sc long-cang   # 按风格补充
python3 scripts/palette.py tokens --out <项目>/render/tokens.css \
  --bg 暖米白 --surface 纯白 --text 炭灰 --primary 鼠尾草绿 --accent 珊瑚橙 --highlight 奶油黄 \
  --font-title noto-sans-sc --font-body noto-sans-sc --font-hand lxgw-wenkai
python3 scripts/workspace.py page <项目名> P02 --composition S   # 生成 pages/P02/page.html
```

`workspace.py new` 已经把 `base.css` 和默认 `tokens.css` 复制到 `<项目>/render/`。P1 采用后按风格锁重新生成 `tokens.css`，之后不逐页修改。`render_page.py` 会自动注入已下载字体的 `@font-face`。

## 二、页面骨架

```html
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="../../render/base.css">
<link rel="stylesheet" href="../../render/tokens.css">
</head>
<body>
<main class="page v03 l-steps">
  <header class="header">
    <span class="kicker">新手养绿萝</span>
    <h1 class="t-title">三步救回<span class="hl">黄叶</span>绿萝</h1>
  </header>
  <!-- 版式内容 -->
  <div class="pagenum">3 / 8</div>
</main>
</body>
</html>
```

- `main.page`：固定 1242×1656，四周 `--margin`（64px），底部多留 56px 给页码。
- 风格类 `v01`～`v12` 和版式类 `l-*` 都加在 `main` 上。
- 封面和 F1 不显示页码：加 `no-pagenum`，并删掉 `.pagenum` 元素。
- 页面级局部样式写在 `<style>` 里，**只用 CSS 变量取色**（`var(--c-primary)`），不写死 HEX，保证整套一致。

## 三、类参考

### 文字角色（检查脚本按角色检查最小字号）

| 类 | 用途 | 默认字号 | 下限 |
|---|---|---|---|
| `.t-cover` | 封面主标题 | 132 | 110 |
| `.t-title` | 页面标题 | 80 | 72 |
| `.t-sub` | 副标题、小标题 | 52 | 48 |
| `.t-body` | 正文 | 42 | 40 |
| `.t-note` | 注释、来源、图注 | 30 | 30 |
| `.t-hand` / `.t-serif` | 改用手写 / 衬线字体 | — | — |
| `.t-center` `.t-muted` `.t-primary` `.t-accent` `.nowrap` | 对齐、颜色、不换行 | — | — |

带角色类的文字低于下限记为错误；其他文字低于 30px 记为警告。确实需要的极少数装饰小字加 `.allow-small`。

### 强调（每页 ≤3 处，`.l-poster` 和 `.v11` ≤2 处）

`.hl` 荧光笔底线 · `.circle` 圈注（脚本计数）· `.em` 强调色加粗（不计数，但同样要克制）

### 组件

| 类 | 说明 |
|---|---|
| `.header` `.kicker` | 标题区；栏目小标签 |
| `.card`（`.soft` `.plain`） | 卡片；浅主色底；无边框 |
| `.tag`（`.outline` `.example`） | 标签徽章；描边；「示例」灰标签 |
| `.badge-num` | 圆形数字徽章 |
| `ul.dots` / `ol.nums` | 圆点列表 / 编号列表 |
| `.row` `.col` `.stack` `.grow` `.spacer` `.center` | 布局辅助 |
| `.divider` | 分隔线 |
| `.photo`（`.contain`）＋ `img` | 照片、截图容器；默认 cover，`.contain` 保留完整截图 |
| `.caption` | 图注 |
| `.source` | 来源条 E09：`<footer class="source"><b>来源</b>名称 · 2026-10</footer>` |
| `.pagenum` | 页码 |
| `.signature` | 署名，右上角 |
| `.mask`（`.blur`） | 盖在截图上遮挡隐私（`position:absolute` 坐标） |
| `.tape` | 胶带装饰（V05） |
| `.ui-bar` `.ui-search` | 界面样式（V12） |
| `.bleed` `.allow-margin` | 允许进入边距区（满版照片等），检查脚本跳过安全区检查 |

## 四、版式片段

### L15 纯字排大字报（封面 C01）

```html
<main class="page v11 l-poster no-pagenum">
  <h1 class="t-cover">下班后<br>可以<span class="hl">不回</span>消息</h1>
  <div class="poster-foot t-note t-muted">一个关于边界的小提醒</div>
</main>
```

### L01 大标题＋核心视觉

```html
<main class="page v03 l-hero no-pagenum">
  <header class="header">
    <span class="kicker">新手向</span>
    <h1 class="t-cover">绿萝黄叶<br>先查这 3 处</h1>
  </header>
  <div class="visual"><div class="photo" style="width:100%;height:100%"><img src="../../inputs/IMG_001.jpg" alt=""></div></div>
</main>
```

### L05 步骤流程

```html
<main class="page v03 l-steps">
  <h1 class="t-title">三步救回黄叶绿萝</h1>
  <ol class="steps">
    <li><span class="badge-num">1</span>
      <div class="step-text"><h3 class="t-sub">剪掉黄叶</h3><p class="t-body">从叶柄底部剪，别只剪一半</p></div></li>
    <li><span class="badge-num">2</span>
      <div class="step-text"><h3 class="t-sub">换疏松土</h3><p class="t-body">泥炭土加珍珠岩，约 3:1</p></div></li>
    <li><span class="badge-num">3</span>
      <div class="step-text"><h3 class="t-sub">放散射光处</h3><p class="t-body">避开正午直晒</p></div></li>
  </ol>
  <div class="pagenum">3 / 8</div>
</main>
```

### L03 左右对照

```html
<main class="page v03 l-split">
  <h1 class="t-title">两种浇水方式</h1>
  <div class="cols">
    <div class="col"><span class="tag outline">定时浇</span><p class="t-body">每周固定一天</p></div>
    <div class="col"><span class="tag">看土浇</span><p class="t-body">表土干 2 厘米再浇</p></div>
  </div>
  <div class="pagenum">4 / 8</div>
</main>
```

`.l-beforeafter`：`.cols` 里放两个 `.photo`，各加 `<span class="label">前</span>`。

### L23 多列对比表

```html
<main class="page v03 l-table">
  <h1 class="t-title">三种土怎么选</h1>
  <table>
    <tr><th>土</th><th>透气</th><th>保水</th><th>适合</th></tr>
    <tr><td>园土</td><td>差</td><td>强</td><td>不建议</td></tr>
    <tr><td>泥炭土</td><td>中</td><td>中</td><td>大多数</td></tr>
    <tr class="verdict"><td>结论</td><td colspan="3">泥炭土加珍珠岩最省心</td></tr>
  </table>
  <footer class="source"><b>来源</b>示例数据 · 仅作演示</footer>
  <div class="pagenum">5 / 8</div>
</main>
```

### L24 对错示范

```html
<main class="page v11 l-dodont">
  <h1 class="t-title">这样说更好接</h1>
  <div class="pairs">
    <div class="bad t-body">「你怎么又没回消息？」</div>
    <div class="good t-body">「这件事今天下班前需要你确认一下」</div>
  </div>
  <div class="pagenum">2 / 3</div>
</main>
```

符号 ✕ / ✓ 由 CSS 自动加，满足「不只靠颜色」。

### L09 分组清单 / L34 目录

```html
<main class="page v03 l-list">
  <h1 class="t-title">换盆要准备的东西</h1>
  <section class="groups">
    <div class="group"><h3>必备</h3><ul class="dots t-body"><li>大一号的花盆</li><li>泥炭土</li></ul></div>
    <div class="group"><h3>可选</h3><ul class="dots t-body"><li>珍珠岩</li></ul></div>
  </section>
  <div class="pagenum">6 / 8</div>
</main>
```

### L29 卡片网格 / L11 图鉴

```html
<main class="page v09 l-grid">
  <h1 class="t-title">4 种常见黄叶</h1>
  <div class="cards" style="--cols:2">
    <div class="card"><span class="no">NO.01</span><h3 class="t-sub">老叶自然黄</h3><p class="t-body">底部 1～2 片，正常</p></div>
    <!-- … -->
  </div>
  <div class="pagenum">2 / 8</div>
</main>
```

### 其他版式的结构

| 版式 | 类 | 结构 |
|---|---|---|
| L02 大数字 | `.l-bignum` | `<div class="num">72<span class="unit">%</span></div>` ＋ 解释 ＋ `.source` |
| L06 时间线 | `.l-timeline` | `ol.timeline > li > .when ＋ .t-body` |
| L07 矩阵 | `.l-matrix` | `.matrix` 里 4 个 `.card`；坐标轴文字用 `.axis` |
| L10 截图批注 | `.l-annot` | `.shot > img ＋ .pin（绝对定位编号）＋ .ring（圈注框）`；下面 `.notes > div > .pin ＋ 说明` |
| L16 金句 | `.l-quote` | `blockquote ＋ cite` |
| L17 段落 | `.l-text` | 最多 3 个 `.para > h3 ＋ p.t-body` |
| L18 问答 | `.l-qa` | `.qa > .q ＋ .a`（Q / A 自动加） |
| L19 大图 | `.l-photo`（满版加 `.full`） | `.photo > img`；满版时文字放 `.overlay` |
| L20 拼贴 | `.l-collage` | `.grid` 设 `--cols`，里面多个 `.photo` |
| L21 部件标注 | `.l-parts` | `.subject > img ＋ .callout（绝对定位标签）` |
| L26 金字塔 | `.l-pyramid` | `.levels > .level`，最多 5 级，自上而下变宽 |
| L28 排行 | `.l-rank` | `ol.rank > li`（名次自动加） |
| L14 打勾表 | `.l-checklist` | `ul.checks > li`（`.done` 已勾选）；`.blank` 填写线 |
| L32 投票 | `.l-vote` | `.options > .option > .letter ＋ 说明` |
| L12 对话 | `.l-chat` | `.thread > .bubble`（`.me` 右侧）；`.who` 说话人 |
| L35 尾页 | `.l-ending` | 回顾要点 ＋ 一个 `.card.soft` 互动句 |
| L33 / L36 通知、征集 | `.l-notice` | 问题或标题 ＋ `dl.facts > dt ＋ dd` |

## 五、内联 SVG：图表与图示

图表的数据写死在 SVG 里，坐标手算。颜色只用 `currentColor` 或 CSS 变量（`style="fill:var(--c-primary)"`）。

**条形图（E27）**

```html
<svg viewBox="0 0 1000 420" width="100%" style="font-size:34px">
  <g style="fill:var(--c-primary)">
    <rect x="220" y="20"  width="720" height="80" rx="16"/>
    <rect x="220" y="160" width="480" height="80" rx="16"/>
    <rect x="220" y="300" width="260" height="80" rx="16"/>
  </g>
  <g style="fill:var(--c-text)" dominant-baseline="middle">
    <text x="0" y="60">泥炭土</text><text x="0" y="200">椰糠</text><text x="0" y="340">园土</text>
    <text x="960" y="60" text-anchor="end" style="fill:var(--c-surface)">90%</text>
  </g>
</svg>
```

**箭头和连线（E18、E23）**

```html
<svg width="0" height="0" style="position:absolute">
  <defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M0 0L10 5L0 10z" style="fill:var(--c-line)"/></marker></defs>
</svg>
<svg viewBox="0 0 1000 200" width="100%">
  <path d="M120 100 H880" style="stroke:var(--c-line);stroke-width:6;fill:none" marker-end="url(#arr)"/>
</svg>
```

- SVG 里的 `<text>` 不会被检查脚本按角色检查字号，字号自己保证 ≥30（viewBox 缩放后）。
- 折线图用 `<polyline>`，环形占比用两个 `<circle>` 加 `stroke-dasharray`。
- 决策树、思维导图（L08、L25）：用 HTML 卡片放文字，SVG 只画连线，文字更容易排好。
- 图标：简单几何图形手画即可；不用品牌 Logo。

## 六、图片与素材

- 路径相对 `pages/PNN/`：用户素材 `../../inputs/xxx.jpg`，角色 PNG `../../../_assets/characters/<名>/poses/point.png`。
- 截图用 `.photo.contain`，保持完整、不变形；照片用 `.photo`（cover 裁切）。
- 遮挡隐私优先在图片文件上处理（`image_tools.py mask … --style blur`），比 CSS 的 `.mask` 更可靠。
- 检查脚本会报告加载失败的图片。

## 七、渲染与检查

```bash
python3 scripts/render_page.py <项目>/pages/P03/page.html --out <项目>/pages/P03/v1.png
python3 scripts/render_page.py <项目>/pages/P0*/page.html --out-dir <项目>/preview   # 批量
python3 scripts/render_page.py <项目>/pages/P03/page.html --check-only --report qa.json
python3 scripts/render_page.py <项目>/pages/P01/page.html --out thumb.png --scale 0.33   # 封面缩略图检查
```

| 检查 | 级别 | 含义 |
|---|---|---|
| overflow | 错误 | 元素内容超出自身（文字被截断） |
| offpage | 错误 | 元素超出画布 |
| safe-area | 警告 | 进入四周 64px 边距（页码、署名、`.bleed`、`.allow-margin` 除外） |
| font-size | 错误 / 警告 | 角色字号低于下限（错误）；其他文字 <30px（警告） |
| font | 警告 | 指定的字体没有加载（没下载或名称错） |
| image | 错误 | 图片加载失败 |
| overlap | 警告 | 两个文字块重叠超过 15% |
| highlight | 警告 | 高亮超过上限 |

有错误时退出码为 1，不能采用。警告逐条判断：确属设计需要（例如满版照片进入边距）就加对应的豁免类，否则修正。

## 八、常见问题

| 问题 | 处理 |
|---|---|
| 文字溢出 | 先删字（移到正文），再缩小间距，最后才降字号（不低于下限）。不要把正文降到 40px 以下 |
| 页面太空 | 增大标题、放大主视觉、加一个来源条或互动卡；不凑内容 |
| 中文显示成方块或宋体 | 运行 `fetch_fonts.py`；检查 `font` 警告 |
| 颜色不统一 | 删掉写死的 HEX，改用变量；重新生成 `tokens.css` |
| 一行只剩一个字 | 调整断行（`<br>`）或加 `.nowrap` 包住词组 |
| H 页文字压在底图图案上 | 用 `.zone.plate` 加半透明底，或重新生成底图并扩大留白区 |
