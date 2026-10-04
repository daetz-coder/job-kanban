#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""求职投递看板 · 本地服务

提供看板页面，并读写你的投递台账（JSON）。按条写入 + 写锁 + 原子替换，
多个标签页同时改也不会互相覆盖。

用法：
    python server.py                     # 数据默认在 ./data/ledger.json，端口 8765
    python server.py --data my.json      # 指定数据文件
    python server.py --port 9000         # 指定端口
    python server.py --no-browser        # 不自动打开浏览器

接口：
    GET    /                  看板页面
    GET    /api/state         整份台账（带 X-File-Mtime 头）
    PUT    /api/app/<id>      新增或更新单条记录
    DELETE /api/app/<id>      删除单条记录
    POST   /api/state         整份替换（导入/重置用）

只依赖 Python 标准库（3.8+），无需安装任何第三方包。
"""
import argparse
import http.server
import io
import json
import os
import socketserver
import sys
import threading
import time
import urllib.parse


# Windows 控制台可能是 GBK / cp1252，直接打印中文会抛 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(HERE, 'dashboard.html')
KEEP_BACKUPS = 50
WRITE_LOCK = threading.Lock()

STATE = os.path.join(HERE, 'data', 'ledger.json')
BACKUP_DIR = os.path.join(HERE, 'data', '.backup')
PORT = 8765


def read_state():
    try:
        return json.loads(io.open(STATE, encoding='utf-8').read())
    except Exception:
        return {'meta': {}, 'applications': []}


def write_state(obj, reason=''):
    """加锁 + 备份 + 原子替换；返回写入后的记录数。"""
    with WRITE_LOCK:
        try:
            if os.path.exists(STATE):
                os.makedirs(BACKUP_DIR, exist_ok=True)
                stamp = time.strftime('%Y%m%d-%H%M%S')
                suffix = ('-' + reason) if reason else ''
                dst = os.path.join(BACKUP_DIR, 'ledger-%s%s.json' % (stamp, suffix))
                io.open(dst, 'w', encoding='utf-8').write(io.open(STATE, encoding='utf-8').read())
                files = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith('.json'))
                while len(files) > KEEP_BACKUPS:
                    try:
                        os.remove(os.path.join(BACKUP_DIR, files.pop(0)))
                    except Exception:
                        break
        except Exception:
            pass
        os.makedirs(os.path.dirname(STATE) or '.', exist_ok=True)
        tmp = STATE + '.tmp'
        io.open(tmp, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=2))
        os.replace(tmp, STATE)                      # 原子替换，避免半截文件
        return len(obj.get('applications', []))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def log_message(self, fmt, *args):
        pass

    # ---------- helpers ----------
    def _send(self, code, body, ctype='application/json; charset=utf-8', extra=None):
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        for k, v in (extra or {}).items():
            self.send_header(k, str(v))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _body(self):
        try:
            n = int(self.headers.get('Content-Length') or 0)
        except Exception:
            n = 0
        raw = self.rfile.read(n) if n else b''
        try:
            return json.loads(raw.decode('utf-8'))
        except Exception as e:
            return {'__error__': str(e)}

    def _path(self):
        return urllib.parse.urlparse(self.path).path

    # ---------- GET ----------
    def do_GET(self):
        path = self._path()
        if path == '/api/state':
            try:
                data = io.open(STATE, encoding='utf-8').read()
            except Exception:
                data = json.dumps({'meta': {}, 'applications': []})
            try:
                mtime = int(os.path.getmtime(STATE) * 1000)
            except Exception:
                mtime = 0
            return self._send(200, data, extra={'X-File-Mtime': mtime})
        if path in ('/', '/index.html', '/dashboard.html'):
            try:
                html = io.open(DASH, encoding='utf-8').read()
            except Exception as e:
                return self._send(500, 'cannot read dashboard.html: %s' % e, 'text/plain; charset=utf-8')
            return self._send(200, html, 'text/html; charset=utf-8')
        return super().do_GET()

    # ---------- PUT 单条 ----------
    def do_PUT(self):
        path = self._path()
        if not path.startswith('/api/app/'):
            return self._send(404, '{"ok":false}')
        rid = urllib.parse.unquote(path[len('/api/app/'):])
        if not rid:
            return self._send(400, '{"ok":false,"error":"missing id"}')
        rec = self._body()
        if not isinstance(rec, dict) or rec.get('__error__'):
            return self._send(400, json.dumps({'ok': False, 'error': rec.get('__error__', 'bad body')}, ensure_ascii=False))
        rec['id'] = rid
        st = read_state()
        apps = st.setdefault('applications', [])
        for i, a in enumerate(apps):
            if a.get('id') == rid:
                apps[i] = rec
                break
        else:
            apps.append(rec)
        n = write_state(st, reason='put')
        return self._send(200, json.dumps({'ok': True, 'id': rid, 'count': n}, ensure_ascii=False))

    # ---------- DELETE 单条 ----------
    def do_DELETE(self):
        path = self._path()
        if not path.startswith('/api/app/'):
            return self._send(404, '{"ok":false}')
        rid = urllib.parse.unquote(path[len('/api/app/'):])
        st = read_state()
        apps = st.setdefault('applications', [])
        before = len(apps)
        st['applications'] = [a for a in apps if a.get('id') != rid]
        if len(st['applications']) == before:
            return self._send(404, json.dumps({'ok': False, 'error': 'id not found', 'id': rid}, ensure_ascii=False))
        n = write_state(st, reason='delete')
        return self._send(200, json.dumps({'ok': True, 'id': rid, 'count': n}, ensure_ascii=False))

    # ---------- POST 整份 ----------
    def do_POST(self):
        if self._path() != '/api/state':
            return self._send(404, '{"ok":false}')
        obj = self._body()
        if not isinstance(obj, dict) or obj.get('__error__') or not isinstance(obj.get('applications'), list):
            return self._send(400, json.dumps({'ok': False, 'error': 'payload must be {applications:[...]}'}, ensure_ascii=False))
        n = write_state(obj, reason='bulk')
        return self._send(200, json.dumps({'ok': True, 'count': n}, ensure_ascii=False))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    global STATE, BACKUP_DIR, PORT
    ap = argparse.ArgumentParser(description='求职投递看板 · 本地服务')
    ap.add_argument('--data', default=os.path.join('data', 'ledger.json'), help='台账 JSON 路径（默认 data/ledger.json）')
    ap.add_argument('--port', type=int, default=8765, help='端口（默认 8765）')
    ap.add_argument('--no-browser', action='store_true', help='启动后不自动打开浏览器')
    args = ap.parse_args()

    STATE = args.data if os.path.isabs(args.data) else os.path.join(HERE, args.data)
    BACKUP_DIR = os.path.join(os.path.dirname(STATE), '.backup')
    PORT = args.port

    if not os.path.exists(DASH):
        sys.exit('找不到 dashboard.html（请与本脚本放在同一目录）')
    if not os.path.exists(STATE):
        os.makedirs(os.path.dirname(STATE) or '.', exist_ok=True)
        sample = os.path.join(HERE, 'data', 'sample-ledger.json')
        if os.path.exists(sample):
            io.open(STATE, 'w', encoding='utf-8').write(io.open(sample, encoding='utf-8').read())
            print('未找到台账，已用示例数据初始化：%s' % STATE)
        else:
            io.open(STATE, 'w', encoding='utf-8').write(json.dumps({'meta': {}, 'applications': []}, ensure_ascii=False, indent=2))

    with Server(('127.0.0.1', PORT), Handler) as httpd:
        url = 'http://127.0.0.1:%d/' % PORT
        print('求职投递看板已启动：%s' % url)
        print('数据文件：%s' % STATE)
        print('改动会自动写入（按条写入 + 写锁 + 原子替换，写前备份到 %s）' % BACKUP_DIR)
        print('Ctrl+C 停止。')
        if not args.no_browser:
            try:
                import webbrowser
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n已停止')


if __name__ == '__main__':
    main()
