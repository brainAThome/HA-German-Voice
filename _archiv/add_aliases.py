#!/usr/bin/env python3
"""
Add aliases to entities in Home Assistant exposed_entities
"""
import json

# Aliase Definition: entity_id -> [alias1, alias2, ...]
ALIASES = {
    "light.h61a2_d4ea": [  # Wandlicht
        "Wand Licht",
        "Wandlampe",
        "Wand Lampe",
        "Licht an der Wand",
        "Wadenlicht",  # Spracherkennungsfehler
        "Wandel Licht",  # Spracherkennungsfehler
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
    # Read exposed_entities
    with open("/config/.storage/homeassistant.exposed_entities", "r") as f:
        data = json.load(f)
    
    exposed = data.get("data", {}).get("exposed_entities", {})
    
    for entity_id, aliases in ALIASES.items():
        if entity_id not in exposed:
            exposed[entity_id] = {"assistants": {"conversation": {"should_expose": True}}}
        
        # Add aliases
        if "assistants" not in exposed[entity_id]:
            exposed[entity_id]["assistants"] = {}
        if "conversation" not in exposed[entity_id]["assistants"]:
            exposed[entity_id]["assistants"]["conversation"] = {}
        
        exposed[entity_id]["assistants"]["conversation"]["aliases"] = aliases
        print(f"Added aliases for {entity_id}: {aliases}")
    
    data["data"]["exposed_entities"] = exposed
    
    # Write back
    with open("/config/.storage/homeassistant.exposed_entities", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("Done! Restart Home Assistant to apply changes.")

if __name__ == "__main__":
    add_aliases()
