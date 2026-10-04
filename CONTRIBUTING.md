# Contributing

Thanks for wanting to improve this tool 🙌

## Before you start

Please read the [design notes](README.en.md#design-notes) first. Three ground rules:

1. **No runtime dependencies** — the frontend is plain vanilla JS in a single file; the backend uses the Python standard library only. Don't add npm/pip runtime deps.
2. **Never lose data** — any change touching writes, import, merging or reset must answer: could it overwrite someone's data? Can it be undone on failure?
3. **Never change record counts automatically** — no silent merging or deleting on load (this caused a real data-loss incident in the past).

## Development setup

```bash
git clone https://github.com/daetz-coder/job-kanban.git
cd job-kanban
python server.py          # starts the local server (initialises from sample data)
```

No dependencies to install. Node is only needed for the tests (Node 14+).

## Running the tests

```bash
make check              # full: lint + frontend tests + smoke + safety + CJK guard
npm test                # frontend regression tests only (112)
npm run test:smoke      # server smoke test only (14)
npm run test:safety     # open-source safety & privacy checks only (5)
npm run test:cjk        # rendered English UI must contain no Chinese (needs Chrome)
```

The tests execute the page script against minimal DOM stubs — **no browser needed**, and they finish in a few hundred milliseconds.

- Assertions must be **data-size independent** (the 12-record sample data must pass) — don't hard-code "50 companies"
- Add tests for new features; for bug fixes, write a failing assertion first
- For UI changes, regenerate the screenshots with `python tools/screenshot.py` (it uses sample data and never touches a real ledger)
- Any new UI string must be added to the i18n table (`const EN`) — `tests/cjk_check.py` will fail otherwise

## Commit conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add a "city" lane grouping
fix: cancel out same-day status reversals in history
docs: document the per-record API
refactor: split the sync layer
test: cover the undo stack
chore: bump CI matrix
```

Commit messages and code comments may be in English or Chinese; user-facing UI text must go through the i18n layer (`const EN` in `dashboard.html`).

## Pull requests

1. Fork → branch (`feat/xxx` or `fix/xxx`)
2. `make check` must pass
3. UI changes: regenerate screenshots and include them
4. Describe **what / why / how you verified it**
5. Schema changes: state the **backwards compatibility** (can old ledgers still load?)

CI runs on Ubuntu (newest + oldest supported versions) and Windows, and also checks:

- the dashboard must not contain real company names (open-source safety)
- `data/ledger.json` must not be tracked (privacy)

## Reporting issues

Use the [issue templates](https://github.com/daetz-coder/job-kanban/issues/new/choose) and include:

- OS / browser / Python version
- Steps to reproduce
- Expected vs. actual behaviour
- Logs or screenshots (**redact personal data first**)

## Code style

- JavaScript: 2-space indent, single quotes, semicolons at statement ends (follow the existing file)
- Python: PEP 8, UTF-8, `# -*- coding: utf-8 -*-` header
- Chinese keys in the data schema are intentional — see [Data format](README.en.md#data-format)

## Security

Please don't open a public issue for security problems — see [SECURITY.md](SECURITY.md).
