# -*- coding: utf-8 -*-
"""``python -m job_kanban`` → same entry point as the ``job-kanban`` command."""
import sys

from . import main

if __name__ == '__main__':
    sys.exit(main())
