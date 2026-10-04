#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开源安全与隐私检查（跨平台，CI 与本地都能跑）。

用法：
    python tests/safety_check.py

检查项：
  1. dashboard.html 内不得出现真实公司名（防止把个人投递数据带进公开仓库）
  2. 个人台账 data/ledger.json 不得被 git 跟踪
  3. 被跟踪的文本文件里不得出现个人身份信息（通用规则 + 可选的本地 .pii-patterns）
  4. 示例数据里的公司名必须是虚构的
"""
import io
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 真实公司名黑名单（出现在看板里说明个人数据泄漏了）
REAL_COMPANIES = [
    '阿里巴巴', '蚂蚁集团', '蚂蚁数科', '字节跳动', '腾讯', '百度', '美团', '京东',
    '拼多多', '快手', '小红书', '哔哩哔哩', '携程', '同花顺', '得物', '海康威视',
    '商汤', '旷视', '云从', '依图', '第四范式', '毫末智行', '元戎启行', '宇树',
    '优必选', '云深处', '华为', '中兴', '紫光展锐', '大华股份', '中控技术',
    '传化智联', '吉利汽车', '零跑汽车', '哪吒汽车', '涂鸦智能', '智谱',
    '月之暗面', '零一万物', '百川智能', '阶跃星辰', '面壁智能', '淘天集团',
]

# Generic personal-identifier patterns (safe to publish: they describe shapes, not values)
PII_PATTERNS = [
    (r'1[3-9]\d{9}', 'phone number'),
    (r'[\w.+-]+@(qq|163|126|gmail|outlook|foxmail)\.com', 'personal email'),
    (r'\b\d{17}[\dXx]\b', 'ID card number'),
]

# Your own private strings (name, school, employer…) belong in a LOCAL, gitignored file:
#   .pii-patterns   — one literal per line, '#' for comments
# See .pii-patterns.example. Nothing from that file is ever committed.
PII_FILE = os.path.join(HERE, '.pii-patterns')


def local_pii_patterns():
    out = []
    if os.path.exists(PII_FILE):
        try:
            for line in io.open(PII_FILE, encoding='utf-8'):
                v = line.strip()
                if v and not v.startswith('#'):
                    out.append((re.escape(v), 'local rule #%d' % (len(out) + 1)))
        except Exception:
            pass
    return out

# 允许出现真实公司名的地方（黑名单守卫本身、示例数据的虚构声明）
ALLOWLIST_FILES = {
    'tests/safety_check.py',
    'tests/dashboard.test.js',
    '.github/workflows/ci.yml',
    'CONTRIBUTING.md',
    'SECURITY.md',
}

ok, bad = [], []


def check(name, cond, extra=''):
    (ok if cond else bad).append(name + ((' -> ' + str(extra)) if extra else ''))
    print('  %s %s%s' % ('[OK]  ' if cond else '[FAIL]', name, ((' -> ' + str(extra)) if extra else '')))


def tracked_files():
    try:
        out = subprocess.check_output(['git', 'ls-files'], cwd=HERE).decode('utf-8')
        return [f for f in out.split('\n') if f.strip()]
    except Exception:
        # 不是 git 仓库时退化为遍历（跳过 .git）
        files = []
        for root, dirs, names in os.walk(HERE):
            if '.git' in root.split(os.sep):
                continue
            for n in names:
                files.append(os.path.relpath(os.path.join(root, n), HERE).replace(os.sep, '/'))
        return files


def read_text(rel):
    p = os.path.join(HERE, rel.replace('/', os.sep))
    if not os.path.isfile(p):
        return None
    try:
        return io.open(p, encoding='utf-8').read()
    except Exception:
        return None


# GitHub UI paths that are valid on github.com but not local files
GH_ONLY = re.compile(r'^(\.\./)+(issues|releases|security|pulls|discussions|compare|graphs|actions|wiki|blob|tree)(/|$)')


def main():
    files = tracked_files()
    print('Checking %d files\n' % len(files))

    # 1. 看板内不得含真实公司名
    dash = read_text('dashboard.html') or ''
    leaked = [c for c in REAL_COMPANIES if c in dash]
    check('No real company names inside dashboard.html', not leaked, ','.join(leaked))

    # 2. 个人台账不得被跟踪
    check('data/ledger.json is not tracked by git', 'data/ledger.json' not in files)

    # 3. 被跟踪文本文件不得含个人身份信息
    pii_hits = []
    for rel in files:
        if rel in ALLOWLIST_FILES or rel.endswith(('.png', '.jpg', '.pdf', '.ico')):
            continue
        text = read_text(rel)
        if text is None:
            continue
        for pattern, label in PII_PATTERNS + local_pii_patterns():
            if re.search(pattern, text):
                pii_hits.append('%s(%s)' % (rel, label))
    check('No personal identifiers in tracked files', not pii_hits, ', '.join(pii_hits[:5]))

    # 4. 示例数据必须是虚构公司
    sample = read_text('data/sample-ledger.json') or ''
    sample_real = [c for c in REAL_COMPANIES if c in sample]
    check('No real company names in the sample data', not sample_real, ','.join(sample_real))

    # 5. 备份与临时文件不得被跟踪
    junk = [f for f in files if f.startswith('data/.backup/') or f.endswith(('.tmp', '.pyc'))]
    check('No backup/temp files tracked', not junk, ', '.join(junk[:5]))

    # 6. README defaults to Chinese; the English one is kept alongside
    readme_zh = read_text('README.md') or ''
    readme_en = read_text('README.en.md')
    check('README.md is the Chinese one (default view)', bool(re.search(r'[\u4e00-\u9fff]', readme_zh)))
    check('README.en.md exists and is English', readme_en is not None and bool(re.search(r'[A-Za-z]', readme_en)))

    # 7. relative Markdown links must resolve (catches dead links after renames)
    broken = []
    for rel in files:
        if not rel.endswith('.md'):
            continue
        text = read_text(rel)
        if text is None:
            continue
        base_dir = os.path.dirname(rel)
        for m in re.finditer(r'\]\(([^)\s]+)\)', text):
            target = m.group(1).split('#')[0].strip()
            if not target or '://' in target or target.startswith('mailto:'):
                continue
            # GitHub-only relative links (../../issues, ../../releases, ...) are not local files
            if GH_ONLY.match(target):
                continue
            p2 = os.path.normpath(os.path.join(HERE, base_dir, target))
            if not os.path.exists(p2):
                broken.append('%s -> %s' % (rel, target))
    check('relative Markdown links resolve', not broken, ', '.join(sorted(set(broken))[:5]))

    print('\n%d passed, %d failed' % (len(ok), len(bad)))
    if bad:
        for b in bad:
            print('  [FAIL] ' + b)
        return 1
    print('Safety check passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
