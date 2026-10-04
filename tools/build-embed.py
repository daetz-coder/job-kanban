#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把台账 JSON 内嵌进 dashboard.html 的 DEFAULT_DATA（离线打开时的兜底数据）。

用法：
    python tools/build-embed.py                        # 用 data/sample-ledger.json
    python tools/build-embed.py --data data/ledger.json

说明：看板在「本地服务模式」下以 data/ledger.json 为准；内嵌数据只在
直接用 file:// 打开、且浏览器本地没有数据时作为初始值使用。
"""
import argparse
import io
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(HERE, 'dashboard.html')
START_MARK = 'const DEFAULT_DATA = '
END_MARK = 'const STORAGE_KEY'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=os.path.join('data', 'sample-ledger.json'))
    args = ap.parse_args()

    data_path = args.data if os.path.isabs(args.data) else os.path.join(HERE, args.data)
    if not os.path.exists(DASH):
        sys.exit('找不到 dashboard.html')
    if not os.path.exists(data_path):
        sys.exit('找不到数据文件：%s' % data_path)

    html = io.open(DASH, encoding='utf-8').read()
    data = io.open(data_path, encoding='utf-8').read().strip()

    i = html.find(START_MARK)
    j = html.find(END_MARK)
    if i < 0 or j < 0 or j < i:
        sys.exit('dashboard.html 里找不到 DEFAULT_DATA 注入点')

    new_html = html[:i] + START_MARK + data + ';\n' + html[j:]
    io.open(DASH, 'w', encoding='utf-8').write(new_html)
    print('已内嵌 %s → dashboard.html（%d 字符）' % (os.path.relpath(data_path, HERE), len(new_html)))


if __name__ == '__main__':
    main()
