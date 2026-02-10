#!/usr/bin/env python3
"""
Add aliases to entities in Home Assistant entity_registry
"""
import json

# Aliase Definition: entity_id -> [alias1, alias2, ...]
ALIASES = {
    "light.h61a2_d4ea": [  # Wandlicht
        "Wand Licht",
        "Wandlampe",
        "Wand Lampe",
        "Licht an der Wand",
        "Wadenlicht",
        "Wandel Licht",
    ],
    "light.buro": [  # Iris im Buero
        "Iris Lampe",
        "Buerolicht",
        "Buero Licht",
    ],
    "light.h6066_1c22": [  # Monitorwand (Govee Hexagons)
        "Monitor Wand",
        "Monitore",
        "Hexagon Licht",
        "Hexagons",
    ],
}

def add_aliases():
    # Read entity_registry
    with open("/config/.storage/core.entity_registry", "r") as f:
        data = json.load(f)
    
    entities = data.get("data", {}).get("entities", [])
    
    for entity in entities:
        entity_id = entity.get("entity_id")
        if entity_id in ALIASES:
            # Merge existing aliases with new ones
            existing = set(entity.get("aliases", []))
            new_aliases = set(ALIASES[entity_id])
            entity["aliases"] = list(existing | new_aliases)
            print(f"Updated {entity_id}: {entity['aliases']}")
    
    # Write back
    with open("/config/.storage/core.entity_registry", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("Done!")

if __name__ == "__main__":
    add_aliases()
