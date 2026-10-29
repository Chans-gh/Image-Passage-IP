# Changelog

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

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
