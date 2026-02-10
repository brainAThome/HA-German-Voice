#!/usr/bin/env python3
"""Set entity aliases in registry while HA is stopped."""
import json

# Aliases to add
ALIASES = {
    "light.buro": ["Bürolicht", "Licht im Büro", "Büro Licht", "Arbeitszimmerlicht"],
    "cover.shelly_relais_vorderes_schlafzimmerrollo_shelly_relais_vorderes_schlafzimmerrollo": [
        "Frontrollo", "Frontrollo im Schlafzimmer", "Schlafzimmer Frontrollo",
        "Vordere Schlafzimmerrollo", "Vorderes Schlafzimmerrollo", 
        "Balkonrollo", "Schlafzimmer Balkonrollo", "vorderes Schlafzimmerrollo"
    ],
    "cover.shelly_relais_seitliches_schlafzimmerrollo": [
        "Seitenrollo", "Seitenrollo im Schlafzimmer", "Schlafzimmerseitenrollo",
        "Seitliche Schlafzimmerrollo", "seitliches Schlafzimmerrollo"
    ],
    "cover.rollos_wohnzimmer": [
        "Wohnzimmerrollos", "Rollos im Wohnzimmer", "Großes Wohnzimmerrollo", 
        "Wohnzimmer Rollo", "große Wohnzimmerrollo", "großes Wohnzimmerrollo",
        "große Wohnzimmer Rollo", "großes Wohnzimmer Rollo"
    ],
    "cover.shelly_relais_kleines_wohnzimmerrollo": [
        "Kleines Wohnzimmerrollo", "kleines Wohnzimmerrollo", "kleine Wohnzimmerrollo",
        "Kleines Wohnzimmer Rollo", "kleines Wohnzimmer Rollo",
        "Wohnzimmer kleines Rollo", "Wohnzimmerrollo klein"
    ],
    "cover.grosseswohnzimmerrollo": [
        "Großes Wohnzimmerrollo", "großes Wohnzimmerrollo", "große Wohnzimmerrollo",
        "große Wohnzimmer Rollo", "großes Wohnzimmer Rollo"
    ]
}

# Load registry
with open('/config/.storage/core.entity_registry', 'r') as f:
    reg = json.load(f)

updated = 0
for entity in reg['data']['entities']:
    eid = entity.get('entity_id', '')
    if eid in ALIASES:
        existing = entity.get('aliases', [])
        new_aliases = list(set(existing + ALIASES[eid]))
        entity['aliases'] = new_aliases
        updated += 1
        print(f"OK {eid}: {new_aliases}")

# Save
with open('/config/.storage/core.entity_registry', 'w') as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)

print(f"\nUpdated {updated} entities")
