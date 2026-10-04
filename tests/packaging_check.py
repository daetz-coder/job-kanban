#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Packaging checks: every distribution path must actually work.

Verifies:
  1. `python server.py --version`      (repo entry point / shim)
  2. `python -m job_kanban --version`  (module entry point)
  3. frozen (PyInstaller) path logic   — data next to the exe, resources from the bundle
  4. `packaging/stage_package_data.py` stage → clean round trip
  5. the version in pyproject.toml matches job_kanban.__version__

Usage:
    python tests/packaging_check.py
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'src')
ok, bad = [], []


def check(name, cond, extra=''):
    (ok if cond else bad).append(name + ((' -> ' + str(extra)) if extra else ''))
    print('  %s %s%s' % ('[OK]  ' if cond else '[FAIL]', name, ((' -> ' + str(extra)) if extra else '')))


def run(args, **kw):
    return subprocess.run(args, cwd=HERE, capture_output=True, text=True, timeout=120, **kw)


def main():
    py = sys.executable

    # 1. repo entry point
    r = run([py, 'server.py', '--version'])
    check('python server.py --version', r.returncode == 0 and 'job-kanban' in r.stdout, r.stdout.strip() or r.stderr.strip()[:80])

    # 2. module entry point
    env = dict(os.environ, PYTHONPATH=SRC)
    r = run([py, '-m', 'job_kanban', '--version'], env=env)
    check('python -m job_kanban --version', r.returncode == 0 and 'job-kanban' in r.stdout, r.stdout.strip() or r.stderr.strip()[:80])

    # 3. frozen path logic (simulate PyInstaller)
    tmp = tempfile.mkdtemp(prefix='jobkanban-frozen-')
    try:
        bundle = os.path.join(tmp, 'bundle')
        os.makedirs(bundle)
        shutil.copy2(os.path.join(HERE, 'dashboard.html'), os.path.join(bundle, 'dashboard.html'))
        exe = os.path.join(tmp, 'job-kanban.exe')
        io.open(exe, 'w').write('')
        code = (
            "import sys, os\n"
            "sys.frozen = True\n"
            "sys._MEIPASS = r'%s'\n"
            "sys.executable = r'%s'\n"
            "sys.path.insert(0, r'%s')\n"
            "from job_kanban import _resource, _default_data_path\n"
            "d = _default_data_path()\n"
            "r = _resource('dashboard.html')\n"
            "assert d == os.path.join(os.path.dirname(sys.executable), 'data', 'ledger.json'), d\n"
            "assert r == os.path.join(sys._MEIPASS, 'dashboard.html'), r\n"
            "print('frozen paths OK')\n"
        ) % (bundle, exe, SRC)
        r = run([py, '-c', code])
        check('frozen mode: data next to exe, resources from bundle',
              r.returncode == 0 and 'frozen paths OK' in r.stdout, (r.stdout + r.stderr).strip()[:120])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # 4. stage / clean round trip
    stage = os.path.join(HERE, 'packaging', 'stage_package_data.py')
    pkg = os.path.join(SRC, 'job_kanban')
    r = run([py, stage])
    staged_ok = (os.path.exists(os.path.join(pkg, 'dashboard.html'))
                 and os.path.exists(os.path.join(pkg, 'data', 'sample-ledger.json'))
                 and os.path.exists(os.path.join(pkg, 'docs', 'icons', 'icon-192.png')))
    check('stage_package_data.py copies app resources into the package',
          r.returncode == 0 and staged_ok, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[:80])
    r = run([py, stage, '--clean'])
    cleaned_ok = not os.path.exists(os.path.join(pkg, 'dashboard.html'))
    check('stage_package_data.py --clean removes them again', r.returncode == 0 and cleaned_ok)

    # 5. version consistency
    v_py = re.search(r"__version__\s*=\s*'([^']+)'",
                     io.open(os.path.join(SRC, 'job_kanban', '__init__.py'), encoding='utf-8').read()).group(1)
    v_toml = re.search(r'^version\s*=\s*"([^"]+)"',
                       io.open(os.path.join(HERE, 'pyproject.toml'), encoding='utf-8').read(), re.M).group(1)
    v_pkg = json.load(io.open(os.path.join(HERE, 'package.json'), encoding='utf-8'))['version']
    check('version consistent (py / pyproject / package.json)', v_py == v_toml == v_pkg,
          '%s / %s / %s' % (v_py, v_toml, v_pkg))

    print('\n%d passed, %d failed' % (len(ok), len(bad)))
    if bad:
        for b in bad:
            print('  [FAIL] ' + b)
        return 1
    print('Packaging check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
