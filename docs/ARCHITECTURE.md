# 架构说明

## 总览

```
┌──────────────────────────┐         ┌───────────────────────────────┐
│  dashboard.html          │  HTTP   │  server.py                    │
│  （单文件前端，零依赖）    │ ──────► │  （Python 标准库，仅回环地址）  │
│                          │         │                               │
│  · 状态机 / 看板渲染      │  PUT    │  · 按条写入 PUT /api/app/<id>  │
│  · 拖拽 / 筛选 / 统计     │  DELETE │  · 整份替换 POST /api/state    │
│  · 差异同步（只发变化）    │  POST   │  · 写锁 + 原子替换 + 写前备份   │
└──────────┬───────────────┘         └───────────────┬───────────────┘
           │                                          │
           │ 兜底（离线打开时）                          │ 读写
           ▼                                          ▼
  内嵌示例数据 DEFAULT_DATA                    data/ledger.json（权威）
  + localStorage（编辑态缓存）                  data/.backup/*.json（快照）
```

## 数据流

### 启动

1. `load()` 先读 localStorage；没有则用内嵌的 `DEFAULT_DATA`（示例数据）
2. `detectServer()` 请求 `GET /api/state`（带 `X-File-Mtime`）
3. **冲突判定**：比较「记录数 → 有进度数 → 岗位数」
   - 磁盘更完整（或同样完整且不旧）→ 用磁盘数据，并记录已同步快照
   - 浏览器更完整 → 保留浏览器数据，稍后整份写回磁盘
4. `syncReady = true` —— **在此之前禁止任何写入**，避免用默认数据覆盖磁盘

### 编辑

1. 任何操作改内存里的 `state`
2. `save()` → `persist()`（写 localStorage + 每日首次快照）+ `render()` + 压入撤销栈
3. `scheduleFileWrite()` 防抖 600ms → `flushSync()`

### 差异同步（核心）

`flushSync()` 把当前 `state` 与「上次已同步快照」对比：

```
变化的记录数 ≤ max(12, 总数 × 40%)  →  逐条 PUT / DELETE
变化过多（导入 / 重置 / 首次同步）    →  整份 POST /api/state
```

因此**拖一张卡只会重写那一条记录**，物理上不可能覆盖别的记录。

## 为什么这样设计

### 按条写入而不是整表提交

最初实现是「每次改动 POST 整份状态」。问题：浏览器里的旧状态（或残缺状态）会把磁盘上更新的数据整体覆盖——真实发生过数据丢失。改成按条写入后，一条记录的改动只影响那一条。

### 写锁 + 原子替换

- `threading.Lock` 串行化所有写入，多标签页 / 多进程同时改不会交错
- 先写 `ledger.json.tmp` 再 `os.replace()` 原子替换，断电 / 崩溃也不会留下半截 JSON
- 写前把旧文件复制到 `.backup/`，形成 50 份滚动快照

### 为什么权威数据在磁盘

localStorage 有三个致命问题：清缓存就没了、换浏览器 / 换电脑不同步、无法进 git。所以把它降级为「编辑态缓存」，磁盘 JSON 才是真相。

### 为什么选 JSON 而不是 SQLite

| 维度 | JSON | SQLite |
|---|---|---|
| git 可读 diff | ✅ 逐行可比 | ❌ 二进制 |
| 人工查看 / 手改 | ✅ 记事本即可 | ❌ 需要工具 |
| 事务 / 并发 | 靠写锁 + 原子替换 | ✅ 原生 |
| 唯一约束 / 索引 | ❌ | ✅ |
| 数据量 1000+ | 一般 | ✅ 更好 |

在「单人 + 几百条 + 要能 git 回看」的场景下，JSON 的综合收益更高；并发与覆盖风险已经用**按条写入 + 写锁 + 原子替换**解决。若将来要做多端同步，可以加一个 SQLite 后端作为可选实现（见路线图）。

### 为什么不做自动合并同名公司

曾经实现过「加载时自动合并同名公司」，结果把用户**真实岗位记录**当作重复项丢弃（合并规则保留了先出现记录的默认岗位），造成数据丢失事故。现在的原则：

> **绝不自动改动记录数。** 任何合并 / 去重 / 删除都必须由用户显式触发并二次确认。

## 状态机

```
PIPELINE = 未投递 → 已投递 → 综合素质评测 → 笔试 → 一面 → 二面 → 三面 → HR面 → offer
TERMINAL = 已拒 / 放弃（任意阶段可终止）
```

- 公司级状态 = 名下岗位**最靠前**的进度（`aggStatus`），完全由岗位推导，可升可降
- 全部岗位终止时，公司状态取第一个终止态
- 公司级投递日期 = 名下岗位最早的非空日期（`aggAppliedDate`）
- 无岗位的公司直接用自身状态

## 状态历史去噪

拖拽容易产生 `已投递→未投递` 这类来回记录。`compactHistory` 做三层处理：

1. **同日精确回退**：同一天内 `A→B` 紧跟 `B→A`，两条一起抵消，并清掉当天自动写入的投递日期
2. **按天净变化为零**：某天所有记录合并后起止状态相同 → 整天丢弃
3. **相邻回退抵消 + 完全重复丢弃**

跨天的记录不合并（保留真实的时间轨迹）。

## 前端结构（dashboard.html）

| 区块 | 职责 |
|---|---|
| `PIPELINE / TERMINAL / BOARD / BADGE` | 状态机与看板列定义 |
| `blank / blankPosition / normalize` | 数据结构与兼容性兜底 |
| `aggStatus / aggAppliedDate / effStatus / syncCompanyFromPositions` | 公司 ↔ 岗位聚合 |
| `setStatus / compactHistory` | 状态流转与历史去噪 |
| `parsePositions` | 招聘页文本 → 岗位数组 |
| `renderBoard / kcardCo / kcardPos / kcardGroup / renderList` | 看板与列表渲染 |
| `detectServer / diffSince / flushSync / putRecord / deleteRecord` | 同步层 |
| `snapshot / listBackups / restoreBackup / undo` | 备份与撤销 |
| `window.__app` | 测试钩子（暴露内部函数供 Node 测试断言） |

## 测试策略

`tests/dashboard.test.js` 用最小 DOM 桩（`document` / `localStorage` / `window`）直接执行 `dashboard.html` 里的脚本，通过 `window.__app` 断言内部行为，**不需要浏览器**。

设计原则：

- 断言**与数据量无关**（不写死「50 家」），示例数据也能跑
- 覆盖：渲染、状态流转、历史去噪、聚合、解析、筛选、增删、撤销、备份、同步降级
- 额外守护：看板内不得出现真实公司名（开源安全）

## 目录职责

```
dashboard.html   前端全部逻辑（含兜底数据，由 tools/build-embed.py 注入）
server.py        本地服务（HTTP + 按条写入 + 备份）
tools/           独立脚本：内嵌构建 / 链接检测 / 时间线生成
tests/           回归测试
docs/            截图与本文档
data/            台账与备份（个人数据不入库）
```
