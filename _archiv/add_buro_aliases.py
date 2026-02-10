#!/usr/bin/env python3
"""Add aliases for Bürolicht and fix Rollo grammar variants"""
import json

# Load registry
with open('/config/.storage/core.entity_registry', 'r') as f:
    reg = json.load(f)

updated = 0
for entity in reg['data']['entities']:
    eid = entity.get('entity_id', '')
    
    # Bürolicht
    if eid == 'light.buro':
        new_aliases = ['Bürolicht', 'Licht im Büro', 'Büro Licht', 'Arbeitszimmerlicht']
        entity['aliases'] = list(set(entity.get('aliases', []) + new_aliases))
        updated += 1
        print(f"Updated {eid}: {entity['aliases']}")
    
    # Vorderes Rollo - add grammar variant "Vordere" (without 's')
    if 'vorderes_schlafzimmerrollo' in eid and entity.get('entity_category') is None:
        new_aliases = ['Vordere Schlafzimmerrollo']  # Grammar variant
        entity['aliases'] = list(set(entity.get('aliases', []) + new_aliases))
        updated += 1
        print(f"Updated {eid}: {entity['aliases']}")

# Save
with open('/config/.storage/core.entity_registry', 'w') as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)

print(f"\nTotal updated: {updated} entities")
