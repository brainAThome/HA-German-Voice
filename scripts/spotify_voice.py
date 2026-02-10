#!/usr/bin/env python3
"""
Spotify Voice Control f├╝r Home Assistant
=========================================
Sucht und spielt Musik ├╝ber die Spotify Web API.
Wird als shell_command von HA aufgerufen.

Verwendet nur Python-Standardbibliotheken (urllib, json) -
keine externen Abh├ñngigkeiten n├Âtig.

Verwendung:
  python3 spotify_voice.py --action search_play --query "Highway to Hell" --type track
  python3 spotify_voice.py --action search_play --query "AC/DC" --type artist
  python3 spotify_voice.py --action search_play --query "Rock Classics" --type playlist
  python3 spotify_voice.py --action device --device "HAL"
"""

import sys
import json
import argparse
import time
import socket
import struct
import urllib.request
import urllib.parse
import urllib.error

# ============================================================================
# KONFIGURATION - ANPASSEN AN DEINE INSTALLATION
# ============================================================================
HA_API = "http://localhost:8123/api"
# HA Long-Lived Access Token
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiIwZWJmMDhlZDk2MTc0MzRmOGRkOWRiNmIyMjhlNDAxOCIsImlhdCI6MTc3MDczNzA5NywiZXhwIjoyMDg2MDk3MDk3fQ.0l4LR5It8sfovVQKeFlfx0Thi_ZKw4ThMeY_EU7gIxA"
# Pfad zur HA Storage-Datei
STORAGE_PATH = "/config/.storage/core.config_entries"
# Spotify Entity in HA
SPOTIFY_ENTITY = "media_player.spotify_sven"
# Jarvis = VACA Echo Show 5 (2nd Gen) mit Spotify-App
# Spotify Connect Name des Ger├ñts (wie es in der Spotify Device-Liste erscheint)
JARVIS_SPOTIFY_NAME = "Echo Show 5 (2nd Generation)"
# ADB-Adresse f├╝r Spotify-App-Wakeup (falls App geschlossen)
JARVIS_ADB_HOST = "192.168.178.103"
JARVIS_ADB_PORT = 5555
# Spotify App Credentials (aus HA Application Credentials)
CLIENT_ID = "c1c5aa30a5cd4954854e16d0a9c2228e"
CLIENT_SECRET = "16947c1cae2f44919a31f0cdc7c76182"
# Spotify Markt f├╝r Suchergebnisse
MARKET = "DE"

# View Assist Navigation (Music Card auf Jarvis-Display)
VA_DEVICE = "sensor.quasselbuechse"      # View Assist Entity f├╝r Navigation
VA_MUSIC_PATH = "/view-assist/music"     # Pfad zur Music-View
VA_HOME_PATH = "/view-assist/clock"      # Pfad zur Startseite (Uhr)


# ============================================================================
# HTTP HELPER (urllib-basiert, kein requests n├Âtig)
# ============================================================================

def http_get(url, headers=None, params=None, timeout=10):
    """HTTP GET mit urllib."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return {"error": body}, e.code
    except Exception as e:
        return {"error": str(e)}, 0


def http_post(url, headers=None, data=None, json_data=None, timeout=10):
    """HTTP POST mit urllib."""
    if json_data is not None:
        body = json.dumps(json_data).encode("utf-8")
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
    elif data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        body = None

    req = urllib.request.Request(url, data=body, method="POST")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return {"error": body}, e.code
    except Exception as e:
        return {"error": str(e)}, 0


def http_put(url, headers=None, json_data=None, timeout=10):
    """HTTP PUT mit urllib."""
    body = json.dumps(json_data).encode("utf-8") if json_data else b""
    if headers is None:
        headers = {}
    headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, method="PUT")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}, resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return {"error": body}, e.code
    except Exception as e:
        return {"error": str(e)}, 0


# ============================================================================
# SPOTIFY TOKEN MANAGEMENT
# ============================================================================

def get_spotify_token():
    """Liest den Spotify Access Token aus der HA-Storage.
    Erneuert ihn automatisch, falls abgelaufen."""
    try:
        with open(STORAGE_PATH, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR:Storage nicht lesbar: {e}")
        return None

    for entry in data.get("data", {}).get("entries", []):
        if entry.get("domain") == "spotify":
            token_data = entry.get("data", {}).get("token", {})
            access_token = token_data.get("access_token")
            expires_at = token_data.get("expires_at", 0)
            refresh_token = token_data.get("refresh_token")

            # Token noch g├╝ltig? (30s Puffer)
            if expires_at > time.time() + 30:
                return access_token

            # Token erneuern
            if refresh_token:
                return refresh_spotify_token(refresh_token)

            print("ERROR:Kein Refresh Token vorhanden")
            return None

    print("ERROR:Keine Spotify-Konfiguration gefunden")
    return None


def refresh_spotify_token(refresh_token):
    """Erneuert den Spotify Access Token."""
    result, status = http_post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    if status == 200:
        return result.get("access_token")
    print(f"ERROR:Token-Erneuerung fehlgeschlagen ({status})")
    return None


# ============================================================================
# SPOTIFY API CALLS
# ============================================================================

def spotify_headers(token):
    return {"Authorization": f"Bearer {token}"}


def search_spotify(token, query, content_type="track", limit=1):
    """Sucht auf Spotify nach dem angegebenen Typ."""
    result, status = http_get(
        "https://api.spotify.com/v1/search",
        headers=spotify_headers(token),
        params={
            "q": query,
            "type": content_type,
            "limit": str(limit),
            "market": MARKET,
        },
    )
    if status == 200:
        return result
    print(f"ERROR:Suche fehlgeschlagen ({status})")
    return None


def get_spotify_devices(token):
    """Listet alle verf├╝gbaren Spotify Connect Ger├ñte."""
    result, status = http_get(
        "https://api.spotify.com/v1/me/player/devices",
        headers=spotify_headers(token),
    )
    if status == 200:
        return result.get("devices", [])
    return []


def find_device(token, device_name):
    """Findet ein Ger├ñt anhand des Namens (case-insensitive, partial match)."""
    devices = get_spotify_devices(token)
    device_name_lower = device_name.lower()

    # Exakter Match zuerst
    for dev in devices:
        if dev["name"].lower() == device_name_lower:
            return dev

    # Partial Match
    for dev in devices:
        if device_name_lower in dev["name"].lower():
            return dev

    # Alias-Map f├╝r h├ñufige deutsche Bezeichnungen
    # Ôû║ ANPASSEN: Trage hier deine Ger├ñte-Aliase ein
    alias_map = {
        "echo show": "Echo Show 5 (2nd Generation)",
        "echo show 5": "Echo Show 5 (2nd Generation)",
        "jarvis": "Echo Show 5 (2nd Generation)",
        "wohnzimmer": "Echo Show 5 (2nd Generation)",
        "echo dot": "Thorins Echo Dot",
        "echo pop": "Svens Echo Pop",
        "echo spot": "Svens Echo Spot",
        "hal": "HAL",
        "computer": "HAL",
        "pc": "HAL",
        "familienzimmer": "Familienzimmer",
        "yamaha": "Familienzimmer",
        "eingang": "Echo Show Eingangsbereich",
        "eingangsbereich": "Echo Show Eingangsbereich",
        "thorin": "Thorins Echo Dot",
        "handy": "S24 Ultra von Sven",
        "telefon": "S24 Ultra von Sven",
        "pop": "Svens Echo Pop",
        "spot": "Svens Echo Spot",
    }

    mapped_name = alias_map.get(device_name_lower, "")
    if mapped_name:
        for dev in devices:
            if dev["name"].lower() == mapped_name.lower():
                return dev

    return None


def play_spotify(token, play_payload, device_id=None):
    """Startet Wiedergabe ├╝ber die Spotify Web API."""
    url = "https://api.spotify.com/v1/me/player/play"
    if device_id:
        url += f"?device_id={device_id}"

    _, status = http_put(url, headers=spotify_headers(token), json_data=play_payload)
    return status in (200, 204)


def transfer_playback(token, device_id, play=True):
    """├£bertr├ñgt die Wiedergabe auf ein anderes Ger├ñt."""
    _, status = http_put(
        "https://api.spotify.com/v1/me/player",
        headers=spotify_headers(token),
        json_data={"device_ids": [device_id], "play": play},
    )
    return status in (200, 204)


# ============================================================================
# HA API HELPER
# ============================================================================

def ha_get_state(entity_id):
    """Liest den State eines HA-Entity aus."""
    result, status = http_get(
        f"{HA_API}/states/{entity_id}",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
    )
    if status == 200:
        return result.get("state", "")
    return ""


def ha_set_input_text(entity_id, value):
    """Setzt einen input_text-Wert in Home Assistant."""
    http_post(
        f"{HA_API}/services/input_text/set_value",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data={"entity_id": entity_id, "value": str(value)[:255]},
    )


def ha_navigate(path, revert_timeout=None):
    """Navigiert das Jarvis-Display zu einer View Assist Seite.
    
    Args:
        path: Dashboard-Pfad, z.B. '/view-assist/music'
        revert_timeout: Sekunden bis automatisch zur├╝ck zur vorherigen View.
                        None = View Assist Default (view_timeout, z.B. 20s).
                        Gro├ƒer Wert (z.B. 3600) = bleibt so lange stehen.
    """
    data = {"device": VA_DEVICE, "path": path}
    if revert_timeout is not None:
        data["revert_timeout"] = revert_timeout
    _, status = http_post(
        f"{HA_API}/services/view_assist/navigate",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data=data,
    )
    if status == 200:
        print(f"INFO:Display ÔåÆ {path}")
    return status == 200


# ============================================================================
# ADB HELPER - Spotify auf Jarvis aufwecken (Pure Python, kein adb-Binary n├Âtig)
# ============================================================================

def adb_wake_spotify(host=JARVIS_ADB_HOST, port=JARVIS_ADB_PORT, uri=""):
    """├ûffnet Spotify auf Jarvis per ADB ├╝ber TCP.
    
    Sendet einen minimalen ADB-Shell-Befehl um die Spotify-App zu starten.
    Falls uri angegeben, wird dieser als Intent-Data mitgegeben.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        
        def adb_send(msg):
            """ADB-Protokoll: 4 Hex-Zeichen L├ñnge + Nachricht."""
            data = f"{len(msg):04x}{msg}".encode()
            s.sendall(data)
        
        def adb_recv():
            """Liest ADB-Antwort (OKAY/FAIL + optionale Daten)."""
            resp = s.recv(4096)
            return resp.decode(errors="replace")
        
        # ADB connect handshake
        adb_send(f"host:transport-any")
        resp = adb_recv()
        if "OKAY" not in resp:
            print(f"WARN:ADB transport failed: {resp}")
            s.close()
            return False
        
        # Shell-Befehl senden
        if uri:
            cmd = f"am start -a android.intent.action.VIEW -d '{uri}'"
        else:
            cmd = "monkey -p com.spotify.music -c android.intent.category.LAUNCHER 1"
        
        adb_send(f"shell:{cmd}")
        resp = adb_recv()
        s.close()
        
        if "OKAY" in resp or "Starting" in resp:
            print(f"INFO:ADB Spotify gestartet auf Jarvis")
            return True
        else:
            print(f"WARN:ADB Antwort: {resp[:200]}")
            return False
            
    except Exception as e:
        print(f"WARN:ADB Verbindung fehlgeschlagen: {e}")
        return False


def find_jarvis_device(token):
    """Findet Jarvis (Echo Show 5) in der Spotify Connect Ger├ñteliste."""
    devices = get_spotify_devices(token)
    for dev in devices:
        if dev.get("name") == JARVIS_SPOTIFY_NAME:
            return dev
    return None


def ensure_jarvis_spotify(token, max_retries=2):
    """Stellt sicher dass Spotify auf Jarvis l├ñuft und gibt Device-ID zur├╝ck.
    
    1. Pr├╝fe ob Echo Show 5 in Spotify-Ger├ñteliste
    2. Falls nicht: ├ûffne Spotify per ADB, warte, pr├╝fe nochmal
    """
    dev = find_jarvis_device(token)
    if dev:
        return dev["id"]
    
    print("WARN:Jarvis nicht in Spotify-Ger├ñteliste, wecke Spotify per ADB...")
    adb_wake_spotify()
    
    # Warten bis Spotify Connect sich registriert
    for attempt in range(max_retries):
        time.sleep(4)
        dev = find_jarvis_device(token)
        if dev:
            print(f"INFO:Jarvis gefunden nach {attempt + 1} Versuch(en)")
            return dev["id"]
    
    print("ERROR:Jarvis nach ADB-Wakeup nicht in Spotify-Ger├ñteliste")
    return None


# ============================================================================
# AKTIONEN
# ============================================================================

def action_search_play(token, query, content_type, device_name=""):
    """Sucht nach Musik und spielt das erste Ergebnis."""
    results = search_spotify(token, query, content_type)
    if not results:
        print(f"ERROR:Suche nach '{query}' fehlgeschlagen")
        return False

    # Ergebnisse parsen
    items_key = f"{content_type}s"
    items = results.get(items_key, {}).get("items", [])
    if not items:
        print(f"ERROR:Nichts gefunden f├╝r '{query}'")
        return False

    item = items[0]
    uri = item["uri"]
    name = item.get("name", "Unbekannt")

    # Play-Payload erstellen
    if content_type == "track":
        play_payload = {"uris": [uri]}
        artist = ", ".join(a.get("name", "") for a in item.get("artists", []))
        display = f"{artist} - {name}" if artist else name
    elif content_type == "artist":
        play_payload = {"context_uri": uri}
        display = name
    elif content_type == "album":
        play_payload = {"context_uri": uri}
        artist = ", ".join(a.get("name", "") for a in item.get("artists", []))
        display = f"{artist} - {name}" if artist else name
    elif content_type == "playlist":
        play_payload = {"context_uri": uri}
        display = name
    else:
        play_payload = {"context_uri": uri}
        display = name

    # Jarvis (Echo Show 5) als Spotify Connect Ger├ñt finden/aufwecken
    device_id = ensure_jarvis_spotify(token)
    if not device_id:
        print(f"ERROR:Kann Jarvis nicht als Spotify-Ger├ñt finden")
        return False

    # Abspielen ├╝ber Spotify Web API direkt auf Jarvis
    print(f"INFO:Spiele '{display}' auf Jarvis ab...")
    if play_spotify(token, play_payload, device_id):
        print(f"OK:{display}")
        ha_set_input_text("input_text.spotify_last_played", display)
        ha_navigate(VA_MUSIC_PATH, revert_timeout=3600)  # Music Card bleibt 1h
        return True

    # Fallback: Transfer + Play
    print("WARN:Direktes Play fehlgeschlagen, versuche Transfer...")
    if transfer_playback(token, device_id, play=False):
        time.sleep(1)
        if play_spotify(token, play_payload, device_id):
            print(f"OK:{display} (via Transfer)")
            ha_set_input_text("input_text.spotify_last_played", display)
            ha_navigate(VA_MUSIC_PATH, revert_timeout=3600)  # Music Card bleibt 1h
            return True

    print(f"ERROR:Wiedergabe von '{display}' auf Jarvis fehlgeschlagen")
    return False


def action_device(token, device_name):
    """├£bertr├ñgt die Wiedergabe auf ein Ger├ñt."""
    device = find_device(token, device_name)
    if not device:
        devices = get_spotify_devices(token)
        available = ", ".join(d["name"] for d in devices)
        print(f"ERROR:Ger├ñt '{device_name}' nicht gefunden. Verf├╝gbar: {available}")
        return False

    if transfer_playback(token, device["id"]):
        print(f"OK:{device['name']}")
        return True
    else:
        print(f"ERROR:Transfer zu '{device['name']}' fehlgeschlagen")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Spotify Voice Control f├╝r HA")
    parser.add_argument(
        "--action",
        required=True,
        choices=["search_play", "device", "from_ha"],
        help="Aktion: search_play, device, from_ha (liest input_text aus HA)",
    )
    parser.add_argument("--query", default="", help="Suchbegriff")
    parser.add_argument(
        "--type",
        default="track",
        choices=["track", "artist", "album", "playlist"],
        help="Typ: track, artist, album, playlist",
    )
    parser.add_argument("--device", default="", help="Zielger├ñt (Name)")
    args = parser.parse_args()

    # from_ha: Liest Query/Type/Device direkt aus HA input_text-Entities
    # ÔåÆ Keine Jinja-Templates in shell_command n├Âtig!
    if args.action == "from_ha":
        args.query = ha_get_state("input_text.spotify_query")
        args.type = ha_get_state("input_text.spotify_type") or "track"
        args.device = ha_get_state("input_text.spotify_device")
        args.action = "search_play"
        if not args.query:
            print("ERROR:input_text.spotify_query ist leer")
            sys.exit(1)

    # Token holen
    token = get_spotify_token()
    if not token:
        print("ERROR:Kein Spotify-Token verf├╝gbar")
        sys.exit(1)

    # Aktion ausf├╝hren
    if args.action == "search_play":
        if not args.query:
            print("ERROR:Kein Suchbegriff angegeben")
            sys.exit(1)
        success = action_search_play(token, args.query, args.type, args.device)
    elif args.action == "device":
        if not args.device:
            print("ERROR:Kein Ger├ñt angegeben")
            sys.exit(1)
        success = action_device(token, args.device)
    else:
        print(f"ERROR:Unbekannte Aktion: {args.action}")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
