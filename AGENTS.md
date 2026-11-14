# AGENTS.md

Notes for AI agents (Claude Code, Codex, WorkBuddy and others) that **use** or **maintain** this repository. The user-facing intro is in [README.md](README.md) (Chinese) and [README.en.md](README.en.md).

## If you are here to install it

Follow [INSTALL.md](INSTALL.md): clone, link the skill for your host agent, install Python dependencies, run `env_check.py`, then report to the user in Chinese.

## If you are here to use the skill

Read `skills/image-passage/SKILL.md` and follow it. It is the entry point; detailed rules live in `skills/image-passage/references/` and are read per stage, on demand. Do not read every reference up front.

Working language for users is Simplified Chinese. Work files go to `./image-passage-work/` in the user's current directory, not inside this repository.

## Repository map

| Path | What it is |
|---|---|
| `skills/image-passage/SKILL.md` | Skill entry: non-overridable principles, stage table ⓪–⑪, routes, scripts, reference index. Keep under 500 lines. |
| `skills/image-passage/references/` | Rule definitions (Chinese). One topic per file; see the ownership table below. |
| `skills/image-passage/templates/` | Files copied into a project by `workspace.py` (`plan.md`, `spec.md`, `style-lock.md`, `state.json`, `copy.md`, `profile.md`, `character.md`, `inputs.md`, `prompt.md`). |
| `skills/image-passage/scripts/` | Python 3.9+ scripts. Standard library plus `requirements.txt`. |
| `skills/image-passage/assets/` | Data used by scripts: `colors.json` (colour names → HEX), `platforms.json` (limits, `verified` flag). |
| `skills/image-passage/agents/openai.yaml` | Codex display metadata. |
| `agents/image-passage.md` | Expert identity and opening for WorkBuddy and as a Claude Code subagent. Defines no rules; it defers to the skill. |
| `.claude-plugin/` | Claude Code `plugin.json` and `marketplace.json` (marketplace `image-passage-ip`, plugin `image-passage`). |
| `.codebuddy-plugin/plugin.json` | WorkBuddy expert manifest. |
| `examples/copy-sample.md` | Copy baseline for `check_copy.py`. |
| `INSTALL.md` | Step-by-step install guide written for AI agents. Keep commands in sync with README and the scripts. |
| `docs/` | Design docs (00–04) and `source-v3.1/`, the read-only archive of the original rules. Not loaded at runtime. |

## Where each rule is defined

Every rule has exactly one defining file. The table is in `skills/image-passage/references/workflow.md` §一; when you change who owns a rule, update that table. Summaries elsewhere (SKILL.md, README, qa-checklist) must point to the definition, not restate it differently.

Some rules are mirrored in code or data. Change both sides together:

| Rule (defined in) | Mirrored in |
|---|---|
| Colour names (`visual-system.md` §七) | `assets/colors.json`; `scripts/palette.py` |
| Length tiers S0–S4, compliance word lists (`copywriting.md` §五, §九) | `scripts/check_copy.py` (`TIERS`, `ABSOLUTE`, `EFFICACY`, `FINANCE`, `INDUCE`) |
| Platform limits (`references/platforms/*.md`) | `assets/platforms.json`; `scripts/check_copy.py` (title, body, tags); `scripts/workspace.py status` (image count); the limits line in SKILL.md principle 8 and the READMEs |
| Final deliverables and first comment (`copywriting.md` §十二, §十四) | `templates/copy.md`; `scripts/check_copy.py` (`首条评论` section); `workflow.md` §七 report format |
| Render modes, reference support, `.env` variables (`render-routing.md` §二, §四) | `.env.example`; `scripts/env_check.py`; `scripts/call_image_api.py` |
| Project files and state (`page-generation.md` §十, `SKILL.md`) | `scripts/workspace.py`; `templates/state.json` |
| Profile fields A–H (`onboarding.md` §三) | `templates/profile.md` |

## Conventions

- **Stable numbering.** Codes such as D01–D20, R01–R18, I00–I10, T01–T23, F1–F5, H01–H15, V01–V12, L01–L36, C01–C13, E01–E39, S0–S4, W1–W9 and K1–K6 are referenced across files and stored in users' `plan.md` / `state.json`. Never renumber. Append new items at the end; mark retired ones as 停用 instead of deleting them.
- **Section numbers are cross-referenced** (for example 「`workflow.md` 第七节」). If you insert, remove or reorder sections, search the whole skill for references to them (`grep -rn "第.节\|§" skills/`) and update them in the same change.
- **Chinese rule files.** Keep references, templates and user-facing script messages in Simplified Chinese, using full-width punctuation and a space between Chinese and Latin text. English is fine in code, manifests and this file.
- **Colours are written as names** in rules and prompts; HEX belongs only in `colors.json` and the 精确版 of a style lock.
- **SKILL.md stays an overview** under 500 lines and the frontmatter `description` stays ≤1024 characters. Put detail in references.
- **No secrets.** Never hardcode keys or endpoints with keys. `.env` is user-supplied and gitignored. Scripts must not print keys; `--dry-run` output masks them.
- **No third-party IP.** Do not add named characters, brand logos or imitations of known IP to examples, prompts or assets. Character support stays generic and opt-in (`characters.md`).
- **Honest status.** Rules and scripts must never report unchecked work as checked. Keep the `unchecked` / `pass-script-only` QA states.
- **Platform limits** were set by the author on 2026-10-30 (title 20, body 800, 15 images, 8 tags, both platforms). Change them only on the author's instruction or a confirmed platform change: update `platforms.json` (`verified_on`), the platform md files, and add a CHANGELOG entry.
- **Final delivery is four parts in a fixed order**: title, body (tags at the end), images, first comment. Keep that order in rules, templates and reports.
- **The avatar is the author's own image** and is excluded from the MIT license (see LICENSE). Do not replace, edit or reuse it without the author's instruction.
- **Version** lives in `.claude-plugin/plugin.json`, `.codebuddy-plugin/plugin.json` and the SKILL.md `metadata.version`. Bump them together, update the version in the README badges line, and add a CHANGELOG entry.
- **WorkBuddy listing material** (submission forms, packaging zips, author contact) is kept outside this repository. Do not add it back.

## Verifying changes

Run from the repository root.

```bash
python3 - <<'PY'
import pathlib
bad = 0
for p in sorted(pathlib.Path("skills/image-passage/scripts").glob("*.py")):
    try:
        compile(p.read_text(encoding="utf-8"), str(p), "exec")
    except SyntaxError as e:
        bad += 1
        print("FAIL", p.name, e)
print("语法错误数:", bad)
PY
```

Check the render-route judgement tree. The `none` results are the ones that changed when the svg route was removed, and `reference_support` is what decides whether pages with real screenshots can be generated at all:

```bash
python3 skills/image-passage/scripts/env_check.py --can-generate yes --can-see yes      # native / visual
python3 skills/image-passage/scripts/env_check.py --can-generate no  --can-see yes      # none  (was svg)
python3 skills/image-passage/scripts/env_check.py --can-generate no  --can-see no       # none
python3 skills/image-passage/scripts/env_check.py --quick
```

Check copy rules against the baseline sample:

```bash
python3 skills/image-passage/scripts/check_copy.py examples/copy-sample.md
```

Evoke the reference-image path without sending anything:

```bash
python3 skills/image-passage/scripts/call_image_api.py --dry-run --prompt "test" --out /tmp/x.png
python3 skills/image-passage/scripts/image_tools.py info <any.png>
```

Smoke-test the workflow scripts in a scratch directory:

```bash
cd "$(mktemp -d)"
python3 <repo>/skills/image-passage/scripts/workspace.py init
python3 <repo>/skills/image-passage/scripts/workspace.py new demo
python3 <repo>/skills/image-passage/scripts/workspace.py page demo P01
python3 <repo>/skills/image-passage/scripts/workspace.py status demo
python3 <repo>/skills/image-passage/scripts/call_image_api.py --help
```

A project must not contain `render/` or `page.html`. `call_image_api.py --dry-run` previews a request without sending it. Do not call a real API in tests unless the user asked and configured one.

## Commit hygiene

- Do not commit `.env`, `image-passage-work/`, font caches or `__pycache__/` (all gitignored).
- Store final images as JPEG; keep sample and baseline files small.
