#!/usr/bin/env python3
# Non-mutating Marketplace browser smoke helper. Default is dry-run.
from __future__ import annotations
import argparse, shutil, subprocess, sys
MARKETPLACE_URLS = ['https://www.facebook.com/marketplace/', 'https://www.facebook.com/marketplace/inbox/']
def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', action='store_true', help='open non-mutating Marketplace pages with browser-use if available')
    ap.add_argument('--dry-run', action='store_true', help='print planned checks only')
    args = ap.parse_args()
    dry = args.dry_run or not args.live
    browser_use = shutil.which('browser-use')
    browser_harness = shutil.which('browser-harness')
    print(f'browser-use: {browser_use or "not found"}')
    print(f'browser-harness: {browser_harness or "not found"}')
    print('mode:', 'dry-run' if dry else 'live non-mutating')
    if browser_use:
        print('browser-use doctor exit:', run([browser_use, 'doctor']).returncode)
    if browser_harness:
        print('browser-harness doctor exit:', run([browser_harness, '--doctor']).returncode)
    print('planned URLs:')
    for url in MARKETPLACE_URLS:
        print('-', url)
    if dry:
        print('OK: dry-run completed without opening Facebook')
        return 0
    if not browser_use:
        print('FAIL: live mode requires browser-use on PATH')
        return 1
    print('Opening Marketplace home in browser-use. This is read-only.')
    print('open exit:', run([browser_use, 'open', MARKETPLACE_URLS[0]]).returncode)
    state = run([browser_use, 'state'])
    print('state exit:', state.returncode)
    if state.returncode == 0:
        print('OK: browser-use state returned successfully; output suppressed for privacy')
        return 0
    print('FAIL: browser-use state failed')
    return 1
if __name__ == '__main__':
    sys.exit(main())
