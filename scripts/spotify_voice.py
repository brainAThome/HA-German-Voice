#!/usr/bin/env python3
"""
Spotify Voice Control für Home Assistant (v2 — HA-Integration)
==============================================================
Sucht Musik über Spotify Web API, spielt über HA media_player.

Architektur v2:
- Suche: direkt über Spotify Web API (schnell, volle Kontrolle)
- Wiedergabe: über HA media_player.play_media (kein ADB, kein Device-Polling)
- Device-Transfer: über HA media_player.select_source
- Keep-Alive + Ducking: spotify_monitor.py (separater Daemon)

Kein ADB in diesem Skript — Monitor hält Spotify App am Leben.

Verwendung:
  python3 spotify_voice.py --action search_play --query "Highway to Hell" --type track
  python3 spotify_voice.py --action search_play --query "Rock Classics" --type playlist
  python3 spotify_voice.py --action device --device "HAL"
  python3 spotify_voice.py --action from_ha
"""

import sys
import json
import argparse
import time
import os
import logging
import urllib.request
import urllib.parse
import urllib.error

# Secrets externalisiert — kein Token mehr im Code
from secrets_config import HA_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# ============================================================================
# LOGGING - Datei + Stdout für shell_command
# ============================================================================
LOG_DIR = "/config/logs"
LOG_FILE = os.path.join(LOG_DIR, "spotify_voice.log")
os.makedirs(LOG_DIR, exist_ok=True)

log = logging.getLogger("spotify_voice")
log.setLevel(logging.DEBUG)
# Datei-Handler (detailliert)
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-5s %(message)s"))
log.addHandler(_fh)
# Stdout-Handler (für shell_command Rückgabe an HA)
_sh = logging.StreamHandler(sys.stdout)
_sh.setLevel(logging.INFO)
_sh.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
log.addHandler(_sh)

# ============================================================================
# KONFIGURATION
# ============================================================================
HA_API = "http://localhost:8123/api"
# Pfad zur HA Storage-Datei
STORAGE_PATH = "/config/.storage/core.config_entries"
# Spotify Entity in HA
SPOTIFY_ENTITY = os.getenv("SPOTIFY_ENTITY", "media_player.spotify_sven")
# Spotify Connect Name des Echo Show 5 (wie in HA source_list)
JARVIS_SPOTIFY_NAME = os.getenv("JARVIS_SPOTIFY_NAME", "Echo Show 5 (2nd Generation)")
# Spotify API Credentials (aus secrets_config)
CLIENT_ID = SPOTIFY_CLIENT_ID
CLIENT_SECRET = SPOTIFY_CLIENT_SECRET
# Spotify Markt für Suchergebnisse
MARKET = "DE"
# View Assist Navigation
VA_DEVICE = os.getenv("VA_DEVICE", "sensor.quasselbuechse")
VA_MUSIC_PATH = os.getenv("VA_MUSIC_PATH", "/view-assist/music")
VA_HOME_PATH = os.getenv("VA_HOME_PATH", "/view-assist/clock")

# ANPASSEN: Alias-Map für Geräte-Namen (deutsch → Spotify Connect Name)
# Eigene Spotify Connect Geräte hier eintragen!
DEVICE_ALIAS_MAP = {
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


# ============================================================================
# HTTP HELPER (urllib-basiert, kein requests nötig)
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


def ha_entity_exists(entity_id):
    if not entity_id:
        return False
    _, status = http_get(
        f"{HA_API}/states/{entity_id}",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        timeout=4,
    )
    return status == 200


def ha_list_states():
    data, status = http_get(
        f"{HA_API}/states",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        timeout=8,
    )
    if status == 200 and isinstance(data, list):
        return data
    return []


def autodiscover_entities():
    global SPOTIFY_ENTITY, VA_DEVICE

    if ha_entity_exists(SPOTIFY_ENTITY) and ha_entity_exists(VA_DEVICE):
        return

    states = ha_list_states()
    if not states:
        return

    if not ha_entity_exists(SPOTIFY_ENTITY):
        for item in states:
            entity_id = item.get("entity_id", "")
            if entity_id.startswith("media_player.spotify"):
                log.info("Auto-Discovery: SPOTIFY_ENTITY %s -> %s", SPOTIFY_ENTITY, entity_id)
                SPOTIFY_ENTITY = entity_id
                break

    if not ha_entity_exists(VA_DEVICE):
        for item in states:
            entity_id = item.get("entity_id", "")
            if entity_id.startswith("sensor.") and (
                "quassel" in entity_id.lower() or "vaca" in entity_id.lower() or "display" in entity_id.lower()
            ):
                log.info("Auto-Discovery: VA_DEVICE %s -> %s", VA_DEVICE, entity_id)
                VA_DEVICE = entity_id
                break


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
        log.error("Storage nicht lesbar: %s", e)
        return None

    for entry in data.get("data", {}).get("entries", []):
        if entry.get("domain") == "spotify":
            token_data = entry.get("data", {}).get("token", {})
            access_token = token_data.get("access_token")
            expires_at = token_data.get("expires_at", 0)
            refresh_token = token_data.get("refresh_token")

            # Token noch gültig? (30s Puffer)
            if expires_at > time.time() + 30:
                return access_token

            # Token erneuern
            if refresh_token:
                return refresh_spotify_token(refresh_token)

            log.error("Kein Refresh Token vorhanden")
            return None

    log.error("Keine Spotify-Konfiguration gefunden")
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
        log.info("Spotify-Token erfolgreich erneuert")
        return result.get("access_token")
    log.error("Token-Erneuerung fehlgeschlagen (%s): %s", status, result)
    return None


# ============================================================================
# SPOTIFY SEARCH API
# ============================================================================

def spotify_headers(token):
    return {"Authorization": f"Bearer {token}"}


def search_spotify(token, query, content_type="track", limit=5):
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
    log.error("Suche fehlgeschlagen (%s): %s", status, result)
    return None


def get_user_playlists(token, limit=50):
    """Holt alle Playlists des Users (eigene + gefolgte)."""
    all_playlists = []
    offset = 0
    while True:
        result, status = http_get(
            "https://api.spotify.com/v1/me/playlists",
            headers=spotify_headers(token),
            params={"limit": str(min(limit, 50)), "offset": str(offset)},
        )
        if status != 200:
            break
        items = result.get("items", [])
        if not items:
            break
        all_playlists.extend(items)
        if len(all_playlists) >= limit or not result.get("next"):
            break
        offset += len(items)
    return all_playlists


def _playlist_match_score(query_words, pl_name_lower):
    """Berechnet einen Match-Score zwischen Query-Wörtern und Playlist-Name.

    Returns: (matched_words, score) — höherer Score = besserer Match.
    """
    pl_words = set(pl_name_lower.split())
    matched = sum(1 for w in query_words if w in pl_words)
    if matched == 0:
        return 0, 0.0
    word_ratio = matched / len(query_words)
    brevity_bonus = 1.0 / (1.0 + len(pl_name_lower))
    return matched, word_ratio + brevity_bonus


def find_best_playlist(token, query):
    """Intelligente Playlist-Suche: eigene Playlists zuerst, dann Spotify.

    Reihenfolge:
    1. Exakter Match in eigenen/gefolgten Playlists (case-insensitive)
    2. Substring-Match in eigenen/gefolgten Playlists
    3. Wort-für-Wort Fuzzy-Match (z.B. 'Jump DNB' findet 'JUMP UP DNB')
    4. Bestes Ergebnis aus Spotify-Globalsuche (limit=5)
    """
    query_lower = query.lower().strip()
    query_words = query_lower.split()
    log.debug("Playlist-Suche: '%s' (Wörter: %s)", query, query_words)

    # 1) Eigene/gefolgte Playlists durchsuchen
    user_playlists = get_user_playlists(token)
    log.debug("%d eigene/gefolgte Playlists geladen", len(user_playlists))

    # Exakter Name-Match
    for pl in user_playlists:
        if pl.get("name", "").lower().strip() == query_lower:
            log.info("Playlist exakt gefunden (eigene): '%s'", pl["name"])
            return pl

    # Substring-Match
    partial_matches = []
    for pl in user_playlists:
        pl_name = pl.get("name", "").lower()
        if query_lower in pl_name:
            partial_matches.append(pl)

    if partial_matches:
        best = min(partial_matches, key=lambda p: len(p.get("name", "")))
        log.info("Playlist substring-gefunden (eigene): '%s'", best["name"])
        return best

    # Wort-Match
    word_matches = []
    for pl in user_playlists:
        pl_name = pl.get("name", "").lower()
        matched, score = _playlist_match_score(query_words, pl_name)
        if matched == len(query_words):
            word_matches.append((pl, score))
        elif matched > 0 and matched >= len(query_words) - 1:
            word_matches.append((pl, score * 0.5))

    if word_matches:
        best_pl, best_score = max(word_matches, key=lambda x: x[1])
        log.info("Playlist wort-gefunden (eigene): '%s' (score=%.2f)",
                 best_pl["name"], best_score)
        return best_pl

    # 2) Spotify-Globalsuche als Fallback
    log.debug("Keine eigene Playlist gefunden, suche global...")
    results = search_spotify(token, query, "playlist", limit=5)
    if results:
        items = [i for i in results.get("playlists", {}).get("items", []) if i]
        if items:
            best = max(items, key=lambda p: p.get("tracks", {}).get("total", 0))
            log.info("Playlist gefunden (global): '%s' (%d Tracks)",
                     best["name"], best.get("tracks", {}).get("total", 0))
            return best

    log.warning("Keine Playlist gefunden für '%s'", query)
    return None


# ============================================================================
# HA MEDIA PLAYER STEUERUNG (ersetzt direkten Spotify API + ADB)
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


def ha_get_entity(entity_id):
    """Liest das vollständige Entity (state + attributes) aus."""
    result, status = http_get(
        f"{HA_API}/states/{entity_id}",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
    )
    if status == 200:
        return result
    return None


def ha_set_input_text(entity_id, value):
    """Setzt einen input_text-Wert in Home Assistant."""
    http_post(
        f"{HA_API}/services/input_text/set_value",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data={"entity_id": entity_id, "value": str(value)[:255]},
    )


def ha_navigate(path, revert_timeout=None):
    """Navigiert das Jarvis-Display zu einer View Assist Seite."""
    data = {"device": VA_DEVICE, "path": path}
    if revert_timeout is not None:
        data["revert_timeout"] = revert_timeout
    _, status = http_post(
        f"{HA_API}/services/view_assist/navigate",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data=data,
    )
    if status == 200:
        log.info("Display → %s", path)
    else:
        log.warning("Navigation zu %s fehlgeschlagen (Status %s)", path, status)
    return status == 200


def ha_select_source(source_name):
    """Wählt Spotify Connect Source über HA media_player.select_source."""
    _, status = http_post(
        f"{HA_API}/services/media_player/select_source",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data={
            "entity_id": SPOTIFY_ENTITY,
            "source": source_name,
        },
        timeout=15,
    )
    if status == 200:
        log.info("Source gewählt: %s", source_name)
        return True
    log.warning("select_source fehlgeschlagen (Status %s)", status)
    return False


def ha_play_media(uri, content_type="playlist"):
    """Spielt Spotify über HA media_player.play_media.

    Vorteile gegenüber direkter Spotify API:
    - HA kümmert sich um Device-Management
    - Kein ADB-Wake nötig (Monitor hält App am Leben)
    - Kein Device-ID-Polling
    """
    _, status = http_post(
        f"{HA_API}/services/media_player/play_media",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data={
            "entity_id": SPOTIFY_ENTITY,
            "media_content_id": uri,
            "media_content_type": content_type,
        },
        timeout=15,
    )
    if status == 200:
        log.info("ha_play_media OK: %s", uri)
        return True
    log.warning("ha_play_media fehlgeschlagen (Status %s)", status)
    return False


def ha_ensure_source():
    """Stellt sicher dass Echo Show als Spotify Source ausgewählt ist.

    Monitor hält Spotify App am Leben → Device ist immer verfügbar.
    Prüft aktuellen Source → wählt Echo Show falls nötig.
    """
    entity = ha_get_entity(SPOTIFY_ENTITY)
    if not entity:
        log.warning("Spotify Entity nicht lesbar")
        return False

    current_source = entity.get("attributes", {}).get("source", "")
    if current_source == JARVIS_SPOTIFY_NAME:
        log.debug("Source bereits korrekt: %s", current_source)
        return True

    log.info("Source wechseln: '%s' → '%s'", current_source, JARVIS_SPOTIFY_NAME)
    return ha_select_source(JARVIS_SPOTIFY_NAME)


def ha_update_entity():
    """Erzwingt sofortige Aktualisierung des Spotify Entity."""
    _, status = http_post(
        f"{HA_API}/services/homeassistant/update_entity",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data={"entity_id": SPOTIFY_ENTITY},
    )
    return status == 200


def find_ha_source(device_name):
    """Findet eine Spotify Source anhand des Namens (über HA source_list).

    Sucht in:
    1. Exakter Match in HA source_list
    2. Partial Match in HA source_list
    3. Alias-Map (deutsch → Spotify Connect Name)
    """
    device_name_lower = device_name.lower().strip()

    # Source-Liste aus HA Entity lesen
    entity = ha_get_entity(SPOTIFY_ENTITY)
    source_list = entity.get("attributes", {}).get("source_list", []) if entity else []
    log.debug("Verfügbare Sources: %s", source_list)

    # Exakter Match
    for src in source_list:
        if src.lower() == device_name_lower:
            return src

    # Partial Match
    for src in source_list:
        if device_name_lower in src.lower():
            return src

    # Alias-Map
    mapped_name = DEVICE_ALIAS_MAP.get(device_name_lower, "")
    if mapped_name:
        # Prüfe ob gemappter Name in source_list ist
        for src in source_list:
            if src.lower() == mapped_name.lower():
                return src
        # Auch ohne source_list-Check verwenden (HA akzeptiert den Namen)
        return mapped_name

    return None


# ============================================================================
# AKTIONEN
# ============================================================================

def action_search_play(token, query, content_type, device_name=""):
    """Sucht nach Musik und spielt über HA media_player.

    Vereinfachter Flow (v2):
    1. Suche über Spotify API (schnell, eigene Playlists zuerst)
    2. Source sicherstellen (ha_ensure_source, ~0s wenn schon korrekt)
    3. Abspielen über HA play_media (~2s)
    4. Display navigieren + input_text setzen

    Kein ADB, kein Device-Polling, kein ensure_jarvis-Loop.
    Monitor hält Spotify App am Leben.
    """
    t0 = time.monotonic()
    log.info("Suche: query='%s', type='%s'", query, content_type)

    # --- 1. Suche ---
    if content_type == "playlist":
        item = find_best_playlist(token, query)
        if not item:
            log.error("Keine Playlist gefunden für '%s'", query)
            return False
        uri = item["uri"]
        name = item.get("name", "Unbekannt")
        display = name
    else:
        results = search_spotify(token, query, content_type)
        if not results:
            log.error("Suche nach '%s' fehlgeschlagen", query)
            return False

        items_key = f"{content_type}s"
        items = [i for i in results.get(items_key, {}).get("items", []) if i]
        if not items:
            log.error("Nichts gefunden für '%s'", query)
            return False

        item = items[0]
        uri = item["uri"]
        name = item.get("name", "Unbekannt")

        if content_type == "track":
            artist = ", ".join(a.get("name", "") for a in item.get("artists", []))
            display = f"{artist} - {name}" if artist else name
        elif content_type in ("album", "artist"):
            artist = ", ".join(a.get("name", "") for a in item.get("artists", []))
            display = f"{artist} - {name}" if artist and content_type == "album" else name
        else:
            display = name

    t_search = time.monotonic()
    log.info("Gefunden: '%s' (URI: %s) [%.1fs]", display, uri, t_search - t0)

    # --- 2. Source sicherstellen ---
    # Device-Name aus Argument oder Default (Jarvis)
    target_source = JARVIS_SPOTIFY_NAME
    if device_name:
        found = find_ha_source(device_name)
        if found:
            target_source = found
            log.info("Ziel-Source: %s", target_source)

    # Source nur wechseln wenn nötig
    entity = ha_get_entity(SPOTIFY_ENTITY)
    current_source = entity.get("attributes", {}).get("source", "") if entity else ""
    if current_source != target_source:
        log.info("Source wechseln: '%s' → '%s'", current_source, target_source)
        if not ha_select_source(target_source):
            log.error("Source-Wechsel fehlgeschlagen")
            return False
        time.sleep(0.5)  # Kurz warten bis Source aktiv

    t_source = time.monotonic()
    log.debug("Source bereit [%.1fs]", t_source - t_search)

    # --- 3. Abspielen über HA ---
    if not ha_play_media(uri, content_type):
        log.error("Wiedergabe fehlgeschlagen")
        return False

    t_play = time.monotonic()
    log.info("OK: '%s' auf '%s' [gesamt=%.1fs, suche=%.1fs, source=%.1fs, play=%.1fs]",
             display, target_source,
             t_play - t0, t_search - t0, t_source - t_search, t_play - t_source)

    # --- 4. Display + Metadata ---
    ha_set_input_text("input_text.spotify_last_played", display)
    ha_navigate(VA_MUSIC_PATH, revert_timeout=3600)

    # Entity-Update erzwingen (Monitor macht das auch, aber hier für sofortiges Feedback)
    ha_update_entity()

    return True


def action_device(token, device_name):
    """Überträgt die Wiedergabe auf ein anderes Gerät über HA select_source."""
    log.info("Device-Transfer zu '%s'", device_name)

    source = find_ha_source(device_name)
    if not source:
        # Zeige verfügbare Sources
        entity = ha_get_entity(SPOTIFY_ENTITY)
        source_list = entity.get("attributes", {}).get("source_list", []) if entity else []
        available = ", ".join(source_list)
        log.error("Gerät '%s' nicht gefunden. Verfügbar: %s", device_name, available)
        return False

    if ha_select_source(source):
        log.info("OK: Transfer zu '%s'", source)
        return True
    else:
        log.error("Transfer zu '%s' fehlgeschlagen", source)
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Spotify Voice Control für HA (v2)")
    parser.add_argument(
        "--action",
        required=True,
        choices=["search_play", "device", "from_ha"],
        help="Aktion: search_play, device, from_ha",
    )
    parser.add_argument("--query", default="", help="Suchbegriff")
    parser.add_argument(
        "--type",
        default="track",
        choices=["track", "artist", "album", "playlist"],
        help="Typ: track, artist, album, playlist",
    )
    parser.add_argument("--device", default="", help="Zielgerät (Name)")
    args = parser.parse_args()

    autodiscover_entities()
    log.info("Entities: spotify=%s display=%s", SPOTIFY_ENTITY, VA_DEVICE)

    # from_ha: Liest Query/Type/Device direkt aus HA input_text-Entities
    if args.action == "from_ha":
        args.query = ha_get_state("input_text.spotify_query")
        args.type = ha_get_state("input_text.spotify_type") or "track"
        args.device = ha_get_state("input_text.spotify_device")
        args.action = "search_play"
        if not args.query:
            log.error("input_text.spotify_query ist leer")
            sys.exit(1)

    # Token holen
    token = get_spotify_token()
    if not token:
        log.error("Kein Spotify-Token verfügbar")
        sys.exit(1)

    # Aktion ausführen
    if args.action == "search_play":
        if not args.query:
            log.error("Kein Suchbegriff angegeben")
            sys.exit(1)
        success = action_search_play(token, args.query, args.type, args.device)
    elif args.action == "device":
        if not args.device:
            log.error("Kein Gerät angegeben")
            sys.exit(1)
        success = action_device(token, args.device)
    else:
        log.error("Unbekannte Aktion: %s", args.action)
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
