# Contributing

Issues and pull requests are welcome. This is a small, opinionated tool, so read the two rules below
before opening one.

## Design rules

1. Standard library only at runtime. A new dependency needs a very good reason and a discussion first.
2. Pure functions per stage. Parsing, timing, captions, assets and checks never touch the filesystem
   except where the CLI passes a path in.

## Workflow

```bash
git checkout -b feature/short-description
python -m pip install -e ".[dev]"
python -m pytest
```

- One behaviour per pull request.
- Every new check needs a test that fails without it.
- Keep formatting and refactors in their own commit.
- Commit messages: `type(scope): summary` where type is feat, fix, test, docs, chore, refactor.

## Reporting a bug

Include the script snippet that triggered it (redact anything private), the command you ran, the
output you expected and the output you got. A failing test is the best bug report.
