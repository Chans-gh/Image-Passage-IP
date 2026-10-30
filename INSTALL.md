# INSTALL.md — installing Image Passage (for AI agents)

This file is written for an AI agent that a user has asked to install this repository. Follow the steps in order, run the commands yourself where your environment allows, and report the result to the user in Simplified Chinese.

- Repository: https://github.com/chans-gh/Image-Passage-IP
- What it is: an Agent Skill (`skills/image-passage/`) that plans and produces 3:4 image-plus-text posts for Xiaohongshu (小红书) and WeChat 贴图号. Output: title, body (with tags), images, first comment.
- Skill name: `image-passage`. Entry file: `skills/image-passage/SKILL.md`.

## 0. Ask nothing you can detect

Detect the host agent from your own environment (Claude Code, Codex, WorkBuddy, or other) and the OS. Only ask the user when a step needs a decision: installing globally vs. for one project (default: global), or how to handle a blocked `pip install` (step 3).

## 1. Get the files

Clone once to a stable location. Default:

```bash
git clone https://github.com/chans-gh/Image-Passage-IP.git "$HOME/.local/share/image-passage"
```

If it already exists, update it instead:

```bash
git -C "$HOME/.local/share/image-passage" pull --ff-only
```

Below, `REPO` means that directory and `SKILL` means `REPO/skills/image-passage`.

## 2. Register the skill with the host agent

Pick the block for your host. Use a symlink so `git pull` updates the installed skill.

### Claude Code

Option A, plugin (the user types these two slash commands; you cannot run them for the user):

```text
/plugin marketplace add chans-gh/Image-Passage-IP
/plugin install image-passage@image-passage-ip
```

Option B, skill only (you can run this):

```bash
mkdir -p "$HOME/.claude/skills"
ln -sfn "$HOME/.local/share/image-passage/skills/image-passage" "$HOME/.claude/skills/image-passage"
```

For one project only, link into `<project>/.claude/skills/image-passage` instead. The skill is picked up in a new session.

### Codex

```bash
mkdir -p "$HOME/.agents/skills"
ln -sfn "$HOME/.local/share/image-passage/skills/image-passage" "$HOME/.agents/skills/image-passage"
```

For one project only, link into `<project>/.agents/skills/image-passage`. Display metadata is in `SKILL/agents/openai.yaml`. Restart Codex so it rescans skills.

### WorkBuddy

The repository root is a WorkBuddy expert package: `.codebuddy-plugin/plugin.json` (manifest), `agents/image-passage.md` (identity and opening), `avatars/expert.png`, and the preloaded skill `skills/image-passage`. The user adds it in the WorkBuddy client (专家市场 →「我的专家」→「创建专家」) by giving it this repository URL or the repository as a zip. Tell the user these steps; you cannot install it from outside the client.

### Other agents

No registration needed. Tell the agent (or yourself) to read `SKILL/SKILL.md` at the start of a task and follow it.

## 3. Python dependencies

The scripts need Python 3.9+. Install the requirements into the interpreter that runs as `python3`:

```bash
python3 -m pip install --user -r "$HOME/.local/share/image-passage/skills/image-passage/scripts/requirements.txt"
```

If pip refuses with `externally-managed-environment`, do not pass `--break-system-packages` on your own. Ask the user which they prefer:

- a virtual environment (`python3 -m venv ~/.local/share/image-passage/.venv`, install there, and activate it before starting the agent), or
- `--break-system-packages` with `--user`.

Then install the browser used for HTML rendering:

```bash
python3 -m playwright install chromium
```

On Linux, if Chromium fails to launch because of missing system libraries, run `python3 -m playwright install-deps chromium` (needs sudo; ask first).

## 4. Fonts

Downloads the default OFL Chinese fonts to `~/.cache/image-passage/fonts` (override with `IMAGE_PASSAGE_FONT_DIR`):

```bash
python3 "$HOME/.local/share/image-passage/skills/image-passage/scripts/fetch_fonts.py"
```

## 5. Optional tools

Install only if the user wants these features; ask before using a package manager.

| Tool | Enables |
|---|---|
| `ffmpeg` | Video frames and audio extraction from video input |
| `tesseract` with the `chi_sim` language pack | OCR check of text on generated images |

## 6. Optional `.env` (image API, transcription)

Only needed for the `api` render route or audio/video transcription. Copy the template into the directory where the user runs the agent:

```bash
cp "$HOME/.local/share/image-passage/.env.example" ./.env
```

Tell the user to fill in `IMAGE_API_BASE_URL`, `IMAGE_API_KEY`, `IMAGE_API_MODEL` (OpenAI-compatible `/images/generations` and `/images/edits`) themselves. **Never ask the user to paste a key into the chat, never print a key, never write one into any file yourself.**

## 7. Verify

```bash
python3 "$HOME/.local/share/image-passage/skills/image-passage/scripts/env_check.py"
```

It reports Chromium, Pillow, ffmpeg, tesseract, fonts and `.env`, and recommends a render route. Output is in Chinese. A working install shows `Chromium：可用` and at least one font on the `字体：` line. Optionally render the demo:

```bash
cd "$HOME/.local/share/image-passage"
cp skills/image-passage/assets/css/base.css examples/demo/render/
python3 skills/image-passage/scripts/render_page.py examples/demo/pages/P0*/page.html --out-dir /tmp/image-passage-demo
```

Expect 5 PNGs at 1242×1656 and `0` errors.

## 8. Report to the user

Tell the user, in Chinese:

1. Where it is installed and for which agent.
2. The `env_check.py` result: recommended route (native / svg / api) and anything missing.
3. How to start: open a new session and say 「帮我做一套小红书图文」, 「只策划，先不出图」 or 「只写标题、正文和首条评论」.
4. That work files will be written to `./image-passage-work/` in the directory where they run the agent.

## Update and uninstall

```bash
git -C "$HOME/.local/share/image-passage" pull --ff-only
```

To uninstall, remove the symlink you created in step 2 and the clone. Fonts are cached in `~/.cache/image-passage/`.

```bash
rm "$HOME/.claude/skills/image-passage" "$HOME/.agents/skills/image-passage" 2>/dev/null; rm -rf "$HOME/.local/share/image-passage" "$HOME/.cache/image-passage"
```
