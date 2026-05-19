#!/usr/bin/env python3
from pathlib import Path
import re
import sys

try:
    import yaml
except Exception as e:
    print(f"FAIL: PyYAML unavailable: {e}")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
errors = []

skill_files = sorted((ROOT / "skills").rglob("SKILL.md"))
if not skill_files:
    errors.append("No SKILL.md files found under skills/")

for path in skill_files:
    text = path.read_text(errors="replace")
    rel = path.relative_to(ROOT)
    if not text.startswith("---"):
        errors.append(f"{rel}: missing opening frontmatter fence")
        continue
    m = re.search(r"\n---\s*\n", text[3:])
    if not m:
        errors.append(f"{rel}: missing closing frontmatter fence")
        continue
    try:
        fm = yaml.safe_load(text[3:m.start() + 3])
    except Exception as e:
        errors.append(f"{rel}: YAML parse failed: {e}")
        continue
    if not isinstance(fm, dict):
        errors.append(f"{rel}: frontmatter is not a mapping")
        continue
    for key in ("name", "description"):
        if not fm.get(key):
            errors.append(f"{rel}: missing {key}")
    if len(str(fm.get("description", ""))) > 1024:
        errors.append(f"{rel}: description exceeds 1024 chars")

required_paths = [
    "docs/facebook-marketplace-ui-runbook.md",
    "docs/state-management.md",
    "examples/buyer-brief.md",
    "examples/scout-output.md",
    "examples/deal-assessment.md",
    "examples/seller-listing-intake.md",
    "examples/listing-draft.md",
    "examples/inbox-triage-summary.md",
    "examples/heartbeat-update.md",
    "examples/state/deal-state-filled-example.md",
    "examples/state/seller-listing-state-example.md",
    "scripts/sanitize_check.py",
    "scripts/browser_smoke.py",
]
for rel in required_paths:
    if not (ROOT / rel).exists():
        errors.append(f"missing required path: {rel}")

if errors:
    print("FAIL")
    for e in errors:
        print("-", e)
    sys.exit(1)

print(f"OK: validated {len(skill_files)} skill files and required docs/examples/scripts")
