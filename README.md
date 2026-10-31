# cutlist

Turn a narration script into a production package: a second-accurate timing plan, SRT captions,
resolved media cues, and constraint checks that fail the build before you sit down to edit.

Built for solo video work where the script is the source of truth. Write the markdown, get the
shot timings and captions back, and stop re-timing your own paragraphs by hand.

```
$ cutlist check examples/ai-signal-ep42.md --assets media/
| Start | End | Dur | Words | Section |
| 00:00 | 00:07 | 7.6s | 19 | **Hook** |
...
No issues found.
```

## Why this exists

Editing a talking-head or voiceover video is mostly arithmetic you do badly at 1am: does this
paragraph fit the runtime, does the hook land inside the first 15 seconds, will these captions read
faster than a human can parse, is the b-roll I referenced actually on disk. `cutlist` answers all
four from the script, in one command, deterministically and offline.

No API keys, no model calls, no network. Python standard library only.

## Install

```bash
git clone https://github.com/prajwalaswar/cutlist
cd cutlist
python -m pip install -e .
```

Python 3.10 or newer. Runtime dependencies: none.

## Quickstart

```bash
cutlist init my-video
cd my-video
cutlist check script.md
cutlist package script.md -o build/
```

`package` writes four files:

| File | What it is |
|---|---|
| `build/report.md` | timing table, media cue table, every diagnostic |
| `build/captions.srt` | ready to drop into CapCut, Premiere, Resolve, YouTube |
| `build/timing.json` | section and beat timings for other tooling |
| `build/assets.json` | every media cue with the file it resolved to |

## Script format

```markdown
---
title: The AI Signal 42
target_duration: 180
words_per_minute: 150
banned_phrases: game changer, mind blowing
---

# Hook
Three labs shipped model updates this week, and none of them were about size.

# Segment one
A blank line starts a new beat. A beat is the smallest timing unit.

Cut to the demo here [[asset: broll/phone-demo.mp4]].

# Close
One line that sends them to the next video.
```

- `# ` starts a section, one per topic.
- Blank lines split beats inside a section.
- `[[asset: name]]` marks a media cue. It is stripped from the spoken text, so word counts and
  captions stay clean.
- Frontmatter is optional. Any key you set overrides the default.

## Commands

| Command | Does |
|---|---|
| `cutlist plan script.md` | timing table, plus `--json` for piping |
| `cutlist captions script.md` | SRT to stdout, or `-o file.srt`, with `--max-chars` and `--max-lines` |
| `cutlist check script.md` | all checks, `--assets DIR` to resolve media, `--json`, `--strict` |
| `cutlist package script.md -o build/` | writes the full package |
| `cutlist init DIR` | scaffolds a script and asset folder |

Exit codes: `0` clean, `1` errors (or any diagnostic with `--strict`), `2` bad input file.

## Checks

| Code | Severity | Triggers when |
|---|---|---|
| `DURATION_OUT_OF_RANGE` | error | total runtime misses the target by more than the tolerance |
| `ASSET_MISSING` | error | a `[[asset: ...]]` cue has no matching file |
| `EMPTY_SCRIPT`, `EMPTY_SECTION`, `CUE_ZERO_DURATION` | error | something produced no content |
| `WPM_OUT_OF_RANGE` | warning | speaking rate sits outside the readable band |
| `HOOK_TOO_LONG`, `HOOK_TOO_SHORT` | warning | the first section will not land |
| `CAPTION_CPS_HIGH` | warning | a cue reads faster than characters-per-second allows |
| `CAPTION_TOO_MANY_LINES` | warning | a cue exceeds the line limit |
| `BANNED_PHRASE` | warning | script contains a phrase you listed in frontmatter |
| `TOO_FEW_SECTIONS`, `MISSING_TITLE` | warning | structure is thinner than configured |
| `BEAT_TOO_LONG` | info | one paragraph runs long, a split may read better |

## How timings are calculated

Total runtime is `words / wpm * 60`. Beat boundaries come from cumulative word counts, so rounding
never drifts and every beat starts exactly where the previous one ended.

Inside a beat, caption cues share the beat's duration **by characters, not words**. A long word
gets the screen time it needs, and characters-per-second stays flat across cues instead of spiking
on the last one. That single decision is why the CPS check is usable at all.

## Architecture

```
script.md
   │
   ├─ parser.py ──► Script (sections, beats, asset refs)
   │                    │
   │                    ├─ config.py ──► Settings (defaults + frontmatter)
   │                    │
   │                    ├─ timing.py ──► TimingPlan (beats, sections, seconds)
   │                    │        │
   │                    │        ├─ captions.py ──► Cue[] ──► SRT
   │                    │        │
   │                    │        └─ assets.py ─────► AssetStatus[]
   │                    │
   │                    └─ checks.py ──► Diagnostic[]
   │
   └─ report.py ──► report.md, timing.json, assets.json
```

Every stage is a pure function over dataclasses. No global state, no I/O outside `cli.py` and
`report.write_text`, which is why the whole suite runs in under a second.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

```
53 tests, no network, no fixtures on disk except temporary directories.
```

## Roadmap

- [ ] `cutlist watch` to re-check on save
- [ ] reading-rate profiles per platform
- [ ] two-pass captions: preview then tighten
- [ ] `--format vtt` and `--format ass`
- [ ] section budgets so one topic cannot eat the runtime

## License

MIT, see [LICENSE](LICENSE).
