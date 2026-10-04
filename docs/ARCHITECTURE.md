# Architecture

## Overview

```
┌──────────────────────────┐         ┌───────────────────────────────┐
│  dashboard.html          │  HTTP   │  server.py                    │
│  (single file, zero deps)│ ──────► │  (Python stdlib, loopback)     │
│                          │         │                               │
│  · state machine, board  │  PUT    │  · per-record PUT /api/app/<id>│
│  · drag / filter / stats │ DELETE  │  · full replace POST /api/state│
│  · diff sync (only delta)│  POST   │  · write lock + atomic replace │
│  · i18n layer (en/zh)    │         │  · pre-write backups           │
└──────────┬───────────────┘         └───────────────┬───────────────┘
           │                                          │
           │ fallback (offline open)                   │ read/write
           ▼                                          ▼
  embedded DEFAULT_DATA                      data/ledger.json  (source of truth)
  + localStorage (edit-time cache)           data/.backup/*.json (snapshots)
```

## Data flow

### Startup

1. `load()` reads localStorage; if empty, it falls back to the embedded `DEFAULT_DATA` (sample data)
2. `detectServer()` calls `GET /api/state` (which carries `X-File-Mtime`)
3. **Conflict resolution** compares record count → progressed count → position count:
   - file is more complete (or equally complete and not older) → use the file, remember it as the synced snapshot
   - browser is more complete → keep it and push the whole state back later
4. `syncReady = true` — **no writes are allowed before this**, so a default state can never overwrite the file

### Editing

1. Any interaction mutates `state` in memory
2. `save()` → `persist()` (localStorage + a once-a-day snapshot) + `render()` + push onto the undo stack
3. `scheduleFileWrite()` debounces 600 ms → `flushSync()`

### Diff sync (the core)

`flushSync()` compares the current `state` against the last synced snapshot:

```
changed records ≤ max(12, total × 40%)  →  per-record PUT / DELETE
more than that (import / reset / first) →  full POST /api/state
```

So **dragging one card rewrites exactly one record** — it is physically impossible for it to clobber another.

## Why it is built this way

### Per-record writes instead of whole-table commits

The first implementation POSTed the entire state on every change. A stale or incomplete browser state could then overwrite a newer file — which really happened, and lost data. With per-record writes, one record's change only affects that record.

### Write lock + atomic replace

- `threading.Lock` serialises all writes; concurrent tabs/processes can't interleave
- write `ledger.json.tmp`, then `os.replace()` — a crash or power loss never leaves a half-written JSON
- before each write, the previous file is copied into `.backup/`, giving 50 rolling snapshots

### Why the on-disk file is authoritative

localStorage has three fatal problems: clearing the cache wipes it, different browsers don't share it, and it can't go into git. So it is demoted to an edit-time cache; the on-disk JSON is the truth.

### Why JSON rather than SQLite

| Dimension | JSON | SQLite |
|---|---|---|
| Readable git diffs | ✅ line by line | ❌ binary |
| Inspect / hand-edit | ✅ any editor | ❌ needs a tool |
| Transactions / concurrency | via write lock + atomic replace | ✅ native |
| Unique constraints / indexes | ❌ | ✅ |
| 1000+ records | okay | ✅ better |

For "one person, a few hundred records, must be reviewable in git", JSON wins overall; the concurrency and overwrite risks are handled by **per-record writes + a write lock + atomic replace**. If multi-device sync is ever needed, a SQLite backend can be added as an optional implementation (see the roadmap).

### No automatic merging of same-name companies

An earlier version auto-merged same-name companies on load. It treated the user's **real position records** as duplicates and discarded them (the merge kept the first record's default position), losing data. The rule now:

> **Record counts are never changed automatically.** Any merge / dedupe / delete must be explicitly triggered by the user and confirmed.

## State machine

```
PIPELINE = 未投递 → 已投递 → 综合素质评测 → 笔试 → 一面 → 二面 → 三面 → HR面 → offer
           (Not applied → Applied → Aptitude test → Written test → Interview 1..3 → HR → offer)
TERMINAL = 已拒 / 放弃   (Rejected / Withdrawn — reachable from any stage)
```

- Company-level status = the **most advanced** stage among its positions (`aggStatus`), derived purely from positions so it can move both up and down
- If every position is terminal, the company takes the first terminal value
- Company applied date = the earliest non-empty date among positions (`aggAppliedDate`)
- Companies without positions use their own status

## Status-history denoising

Dragging easily produces `已投递→未投递` style churn. `compactHistory` applies three layers:

1. **Same-day exact reversal**: `A→B` immediately followed by `B→A` on the same day — both are dropped, and the auto-filled applied date from that day is cleared
2. **Whole-day net zero**: if a day's transitions net out to no change, the whole day is dropped
3. **Adjacent reversals + exact duplicates**

Transitions across days are never merged (they are real history).

## i18n layer

The UI is English by default with a 中文 toggle. Design:

- **Data keys and stage values stay Chinese** (`企业`, `投递状态`, `未投递`, …) — the schema never changes, so existing ledgers keep working
- `T(s)` translates an exact string, then tries `EN_RULES` (regex rules for text containing numbers/names)
- `TT(tpl, vars)` handles templates with `{x}` placeholders (dialogs, toasts)
- `localize(html)` translates **text nodes and `placeholder`/`title` only**. It deliberately never touches `value="…"` attributes or `<textarea>` content, so display translation can never corrupt data
- Every `<option>` for a data value carries an explicit `value="…"`, so translating its label can't change what gets saved
- `applyLang()` runs at the end of `render()`, re-localising the known containers; static chrome is handled once at startup by a text-node walk (which preserves event listeners)
- Switching language persists the choice and reloads

## Frontend structure (dashboard.html)

| Section | Responsibility |
|---|---|
| `PIPELINE / TERMINAL / BOARD / BADGE` | state machine and lane definitions |
| `blank / blankPosition / normalize` | data shape and backwards-compatible defaults |
| `aggStatus / aggAppliedDate / effStatus / syncCompanyFromPositions` | company ↔ position aggregation |
| `setStatus / compactHistory` | stage transitions and history denoising |
| `parsePositions` | career-page text → position array |
| `renderBoard / kcardCo / kcardPos / kcardGroup / renderList` | board and list rendering |
| `EN / EN_TPL / EN_RULES / T / TT / localize / applyLang` | i18n layer |
| `detectServer / diffSince / flushSync / putRecord / deleteRecord` | sync layer |
| `snapshot / listBackups / restoreBackup / undo` | backups and undo |
| `window.__app` | test hooks (internal functions exposed for Node assertions) |

## Testing strategy

`tests/dashboard.test.js` executes the page script against minimal DOM stubs (`document`, `localStorage`, `window`) and asserts internal behaviour through `window.__app` — **no browser required**.

Principles:

- assertions are **data-size independent** (never hard-code "50 companies"), so the 12-record sample data passes
- coverage: rendering, stage transitions, history denoising, aggregation, parsing, filtering, CRUD, undo, backups, sync fallback, i18n
- extra guards: the dashboard must not contain real company names; `data/ledger.json` must not be tracked

`tests/smoke_test.py` starts a real server on a free port with a temporary ledger and exercises the API end to end. `tests/safety_check.py` enforces the privacy rules. Both are cross-platform and dependency-free.

## Directory responsibilities

```
dashboard.html   all frontend logic (fallback data injected by tools/build-embed.py)
server.py        local server (HTTP + per-record writes + backups)
tools/           standalone scripts: embed / link check / timeline / screenshots
tests/           regression, smoke and safety checks
docs/            screenshots and these documents
data/            ledger and backups (personal data never committed)
```
