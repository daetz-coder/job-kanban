#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copy the app resources into the Python package before building a wheel/sdist.

The repository keeps a single copy of dashboard.html & friends at the root; the
packaged distribution needs them *inside* ``src/job_kanban`` so an installed
``job-kanban`` command is self-contained.

Usage:
    python packaging/stage_package_data.py          # copy
    python packaging/stage_package_data.py --clean  # remove the copies again
"""
import argparse
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(BASE, 'src', 'job_kanban')

FILES = ['dashboard.html', 'manifest.webmanifest', 'sw.js']
TREES = [(os.path.join('data', 'sample-ledger.json'), os.path.join('data', 'sample-ledger.json')),
         (os.path.join('docs', 'icons'), os.path.join('docs', 'icons'))]


def clean():
    for f in FILES:
        p = os.path.join(PKG, f)
        if os.path.exists(p):
            os.remove(p)
    for d in ('data', 'docs'):
        p = os.path.join(PKG, d)
        if os.path.isdir(p):
            shutil.rmtree(p)
    print('cleaned staged package data')


def stage():
    for f in FILES:
        shutil.copy2(os.path.join(BASE, f), os.path.join(PKG, f))
        print('  staged %s' % f)
    for src_rel, dst_rel in TREES:
        src = os.path.join(BASE, src_rel)
        dst = os.path.join(PKG, dst_rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        print('  staged %s' % src_rel)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--clean', action='store_true')
    args = ap.parse_args()
    clean() if args.clean else stage()
