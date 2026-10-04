"""Export a dated, read-only view of the vault task list for the HUD."""
import json, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
VAULT = ROOT.parents[2]
source = VAULT / 'Active Priorities.md'
section = 'Other'
tasks = []
for line in source.read_text(encoding='utf-8-sig').splitlines():
    if line.startswith('### Completed Tasks'):
        break
    if line.startswith('**'):
        section = line.strip('*').split(' — ')[0]
    if line.startswith('- [ ] '):
        body = line[6:].strip()
        body = re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', lambda m: m[2] or m[1], body)
        body = body.replace('**', '').replace('`', '')
        tasks.append({'id': f'task-{len(tasks)+1}', 'business': section, 'text': body})
payload = {'source': 'Active Priorities.md', 'capturedAt': datetime.now(timezone.utc).isoformat(), 'sourceModifiedAt': datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(), 'tasks': tasks}
(ROOT / 'snapshot.js').write_text('window.DRAEVEN_SNAPSHOT = ' + json.dumps(payload, ensure_ascii=False) + ';\n', encoding='utf-8')
print(f'Exported {len(tasks)} open task records; source unchanged.')
