# job-tracker 常用命令
# 用法：make / make test / make run / make shots

PY ?= python
PORT ?= 8765

.PHONY: help run test smoke safety cjk packaging check lint shots links timeline embed clean

help:            ## 显示可用命令
	@echo "job-tracker 可用命令："
	@echo "  make run       启动本地服务（默认端口 $(PORT)）"
	@echo "  make test      前端回归测试（Node，100 项）"
	@echo "  make smoke     服务冒烟测试（启动 → 按条读写删 → 关掉）"
	@echo "  make safety    开源安全与隐私检查"
	@echo "  make cjk       渲染后 DOM 不得含中文（英文界面守卫）"
	@echo "  make packaging 各分发形态自检（server.py / 模块 / 冻结路径 / 版本一致）"
	@echo "  make lint      Python 语法检查"
	@echo "  make check     lint + test + smoke + safety（提交前跑这个）"
	@echo "  make shots     重新生成 README 截图（需 Chrome/Edge）"
	@echo "  make links     检测投递链接可访问性"
	@echo "  make timeline  生成 Markdown 时间线"
	@echo "  make embed     把 data/sample-ledger.json 内嵌进看板"
	@echo "  make clean     清理缓存与临时文件"

run:             ## 启动本地服务
	$(PY) server.py --port $(PORT)

test:            ## 前端回归测试
	node tests/dashboard.test.js

smoke:           ## 服务冒烟测试
	$(PY) tests/smoke_test.py

safety:          ## 开源安全与隐私检查
	$(PY) tests/safety_check.py

cjk:             ## 英文界面不得含中文（需 Chrome/Edge）
	$(PY) tests/cjk_check.py

packaging:       ## 各分发形态自检
	$(PY) tests/packaging_check.py

lint:            ## Python 语法检查
	$(PY) -m py_compile server.py tools/build-embed.py tools/check-links.py tools/sync-timeline.py tools/screenshot.py tests/smoke_test.py tests/safety_check.py tests/cjk_check.py tests/packaging_check.py

check: lint test smoke safety cjk packaging ## 提交前完整检查

shots:           ## 重新生成 README 截图
	$(PY) tools/screenshot.py

links:           ## 检测投递链接
	$(PY) tools/check-links.py

timeline:        ## 生成时间线
	$(PY) tools/sync-timeline.py

embed:           ## 内嵌兜底数据
	$(PY) tools/build-embed.py

clean:           ## 清理
	rm -rf __pycache__ tools/__pycache__ tests/__pycache__ node_modules
	rm -f data/*.tmp
