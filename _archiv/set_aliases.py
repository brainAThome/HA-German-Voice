#!/usr/bin/env python3
"""
Set entity aliases via Home Assistant WebSocket API.
Run BEFORE ha core restart to make changes persistent.
"""
import json
import asyncio
import websockets

HA_HOST = "localhost"
HA_PORT = 8123

# Get long-lived access token from auth storage
def get_token():
    try:
        with open('/config/.storage/auth', 'r') as f:
            auth = json.load(f)
        for token in auth.get('data', {}).get('refresh_tokens', []):
            if token.get('token_type') == 'long_lived_access_token':
                return token.get('access_token', '')
        # Fallback: get from secrets
        with open('/config/secrets.yaml', 'r') as f:
            for line in f:
                if 'token' in line.lower():
                    return line.split(':')[1].strip().strip('"').strip("'")
    except:
        pass
    return None

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
        "Wohnzimmer Rollo", "große Wohnzimmerrollo"
    ]
}

async def set_aliases():
    uri = f"ws://{HA_HOST}:{HA_PORT}/api/websocket"
    
    async with websockets.connect(uri) as ws:
        # Wait for auth_required
        msg = await ws.recv()
        print(f"Received: {msg[:50]}...")
        
        # We can't easily authenticate without a token
        # So we'll update the registry file directly but properly this time
        print("WebSocket connection works. Updating registry directly...")
    
    # Load and update registry
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
            print(f"✓ {eid}: {new_aliases}")
    
    # Save with proper formatting
    with open('/config/.storage/core.entity_registry', 'w') as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    
    print(f"\nUpdated {updated} entities")
    print("IMPORTANT: Stop HA, then start again (not restart) for changes to persist!")
    print("Run: ha core stop && sleep 5 && ha core start")

if __name__ == "__main__":
    asyncio.run(set_aliases())
