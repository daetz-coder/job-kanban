#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard: the English UI must contain no CJK characters.

Renders the dashboard with headless Chrome, strips <script>/<style>, then scans
all visible text plus placeholder/title/aria-label attributes for CJK. Any hit
fails the check.

Usage:
    python tests/cjk_check.py
    python tests/cjk_check.py --dump out.html    # keep the rendered DOM

Needs Chrome or Edge; exits 0 with a notice when no browser is available
(so CI without a browser does not fail spuriously).
"""
import argparse
import glob
import io
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(HERE, 'data', 'sample-ledger.json')
CJK = re.compile(r'[\u4e00-\u9fff]')

CANDIDATES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/usr/bin/microsoft-edge',
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump', default='', help='write the rendered DOM to this path')
    args = ap.parse_args()

    browser = find_browser()
    if not browser:
        print('SKIP: no Chrome/Edge found — cannot verify the rendered DOM')
        return 0
    if not os.path.exists(SAMPLE):
        sys.exit('sample data not found: %s' % SAMPLE)

    tmp = tempfile.mkdtemp(prefix='jobkanban-cjk-')
    data = os.path.join(tmp, 'demo.json')
    io.open(data, 'w', encoding='utf-8').write(io.open(SAMPLE, encoding='utf-8').read())
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, 'server.py'),
         '--port', str(port), '--no-browser', '--data', data],
        cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        url = 'http://127.0.0.1:%d/' % port
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                urllib.request.urlopen(url + 'api/state', timeout=2).read()
                break
            except Exception:
                time.sleep(0.4)
        else:
            sys.exit('server did not start')

        dom = subprocess.run(
            [browser, '--headless=new', '--disable-gpu', '--no-first-run',
             '--virtual-time-budget=4000', '--dump-dom', url],
            capture_output=True, timeout=120).stdout.decode('utf-8', 'replace')
        if args.dump:
            io.open(args.dump, 'w', encoding='utf-8').write(dom)

        body = re.sub(r'<script[\s\S]*?</script>', '', dom)
        body = re.sub(r'<style[\s\S]*?</style>', '', body)

        hits = []
        for m in re.finditer(r'>([^<>]+)<', body):
            s = m.group(1).strip()
            if s and CJK.search(s):
                hits.append('text: ' + s)
        for m in re.finditer(r'(placeholder|title|aria-label)="([^"]*)"', body):
            if CJK.search(m.group(2)):
                hits.append('%s: %s' % (m.group(1), m.group(2)))

        seen, uniq = set(), []
        for h in hits:
            if h not in seen:
                seen.add(h)
                uniq.append(h)

        print('Rendered English UI — CJK occurrences: %d' % len(uniq))
        for h in uniq:
            print('  [CJK] ' + h)
        if uniq:
            print('\nFAIL: the English UI still contains Chinese text')
            return 1
        print('OK: no Chinese text in the rendered English UI')
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
