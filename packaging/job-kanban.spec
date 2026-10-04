# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — builds a single-file, dependency-free executable.

    pyinstaller packaging/job-kanban.spec --noconfirm

Bundles the dashboard, PWA assets and sample data so the binary is self-contained.
The ledger itself is written next to the executable (see job_kanban._default_data_path).
"""
import os

BASE = os.path.abspath(os.path.join(SPECPATH, '..'))

datas = [
    (os.path.join(BASE, 'dashboard.html'), '.'),
    (os.path.join(BASE, 'manifest.webmanifest'), '.'),
    (os.path.join(BASE, 'sw.js'), '.'),
    (os.path.join(BASE, 'data', 'sample-ledger.json'), 'data'),
    (os.path.join(BASE, 'docs', 'icons'), os.path.join('docs', 'icons')),
]

a = Analysis(
    [os.path.join(BASE, 'server.py')],
    pathex=[os.path.join(BASE, 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=['job_kanban'],
    hookspath=[],
    runtime_hooks=[],
    # 只排除真正用不到的：email / http.cookiejar 是 http.server 的依赖，排除会导致
    # 打包后启动即 ModuleNotFoundError
    excludes=['tkinter', 'pydoc', 'doctest', 'unittest'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='job-kanban',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,          # keep the console: it shows the URL and allows Ctrl+C to stop
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
