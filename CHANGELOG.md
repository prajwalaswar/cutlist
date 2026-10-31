# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioning follows SemVer.

## [0.3.0] - 2026-10-31

### Added
- `check` command with eleven diagnostics, `--json` and `--strict`.
- `package` command writing report.md, captions.srt, timing.json and assets.json.
- `init` command that scaffolds a starter script.
- Asset resolution against a media folder, matching by full name or stem, case-insensitive.
- Banned-phrase scanning driven by frontmatter.

### Changed
- Caption cues now share beat duration by characters instead of words, which flattens
  characters-per-second and stops the last cue of a beat being unreadable.

## [0.2.0] - 2026-10-31

### Added
- SRT caption generation with greedy line wrapping and a configurable line limit.
- Timing plan built from cumulative word counts.

## [0.1.0] - 2026-10-31

### Added
- Markdown script parser: frontmatter, sections, beats, inline asset cues.
- `plan` command.
