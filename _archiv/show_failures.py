#!/usr/bin/env python3
import json
m = json.load(open('/config/conversation_memory.json'))
total = len(m['conversations'])
success = sum(1 for c in m['conversations'] if c.get('success', True))
failed = total - success
print(f'=== MEMORY STATS ===')
print(f'Total: {total}')
print(f'Erfolgreich: {success}')
print(f'FEHLGESCHLAGEN: {failed}')
print()
print('=== FEHLGESCHLAGENE ERKENNUNGEN ===')
count = 0
for c in m['conversations']:
    if not c.get('success', True):
        count += 1
        resp = c["response"][:60] + "..." if len(c["response"]) > 60 else c["response"]
        print(f'{count:2}. "{c["input"]}"')
        print(f'    -> {resp}')
        print()
