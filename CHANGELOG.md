# 更新日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 与 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [1.0.1] - 2026-10-04

修复 CI 在 Windows 上暴露的三个真实问题。

### 修复

- **备份 key 可能互相覆盖**：snapshot() 原先用 Date.now() 当 key，同一毫秒内两次快照（例如保存时触发的每日备份）会覆盖前一份，导致「恢复快照」可能拿回空状态。现在 key 追加自增序号，并按时间 + 序号稳定排序。
- **非 UTF-8 控制台打印中文会崩溃**：Windows 上控制台代码页为 GBK/cp1252 时，server.py 与各工具启动时打印中文会抛 UnicodeEncodeError（服务直接起不来）。现在启动时把 stdout/stderr 重配置为 UTF-8 并允许替换字符。
- **CI 冒烟测试依赖 bash / curl**：在 Windows runner 上不稳定。改为跨平台 Python 脚本 	ests/smoke_test.py。

### 新增

- 	ests/smoke_test.py：跨平台冒烟测试（页面 / 整份读取 / 按条新增 / 按条更新不影响其它记录 / 按条删除 / 404 / 写前备份 / 非法载荷拒绝，共 14 项）
- 	ests/safety_check.py：开源安全与隐私检查（看板无真实公司名、个人台账未被跟踪、无个人身份信息、示例数据虚构、无备份临时文件入库，共 5 项）
- make check 与 
pm run check 一键跑完整检查
- CI 矩阵精简为 3 个组合（ubuntu 最新 / ubuntu 最低版本 / windows 交叉验证）

## [1.0.0] - 2026-10-04

首个公开版本。

### 新增

**看板**
- 7 条泳道：未投递 / 已投递 / 综合素质评测 / 笔试 / 面试中 / Offer / 已结束
- 整列投放区（拖到列内任意位置即可改状态）+ 拖拽到视口边缘自动滚动
- 卡片显示优先级、投递日期、停滞天数、待办逾期标红
- 分组卡：同一家公司的多个在招岗位合并成一张卡，卡内逐岗位改状态 / 推进 / 编辑

**列表**
- 表格视图 + 搜索（企业 / 岗位 / 城市 / 渠道 / 备注）
- 梯队筛选 + 5 种排序（含「停滞最久」）
- 投递链接一键新标签打开，附可访问性标记

**数据**
- 一家公司多个岗位：岗位级状态、日期、历史；公司级状态按最靠前进度聚合
- 批量粘贴招聘页文本，自动解析岗位名 / 类型 / 城市 / 在招业务 / 更新日期
- 漏斗统计：投递率 / 测评率 / 笔试率 / 面试率 / Offer 转化率 / 停滞数
- 状态历史自动留痕，同日来回拖动自动抵消（不产生噪音）
- 撤销最近 40 步操作

**本地服务**
- `GET /api/state`、`PUT /api/app/<id>`、`DELETE /api/app/<id>`、`POST /api/state`
- 按条写入 + 全局写锁 + 原子替换（`os.replace`）
- 每次写入前自动备份到 `data/.backup/`（保留 50 份）
- 打开时按「记录数 → 有进度数 → 岗位数」判断以哪份为准，残缺缓存不会覆盖磁盘数据
- 仅依赖 Python 标准库

**工具**
- `tools/check-links.py`：投递链接可访问性检测（三分类，避免代理环境误判）
- `tools/sync-timeline.py`：生成 Markdown 时间线视图
- `tools/build-embed.py`：把 JSON 内嵌进 `dashboard.html`

**其他**
- URL hash 深链：`#list` / `#board`、`#pos` / `#co`、`#issue`
- 100 项回归测试（Node + DOM 桩，无需浏览器）
- GitHub Actions CI（Ubuntu / Windows × 多版本 Node / Python）

### 设计决策（来自真实踩坑）

- **不做同名公司自动合并**：曾把用户真实岗位记录当重复项丢弃，导致数据丢失。现在绝不自动改动记录数，合并类操作一律由用户显式确认。
- **权威数据在磁盘而非 localStorage**：localStorage 会被清缓存 / 换浏览器清掉，且无法进 git。
- **选择 JSON 而非 SQLite**：单人几百条数据，JSON 的 git 可读性与可迁移性更重要；数据风险用「按条写入 + 写锁 + 原子替换」解决，而非换存储引擎。

[1.0.0]: https://github.com/daetz-coder/job-tracker/releases/tag/v1.0.0
