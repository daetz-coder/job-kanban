#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repo entry point — start the local server:

    python server.py [--data PATH] [--port N] [--no-browser]

The implementation lives in ``src/job_kanban`` so the same code can be installed
and run as the ``job-kanban`` command (pip / pipx / uvx) or as
``python -m job_kanban``. This file just puts ``src`` on the path and calls it.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from job_kanban import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
