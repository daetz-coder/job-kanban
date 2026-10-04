# 求职投递看板 · Job Tracker

> 一个**单文件前端 + 零依赖本地服务**的求职投递管理工具：看板拖拽推进状态、按条自动落盘、数据就是你自己的一份 JSON。
>
> A local-first job-application tracker: single-file dashboard, stdlib-only Python server, your data stays in a plain JSON file you own.

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
![No dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

---

## 为什么做这个

秋招投递几十上百家，表格记不住「投了哪版简历、什么时候投的、卡在哪一轮、哪家该跟进了」。现有工具要么是 SaaS（数据在别人服务器），要么要登录、要订阅、要联网。

这个工具的原则：

- **数据是你的**：就是一份 `data/ledger.json`，可以放进 git、可以随时打开看
- **零依赖**：前端一个 HTML 文件，后端只用 Python 标准库
- **不丢数据**：按条写入 + 写锁 + 原子替换 + 写前备份
- **离线可用**：不联网、不注册、不上传

## 快速开始

需要 Python 3.8+（无需 pip 安装任何东西）。

```bash
python server.py
# 浏览器自动打开 http://127.0.0.1:8765/
```

Windows 也可以直接双击 **`start.bat`**；macOS / Linux 用 `./start.sh`。

首次启动若没有台账文件，会用 `data/sample-ledger.json`（示例数据）初始化，随便改。

常用参数：

```bash
python server.py --data my-ledger.json   # 指定台账文件（可以指向任意路径）
python server.py --port 9000             # 指定端口
python server.py --no-browser            # 不自动打开浏览器
```

## 功能

**看板视图**
- 7 条泳道：未投递 → 已投递 → 综合素质评测 → 笔试 → 面试中 → Offer → 已结束
- 整列都是投放区，拖拽即改状态（不用精确拖到卡片上），拖到视口边缘自动滚动
- 卡片显示优先级、投递日期、停滞天数、待办逾期

**列表视图**
- 表格 + 搜索 + 梯队筛选 + 5 种排序（含「停滞最久」）
- 一键「投递 ↗」新标签打开投递页，附链接可访问性标记

**一家公司多个岗位**
- 每家公司可挂多个在招岗位（类型 / 城市 / 在招业务 / 更新日期 / 各自状态）
- 支持**批量粘贴**招聘页复制的内容，自动解析成岗位列表
- 「按岗位」视图里同一家公司合并成一张分组卡，卡内逐岗位改状态

**质量与效率**
- 漏斗统计：投递率 / 测评率 / 笔试率 / 面试率 / Offer 转化率 / 停滞数
- 停滞提醒（默认 7 天无进展高亮）、待办逾期标红
- 状态历史自动留痕（推进、拖拽、手动改都会记录，来回拖动不会产生噪音）
- 撤销（最近 40 步）、导入 / 导出 JSON、重置

## 数据与安全

| 机制 | 说明 |
|---|---|
| **按条写入** | 拖一张卡只会重写那一条记录（`PUT /api/app/<id>`），不会整表覆盖 |
| **写锁串行** | 多标签页 / 多进程同时写也不会互相覆盖 |
| **原子替换** | 先写 `.tmp` 再 `os.replace`，不会出现半截文件 |
| **写前备份** | 每次写入前把旧文件存进 `data/.backup/`（保留最近 50 份） |
| **撤销** | 界面上可回退最近 40 步操作 |
| **git 友好** | 数据是缩进过的 JSON，`git diff` 能看清改了哪一条 |

`data/ledger.json` 与 `data/.backup/` 已在 `.gitignore` 中忽略——**你的投递数据不会被提交到仓库**。

## 项目结构

```
job-tracker/
├── dashboard.html          # 看板（单文件：界面 + 逻辑 + 兜底数据）
├── server.py               # 本地服务（静态页 + 按条写入 API，仅标准库）
├── start.bat / start.sh    # 一键启动
├── data/
│   ├── sample-ledger.json  # 示例数据（可提交）
│   └── ledger.json         # 你的台账（gitignore）
├── tools/
│   ├── build-embed.py      # 把 JSON 内嵌进 dashboard.html
│   ├── check-links.py      # 批量检测投递链接可访问性
│   └── sync-timeline.py    # 生成 Markdown 时间线视图
└── tests/
    └── dashboard.test.js   # 回归测试（Node + DOM 桩，无需浏览器）
```

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 看板页面 |
| `GET` | `/api/state` | 整份台账（响应头 `X-File-Mtime` 为文件修改时间） |
| `PUT` | `/api/app/<id>` | 新增或更新单条记录 |
| `DELETE` | `/api/app/<id>` | 删除单条记录 |
| `POST` | `/api/state` | 整份替换（导入 / 重置用） |

## 数据格式

```jsonc
{
  "meta": { "状态可选值": ["未投递", "已投递", "综合素质评测", "笔试", "一面", "二面", "三面", "HR面", "offer", "已拒", "放弃"] },
  "applications": [
    {
      "id": "sample-001",
      "企业": "示例科技",
      "梯队": "第一梯队-互联网大厂",
      "岗位": "AI 应用开发工程师",
      "工作地点": "杭州 / 北京",
      "投递链接": "https://example.com/campus",
      "投递状态": "已投递",
      "投递日期": "2026-09-20",
      "简历版本": "v2 Agent强化版",
      "渠道": "官网",
      "内推": "",
      "优先级": 5,
      "下一步": "等待笔试通知",
      "下一步截止": "",
      "备注": "",
      "岗位列表": [],          // 一家公司多个在招岗位
      "面试记录": [],          // [{日期, 轮次, 结果, 备注}]
      "状态历史": []           // [{日期, 从, 到, 备注}]，自动追加
    }
  ]
}
```

字段可以随意增删——看板只依赖上面这些键，多出来的字段会原样保留。

## 开发

```bash
node tests/dashboard.test.js     # 回归测试（130+ 项，无需浏览器）
python tools/build-embed.py      # 改了 JSON 后重新内嵌兜底数据
python tools/check-links.py      # 批量检测投递链接
python tools/sync-timeline.py    # 生成 timeline.md
```

改 `dashboard.html` 后刷新页面即可（服务每次请求都实时读取文件，不用重启）。

## 设计取舍

- **为什么不用 SQLite**：单人、几百条数据，SQLite 的索引/连接/聚合收益很小；而 JSON 能直接进 git、能人工 diff、能随时打开看。真正的数据风险来自「整表覆盖」和「并发写」，这两点用**按条写入 + 写锁 + 原子替换**就解决了，不必换存储引擎。
- **为什么数据文件放在 `data/` 而不是浏览器 localStorage**：localStorage 只当编辑态缓存，权威数据始终是磁盘上的 JSON——浏览器清缓存、换电脑都不会丢。
- **为什么前端是单文件**：双击即用、无构建步骤、便于 fork 和二次修改。

## License

[MIT](LICENSE)
