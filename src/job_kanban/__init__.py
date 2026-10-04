#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Job Kanban · local server.

Serves the dashboard and reads/writes your ledger (JSON) with per-record writes,
a write lock, atomic replacement and pre-write backups.

Run it from a git clone:      python server.py
Run it as an installed tool:  job-kanban          (pip / pipx / uvx)
Or as a module:               python -m job_kanban

Options:
    --data PATH      ledger JSON path (default: ./data/ledger.json, or ~/.job-kanban/ledger.json when installed)
    --port N         port (default 8765)
    --no-browser     do not open the browser
    --version        print the version and exit

API:
    GET    /                  dashboard page
    GET    /api/state         whole ledger (X-File-Mtime header)
    PUT    /api/app/<id>      create or update one record
    DELETE /api/app/<id>      delete one record
    POST   /api/state         full replace (import / reset)

Standard library only (Python 3.8+).
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

__version__ = '1.2.1'

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN = bool(getattr(sys, 'frozen', False))
KEEP_BACKUPS = 50
WRITE_LOCK = threading.Lock()


def _resource(name):
    """Locate a bundled resource (dashboard.html, icons, sample data).

    Search order: package dir (installed wheel / PyInstaller bundle) →
    repo root (running from a git clone) → current directory.
    """
    pkg = HERE
    repo = os.path.dirname(os.path.dirname(pkg))          # src/job_kanban → repo root
    bundle = getattr(sys, '_MEIPASS', None)
    cands = []
    if bundle:
        cands.append(os.path.join(bundle, name))
    cands += [os.path.join(pkg, name), os.path.join(repo, name), os.path.join(os.getcwd(), name)]
    for c in cands:
        if os.path.exists(c):
            return c
    return cands[0]


def _default_data_path():
    """Where the ledger lives when --data is not given."""
    if FROZEN:                                            # next to the executable
        return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), 'data', 'ledger.json')
    repo = os.path.dirname(os.path.dirname(HERE))
    if os.path.exists(os.path.join(repo, 'dashboard.html')):   # running from a clone
        return os.path.join(repo, 'data', 'ledger.json')
    return os.path.join(os.path.expanduser('~'), '.job-kanban', 'ledger.json')   # installed


DASH = _resource('dashboard.html')
STATE = _default_data_path()
BACKUP_DIR = os.path.join(os.path.dirname(STATE), '.backup')
PORT = 8765


def read_state():
    try:
        return json.loads(io.open(STATE, encoding='utf-8').read())
    except Exception:
        return {'meta': {}, 'applications': []}


def write_state(obj, reason=''):
    """Lock, back up, then atomically replace. Returns the record count written."""
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
        os.replace(tmp, STATE)                      # atomic replace — never a half-written file
        return len(obj.get('applications', []))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(DASH) or '.', **kwargs)

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

    # ---------- PUT one record ----------
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

    # ---------- DELETE one record ----------
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

    # ---------- POST whole ledger ----------
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


def main(argv=None):
    global STATE, BACKUP_DIR, PORT, DASH
    ap = argparse.ArgumentParser(prog='job-kanban', description='Job Kanban · local server')
    ap.add_argument('--data', default='', help='ledger JSON path (default: %s)' % _default_data_path())
    ap.add_argument('--port', type=int, default=8765, help='port (default: 8765)')
    ap.add_argument('--no-browser', action='store_true', help='do not open the browser automatically')
    ap.add_argument('--version', action='version', version='job-kanban %s' % __version__)
    args = ap.parse_args(argv)

    DASH = _resource('dashboard.html')
    if not os.path.exists(DASH):
        print('dashboard.html not found — is the install complete?')
        return 1
    STATE = os.path.abspath(args.data) if args.data else _default_data_path()
    BACKUP_DIR = os.path.join(os.path.dirname(STATE), '.backup')
    PORT = args.port

    if not os.path.exists(STATE):
        os.makedirs(os.path.dirname(STATE) or '.', exist_ok=True)
        sample = _resource(os.path.join('data', 'sample-ledger.json'))
        if os.path.exists(sample):
            io.open(STATE, 'w', encoding='utf-8').write(io.open(sample, encoding='utf-8').read())
            print('No ledger found — initialised from sample data: %s' % STATE)
        else:
            io.open(STATE, 'w', encoding='utf-8').write(
                json.dumps({'meta': {}, 'applications': []}, ensure_ascii=False, indent=2))

    try:
        httpd = Server(('127.0.0.1', PORT), Handler)
    except OSError as e:
        msg = str(e).lower()
        if 'in use' in msg or getattr(e, 'errno', None) in (48, 98, 10048):
            print('Port %d is already in use.' % PORT)
            print('  * Job Kanban may already be running — just open: http://127.0.0.1:%d/' % PORT)
            print('  * Or start it on another port:  job-kanban --port %d' % (PORT + 1))
            return 1
        raise

    with httpd:
        url = 'http://127.0.0.1:%d/' % PORT
        print('Job Kanban is running at %s' % url)
        print('Ledger file: %s' % STATE)
        print('Changes are written automatically (per-record, write lock, atomic replace; backups in %s)' % BACKUP_DIR)
        print('Press Ctrl+C to stop.')
        if not args.no_browser:
            try:
                import webbrowser
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nStopped')
    return 0


if __name__ == '__main__':
    sys.exit(main())
