# 贡献指南

感谢愿意一起改进这个工具 🙌

## 开始之前

请先读一下 [README 的设计取舍](README.md#设计取舍)。本项目的三条底线：

1. **零运行时依赖** —— 前端纯 vanilla JS（单文件），后端仅 Python 标准库。PR 不要引入 npm / pip 运行时依赖。
2. **不丢数据** —— 任何涉及写入、导入、合并、重置的改动，必须考虑：会不会覆盖别人的数据？失败时能不能回退？
3. **不自动改动记录数** —— 不要在加载时静默合并 / 删除记录（历史上出过真实事故）。

## 开发环境

```bash
git clone https://github.com/<your-name>/job-tracker.git
cd job-tracker
python server.py          # 启动本地服务（会自动用示例数据初始化）
```

无需安装依赖。Node 仅用于跑测试（Node 14+）。

## 跑测试

```bash
make check                      # Python 语法检查 + 前端回归测试（推荐）
npm test                        # 只跑前端测试
python -m py_compile server.py  # 只做语法检查
```

测试用最小 DOM 桩直接执行 `dashboard.html` 里的脚本，**不需要浏览器**，几百毫秒跑完。

- 断言必须**与数据量无关**（示例数据只有 12 条也能跑），不要写死「50 家」这类数字
- 新增功能请补测试；修 bug 请先写一个能复现的断言
- 界面改动请用 `python tools/screenshot.py` 重新生成截图（它用示例数据起临时服务，不会碰真实台账）

## 提交规范

采用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: 新增 xxx
fix: 修复 xxx
docs: 更新 xxx
refactor: 重构 xxx
test: 补充 xxx
chore: 杂项
```

示例：

```
feat: 看板支持按「城市」泳道分组
fix: 拖拽跨天回退时状态历史未抵消
docs: 补充 API 示例
```

## Pull Request

1. Fork → 新建分支（`feat/xxx` 或 `fix/xxx`）
2. 保证 `make check` 全绿
3. 若改了界面，用 `python tools/screenshot.py` 重新生成截图并一并提交
4. PR 描述里说明：**改了什么 / 为什么 / 怎么验证的**
5. 如果改动涉及数据格式，请说明**向后兼容性**（老数据能否直接读）

CI 会在 Ubuntu 与 Windows、多个 Node / Python 版本上跑测试，并检查：

- 看板内不得含真实公司名（开源安全）
- `data/ledger.json` 不得被提交（隐私）

## 报告问题

请用 [Issue 模板](https://github.com/<your-name>/job-tracker/issues/new/choose)，并尽量附上：

- 操作系统 / 浏览器版本 / Python 版本
- 复现步骤
- 期望结果与实际结果
- 相关日志或截图（**请先脱敏，不要贴真实投递数据**）

## 代码风格

- JavaScript：2 空格缩进、单引号、语句末尾不加分号后置风格保持一致（跟随现有文件）
- Python：PEP 8、UTF-8、文件头 `# -*- coding: utf-8 -*-`
- 注释与提交信息用中文（面向中文用户），变量名可中英混用（数据字段是中文键）

## 安全

发现安全问题请勿公开提交 Issue，见 [SECURITY.md](SECURITY.md)。
