#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT = Path(__file__).resolve().parents[1]
errors = []
secret_patterns = [re.compile(r'(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[A-Za-z0-9_\-]{12,}'), re.compile(r'AIza[0-9A-Za-z_\-]{20,}'), re.compile(r'sk-[A-Za-z0-9]{20,}'), re.compile(r'ghp_[A-Za-z0-9]{20,}')]
phone_pattern = re.compile(r'(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)')
email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
for path in ROOT.rglob('*'):
    if any(part in {'.git','__pycache__'} for part in path.parts) or not path.is_file():
        continue
    if path.suffix.lower() not in {'.md','.py','.txt','.yaml','.yml','.json'} and path.name != 'README.md':
        continue
    text = path.read_text(errors='replace')
    rel = path.relative_to(ROOT)
    for pat in secret_patterns:
        if pat.search(text):
            errors.append(f'{rel}: possible secret/token pattern')
    if str(rel).startswith('examples/'):
        if phone_pattern.search(text):
            errors.append(f'{rel}: real-looking phone number in example')
        emails = [e for e in email_pattern.findall(text) if not e.endswith('@example.com')]
        if emails:
            errors.append(f'{rel}: real-looking email in example')
if errors:
    print('FAIL')
    for e in errors:
        print('-', e)
    sys.exit(1)
print('OK: no obvious secrets, credentials, or real contact data found in checked files')
