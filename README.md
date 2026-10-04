<div align="center">

# Job Kanban

**A local-first job-application kanban: drag cards to advance stages, and your data stays in a plain JSON file you own.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)](server.py)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-112%20passed-success)](tests/dashboard.test.js)
[![Local First](https://img.shields.io/badge/local--first-no%20cloud-blueviolet)](#why-this-exists)
[![English](https://img.shields.io/badge/README-English-blue)](README.md)
[![中文](https://img.shields.io/badge/README-中文-red)](README.zh-CN.md)

<img src="docs/screenshot-board.png" alt="Board view" width="100%">

</div>

---

> **Language**: the UI ships in **English** with a one-click 中文 toggle (top-left). Data keys and stage values stay in Chinese so existing ledgers keep working — see [Data format](#data-format).

## Install

Five ways in — pick whichever fits. **None of them upload your data anywhere.**

| Way | How | Needs | Autosave to disk |
|---|---|---|---|
| **Online (PWA)** | <https://daetz-coder.github.io/job-kanban/> | a browser | Chrome/Edge: bind a local file |
| **Download & run** | [Releases](../../releases) → `job-kanban-windows.exe` · `-macos` · `-linux` | nothing | ✅ (next to the binary) |
| **One command** | `uvx job-kanban` or `pipx run job-kanban` | Python 3.8+ | ✅ |
| **From source** | `git clone … && python server.py` | Python 3.8+ | ✅ |
| **Single file** | [Releases](../../releases) → `job-kanban-standalone.html` | a browser | export / import JSON |

### Online — installable, works offline

Open <https://daetz-coder.github.io/job-kanban/>, then use your browser's **Install app** (or *Add to Home Screen* on mobile): it gets an icon, runs full-screen and works offline. Everything happens in your browser — nothing is uploaded.

In **Chrome / Edge** you can click **Bind a local JSON file** and every change is written straight to the file you pick (the same autosave you get from the local server). Other browsers fall back to export / import.

### Download & run — no Python needed

Grab the binary for your OS from [Releases](../../releases) and run it; the browser opens automatically and the ledger is created next to the binary in `data/ledger.json`.

```bash
job-kanban-windows.exe            # Windows
./job-kanban-macos                # macOS (right-click → Open the first time: unsigned)
./job-kanban-linux                # Linux
```

### One command — for developers

```bash
uvx job-kanban        # or: pipx run job-kanban
job-kanban --port 9000 --data ~/my-ledger.json
```

### From source

```bash
git clone https://github.com/daetz-coder/job-kanban.git
cd job-kanban
python server.py
```

### Single file — the simplest possible artifact

Download `job-kanban-standalone.html` and double-click it. Frontend-only: data lives in browser storage, use **Export** / **Import** for backups.

## Table of contents

- [Install](#install)
- [Why this exists](#why-this-exists)
- [Features](#features)
- [Quick start](#quick-start)
- [Screenshots](#screenshots)
- [Data & safety](#data--safety)
- [Project layout](#project-layout)
- [Configuration](#configuration)
- [API](#api)
- [Data format](#data-format)
- [Bundled tools](#bundled-tools)
- [Development](#development)
- [FAQ](#faq)
- [Design notes](#design-notes)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Why this exists

Tracking dozens of applications in a spreadsheet doesn't work: which résumé version did I send, when, which interview round am I stuck at, and who should I follow up with?

Most existing tools are SaaS (your data on someone else's server), need an account, or are a flat list with no pipeline view.

Four principles:

| Principle | How it works |
|---|---|
| **Your data is yours** | A single `data/ledger.json` — git-friendly, human-readable, portable |
| **Zero dependencies** | One HTML file for the frontend; Python standard library only on the backend |
| **No data loss** | Per-record writes + write lock + atomic replace + pre-write backups + undo |
| **Works offline** | No network, no sign-up, no upload |

## Features

### Kanban board
- **7 lanes**: Not applied → Applied → Aptitude test → Written test → Interviewing → Offer → Closed
- **Drop anywhere in a lane** — no need to aim at an existing card
- **Auto-scroll while dragging** near the viewport edges
- Cards show priority, applied date, **days stale**, and overdue next steps

### List view
- Table with search (company / position / city / channel / notes)
- Tier filter and 5 sort modes (including "stalest")
- One-click **Apply ↗** links opening in a new tab, with link-health badges

### Multiple positions per company
- Each company can hold several open positions, each tracked independently (status, dates, history)
- **Bulk paste** from a career page — positions, type, city, business unit and update date are parsed automatically
- In "By position" view, one company's positions are merged into a **single grouped card** with per-position status controls
- Company-level status = the most advanced stage among its positions; applied date = the earliest

### Analytics & quality
- **Funnel**: applied / aptitude / written / interview rates, offer conversion, stale count
- **Stale reminders** (default 7 days, `STALE_DAYS`)
- **Status history** recorded automatically — and drag noise is suppressed (same-day reversals cancel out)
- **Undo** the last 40 operations
- Import / export JSON and reset (all auto-backed-up first)

## Quick start

Requires **Python 3.8+**. Nothing to `pip install`.

```bash
git clone https://github.com/daetz-coder/job-kanban.git
cd job-kanban
python server.py
```

The browser opens at <http://127.0.0.1:8765/>. On first run the ledger is initialised from `data/sample-ledger.json` (12 fictional companies) — edit freely.

On Windows just double-click **`start.bat`**; on macOS/Linux run `./start.sh`.

```bash
python server.py --data my-ledger.json   # custom ledger path
python server.py --port 9000             # custom port
python server.py --no-browser            # don't open the browser
python server.py --help
```

> **Online demo**: <https://daetz-coder.github.io/job-kanban/> — frontend-only mode, data stays in your browser. Published automatically by `.github/workflows/pages.yml` (GitHub Pages requires a public repo, so it activates once this repo goes public).
>
> **No server?** You can also just open `dashboard.html` directly (frontend-only: data lives in browser storage, export to JSON when needed). Server mode is recommended — it writes straight to disk.

### Handy commands

```bash
make            # list all commands
make run        # start the server
make check      # full check: lint + frontend tests + smoke + safety
make shots      # regenerate the README screenshots
```

## Screenshots

**Board view** — drag to advance a stage

<img src="docs/screenshot-board.png" alt="Board view" width="100%">

**By-position view** — several positions of one company merged into one card

<img src="docs/screenshot-positions.png" alt="By position view" width="100%">

**List view** — search / filter / sort / link health

<img src="docs/screenshot-list.png" alt="List view" width="100%">

## Data & safety

The ledger lives in `data/ledger.json` (indented JSON, so `git diff` shows exactly which record changed).

| Mechanism | Detail |
|---|---|
| **Per-record writes** | Dragging a card rewrites only that record (`PUT /api/app/<id>`) — never the whole table |
| **Write lock** | Concurrent tabs/processes are serialised |
| **Atomic replace** | Write to `.tmp`, then `os.replace` — no half-written files |
| **Pre-write backup** | The previous file is copied to `data/.backup/` (last 50 kept) |
| **Undo** | Last 40 operations in the UI |
| **Conflict resolution** | On load, compares record count → progressed count → position count; the more complete side wins, so a stale browser cache can never overwrite a fuller file |

`data/ledger.json` and `data/.backup/` are **gitignored** — your application data is never committed.

Keep the ledger in your own **private** git repo for history:

```bash
cp /path/to/job-kanban/data/ledger.json /path/to/private-repo/
cd /path/to/private-repo && git add ledger.json && git commit -m "applications 2026-10-04"
```

## Project layout

```
job-kanban/
├── dashboard.html            # the kanban (single file: UI + logic + fallback data)
├── manifest.webmanifest      # PWA manifest (installable, offline)
├── sw.js                     # service worker (caches the shell, never /api)
├── server.py                 # repo entry point (thin shim)
├── src/job_kanban/           # server implementation (the installable package)
├── packaging/                # PyInstaller spec + package-data staging
├── start.bat / start.sh      # one-click launch (Windows / macOS·Linux)
├── Makefile                  # run / test / check / shots / release
├── data/
│   ├── sample-ledger.json    # sample data (12 fictional companies, committable)
│   └── ledger.json           # your ledger (gitignored)
├── tools/
│   ├── build-embed.py        # embed JSON into dashboard.html
│   ├── check-links.py        # batch-check job link health
│   ├── sync-timeline.py      # generate a Markdown timeline
│   └── screenshot.py         # regenerate the README screenshots (headless Chrome)
├── docs/                     # screenshots, architecture, customization guide
└── tests/
    ├── dashboard.test.js     # 112 regression tests (Node + DOM stubs, no browser)
    ├── smoke_test.py         # 14 server smoke checks (cross-platform)
    └── safety_check.py       # 5 open-source safety & privacy checks
```

## Configuration

| Setting | Where | Default |
|---|---|---|
| Ledger path | `--data` | `data/ledger.json` |
| Port | `--port` | `8765` |
| Open browser | `--no-browser` | opens automatically |
| UI language | `langBtn` in the sidebar (persisted as `jobkanban_lang`) | `en` |
| Stale threshold | `const STALE_DAYS` in `dashboard.html` | `7` |
| Pipeline stages | `const PIPELINE` in `dashboard.html` | see below |
| Backups kept | `KEEP_BACKUPS` in `server.py` | `50` |

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Dashboard page |
| `GET` | `/api/state` | Full ledger (`X-File-Mtime` header = file mtime in ms) |
| `PUT` | `/api/app/<id>` | Create or update a **single** record |
| `DELETE` | `/api/app/<id>` | Delete a **single** record |
| `POST` | `/api/state` | Full replace (import / reset only) |

```bash
# Advance one company to the written-test stage
curl -X PUT http://127.0.0.1:8765/api/app/sample-001 \
  -H 'Content-Type: application/json' \
  -d '{"id":"sample-001","企业":"Sample Tech","投递状态":"笔试"}'
```

## Data format

> Keys and stage values are in Chinese (the tool was built for the Chinese campus-recruitment season). The UI translates them for display; the stored schema stays stable so existing ledgers keep working. A machine-translation map lives in `dashboard.html` (`const EN`).

```jsonc
{
  "meta": {
    "状态可选值": ["未投递", "已投递", "综合素质评测", "笔试", "一面", "二面", "三面", "HR面", "offer", "已拒", "放弃"]
  },
  "applications": [
    {
      "id": "sample-001",              // stable id, generated on create
      "企业": "Sample Tech",            // company
      "梯队": "第一梯队-互联网大厂",      // tier
      "岗位": "AI Application Engineer",// position summary
      "工作地点": "Hangzhou / Beijing",  // location
      "投递链接": "https://example.com/campus",
      "投递状态": "已投递",              // stage (see 状态可选值)
      "投递日期": "2026-09-20",          // applied on
      "简历版本": "v2 Agent-focused",    // résumé version
      "渠道": "官网",                    // channel
      "内推": "",                        // referral / contact
      "优先级": 5,                       // 1-5
      "下一步": "Wait for the test invite",
      "下一步截止": "",
      "备注": "",
      "岗位列表": [],                    // open positions (per-position tracking)
      "面试记录": [],                    // [{日期, 轮次, 结果, 备注}]
      "状态历史": []                     // [{日期, 从, 到, 备注}], appended automatically
    }
  ]
}
```

Extra keys are preserved verbatim — add your own fields (salary range, contact, req id…) without touching the code.

## Bundled tools

```bash
python tools/check-links.py      # check every job link, write results back into the ledger
python tools/sync-timeline.py    # generate timeline.md (overview + timeline + to-apply list)
python tools/build-embed.py      # embed JSON into dashboard.html (fallback data)
python tools/screenshot.py       # regenerate README screenshots from the sample data
```

`check-links.py` classifies results into three buckets to avoid false alarms: `ok` / `problem·404|dns` / `unverified·proxy|ssl|timeout`. Run it on a machine with normal internet access for the most accurate results.

`screenshot.py` starts a throwaway server on the **sample data** — it never touches your real ledger.

## Development

```bash
make check              # lint + test + smoke + safety + CJK + packaging
npm test                # frontend regression tests only (112)
npm run test:smoke      # server smoke test only (14)
npm run test:safety     # open-source safety & privacy checks only (5)
npm run test:cjk        # rendered English UI must contain no Chinese (needs Chrome)
npm run test:packaging  # entry points, frozen paths, version consistency (6)

make release            # how a release is produced (see .github/workflows/release.yml)
```

- Edit `dashboard.html` → just refresh the page (the server reads it per request)
- Edit `server.py` → restart the server
- Tests run the page script against minimal DOM stubs — **no browser needed**, and assertions are data-size independent

Want to change stages, metrics, custom fields or the theme? See the **[customization guide](docs/CUSTOMIZATION.md)**. Architecture and trade-offs: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## FAQ

<details>
<summary><b>Which install should I pick?</b></summary>

For a quick look: the **online version** (a link, nothing to install — Chrome/Edge can bind a local file for autosave). For everyday use on your own machine: **the binary from Releases** or `python server.py` from a clone. For scripting/automation: `uvx job-kanban`. See [Install](#install).
</details>

<details>
<summary><b>Where is my data, and can it be lost?</b></summary>

The source of truth is `data/ledger.json` on disk (not browser storage). Every write is backed up to `data/.backup/` (last 50), and the UI can undo the last 40 operations. Browser localStorage is only an edit-time cache.
</details>

<details>
<summary><b>Why not SQLite?</b></summary>

For a single user with a few hundred records, SQLite's indexing/joins/aggregations add little, while JSON gives you git-diffable, human-readable, portable data. The real risks — full-table overwrite and concurrent writes — are solved with per-record writes + a write lock + atomic replace. See [design notes](#design-notes).
</details>

<details>
<summary><b>Can I sync across machines?</b></summary>

Put `data/ledger.json` in your own private git repo and pull/push. The tool itself never talks to the network.
</details>

<details>
<summary><b>Can I change the stages? (e.g. add "Group interview")</b></summary>

Yes — edit `const PIPELINE` and `const BOARD` in `dashboard.html`. Lanes, the advance button, the progress bar, drag targets and the funnel all follow automatically. Details in the [customization guide](docs/CUSTOMIZATION.md).
</details>

<details>
<summary><b>Dragging does nothing / the card won't move?</b></summary>

Company cards are draggable in "By company" view. In "By position" view, grouped cards are **intentionally not draggable** (with several positions, dragging the whole card is ambiguous) — use the per-position dropdown instead.
</details>

<details>
<summary><b>Port already in use?</b></summary>

`python server.py --port 9000`. If it complains, an instance is probably already running — just open the URL.
</details>

<details>
<summary><b>Can I switch the UI back to Chinese?</b></summary>

Yes — click the **中文** button in the top-left. The choice is remembered (`jobkanban_lang` in localStorage).
</details>

## Design notes

**The English UI is guarded by a test**: `tests/cjk_check.py` renders the dashboard with headless Chrome and fails if any CJK character appears in visible text or in `placeholder`/`title`/`aria-label`. Data keys and stage values are exempt by design — they are never rendered raw in the English UI.

**Single-file frontend**: double-click to run, no build step, easy to fork. The trade-off is that the HTML embeds a fallback dataset — run `tools/build-embed.py` after changing it.

**On-disk file is authoritative, not localStorage**: localStorage gets wiped by cache clearing, differs per browser, and can't go into git. It is demoted to an edit-time cache.

**More complete side wins on conflict**: a stale, incomplete browser state once overwrote a fuller on-disk ledger. Now the comparison is record count → progressed count → position count, and the fuller file always wins.

**No automatic merging of same-name companies**: an earlier version auto-merged duplicates on load and silently dropped real position records (a genuine data-loss incident). Record counts are never changed automatically now — merging is always an explicit, confirmed action.

## Roadmap

- [ ] Stats page (application pace, funnel trends)
- [ ] Interview question bank linked to debriefs
- [ ] Export to Excel / Feishu Bitable
- [ ] Dark mode
- [ ] Optional SQLite backend (for multi-device sync)

Feature requests welcome in [Issues](../../issues).

## Contributing

PRs and issues are welcome. Before submitting:

1. `make check` passes
2. No runtime third-party dependencies (zero-dep frontend, stdlib-only backend)
3. Data-related changes must be backwards compatible and must not lose data

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

[MIT](LICENSE) © job-kanban contributors

<div align="center">

If this helped you keep your job hunt under control, a ⭐ helps others find it.

</div>
