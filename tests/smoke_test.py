#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨平台冒烟测试：启动本地服务 → 走一遍按条写入 API → 关掉。

用法：
    python tests/smoke_test.py
    python tests/smoke_test.py --keep        # 结束后保留服务（调试用）

CI 与本地都用它验证「服务能起来、接口能读能写能删」，不依赖 bash / curl。
只使用 Python 标准库。
"""
import argparse
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(HERE, 'data', 'sample-ledger.json')

ok, bad = [], []


def check(name, cond, extra=''):
    (ok if cond else bad).append(name + ((' -> ' + str(extra)) if extra else ''))
    print('  %s %s%s' % ('[OK]  ' if cond else '[FAIL]', name, ((' -> ' + str(extra)) if extra else '')))


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def call(method, url, obj=None, timeout=8):
    data = json.dumps(obj).encode('utf-8') if obj is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={'Content-Type': 'application/json'} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode('utf-8'), dict(r.headers)


def wait_up(base, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            status, _, _ = call('GET', base + '/api/state', timeout=2)
            if status == 200:
                return True
        except Exception:
            time.sleep(0.4)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true', help='do not stop the server afterwards')
    args = ap.parse_args()

    if not os.path.exists(SAMPLE):
        sys.exit('Sample data not found: %s' % SAMPLE)

    tmpdir = tempfile.mkdtemp(prefix='jobtracker-smoke-')
    data = os.path.join(tmpdir, 'smoke.json')
    io.open(data, 'w', encoding='utf-8').write(io.open(SAMPLE, encoding='utf-8').read())
    port = free_port()
    base = 'http://127.0.0.1:%d' % port

    print('Starting server: %s (temporary data file)' % base)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, 'server.py'),
         '--port', str(port), '--no-browser', '--data', data],
        cwd=HERE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        check('Server is ready within 20s', wait_up(base))
        if not ok:
            out = proc.stdout.read(2000).decode('utf-8', 'replace') if proc.stdout else ''
            print('Server output:\n' + out)
            return finish(proc, tmpdir, args)

        # 1. 页面
        status, html, _ = call('GET', base + '/')
        check('GET / returns the dashboard page', status == 200 and 'Job Kanban' in html, 'status=%s' % status)

        # 2. 整份读取
        status, body, headers = call('GET', base + '/api/state')
        state = json.loads(body)
        n0 = len(state['applications'])
        check('GET /api/state is readable', status == 200 and n0 > 0, '%d records' % n0)
        check('Response carries X-File-Mtime', headers.get('X-File-Mtime') not in (None, '', '0'),
              headers.get('X-File-Mtime'))

        # 3. 按条新增
        rec = {'id': 'smoke-001', '企业': 'Smoke Test Co', '投递状态': '已投递', '岗位': 'Test Position'}
        status, body, _ = call('PUT', base + '/api/app/smoke-001', rec)
        check('PUT creates a single record', status == 200, body.strip()[:60])
        _, body, _ = call('GET', base + '/api/state')
        apps = json.loads(body)['applications']
        check('Record count +1 after create', len(apps) == n0 + 1, '%d -> %d' % (n0, len(apps)))
        check('New record content is correct',
              any(a.get('id') == 'smoke-001' and a.get('企业') == 'Smoke Test Co' for a in apps))

        # 4. 按条更新（不影响其它记录）
        rec2 = dict(rec)
        rec2['投递状态'] = '笔试'
        status, _, _ = call('PUT', base + '/api/app/smoke-001', rec2)
        _, body, _ = call('GET', base + '/api/state')
        apps2 = json.loads(body)['applications']
        target = [a for a in apps2 if a.get('id') == 'smoke-001'][0]
        others = [a for a in apps2 if a.get('id') != 'smoke-001']
        check('PUT updates the record', target.get('投递状态') == '笔试', target.get('投递状态'))
        check('Update left other records untouched', len(others) == n0, '%d records' % len(others))

        # 5. 按条删除
        status, _, _ = call('DELETE', base + '/api/app/smoke-001')
        check('DELETE removes a single record', status == 200, 'status=%s' % status)
        _, body, _ = call('GET', base + '/api/state')
        apps3 = json.loads(body)['applications']
        check('Record count restored after delete', len(apps3) == n0, '%d -> %d' % (n0, len(apps3)))

        # 6. 删除不存在的 id
        try:
            call('DELETE', base + '/api/app/not-exist-xyz')
            check('Deleting an unknown id returns 404', False, 'no error raised')
        except urllib.error.HTTPError as e:
            check('Deleting an unknown id returns 404', e.code == 404, 'status=%s' % e.code)

        # 7. 写入前自动备份
        backup_dir = os.path.join(os.path.dirname(data), '.backup')
        n_bak = len(os.listdir(backup_dir)) if os.path.isdir(backup_dir) else 0
        check('Pre-write backup created in .backup/', n_bak > 0, '%d files' % n_bak)

        # 8. 非法载荷被拒绝
        try:
            call('POST', base + '/api/state', {'nope': 1})
            check('Invalid full payload rejected (400)', False, 'no error raised')
        except urllib.error.HTTPError as e:
            check('Invalid full payload rejected (400)', e.code == 400, 'status=%s' % e.code)

    finally:
        finish(proc, tmpdir, args)


def finish(proc, tmpdir, args):
    if not args.keep:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print('\n%d passed, %d failed' % (len(ok), len(bad)))
    if bad:
        for b in bad:
            print('  [FAIL] ' + b)
        return 1
    print('Smoke test passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
