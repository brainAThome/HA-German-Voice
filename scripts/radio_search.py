#!/usr/bin/env python3
"""
Radio Search - Sucht und spielt Radiosender via Radio Browser API.

Wird von Home Assistant über shell_command aufgerufen.
Nutzt die kostenlose Radio Browser API (30.000+ Sender weltweit).

Usage:
    python3 radio_search.py --query "Radio Hamburg"
    python3 radio_search.py --query "SomaFM Groove Salad"
    python3 radio_search.py --query "FFN"
"""

import argparse
import json
import logging
import os
import ssl
import sys
import urllib.request
import urllib.parse

# Secrets externalisiert — kein Token mehr im Code
from secrets_config import HA_TOKEN

# ============================================================================
# Konfiguration
# ============================================================================
HA_URL = "http://localhost:8123"
# HA_TOKEN wird aus secrets_config importiert (Environment oder /config/secrets.yaml)
MEDIA_PLAYER = "media_player.vaca_362812d56_mediaplayer"
VA_DEVICE = "sensor.quasselbuechse"
RADIO_STATION_ENTITY = "input_text.radio_current_station"
DUCKING_ENTITY = "input_boolean.spotify_ducking_active"
LOGO_DIR = "/config/www/radio_logos"

# Radio Browser API - mehrere Server für Redundanz
RADIO_BROWSER_SERVERS = [
    "https://de1.api.radio-browser.info",
    "https://at1.api.radio-browser.info",
    "https://nl1.api.radio-browser.info",
]

LOG_FILE = "/config/logs/radio_search.log"

# ============================================================================
# Logging
# ============================================================================
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("radio_search")

# ============================================================================
# SSL Context (für Radio Browser API)
# ============================================================================
ssl_ctx = ssl.create_default_context()
# SSL-Verifikation aktiv — sicherer als CERT_NONE
# Falls Zertifikatsprobleme: certifi installieren oder CA-Bundle angeben


def ha_api(endpoint, method="GET", data=None):
    """Home Assistant API aufrufen."""
    url = f"{HA_URL}/api/{endpoint}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read()) if resp.status == 200 else None
    except Exception as e:
        log.error(f"HA API error ({endpoint}): {e}")
        return None


def ha_set_state(entity_id, value):
    """Input-Text/Boolean setzen."""
    domain = entity_id.split(".")[0]
    if domain == "input_text":
        ha_api("services/input_text/set_value", "POST", {
            "entity_id": entity_id,
            "value": str(value)[:255],  # max 255 chars
        })
    elif domain == "input_boolean":
        action = "turn_on" if value else "turn_off"
        ha_api(f"services/input_boolean/{action}", "POST", {
            "entity_id": entity_id,
        })


def ha_play_media(url, title="Radio"):
    """Medien auf dem VACA Media Player abspielen."""
    ha_api("services/media_player/play_media", "POST", {
        "entity_id": MEDIA_PLAYER,
        "media_content_type": "music",
        "media_content_id": url,
    })
    log.info(f"Playing: {title} -> {url}")


def ha_navigate(path, revert_timeout=3600):
    """View Assist Navigation."""
    ha_api("services/view_assist/navigate", "POST", {
        "device": VA_DEVICE,
        "path": path,
        "revert_timeout": revert_timeout,
    })


def ha_tts(message):
    """Sprachausgabe über die Conversation API."""
    # Wir setzen die Antwort als HA notification / persistent_notification
    # Das TTS wird vom Intent-Script übernommen
    log.info(f"TTS: {message}")


def download_logo(station_name, favicon_url):
    """Sender-Logo herunterladen falls noch nicht vorhanden."""
    if not favicon_url or len(favicon_url) < 5:
        return False

    # Sanitize filename
    safe_name = "".join(c for c in station_name if c.isalnum() or c in "-_ ").strip()
    safe_name = safe_name.replace(" ", "_")
    if not safe_name:
        return False

    path = os.path.join(LOGO_DIR, f"{safe_name}.png")
    if os.path.exists(path) and os.path.getsize(path) > 200:
        return safe_name

    try:
        req = urllib.request.Request(
            favicon_url,
            headers={"User-Agent": "Mozilla/5.0 (ha-radio/1.0)"},
        )
        data = urllib.request.urlopen(req, context=ssl_ctx, timeout=10).read()
        if len(data) > 100:
            os.makedirs(LOGO_DIR, exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
            log.info(f"Logo saved: {safe_name} ({len(data)} bytes)")
            return safe_name
    except Exception as e:
        log.warning(f"Logo download failed for {station_name}: {e}")

    return False


def search_radio_browser(query, limit=5):
    """Radio Browser API durchsuchen."""
    for server in RADIO_BROWSER_SERVERS:
        try:
            url = f"{server}/json/stations/byname/{urllib.parse.quote(query)}?limit={limit}&order=votes&reverse=true&hidebroken=true"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ha-german-voice-radio/1.0"},
            )
            resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=10)
            stations = json.loads(resp.read())

            if stations:
                log.info(f"Found {len(stations)} stations for '{query}' via {server}")
                return stations

        except Exception as e:
            log.warning(f"Radio Browser API error ({server}): {e}")
            continue

    # Fallback: Exact name search didn't work, try search
    for server in RADIO_BROWSER_SERVERS:
        try:
            url = f"{server}/json/stations/search"
            data = json.dumps({
                "name": query,
                "limit": limit,
                "order": "votes",
                "reverse": True,
                "hidebroken": True,
            }).encode()
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "User-Agent": "ha-german-voice-radio/1.0",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=10)
            stations = json.loads(resp.read())

            if stations:
                log.info(f"Found {len(stations)} stations via search for '{query}'")
                return stations

        except Exception as e:
            log.warning(f"Radio Browser search error ({server}): {e}")
            continue

    return []


def pick_best_station(stations, query):
    """Besten Sender aus den Ergebnissen wählen."""
    if not stations:
        return None

    query_lower = query.lower().strip()

    # Priorität 1: Exakter Name-Match
    for s in stations:
        if s.get("name", "").lower().strip() == query_lower:
            return s

    # Priorität 2: Name beginnt mit Query
    for s in stations:
        if s.get("name", "").lower().startswith(query_lower):
            return s

    # Priorität 3: Query ist im Namen enthalten + hat viele Votes
    matching = [s for s in stations if query_lower in s.get("name", "").lower()]
    if matching:
        # Sortiere nach Votes
        matching.sort(key=lambda x: x.get("votes", 0), reverse=True)
        return matching[0]

    # Priorität 4: Einfach der erste (bereits nach Votes sortiert)
    return stations[0]


def get_stream_url(station):
    """Stream-URL aus dem Station-Dict extrahieren."""
    url = station.get("url_resolved") or station.get("url", "")
    return url.strip()


def main():
    parser = argparse.ArgumentParser(description="Radio Search via Radio Browser API")
    parser.add_argument("--query", default="", help="Suchbegriff f\u00fcr den Radiosender")
    parser.add_argument("--action", default="play", choices=["play", "search"],
                        help="play = suchen + abspielen, search = nur suchen")
    args = parser.parse_args()

    query = args.query.strip()

    # Wenn kein Query per CLI, aus HA Entity lesen
    if not query:
        state = ha_api("states/input_text.radio_search_query")
        if state and "state" in state:
            query = state["state"].strip()

    if not query or query in ("unknown", "unavailable", ""):
        log.error("Leere Suchanfrage")
        ha_set_state("input_text.radio_search_result", "NOT_FOUND:unbekannt")
        sys.exit(1)

    log.info(f"=== Radio Search: '{query}' ===")

    # Suche via Radio Browser API
    stations = search_radio_browser(query, limit=10)

    if not stations:
        log.warning(f"Kein Sender gefunden für: {query}")
        # Setze den Status damit das Intent-Script eine Fehlermeldung geben kann
        ha_set_state("input_text.radio_search_result", f"NOT_FOUND:{query}")
        sys.exit(1)

    # Besten Sender wählen
    best = pick_best_station(stations, query)
    if not best:
        ha_set_state("input_text.radio_search_result", f"NOT_FOUND:{query}")
        sys.exit(1)

    station_name = best.get("name", query).strip()
    stream_url = get_stream_url(best)
    favicon = best.get("favicon", "")
    country = best.get("country", "")
    codec = best.get("codec", "")
    bitrate = best.get("bitrate", 0)

    log.info(f"Best match: {station_name} ({country}, {codec} {bitrate}kbps)")
    log.info(f"Stream: {stream_url}")
    log.info(f"Favicon: {favicon}")

    if not stream_url:
        log.error("Keine Stream-URL gefunden")
        ha_set_state("input_text.radio_search_result", f"NO_STREAM:{station_name}")
        sys.exit(1)

    if args.action == "play":
        # Ducking deaktivieren
        ha_set_state(DUCKING_ENTITY, False)

        # Logo herunterladen - Dateiname = sanitized Station-Name
        logo_key = download_logo(station_name, favicon)

        # Station-Name setzen (für Display) - schöner Name, nicht der Dateiname
        # Wir speichern "<logo_key>|<display_name>" damit View beides hat
        display_name = station_name
        if logo_key:
            ha_set_state(RADIO_STATION_ENTITY, f"{logo_key}|{display_name}")
        else:
            ha_set_state(RADIO_STATION_ENTITY, f"|{display_name}")

        # Stream abspielen
        ha_play_media(stream_url, station_name)

        # Suchergebnis für Speech setzen (Navigation erfolgt über intent_script)
        ha_set_state("input_text.radio_search_result", f"OK:{station_name}")

        log.info(f"=== Radio gestartet: {station_name} ===")

    elif args.action == "search":
        # Nur Ergebnis melden
        results = []
        for s in stations[:5]:
            results.append(f"{s.get('name', '?')} ({s.get('country', '?')})")
        result_text = ", ".join(results)
        ha_set_state("input_text.radio_search_result", f"LIST:{result_text}")
        log.info(f"Search results: {result_text}")


if __name__ == "__main__":
    main()
