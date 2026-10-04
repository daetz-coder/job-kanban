#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 headless Chrome/Edge 生成 README 里的界面截图（可复现）。

用法：
    python tools/screenshot.py                # 生成 docs/screenshot-*.png
    python tools/screenshot.py --keep-server  # 不自动停止临时服务

原理：以「示例数据」启动一个临时服务（随机端口、独立临时数据文件），
用 headless 浏览器分别截取看板 / 列表 / 按岗位三个视图，然后清理临时文件。
仅用 Python 标准库；需要本机已安装 Chrome 或 Edge。
"""
import argparse
import glob
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(HERE, 'docs')
SAMPLE = os.path.join(HERE, 'data', 'sample-ledger.json')

CANDIDATES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/usr/bin/microsoft-edge',
]

SHOTS = [
    ('screenshot-board.png', '', 1600, 1000),
    ('screenshot-list.png', '#list', 1600, 1000),
    ('screenshot-positions.png', '#pos', 1600, 1000),
]


def find_browser():
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    for name in ('google-chrome', 'chromium', 'chrome', 'msedge'):
        p = shutil.which(name)
        if p:
            return p
    return None


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def wait_server(port, timeout=15):
    url = 'http://127.0.0.1:%d/api/state' % port
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep-server', action='store_true', help='截完不停止临时服务')
    args = ap.parse_args()

    browser = find_browser()
    if not browser:
        sys.exit('找不到 Chrome / Edge，请先安装或用 --help 查看支持的路径')
    if not os.path.exists(SAMPLE):
        sys.exit('找不到示例数据：%s' % SAMPLE)

    os.makedirs(DOCS, exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix='jobtracker-shots-')
    data = os.path.join(tmpdir, 'demo.json')
    io.open(data, 'w', encoding='utf-8').write(io.open(SAMPLE, encoding='utf-8').read())
    port = free_port()

    print('浏览器：%s' % browser)
    print('临时服务：http://127.0.0.1:%d/  （数据：示例数据）' % port)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, 'server.py'),
         '--port', str(port), '--no-browser', '--data', data],
        cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_server(port):
            sys.exit('临时服务启动失败')
        for name, frag, w, h in SHOTS:
            out = os.path.join(DOCS, name)
            if os.path.exists(out):
                os.remove(out)
            subprocess.run([
                browser, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                '--no-first-run', '--no-default-browser-check',
                '--virtual-time-budget=3000',
                '--window-size=%d,%d' % (w, h),
                '--screenshot=' + out,
                'http://127.0.0.1:%d/%s' % (port, frag),
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
            if os.path.exists(out):
                print('  [OK]   %-28s %6.1f KB' % (name, os.path.getsize(out) / 1024))
            else:
                print('  [FAIL] %s 生成失败' % name)
    finally:
        if not args.keep_server:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        shutil.rmtree(tmpdir, ignore_errors=True)
        for junk in glob.glob(os.path.join(DOCS, '*.tmp')):
            os.remove(junk)
    print('完成，截图在 %s' % os.path.relpath(DOCS, HERE))


if __name__ == '__main__':
    main()
