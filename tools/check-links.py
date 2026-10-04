#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检测台账里所有投递链接的可访问性，把结果写回 JSON。

用法：
    python tools/check-links.py
    python tools/check-links.py --data data/ledger.json

写回字段：链接状态 / 链接原始码 / 链接检测日期 / 链接最终URL（跳转后不同才写）

注意：脚本在受限网络（公司代理/沙箱）下运行时，大量失败可能是「代理隧道失败」而非网站不可用，
因此状态分三类：可访问 / 真问题(404·域名解析失败) / 待确认(环境受限·超时·SSL)。
在能正常上网的机器上运行结果最准确。
"""
import argparse
import datetime
import io
import json
import os
import socket
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


# Windows 控制台可能是 GBK / cp1252，直接打印中文会抛 UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
TIMEOUT = 15


def probe(url):
    if not url or not url.strip():
        return ('无链接', '', '')
    url = url.strip()
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            r.read(4096)
            return (str(r.status), r.geturl(), '')
    except urllib.error.HTTPError as e:
        return (str(e.code), url, 'HTTPError')
    except urllib.error.URLError as e:
        reason = getattr(e, 'reason', e)
        text = str(reason)
        if isinstance(reason, socket.timeout) or 'timed out' in text.lower():
            return ('超时', url, text[:80])
        if any(k in text for k in ('Name or service not known', 'getaddrinfo', 'nodename')):
            return ('DNS失败', url, text[:80])
        return ('连接失败', url, text[:80])
    except socket.timeout:
        return ('超时', url, 'timeout')
    except Exception as e:
        return ('异常', url, type(e).__name__)


def classify(code, note):
    if code.startswith('2') or code.startswith('3'):
        return '可访问'
    if code == '无链接':
        return '无链接'
    if code == '404':
        return '真问题·404'
    if code == 'DNS失败':
        return '真问题·域名解析失败'
    if code in ('401', '403'):
        return '需人工确认·' + code
    if 'CERTIFICATE_VERIFY_FAILED' in note or 'SSL' in note or 'TLS' in note:
        return '待确认·SSL证书'          # 代理中间人也会导致证书校验失败
    if 'Tunnel connection failed' in note or '502' in note or '503' in note:
        return '待确认·环境受限'
    if code == '超时':
        return '待确认·超时'
    return '待确认·' + code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=os.path.join('data', 'ledger.json'))
    args = ap.parse_args()
    path = args.data if os.path.isabs(args.data) else os.path.join(HERE, args.data)
    if not os.path.exists(path):
        sys.exit('Ledger file not found: %s' % path)

    data = json.load(io.open(path, encoding='utf-8'))
    apps = data['applications']
    today = datetime.date.today().isoformat()

    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(lambda a: probe(a.get('投递链接', '')), apps))

    tally = {}
    for a, (code, final, note) in zip(apps, results):
        label = classify(code, note)
        a['链接状态'] = label
        a['链接原始码'] = code
        a['链接检测日期'] = today
        if final and final.rstrip('/') != (a.get('投递链接', '') or '').rstrip('/'):
            a['链接最终URL'] = final
        else:
            a.pop('链接最终URL', None)
        tally[label] = tally.get(label, 0) + 1

    json.dump(data, io.open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print('Checked %d links:' % len(apps))
    for k, v in sorted(tally.items(), key=lambda kv: -kv[1]):
        print('  %-20s %d' % (k, v))
    bad = [(a['企业'], classify(c, n), a.get('投递链接', ''))
           for a, (c, f, n) in zip(apps, results)
           if classify(c, n).startswith('真问题')]
    if bad:
        print('\nNeeds attention:')
        for co, label, url in bad:
            print('  %-14s %-22s %s' % (co, label, url))


if __name__ == '__main__':
    main()
