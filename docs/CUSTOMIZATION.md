# Customization guide

This tool is deliberately easy to modify: no build step, no dependencies — edit and refresh the page.

## 1. Change the stages (add "Group interview", "AI interview", …)

In `dashboard.html`, near the top of the script:

```js
const PIPELINE = ['未投递','已投递','综合素质评测','笔试','一面','二面','三面','HR面','offer'];
const TERMINAL = ['已拒','放弃'];
const BOARD = [
  {key:'todo',      label:'未投递',      status:'未投递',      match:s=>s==='未投递'},
  {key:'applied',   label:'已投递',      status:'已投递',      match:s=>s==='已投递'},
  {key:'quality',   label:'综合素质评测', status:'综合素质评测', match:s=>s==='综合素质评测'},
  {key:'oa',        label:'笔试',        status:'笔试',        match:s=>s==='笔试'},
  {key:'interview', label:'面试中',      status:'一面',        match:s=>['一面','二面','三面','HR面'].includes(s)},
  {key:'offer',     label:'Offer',       status:'offer',       match:s=>s==='offer'},
  {key:'closed',    label:'已结束',      status:'已拒',        match:s=>TERMINAL.includes(s)},
];
const BADGE = { '未投递':'b-todo', /* … */ };
```

Changing these **automatically updates** the lanes, the advance button, the progress bar, drag targets, dropdown options and the funnel.

Example — insert a "Group interview" stage before Interview 1:

```js
const PIPELINE = ['未投递','已投递','综合素质评测','笔试','群面','一面','二面','三面','HR面','offer'];
const BOARD = [
  // …unchanged above
  {key:'group', label:'群面', status:'群面', match:s=>s==='群面'},          // new lane
  {key:'interview', label:'面试中', status:'一面', match:s=>['一面','二面','三面','HR面'].includes(s)},
  // …unchanged below
];
const BADGE = { /* … */ '群面':'b-quality' };    // reuse a colour or add your own .b-xxx
```

> The lane count changed, so also update the CSS: `grid-template-columns: repeat(N, …)` and `min-width` for `.board`.

Add the English label to the i18n table (`const EN`) so the English UI shows it too — or leave it, in which case the Chinese value is displayed as-is.

## 2. Change the metrics

Each funnel metric is one line in `renderFunnel()`:

```js
const oa = state.applications.filter(a=>reached(a,['笔试','一面','二面','三面','HR面','offer'])).length;
```

Copy a line and change the stage array to add e.g. "interview-2 rate"; reorder the cards via the `cards` array below it.

## 3. Change the stale threshold

```js
const STALE_DAYS = 7;   // set to 5 for a 5-day reminder
```

## 4. Add custom fields (salary range, contact, req id…)

**No code change needed.** Extra keys are preserved verbatim (`normalize()` only fills defaults; it never deletes unknown keys).

To make it editable in the dialog, add one row in `openEditor()`:

```js
${field('薪资范围', a['薪资范围'], 'wide')}
```

(`field` is the existing helper — copy the style of the neighbouring fields.)

## 5. Change the tier categories

Tiers are a plain data field (`梯队`). Either edit values in `data/ledger.json`, or extend the filter dropdown in `renderTier()`:

```js
['', '第一梯队-互联网大厂', '第二梯队-AI/科技独角兽', 'your-new-tier']
```

## 6. Use your own company library (auto-fill)

The board can auto-fill position/location/link/tier when you type a company name; the library comes from the current ledger (`LIBRARY`). Import your own list:

```bash
python - <<'PY'
import io, json
d = json.load(io.open('data/sample-ledger.json', encoding='utf-8'))
d['applications'] = [ /* your companies */ ]
json.dump(d, io.open('data/ledger.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
PY
```

## 7. Theme colours / dark mode

Everything is a CSS variable in `:root`:

```css
:root{
  --bg:#f5f6f8; --card:#fff; --line:#e5e7eb; --ink:#1f2329; --muted:#7a828c;
  --brand:#2f6fed; --brand-soft:#eaf1ff; --warn:#d97706; --danger:#d14343; --ok:#1c8a4a;
}
```

Dark mode is a single override (PRs welcome):

```css
@media (prefers-color-scheme: dark){
  :root{ --bg:#14161a; --card:#1c1f24; --line:#2c313a; --ink:#e6e8eb; --muted:#9aa3ae; }
}
```

## 8. Change the port or the data location

```bash
python server.py --port 9000 --data ~/Documents/my-ledger.json
```

Put it in `start.bat` / `start.sh` to make it permanent.

## 9. Deploy an online demo (GitHub Pages)

`.github/workflows/pages.yml` publishes `dashboard.html` as the site root on every push to `main`. The hosted version has no backend: data lives in browser storage (you can still use "Bind local file" to write to disk directly).

## 10. Add a UI language

1. Add entries to `const EN` (exact strings) or `EN_RULES` (strings containing numbers/names)
2. Add dialog/toast templates to `const EN_TPL`
3. For a third language, generalise `T()`/`localize()` to pick a dictionary by `lang`

## 11. What happens to old data after adding a stage?

Nothing to migrate. Existing status values stay valid; the new stage is simply an extra option. If you **rename** a stage, replace the old value across `data/ledger.json` (editor or script) — otherwise those records fall into the "Not applied" lane.
