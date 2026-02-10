#!/usr/bin/env python3
"""Add rollo aliases to entity registry"""
import json

# Load registry
with open('/config/.storage/core.entity_registry', 'r') as f:
    reg = json.load(f)

# Find and update cover entities
updated = 0
for entity in reg['data']['entities']:
    eid = entity.get('entity_id', '')
    
    # Seitliches Rollo
    if 'seitliches_schlafzimmerrollo' in eid:
        new_aliases = ['Seitenrollo', 'Seitenrollo im Schlafzimmer', 'Seitliche Schlafzimmerrollo', 'seitliches Schlafzimmerrollo', 'Schlafzimmerseitenrollo']
        entity['aliases'] = list(set(entity.get('aliases', []) + new_aliases))
        updated += 1
        print(f"Updated {eid}: {entity['aliases']}")
        
    # Vorderes/Front Rollo  
    if 'vorderes_schlafzimmerrollo' in eid and entity.get('entity_category') is None:
        new_aliases = ['Frontrollo im Schlafzimmer', 'Schlafzimmer Frontrollo', 'Vordere Schlafzimmerrollo', 'Frontrollo', 'Balkonrollo']
        entity['aliases'] = list(set(entity.get('aliases', []) + new_aliases))
        updated += 1
        print(f"Updated {eid}: {entity['aliases']}")

# Save
with open('/config/.storage/core.entity_registry', 'w') as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)
    
print(f"\nTotal updated: {updated} entities")
print("Restart HA to apply changes!")
