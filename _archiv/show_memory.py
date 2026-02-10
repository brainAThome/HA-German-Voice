#!/usr/bin/env python3
import json
with open('/config/conversation_memory.json') as f:
    d = json.load(f)
print('=== GESPEICHERTE GESPRÄCHE ===')
print(f"Total: {d['stats']['total_count']}, Gespeichert: {len(d['conversations'])}/500")
print()
for c in d['conversations'][:25]:
    print(f"{c['timestamp']} | {c['intent']:20} | {c['input'][:45]}...")
