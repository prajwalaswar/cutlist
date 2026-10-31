# Architecture

Five stages, each a pure function. The CLI wires them together and nothing else does I/O.

## Stage 1, parse

`parser.py` turns markdown into a `Script` of `Section` and `Beat` objects. It owns every format
rule: frontmatter between `---` fences, `# ` headings, blank-line beat separators, and
`[[asset: ...]]` tokens. Asset tokens are removed from the spoken text at this stage so nothing
downstream has to know they exist. Errors raise `ScriptError` with the source line number.

## Stage 2, configure

`config.py` builds a frozen `Settings` from defaults, then applies frontmatter overrides, then CLI
overrides. Every number that a check or a caption limit uses lives here, so the report and the checks
can never disagree about what the limits were.

## Stage 3, time

`timing.py` converts words into seconds using cumulative word counts:

```
start_i = (sum of words before i) * 60 / wpm
```

Cumulative counts mean rounding cannot drift and beat `i` always ends where beat `i + 1` starts.

## Stage 4, captions and assets

`captions.py` splits each beat into sentences, wraps them to a character limit, groups the lines into
cues, then shares the beat duration across cues **by characters**. Characters-per-second is a reading
speed measure, so character weighting is the honest distribution; word weighting squeezes long words
into unreadable flashes.

`assets.py` walks a media folder once, indexes files by full name and by stem (lowercased), and
resolves every request. Missing files are not exceptions, they are data, so the check stage decides
whether they are fatal.

## Stage 5, check and report

`checks.py` takes the script, the plan, the cues, the settings and the asset statuses, and returns a
sorted list of diagnostics. Severity is the contract: `error` fails the exit code, `warning` and `info`
do not, `--strict` promotes warnings.

`report.py` renders markdown and stable JSON. It writes only when the CLI asks it to.

## Why no plugins

The tool is deterministic on purpose. A user can pin it in CI and trust that the same script produces
the same timings. Extensibility lives in frontmatter and CLI flags, not in import hooks.
