#!/usr/bin/env python3
"""
Wikipedia-Suche für HA-German-Voice
====================================
Sucht einen deutschen Wikipedia-Artikel und schreibt eine TTS-taugliche
Zusammenfassung (max. 3 Sätze) als HA-Sensor (sensor.wikipedia_result)
via REST API.

Verwendung (als shell_command):
  python3 /config/scripts/wikipedia_search.py "Quantenphysik"

Ergebnis in sensor.wikipedia_result:
  state:       "ready" | "not_found" | "error"
  attributes:  summary, title, extract, query, url, friendly_name

Konfiguration via Umgebungsvariablen:
  HA_API          - HA REST API URL       (default: http://localhost:8123/api)
  HA_TOKEN        - Long-Lived Access Token
"""

import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import logging

# ============================================================================
# KONFIGURATION
# ============================================================================

HA_API = os.getenv("HA_API", "http://localhost:8123/api")
SENSOR_ENTITY = "sensor.wikipedia_result"
WIKIPEDIA_LANG = "de"
MAX_SENTENCES = 3  # Max Sätze für TTS-Ausgabe

# HA Token aus secrets_config.py oder Umgebungsvariable
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from secrets_config import HA_TOKEN
except ImportError:
    HA_TOKEN = os.getenv("HA_TOKEN", "")

# Logging
LOG_DIR = "/config/logs"
LOG_FILE = os.path.join(LOG_DIR, "wikipedia_search.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("wikipedia_search")


# ============================================================================
# HA API
# ============================================================================

def ha_set_state(entity_id, state, attributes=None):
    """Setzt einen HA-Entity-State via REST API."""
    url = f"{HA_API}/states/{entity_id}"
    data = {"state": state, "attributes": attributes or {}}
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {HA_TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except Exception as e:
        log.error("HA API Fehler: %s", e)
        return None


# ============================================================================
# WIKIPEDIA API
# ============================================================================

def wikipedia_summary(query):
    """
    Holt die Zusammenfassung eines Wikipedia-Artikels (REST API v1).
    Fallback: Wikipedia Search API → dann nochmal Summary.
    """
    encoded = urllib.parse.quote(query)
    url = f"https://{WIKIPEDIA_LANG}.wikipedia.org/api/rest_v1/page/summary/{encoded}"

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "HA-German-Voice/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("type") == "standard":
                return {
                    "title": data.get("title", query),
                    "extract": data.get("extract", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            log.info("Kein direkter Artikel fuer '%s', versuche Suche...", query)
        else:
            log.error("Wikipedia REST Fehler: %s", e)
    except Exception as e:
        log.error("Wikipedia Fehler: %s", e)

    # --- Fallback: Freitext-Suche ---
    return _wikipedia_search_fallback(query)


def _wikipedia_search_fallback(query):
    """Sucht per Wikipedia Search API und holt den ersten Treffer."""
    encoded = urllib.parse.quote(query)
    search_url = (
        f"https://{WIKIPEDIA_LANG}.wikipedia.org/w/api.php?"
        f"action=query&list=search&srsearch={encoded}"
        f"&srnamespace=0&srlimit=1&format=json"
    )
    try:
        req = urllib.request.Request(search_url)
        req.add_header("User-Agent", "HA-German-Voice/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("query", {}).get("search", [])
            if results:
                title = results[0]["title"]
                log.info("Suche ergab: '%s'", title)
                # Summary für gefundenen Titel holen
                title_encoded = urllib.parse.quote(title)
                summary_url = (
                    f"https://{WIKIPEDIA_LANG}.wikipedia.org"
                    f"/api/rest_v1/page/summary/{title_encoded}"
                )
                req2 = urllib.request.Request(summary_url)
                req2.add_header("User-Agent", "HA-German-Voice/1.0")
                with urllib.request.urlopen(req2, timeout=10) as resp2:
                    data2 = json.loads(resp2.read().decode("utf-8"))
                    return {
                        "title": data2.get("title", title),
                        "extract": data2.get("extract", ""),
                        "url": data2.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    }
    except Exception as e:
        log.error("Wikipedia Suche Fehler: %s", e)

    return None


# ============================================================================
# TTS-TAUGLICHE ZUSAMMENFASSUNG
# ============================================================================

def tts_summary(text, max_sentences=MAX_SENTENCES):
    """
    Kürzt den Wikipedia-Extrakt auf max_sentences Sätze und bereinigt
    ihn für TTS-Ausgabe (keine Klammern, keine Sonderzeichen).
    """
    import re

    # Klammer-Inhalte entfernen: (geb. 1879) etc.
    text = re.sub(r"\s*\([^)]*\)", "", text)
    # Eckige Klammern entfernen: [1], [Anm. 2] etc.
    text = re.sub(r"\s*\[[^\]]*\]", "", text)
    # Doppelte Leerzeichen bereinigen
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Sätze aufteilen (am Punkt, Ausrufezeichen, Fragezeichen)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Auf max_sentences begrenzen
    summary = " ".join(sentences[:max_sentences])

    return summary if summary else text[:400]


# ============================================================================
# MAIN
# ============================================================================

def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        log.error("Kein Suchbegriff angegeben")
        ha_set_state(SENSOR_ENTITY, "error", {
            "friendly_name": "Wikipedia Ergebnis",
            "summary": "Kein Suchbegriff angegeben.",
            "extract": "",
            "query": "",
            "title": "",
            "url": "",
        })
        sys.exit(1)

    query = " ".join(sys.argv[1:]).strip()
    log.info("Wikipedia-Suche: '%s'", query)

    # Sensor auf "searching" setzen
    ha_set_state(SENSOR_ENTITY, "searching", {
        "friendly_name": "Wikipedia Ergebnis",
        "summary": "",
        "extract": "",
        "query": query,
        "title": "",
        "url": "",
    })

    # 1. Wikipedia-Artikel holen
    article = wikipedia_summary(query)

    if not article or not article.get("extract"):
        log.warning("Kein Artikel fuer '%s' gefunden", query)
        ha_set_state(SENSOR_ENTITY, "not_found", {
            "friendly_name": "Wikipedia Ergebnis",
            "summary": f"Zu {query} habe ich leider keinen Wikipedia-Artikel gefunden.",
            "extract": "",
            "query": query,
            "title": "",
            "url": "",
        })
        return

    extract = article["extract"]
    title = article["title"]
    log.info("Artikel gefunden: '%s' (%d Zeichen)", title, len(extract))

    # 2. TTS-taugliche Zusammenfassung (max. 3 Sätze, bereinigt)
    summary = tts_summary(extract)

    log.info("Zusammenfassung (%d Zeichen): %s", len(summary), summary[:100])

    # 3. Ergebnis in HA-Sensor schreiben
    ha_set_state(SENSOR_ENTITY, "ready", {
        "friendly_name": "Wikipedia Ergebnis",
        "summary": summary,
        "extract": extract,
        "query": query,
        "title": title,
        "url": article.get("url", ""),
    })

    log.info("Ergebnis in sensor.wikipedia_result geschrieben")


if __name__ == "__main__":
    main()
