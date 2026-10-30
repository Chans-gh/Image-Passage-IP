# WorkBuddy 上架材料

本文件整理把「图文策划师」上传到 WorkBuddy 需要的全部描述、字段和要求。规则来源：[WorkBuddy 专家开发文档](https://open.workbuddy.cn/docs/expert)（2026-10-30 查阅）。字段的实际值以 `.codebuddy-plugin/plugin.json` 为准，本文件只是方便复制和核对。

## 一、上传前必须补的一项

| 项 | 说明 |
|---|---|
| `author.email` | WorkBuddy 要求必填。仓库是公开的，这个邮箱会随 `plugin.json` 公开。可以用专门的联系邮箱，或 GitHub 的 noreply 邮箱。填好后运行第五节的检查命令。 |

其余字段都已填好，并通过 `tools/workbuddy_package.py check` 的格式检查。

## 二、包结构

```
image-passage/
├── .codebuddy-plugin/plugin.json   专家清单
├── agents/image-passage.md         专家身份与开场（系统提示词）
├── avatars/expert.png              头像 512×512 PNG
├── skills/image-passage/           预加载的技能（规则、模板、脚本）
├── README.md
├── LICENSE
└── .env.example                    可选配置模板（不含任何真实 KEY）
```

`docs/`、`examples/`、`.claude-plugin/` 不进包。

## 三、可直接复制的字段

### 基本信息

| 字段 | 中文 | English |
|---|---|---|
| 名称 `displayName` | 图文策划师 | Image Passage |
| 职业 `profession` | 图文策划与视觉制作 | Image-Text Post Producer |
| 分类 `categoryId` | `06-ContentCreative`（内容创意） | |
| 标识 `name` / `plugin` / `agentName` | `image-passage` | |
| 版本 `version` | `0.2.0` | |
| 协议 `license` | MIT | |
| 主页 `homepage` | https://github.com/chans-gh/Image-Passage-IP | |

### 简介 `displayDescription`（中文要求 40～50 字）

- 中文（48 字）：为小红书和微信贴图号策划整套图文，从选题核实、风格选型到逐页出图，配齐标题、正文与首条评论并质检
- English：Plans complete image-text posts for Xiaohongshu and WeChat: topic checks, style selection, page-by-page images, title, body and first comment, with QA

### 英文短描述 `description`

Plans and produces image-text posts for Xiaohongshu and WeChat: title, body, images and first comment

### 快捷提示 `quickPrompts`（恰好 3 个，第一个同时是 `defaultInitPrompt`）

| # | 中文 | English |
|---|---|---|
| 1 | 帮我做一套小红书图文 | Make a Xiaohongshu image-text post |
| 2 | 只策划，先不出图 | Plan only, no images yet |
| 3 | 只写标题、正文和首条评论 | Write the title, body and first comment only |

### 标签 `tags`（恰好 3 个）

| 中文 | English |
|---|---|
| 图文策划 | Post Planning |
| 小红书 | Xiaohongshu |
| 微信贴图 | WeChat Images |

### 关键词 `keywords`

xiaohongshu、wechat、carousel、image-text post、content planning、小红书、图文

### 头像

`avatars/expert.png`：512×512 PNG，约 260KB（要求 ≤500KB，插画风格，与角色相符）。由作者提供的形象裁切而成。

### 专家介绍（市场详情页可用的长描述）

> 图文策划师帮你把一句话、一段经历或一堆素材，做成一套能直接发布的小红书 / 微信贴图号图文。
>
> - **完整交付四项**：标题、正文（含标签）、图片、首条评论。
> - **先策划再出图**：选题核实、读者价值、内容模板、视觉风格和每页版式都写进策划，你确认后再出图。
> - **字不出错**：字多的页用排版渲染或「底图＋叠字」，截图原样嵌入，避免生图模型写错字。
> - **风格统一**：封面确认后锁定配色、字体和版式参数，整套图保持一致。
> - **如实报告**：不编造经历和数据；哪些页检查过、哪些没检查，交付时说清楚。
> - **可选个性化**：设置账号定位、口吻和视觉偏好，或发几张过往笔记截图让它提取风格。
>
> 默认上限：标题 20 字、正文 800 字、图片 15 张、标签 8 个。

## 四、agent 文件要求（已满足）

| 要求 | 本项目 |
|---|---|
| frontmatter 有 `name`，且等于文件名 | `image-passage` |
| `description` 用英文，供系统判断何时启用 | 已写 |
| `displayName`、`profession` 中英双语 | 已写 |
| 不能声明 `tools`，权限由系统分配 | 未声明。依赖的 Read、Write、Bash、WebSearch、WebFetch 都是内置工具 |
| `maxTurns`（可选，默认 50） | 100：整套图逐页生成，轮次较多 |
| `skills`（可选） | `[image-passage]` |

## 五、检查与打包

在仓库根目录：

```bash
python3 tools/workbuddy_package.py check
```

```bash
python3 tools/workbuddy_package.py zip
```

生成 `dist/image-passage-workbuddy.zip`，只包含 git 已跟踪的文件，`.env`、工作区和缓存不会进包。zip 里默认套一层 `image-passage/` 目录（与官方模板一致）；平台提示解析失败时，加 `--flat` 重新打包试试。仍然失败时，官方建议发邮件到 openworkbuddy@tencent.com。

## 六、两种上架方式

1. **开放平台上传**：在 WorkBuddy 开放平台创建专家，上传第五节的 zip。
2. **客户端创建**：在专家市场右上角「我的专家」→「创建专家」，会打开一个对话。可以把本仓库地址和下面这段话发给它：

> 请按这个仓库创建专家：https://github.com/chans-gh/Image-Passage-IP 。专家清单在 `.codebuddy-plugin/plugin.json`，身份与开场在 `agents/image-passage.md`，预加载技能 `skills/image-passage`，头像 `avatars/expert.png`。字段按清单原样使用，不要改写规则文件。

## 七、上架后自测清单

| # | 测试 | 期望 |
|---|---|---|
| 1 | 首次打开，不说需求 | 简短自我介绍，给出四个开场选择 |
| 2 | 点「帮我做一套小红书图文」，给一个主题 | 先给策划（每页一行），等你确认 |
| 3 | 确认策划 | 生成封面 P1，等你确认 |
| 4 | 确认 P1 | 逐页出图，最后按「标题、正文、图片、首条评论」交付，并报告质检方式 |
| 5 | 「改第 3 页的标题」 | 只改 P03，生成新版本，其他页不动 |
| 6 | 新开会话说「继续」 | 读取 `image-passage-work/` 里的状态接着做 |
| 7 | 「只写标题、正文和首条评论」 | 不出图，交付三项，标为「文案版本」 |
| 8 | 记录环境能力 | WorkBuddy 能否原生生图、能否看图、能否运行 Python 脚本。结果告诉维护者，用于完善 `render-routing.md` |

## 八、不能做的事

- 包里不能有真实的 KEY 或 token。图片接口 KEY 只放在用户自己的 `.env`，`.env` 不进包。
- 头像和示例不能使用他人肖像、知名 IP 或品牌标识。
- 不声明 `tools` 字段。
