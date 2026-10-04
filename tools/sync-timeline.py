#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由台账 JSON 生成人读的 Markdown 视图（投递时间线）。

用法：
    python tools/sync-timeline.py
    python tools/sync-timeline.py --data data/ledger.json --out timeline.md
"""
import argparse
import collections
import io
import json
import os
import sys


# Windows 控制台可能是 GBK / cp1252，直接打印中文会抛 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE = ['未投递', '已投递', '综合素质评测', '笔试', '一面', '二面', '三面', 'HR面', 'offer']
TERMINAL = ['已拒', '放弃']
EN = {'未投递': 'Not applied', '已投递': 'Applied', '综合素质评测': 'Aptitude test', '笔试': 'Written test',
      '一面': 'Interview 1', '二面': 'Interview 2', '三面': 'Interview 3', 'HR面': 'HR interview',
      'offer': 'Offer', '已拒': 'Rejected', '放弃': 'Withdrawn'}


def en(s):
    return EN.get(s, s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=os.path.join('data', 'ledger.json'))
    ap.add_argument('--out', default='timeline.md')
    args = ap.parse_args()

    path = args.data if os.path.isabs(args.data) else os.path.join(HERE, args.data)
    out = args.out if os.path.isabs(args.out) else os.path.join(HERE, args.out)
    data = json.load(io.open(path, encoding='utf-8'))
    apps = data['applications']

    def eff(a):
        lst = a.get('岗位列表') or []
        if not lst:
            return a.get('投递状态', '未投递')
        rank = lambda s: -1 if s in TERMINAL else (PIPELINE.index(s) if s in PIPELINE else 0)
        alive = [p for p in lst if p.get('投递状态') not in TERMINAL]
        if not alive:
            return lst[0].get('投递状态', '未投递')
        return max(alive, key=lambda p: rank(p.get('投递状态', '未投递'))).get('投递状态', '未投递')

    L = []
    L.append('# Job application timeline\n')
    L.append('> Generated from the ledger JSON by `tools/sync-timeline.py` — do not edit by hand.\n')

    cnt = collections.Counter(eff(a) for a in apps)
    L.append('## Status overview\n')
    L.append('| Status | Count |')
    L.append('|---|---|')
    for s in PIPELINE + TERMINAL:
        if cnt.get(s):
            L.append('| %s | %d |' % (en(s), cnt[s]))
    L.append('| **Total** | **%d** |\n' % len(apps))

    active = [a for a in apps if a.get('投递日期') and eff(a) != '未投递']
    L.append('## Timeline (newest first)\n')
    if not active:
        L.append('_(no applications yet)_\n')
    else:
        for a in sorted(active, key=lambda x: x['投递日期'], reverse=True):
            L.append('- **%s** · %s（%s）· %s · 简历 %s · %s' % (
                a['投递日期'], a.get('企业', ''), a.get('岗位', ''), en(eff(a)),
                a.get('简历版本') or '—', a.get('渠道') or '—'))
            for r in a.get('面试记录') or []:
                L.append('    - %s｜%s｜%s｜%s' % (r.get('日期', ''), r.get('轮次', ''),
                                                 r.get('结果', ''), r.get('备注', '')))

    L.append('\n## To apply\n')
    for a in apps:
        if eff(a) == '未投递':
            L.append('- [ ] **%s**｜%s｜%s' % (a.get('企业', ''), a.get('岗位', ''), a.get('工作地点', '')))

    io.open(out, 'w', encoding='utf-8').write('\n'.join(L))
    print('Wrote %s (%d companies, %d in progress)' % (os.path.relpath(out, HERE), len(apps), len(active)))


if __name__ == '__main__':
    main()
