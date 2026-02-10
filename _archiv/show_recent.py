#!/usr/bin/env python3
import json
m = json.load(open('/config/conversation_memory.json'))
print('=== LETZTE 20 GESPRÄCHE ===')
for c in m['conversations'][:20]:
    status = 'OK' if c.get('success', True) else 'FAIL'
    intent = c.get('intent', 'FAILED') or 'FAILED'
    print(f'{status:4} | {c["timestamp"]} | {intent:22} | {c["input"]}')
