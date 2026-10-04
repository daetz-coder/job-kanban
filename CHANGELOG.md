# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [1.2.2] - 2026-10-04

### Changed

- **The README now defaults to Chinese**, matching the UI: `README.md` is the Chinese version and `README.en.md` is the English one. The language-switch badges at the top of both point at each other, and `pyproject.toml` therefore publishes the Chinese README to PyPI.
- Documentation cross-references updated: English docs (`CONTRIBUTING.md`, `SECURITY.md`, `docs/*.md`) link to `README.en.md`; Chinese docs (`*.zh-CN.md`) link to `README.md`.
- Both READMEs refreshed: test counts (124) and the complete `tests/` tree (dashboard / smoke / safety / cjk / packaging).

### Added

- `tests/safety_check.py` gained two checks (now 8 in total):
  - `README.md` must be the Chinese one and `README.en.md` must exist and be English — the default-language decision is now enforced by a test;
  - every relative Markdown link must resolve to a real file. This caught stale links immediately after the rename, and it whitelists GitHub-only paths such as `../../issues` and `../../releases`.

## [1.2.1] - 2026-10-04

### Changed

- **The UI now defaults to Chinese** (the tool is built for the Chinese campus-recruitment season); the top-left button switches to English and the choice is remembered. Append `#en` (or `#zh`) to any URL to force a language for that load — useful for sharing and for the English screenshots in this README.
- README screenshots now come in both languages: `docs/screenshot-*.png` (English, taken with `#en`) and `docs/screenshot-*.zh.png` (Chinese, the default).
- The first-run onboarding is Chinese in the source and translated through the i18n table, so it reads correctly in both languages.
- `manifest.webmanifest` uses the Chinese app name (`求职投递看板 · Job Kanban`, short name `投递看板`) and `lang: zh-CN`.

### Fixed

- In English mode the language toggle showed `中文` and a bilingual `title`; it now reads `Chinese` and the tooltip goes through the i18n table, so the English UI contains **zero** CJK characters again.
- `tests/cjk_check.py` now verifies **both directions**: the default UI must be Chinese, and the UI forced with `#en` (4 views) must contain no Chinese at all.
- Frontend regression tests grew to **124** (11 new assertions covering the Chinese default and the English switch).

## [1.2.0] - 2026-10-04

### Added

**Four distribution channels** — all local-first, none of them upload anything:

- **PWA / online version**: `manifest.webmanifest`, a service worker that caches the app shell but **never** `/api`, generated icons, installable as an app (works offline), and a first-run onboarding that asks where your data should live (bind a local JSON file / keep it in the browser / import an existing ledger).
- **Standalone executable**: `packaging/job-kanban.spec` plus a release workflow that builds Windows / macOS / Linux binaries with PyInstaller, smoke-tests each one, and attaches them to the GitHub Release. The ledger is created next to the binary.
- **Python package**: `pyproject.toml` with a `job-kanban` console script, so `uvx job-kanban` / `pipx run job-kanban` work. The implementation moved to `src/job_kanban/`; `server.py` is now a thin repo entry point (same CLI).
- **Single-file HTML**: every release also ships `job-kanban-standalone.html`.

**Tests & tooling**

- `tests/packaging_check.py` (6 checks): both entry points, frozen (PyInstaller) path resolution, package-data staging round trip, and version consistency across `job_kanban.__version__` / `pyproject.toml` / `package.json`.
- `#onboard` deep link to preview the onboarding; `--version` flag.
- Friendly message when the port is already in use (instead of a traceback).

### Changed

- Resource lookup now handles three layouts: git clone, installed wheel, PyInstaller bundle.
- Ledger location: repo → `data/ledger.json`; binary → next to the executable; installed package → `~/.job-kanban/ledger.json`.

### Fixed

- `syncHash()` rewrote the URL hash during startup, so `#onboard` never appeared — the flag is now captured before the hash is rewritten.
- The CJK guard's onboarding view now requires the overlay to be **visible** (`class="onb show"`), not merely present in the DOM; previously it passed without testing anything.
- The CJK guard renders **four** views (board / list / by position / onboarding) instead of one.

## [1.1.1] - 2026-10-04

### Fixed

- **Leftover Chinese in the English UI** (e.g. the file-sync line in the bottom-left):
  - `localize()` only translated text nodes *followed by a tag*, so a container's trailing text node was skipped — `Autosaved to ledger.json …` now renders correctly.
  - Rule order: specific rules (`停滞 ≥7天`) now run before the generic `停滞 (.+)` rule, so dynamic text is no longer half-translated.
  - Static datalists (résumé version / channel) and the link-badge `title` are English now.
  - The language toggle reads **Chinese** / **English**, so the English UI contains no Chinese at all.

### Added

- `tests/cjk_check.py`: renders the dashboard with headless Chrome, strips `<script>`/`<style>`, and fails if any CJK character appears in visible text or in `placeholder`/`title`/`aria-label` (it skips gracefully when no browser is available). Wired into `make check`, `npm run check` and CI.
- Current result on all platforms: `Rendered English UI — CJK occurrences: 0`.

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

### Fixed

- Status `<option>` elements now carry explicit `value` attributes, so translating their labels cannot change the stored value.

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

[1.2.2]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.2.2
[1.2.1]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.2.1
[1.2.0]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.2.0
[1.1.1]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.1.1
[1.1.0]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.1.0
[1.0.1]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.0.1
[1.0.0]: https://github.com/daetz-coder/job-kanban/releases/tag/v1.0.0
