#!/usr/bin/env python3
import json
m = json.load(open('/config/conversation_memory.json'))

# Get conversations after restart
new_convs = [c for c in m['conversations'] if c['timestamp'] > '2026-02-10 15:33:00']

print('=== NEUE TESTS NACH RESTART ===')
success = [c for c in new_convs if c.get('success', True)]
failed = [c for c in new_convs if not c.get('success', True)]

print(f'Erfolgreich: {len(success)}')
for c in success:
    print(f'  OK: "{c["input"]}" -> {c.get("intent", "?")}')

print(f'\nFehlgeschlagen: {len(failed)}')
for c in failed:
    resp = c.get('response', '')[:50]
    print(f'  X: "{c["input"]}"')
    print(f'     -> {resp}')
