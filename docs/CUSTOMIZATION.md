# 自定义指南

这个工具刻意做得「好改」：没有构建步骤，没有依赖，改完刷新页面即可。

## 1. 改状态阶段（加「群面」「AI 面试」「背调」等）

编辑 `dashboard.html`，找到顶部这几行：

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

改完这些，**看板列、推进按钮、进度条、拖拽目标、下拉选项、漏斗统计会全线自动生效**，不需要改别处。

新增阶段示例（插入「群面」到一面之前）：

```js
const PIPELINE = ['未投递','已投递','综合素质评测','笔试','群面','一面','二面','三面','HR面','offer'];
const BOARD = [
  // …前面不变
  {key:'group', label:'群面', status:'群面', match:s=>s==='群面'},   // 新增一列
  {key:'interview', label:'面试中', status:'一面', match:s=>['一面','二面','三面','HR面'].includes(s)},
  // …后面不变
];
const BADGE = { /* … */ '群面':'b-quality' };   // 复用已有配色，或自定义 .b-xxx
```

> 注意：`BOARD` 的列数变了，记得同步调整 CSS 里的 `grid-template-columns: repeat(N, …)` 和 `min-width`。

## 2. 改统计口径

`renderFunnel()` 里每个指标就是一行：

```js
const oa = state.applications.filter(a=>reached(a,['笔试','一面','二面','三面','HR面','offer'])).length;
```

想加「进二面率」就照抄一行，改状态数组即可；想改漏斗卡片顺序，调整下面的 `cards` 数组。

## 3. 改停滞提醒天数

```js
const STALE_DAYS = 7;   // 改成 5 就是 5 天无进展高亮
```

## 4. 加自定义字段（薪资范围、联系人、投递编号…）

**不需要改代码**。数据里多出来的键会被原样保留（`normalize()` 只补默认键，不删未知键）。

想让它在编辑弹窗里可编辑，在 `openEditor()` 里的字段区加一行：

```js
${field('薪资范围', a['薪资范围'], 'wide')}
```

（`field` 是现有的小工具函数，照抄旁边的字段写法即可。）

## 5. 改梯队分类

梯队是纯数据字段（`梯队`），改 `data/ledger.json` 里的值，或在「筛选」下拉里新增选项：

```js
// renderTier() 里
['', '第一梯队-互联网大厂', '第二梯队-AI/科技独角兽', '你的新梯队']
```

## 6. 换成自己的企业库（自动补齐）

看板支持「输入企业名 → 自动补齐岗位/地点/链接/梯队」，数据来自当前台账本身（`LIBRARY`）。把你自己的企业清单导进去即可：

```bash
# 最省事的做法：直接用示例数据改，或写个脚本生成
python - <<'PY'
import io, json
d = json.load(io.open('data/sample-ledger.json', encoding='utf-8'))
d['applications'] = [ /* 你的企业列表 */ ]
json.dump(d, io.open('data/ledger.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
PY
```

## 7. 换主题色 / 深色模式

顶部 `:root` 里全是 CSS 变量：

```css
:root{
  --bg:#f5f6f8; --card:#fff; --line:#e5e7eb; --ink:#1f2329; --muted:#7a828c;
  --brand:#2f6fed; --brand-soft:#eaf1ff; --warn:#d97706; --danger:#d14343; --ok:#1c8a4a;
}
```

深色模式只需加一段覆盖（社区 PR 欢迎）：

```css
@media (prefers-color-scheme: dark){
  :root{ --bg:#14161a; --card:#1c1f24; --line:#2c313a; --ink:#e6e8eb; --muted:#9aa3ae; }
}
```

## 8. 改端口 / 数据位置

```bash
python server.py --port 9000 --data ~/Documents/my-ledger.json
```

写进 `start.bat` / `start.sh` 就能固化下来。

## 9. 部署成在线 Demo（GitHub Pages）

仓库自带 `.github/workflows/pages.yml`：推到 `main` 后会自动把 `dashboard.html` 发布为站点首页。在线版本没有后端，数据存在浏览器本地（也可用「绑定本地文件」直接写盘）。

## 10. 加阶段后老数据怎么办

不用迁移。老记录的状态值仍然有效；新阶段只是多了一个可选项。若你把某个阶段**改名**，请顺带在 `data/ledger.json` 里全局替换旧值（编辑器或脚本均可），否则该状态会落到「未投递」列。
