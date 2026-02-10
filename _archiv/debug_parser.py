#!/usr/bin/env python3
"""Debug conversation parsing"""
import re
import subprocess
import json
from datetime import datetime

# Get logs
result = subprocess.run(['ha', 'core', 'logs', '--lines', '500'], capture_output=True, text=True, timeout=60)
ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
logs = ansi_escape.sub('', result.stdout)

# Join lines
lines = logs.split('\n')
joined = []
curr = ''
for l in lines:
    if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', l):
        if curr: joined.append(curr)
        curr = l
    else:
        curr += ' ' + l.strip()
if curr: joined.append(curr)
cleaned = '\n'.join(joined)

# Patterns
up = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*UserContent.*content='([^']+)'"
tp = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*ToolResultContent.*tool_name='(\w+)'.*'speech': '([^']+)'"

um = list(re.finditer(up, cleaned))
tm = list(re.finditer(tp, cleaned))

print(f'User: {len(um)}, Tool: {len(tm)}')

# Load memory
with open('/config/conversation_memory.json') as f:
    mem = json.load(f)
existing_keys = set((c['timestamp'], c['input'][:30]) for c in mem['conversations'])
print(f'Existing keys: {len(existing_keys)}')

# Check each parsed
matched = []
for u in um:
    uts = datetime.strptime(u.group(1), '%Y-%m-%d %H:%M:%S')
    txt = u.group(2)
    for t in tm:
        tts = datetime.strptime(t.group(1), '%Y-%m-%d %H:%M:%S')
        diff = (tts - uts).total_seconds()
        if 0 <= diff < 5:  # Include same-second matches
            matched.append((u.group(1), txt, t.group(2)))
            break

print(f'Matched pairs: {len(matched)}')
for m in matched:
    key = (m[0], m[1][:30])
    dup = key in existing_keys
    print(f"  {m[0]} - {m[1][:40]}... -> {m[2]} dup={dup}")
