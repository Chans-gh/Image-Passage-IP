# AGENTS.md

Notes for AI agents (Claude Code, Codex, WorkBuddy and others) that **use** or **maintain** this repository. The user-facing intro is in [README.md](README.md) (Chinese) and [README.en.md](README.en.md).

## If you are here to use the skill

Read `skills/image-passage/SKILL.md` and follow it. It is the entry point; detailed rules live in `skills/image-passage/references/` and are read per stage, on demand. Do not read every reference up front.

Working language for users is Simplified Chinese. Work files go to `./image-passage-work/` in the user's current directory, not inside this repository.

## Repository map

| Path | What it is |
|---|---|
| `skills/image-passage/SKILL.md` | Skill entry: non-overridable principles, stage table ⓪–⑪, routes, scripts, reference index. Keep under 500 lines. |
| `skills/image-passage/references/` | Rule definitions (Chinese). One topic per file; see the ownership table below. |
| `skills/image-passage/templates/` | Files copied into a project by `workspace.py` (`plan.md`, `spec.md`, `style-lock.md`, `state.json`, `page.html`, `page-compose.html`, `tokens.css`, `copy.md`, `profile.md`, `character.md`, `inputs.md`, `prompt.md`). |
| `skills/image-passage/scripts/` | Python 3.9+ scripts. Standard library plus `requirements.txt`. |
| `skills/image-passage/assets/` | Data used by scripts: `colors.json` (colour names → HEX), `fonts.json` (OFL fonts), `platforms.json` (limits, `verified` flag), `css/base.css` (layout and component classes). |
| `skills/image-passage/agents/openai.yaml` | Codex display metadata. |
| `agents/image-passage.md` | Expert identity and opening for WorkBuddy and as a Claude Code subagent. Defines no rules; it defers to the skill. |
| `.claude-plugin/` | Claude Code `plugin.json` and `marketplace.json` (marketplace `image-passage-ip`, plugin `image-passage`). |
| `.codebuddy-plugin/plugin.json` | WorkBuddy expert manifest. |
| `examples/demo/` | 5-page demo on the svg route; used as a regression check. |
| `docs/` | Design docs (00–03) and `source-v3.1/`, the read-only archive of the original rules. Not loaded at runtime. |

## Where each rule is defined

Every rule has exactly one defining file. The table is in `skills/image-passage/references/workflow.md` §一; when you change who owns a rule, update that table. Summaries elsewhere (SKILL.md, README, qa-checklist) must point to the definition, not restate it differently.

Some rules are mirrored in code or data. Change both sides together:

| Rule (defined in) | Mirrored in |
|---|---|
| Quantified layout constraints, highlight limits (`visual-system.md` §五, §六) | `scripts/render_page.py` checks; `html-recipes.md` §七 check-level table |
| Layout classes L01–L36, components, role font sizes (`visual-system.md` §三, `html-recipes.md` §三, §四) | `assets/css/base.css` |
| Colour names (`visual-system.md` §七) | `assets/colors.json`; `scripts/palette.py` |
| Fonts (`visual-system.md` §七) | `assets/fonts.json`; `scripts/fetch_fonts.py` |
| Length tiers S0–S4, compliance word lists (`copywriting.md` §五, §九) | `scripts/check_copy.py` (`TIERS`, `ABSOLUTE`, `EFFICACY`, `FINANCE`, `INDUCE`) |
| Platform limits (`references/platforms/*.md`) | `assets/platforms.json` (`verified` flag) |
| Composition G/H/S (`page-generation.md` §二) | `templates/spec.md` (构成方式 field); H layer structure in `templates/page-compose.html` and `base.css` (`.compose`, `.base-layer`, `.zone`) |
| Render modes, `.env` variables (`render-routing.md` §二, §四) | `.env.example`; `scripts/env_check.py`; `scripts/call_image_api.py` |
| Project files and state (`page-generation.md` §十, `SKILL.md`) | `scripts/workspace.py`; `templates/state.json` |
| Profile fields A–H (`onboarding.md` §三) | `templates/profile.md` |

## Conventions

- **Stable numbering.** Codes such as D01–D20, R01–R18, I00–I10, T01–T23, F1–F5, H01–H15, V01–V12, L01–L36, C01–C13, E01–E39, S0–S4, W1–W9 and K1–K6 are referenced across files and stored in users' `plan.md` / `state.json`. Never renumber. Append new items at the end; mark retired ones as 停用 instead of deleting them.
- **Section numbers are cross-referenced** (for example 「`workflow.md` 第七节」). If you insert, remove or reorder sections, search the whole skill for references to them (`grep -rn "第.节\|§" skills/`) and update them in the same change.
- **Chinese rule files.** Keep references, templates and user-facing script messages in Simplified Chinese, using full-width punctuation and a space between Chinese and Latin text. English is fine in code, manifests and this file.
- **Colours are written as names** in rules and prompts; HEX belongs only in `colors.json`, `tokens.css` and the 精确版 of a style lock.
- **SKILL.md stays an overview** under 500 lines and the frontmatter `description` stays ≤1024 characters. Put detail in references.
- **No secrets.** Never hardcode keys or endpoints with keys. `.env` is user-supplied and gitignored. Scripts must not print keys; `--dry-run` output masks them.
- **No third-party IP.** Do not add named characters, brand logos or imitations of known IP to examples, prompts or assets. Character support stays generic and opt-in (`characters.md`).
- **Honest status.** Rules and scripts must never report unchecked work as checked. Keep the `unchecked` / `pass-script-only` QA states.
- **Platform limits are unverified** until someone checks them in the apps. When verifying, set `verified: true` in `platforms.json`, update the platform md, and add a CHANGELOG entry with the date.
- **Version** lives in `.claude-plugin/plugin.json`, `.codebuddy-plugin/plugin.json` and the SKILL.md `metadata.version`. Bump them together and add a CHANGELOG entry.

## Verifying changes

Run from the repository root.

```bash
python3 -m py_compile skills/image-passage/scripts/*.py
```

Render the demo and check layout. A change to `base.css`, `render_page.py` or `html-recipes.md` should keep 0 errors:

```bash
pip install -r skills/image-passage/scripts/requirements.txt && python -m playwright install chromium
python3 skills/image-passage/scripts/fetch_fonts.py
cp skills/image-passage/assets/css/base.css examples/demo/render/
python3 skills/image-passage/scripts/render_page.py examples/demo/pages/P0*/page.html --out-dir /tmp/demo-out
```

Look at the PNGs in `/tmp/demo-out` if you can view images. Regenerate the preview sheet only when the look changes on purpose:

```bash
python3 skills/image-passage/scripts/image_tools.py sheet /tmp/demo-out/preview.png /tmp/demo-out/P0*.png --cols 3 --label
```

Check copy rules:

```bash
python3 skills/image-passage/scripts/check_copy.py examples/demo/copy.md
```

Smoke-test the workflow scripts in a scratch directory:

```bash
cd "$(mktemp -d)"
python3 <repo>/skills/image-passage/scripts/workspace.py init
python3 <repo>/skills/image-passage/scripts/workspace.py new demo
python3 <repo>/skills/image-passage/scripts/workspace.py status demo
python3 <repo>/skills/image-passage/scripts/env_check.py --quick
python3 <repo>/skills/image-passage/scripts/call_image_api.py --help
```

`call_image_api.py --dry-run` previews a request without sending it. Do not call a real API in tests unless the user asked and configured one.

## Commit hygiene

- Do not commit `.env`, `image-passage-work/`, font caches, `__pycache__/` or `examples/demo/render/base.css` (all gitignored).
- Keep `examples/demo/` small (currently about 0.5 MB). Store final images as JPEG.
