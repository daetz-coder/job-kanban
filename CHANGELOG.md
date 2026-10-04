# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-04

### Changed

- **Renamed to Job Kanban** (repo, directory, package, docs). Data file is now `data/ledger.json`.
- **English UI by default**, with a one-click 中文 toggle in the sidebar (persisted as `jobkanban_lang`). Data keys and stage values stay Chinese so existing ledgers keep working.
- **English is now the primary documentation language**; Chinese docs are kept as `*.zh-CN.md`.
- Sample data now uses English company / position / note text.

### Added

- i18n layer: `T()` / `TT()` for strings, `localize()` for rendered HTML (translates text nodes and `placeholder`/`title` only — never `value`, so data can't be corrupted), plus regex rules for dynamic text.
- Language toggle button and URL hash deep links (`#list`, `#pos`, `#issue`).
- 12 new i18n regression tests (112 total).
- `tests/cjk_check.py`: renders the dashboard with headless Chrome and fails if the English UI contains any Chinese — wired into `make check` and CI.

### Fixed

- Status `<option>` elements now carry explicit `value` attributes, so translating their labels cannot change the stored value.
- `renderFileStatus()` is wrapped so its output is translated on every call path.
- `localize()` now also translates the trailing text node of a container (previously only text followed by a tag).
- Rule order: specific rules (`停滞 ≥7天`) now run before generic ones, so dynamic text is not partially translated.
- Static datalists (résumé version, channel) and the link-badge `title` are now English; the language toggle reads "Chinese"/"English" so the English UI has zero Chinese characters.

## [1.0.1] - 2026-10-04

Fixes for three real issues surfaced by CI on Windows.

### Fixed

- **Backup keys could overwrite each other**: `snapshot()` used `Date.now()` as the key, so two snapshots in the same millisecond (e.g. the daily autosave triggered by a save) overwrote each other, and "restore snapshot" could return an empty state. Keys now include a sequence number and are ordered by time + sequence.
- **Printing Chinese crashed on non-UTF-8 consoles**: on Windows with a GBK/cp1252 code page, `server.py` and the tools raised `UnicodeEncodeError` on startup (the server would not start). stdout/stderr are now reconfigured to UTF-8 with `errors='replace'`.
- **The CI smoke test relied on bash/curl**, which was flaky on Windows runners. Replaced with the cross-platform `tests/smoke_test.py`.

### Added

- `tests/smoke_test.py` — 14 cross-platform server checks (page, full read, per-record create / update-isolated / delete, 404, pre-write backup, invalid payload rejection)
- `tests/safety_check.py` — 5 open-source safety & privacy checks (no real company names in the dashboard, ledger not tracked, no personal identifiers, sample data fictional, no backup/temp files committed)
- `make check` and `npm run check` for a full local check
- CI matrix trimmed to 3 combinations (newest / oldest supported / Windows)

## [1.0.0] - 2026-10-04

First public release.

### Added

**Board**
- 7 lanes: Not applied / Applied / Aptitude test / Written test / Interviewing / Offer / Closed
- Drop anywhere in a lane; auto-scroll while dragging near viewport edges
- Cards show priority, applied date, days stale, overdue next steps
- Grouped cards: several open positions of one company merged into a single card with per-position controls

**List**
- Table view with search (company / position / city / channel / notes)
- Tier filter, 5 sort modes (including "stalest")
- One-click apply links with link-health badges

**Data**
- Multiple positions per company, each with independent status/date/history; company status aggregates the most advanced position
- Bulk paste parsing from a career page
- Funnel metrics: applied / aptitude / written / interview rates, offer conversion, stale count
- Status history recorded automatically, with same-day drag noise cancelled out
- Undo for the last 40 operations

**Local server**
- `GET /api/state`, `PUT /api/app/<id>`, `DELETE /api/app/<id>`, `POST /api/state`
- Per-record writes, global write lock, atomic replace (`os.replace`)
- Pre-write backups to `data/.backup/` (last 50 kept)
- Conflict resolution on load: record count → progressed count → position count
- Python standard library only

**Tools**
- `tools/check-links.py` — job link health (three-way classification to avoid proxy false alarms)
- `tools/sync-timeline.py` — Markdown timeline view
- `tools/build-embed.py` — embed JSON into `dashboard.html`
- `tools/screenshot.py` — regenerate README screenshots with headless Chrome

**Other**
- 100 regression tests (Node + DOM stubs, no browser)
- GitHub Actions CI (Ubuntu / Windows × Node / Python)

### Design decisions (learned the hard way)

- **No automatic merging of same-name companies**: it once discarded real position records. Record counts are never changed automatically now.
- **The on-disk file is authoritative, not localStorage**: localStorage gets wiped, differs per browser and can't go into git.
- **JSON over SQLite**: for a single user with a few hundred records, git-diffability and portability matter more; the real risks are solved with per-record writes + a write lock + atomic replace.

[1.1.0]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.1.0
[1.0.1]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.0.1
[1.0.0]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.0.0
