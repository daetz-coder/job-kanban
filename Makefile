# job-tracker 常用命令
# 用法：make / make test / make run / make shots

PY ?= python
PORT ?= 8765

.PHONY: help run test lint shots links timeline embed clean check

help:            ## 显示可用命令
	@echo "job-tracker 可用命令："
	@echo "  make run       启动本地服务（默认端口 $(PORT)）"
	@echo "  make test      跑前端回归测试（Node）"
	@echo "  make lint      Python 语法检查"
	@echo "  make shots     重新生成 README 截图（需 Chrome/Edge）"
	@echo "  make links     检测投递链接可访问性"
	@echo "  make timeline  生成 Markdown 时间线"
	@echo "  make embed     把 data/sample-ledger.json 内嵌进看板"
	@echo "  make check     lint + test（提交前跑这个）"
	@echo "  make clean     清理缓存与临时文件"

run:             ## 启动本地服务
	$(PY) server.py --port $(PORT)

test:            ## 前端回归测试
	node tests/dashboard.test.js

lint:            ## Python 语法检查
	$(PY) -m py_compile server.py tools/build-embed.py tools/check-links.py tools/sync-timeline.py tools/screenshot.py

shots:           ## 重新生成 README 截图
	$(PY) tools/screenshot.py

links:           ## 检测投递链接
	$(PY) tools/check-links.py

timeline:        ## 生成时间线
	$(PY) tools/sync-timeline.py

embed:           ## 内嵌兜底数据
	$(PY) tools/build-embed.py

check: lint test ## 提交前检查

clean:           ## 清理
	rm -rf __pycache__ tools/__pycache__ node_modules
	rm -f data/*.tmp
