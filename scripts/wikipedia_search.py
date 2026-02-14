#!/usr/bin/env python3
"""
Wikipedia + Ollama Zusammenfasser für HA-German-Voice
=====================================================
Sucht einen deutschen Wikipedia-Artikel, lässt Ollama eine
TTS-taugliche Zusammenfassung erstellen und schreibt das Ergebnis
als HA-Sensor (sensor.wikipedia_result) via REST API.

Verwendung (als shell_command):
  python3 /config/scripts/wikipedia_search.py "Quantenphysik"

Ergebnis in sensor.wikipedia_result:
  state:       "ready" | "not_found" | "error"
  attributes:  summary, title, extract, query, url, friendly_name

Konfiguration via Umgebungsvariablen:
  HA_API          - HA REST API URL       (default: http://localhost:8123/api)
  HA_TOKEN        - Long-Lived Access Token
  OLLAMA_API      - Ollama API URL         (default: http://localhost:11434)
  OLLAMA_MODEL    - Ollama Modell          (default: llama3)
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

# HA Token aus secrets_config.py oder Umgebungsvariable
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from secrets_config import HA_TOKEN
except ImportError:
    HA_TOKEN = os.getenv("HA_TOKEN", "")

# ANPASSEN: Ollama-Server URL und Modell
OLLAMA_API = os.getenv("OLLAMA_API", "http://192.168.178.95:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

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
# OLLAMA ZUSAMMENFASSUNG
# ============================================================================

def ollama_summarize(text, title):
    """
    Lässt Ollama den Wikipedia-Extrakt in 2-3 TTS-taugliche Sätze
    zusammenfassen. Gibt None zurück bei Fehler.
    """
    prompt = (
        f'Fasse den folgenden Wikipedia-Artikel über "{title}" in genau '
        f"2 bis 3 kurzen, gut verständlichen Sätzen zusammen. "
        f"Die Zusammenfassung soll für eine Sprachausgabe geeignet sein: "
        f"natürlich klingen, keine Sonderzeichen, keine Aufzählungen, "
        f"keine URLs, keine Klammern. Duze den Zuhörer nicht. "
        f"Antworte NUR mit der Zusammenfassung, ohne Einleitung.\n\n"
        f"Artikel:\n{text}"
    )

    url = f"{OLLAMA_API}/api/generate"
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 250,
        },
    }

    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            summary = result.get("response", "").strip()
            if summary:
                log.info("Ollama Zusammenfassung erhalten (%d Zeichen)", len(summary))
                return summary
            log.warning("Ollama gab leere Antwort zurück")
            return None
    except urllib.error.URLError as e:
        log.error("Ollama nicht erreichbar (%s): %s", OLLAMA_API, e)
        return None
    except Exception as e:
        log.error("Ollama Fehler: %s", e)
        return None


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

    # 2. Ollama-Zusammenfassung
    summary = ollama_summarize(extract, title)

    if not summary:
        # Fallback: Wikipedia-Extrakt direkt verwenden (gekürzt)
        log.warning("Ollama nicht erreichbar, verwende Wikipedia-Extrakt direkt")
        summary = extract
        if len(summary) > 500:
            # Am letzten Satzende kürzen
            cut = summary[:500].rfind(".")
            if cut > 100:
                summary = summary[: cut + 1]
            else:
                summary = summary[:497] + "..."

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
