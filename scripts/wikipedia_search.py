#!/usr/bin/env python3
"""
Wikipedia-Suche für HA-German-Voice
====================================
Sucht einen deutschen Wikipedia-Artikel und schreibt eine TTS-taugliche
Zusammenfassung (max. 5 Sätze) als HA-Sensor (sensor.wikipedia_result)
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
import re
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
MAX_SENTENCES = 5  # Max Sätze für TTS-Ausgabe

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
# ROLLEN-ERKENNUNG (Trainer, Präsident, …) via Wikidata
# ============================================================================

# Rollen-Keywords → Wikidata-Properties
ROLE_MAP = {
    "trainer": "P286",       # head coach
    "cheftrainer": "P286",
    "coach": "P286",
    "manager": "P286",
    "präsident": "P488",     # chairperson
    "vorsitzender": "P488",
    "vorsitzende": "P488",
}


def detect_role_query(query):
    """Erkennt Rollen-Fragen wie 'Trainer von Bayern München'.

    Returns:
        (role, wikidata_property, entity_name) oder (None, None, None)
    """
    q = query.lower().strip()
    # Führende Fragewörter / Artikel entfernen
    q = re.sub(
        r"^(wer\s+ist\s+|wer\s+war\s+|wie\s+heißt\s+)"
        r"(der\s+|die\s+|das\s+|den\s+|dem\s+)?",
        "", q,
    ).strip()
    # Weitere führende Artikel
    q = re.sub(r"^(den|der|die|das|dem)\s+", "", q).strip()

    for role, prop in ROLE_MAP.items():
        if q.startswith(role):
            # Entity-Name extrahieren (Rolle + optionale Präposition entfernen)
            entity = re.sub(
                r"^" + re.escape(role) + r"\s*(von|vom|des|der|bei|beim)?\s*",
                "", q,
            ).strip()
            if entity:
                return role, prop, entity
    return None, None, None


def _wikidata_find_entity(article_title):
    """Findet die Wikidata-Entity-ID für einen Wikipedia-Artikeltitel."""
    encoded = urllib.parse.quote(article_title)
    url = (
        f"https://{WIKIPEDIA_LANG}.wikipedia.org/w/api.php?"
        f"action=query&titles={encoded}&prop=pageprops&format=json"
    )
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "HA-German-Voice/1.0")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for page in data.get("query", {}).get("pages", {}).values():
        return page.get("pageprops", {}).get("wikibase_item", "")
    return ""


def _wikidata_get_role_person(entity_id, property_id):
    """Holt die aktuelle Person für eine Rolle aus Wikidata.

    Bevorzugt den Eintrag mit rank='preferred' (= aktuell).
    """
    url = (
        f"https://www.wikidata.org/w/api.php?"
        f"action=wbgetclaims&entity={entity_id}&property={property_id}&format=json"
    )
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "HA-German-Voice/1.0")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    claims = data.get("claims", {}).get(property_id, [])
    preferred = None
    latest_normal = None
    for claim in claims:
        pid = (claim.get("mainsnak", {})
               .get("datavalue", {})
               .get("value", {})
               .get("id", ""))
        rank = claim.get("rank", "")
        if rank == "preferred":
            preferred = pid
            break
        if rank == "normal":
            latest_normal = pid

    person_id = preferred or latest_normal
    if not person_id:
        return None, None

    # Label der Person holen
    label_url = (
        f"https://www.wikidata.org/w/api.php?"
        f"action=wbgetentities&ids={person_id}"
        f"&props=labels&languages=de|en&format=json"
    )
    req2 = urllib.request.Request(label_url)
    req2.add_header("User-Agent", "HA-German-Voice/1.0")
    with urllib.request.urlopen(req2, timeout=10) as resp2:
        data2 = json.loads(resp2.read().decode("utf-8"))
    labels = data2.get("entities", {}).get(person_id, {}).get("labels", {})
    name = (labels.get("de", {}).get("value", "")
            or labels.get("en", {}).get("value", ""))
    return name, person_id


def try_role_query(query):
    """Versucht eine Rollen-Frage über Wikidata zu beantworten.

    Returns:
        dict mit title, extract, url, summary   oder  None
    """
    role, prop, entity = detect_role_query(query)
    if not role:
        return None

    log.info("Rollen-Frage erkannt: %s → Eigenschaft %s, Entität '%s'", role, prop, entity)

    # 1. Wikipedia-Artikel für die Entität finden
    encoded = urllib.parse.quote(entity)
    search_url = (
        f"https://{WIKIPEDIA_LANG}.wikipedia.org/w/api.php?"
        f"action=query&list=search&srsearch={encoded}"
        f"&srnamespace=0&srlimit=1&format=json"
    )
    req = urllib.request.Request(search_url)
    req.add_header("User-Agent", "HA-German-Voice/1.0")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    results = data.get("query", {}).get("search", [])
    if not results:
        log.info("Kein Wikipedia-Artikel für '%s' gefunden", entity)
        return None

    article_title = results[0]["title"]
    log.info("Wikipedia-Artikel: '%s'", article_title)

    # 2. Wikidata-ID holen
    wikidata_id = _wikidata_find_entity(article_title)
    if not wikidata_id:
        log.info("Keine Wikidata-ID für '%s'", article_title)
        return None
    log.info("Wikidata-ID: %s", wikidata_id)

    # 3. Person für die Rolle holen
    person_name, person_id = _wikidata_get_role_person(wikidata_id, prop)
    if not person_name:
        log.info("Keine Person für %s/%s gefunden", wikidata_id, prop)
        return None
    log.info("%s von '%s' ist: %s (%s)", role.capitalize(), article_title, person_name, person_id)

    # 4. Wikipedia-Summary der Person holen
    person_extract = ""
    person_url = ""
    try:
        person_article = wikipedia_summary(person_name)
        if person_article:
            person_extract = person_article.get("extract", "")
            person_url = person_article.get("url", "")
    except Exception as e:
        log.warning("Wikipedia-Summary für '%s' fehlgeschlagen: %s", person_name, e)

    # 5. TTS-Antwort zusammenbauen
    answer = f"Der {role.capitalize()} von {article_title} ist {person_name}."
    if person_extract:
        # Ersten Satz der Person anhängen für Kontext
        person_summary = tts_summary(person_extract, max_sentences=2)
        answer += f" {person_summary}"

    return {
        "title": person_name,
        "extract": person_extract or answer,
        "url": person_url,
        "summary": answer,
    }


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
    Erkennt deutsche Abkürzungen (e. V., z. B.) und Ordinalzahlen (27.)
    korrekt, sodass Sätze nicht mitten im Text abgeschnitten werden.
    """
    # Klammer-Inhalte entfernen: (geb. 1879) etc.
    text = re.sub(r"\s*\([^)]*\)", "", text)
    # Eckige Klammern entfernen: [1], [Anm. 2] etc.
    text = re.sub(r"\s*\[[^\]]*\]", "", text)
    # Doppelte Leerzeichen bereinigen
    text = re.sub(r"\s{2,}", " ", text).strip()

    # Smarte Satzerkennung: Wörter durchgehen und echte Satzenden finden
    # (statt einfachem Regex-Split, der bei "e. V." oder "27." bricht)
    sentences = []
    current_words = []

    for word in text.split():
        current_words.append(word)
        # Endet das Wort mit Satzzeichen?
        if re.search(r"[.!?]$", word):
            # Einzelbuchstaben-Abkürzung: e. V. z. B. → kein Satzende
            if re.match(r"^[A-Za-zÄÖÜäöü]\.$", word):
                continue
            # Ordinalzahlen: 27. 1. 100. → kein Satzende
            if re.match(r"^\d+\.$", word):
                continue
            # Bekannte Abkürzungen (Stamm ohne Schlusszeichen)
            stem = re.sub(r"[.,;:!?]+$", "", word).lower()
            if stem in (
                "dr", "prof", "nr", "st", "ca", "geb", "gest",
                "bzw", "etc", "usw", "vgl", "evtl", "ggf",
                "inkl", "max", "min", "mrd", "mio", "hl",
                "sog", "sen", "jun", "abs", "tel", "str",
            ):
                continue
            # Echtes Satzende gefunden
            sentences.append(" ".join(current_words))
            current_words = []

    # Restliche Wörter an den letzten Satz anhängen
    if current_words:
        if sentences:
            sentences[-1] += " " + " ".join(current_words)
        else:
            sentences.append(" ".join(current_words))

    # Auf max_sentences begrenzen
    summary = " ".join(sentences[:max_sentences])

    return summary if summary else text[:500]


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

    # 1. Rollen-Frage prüfen (Trainer, Präsident, …)
    role_result = None
    try:
        role_result = try_role_query(query)
    except Exception as e:
        log.warning("Rollen-Abfrage fehlgeschlagen: %s", e)

    if role_result and role_result.get("summary"):
        log.info("Rollen-Antwort: %s", role_result["summary"][:100])
        ha_set_state(SENSOR_ENTITY, "ready", {
            "friendly_name": "Wikipedia Ergebnis",
            "summary": role_result["summary"],
            "extract": role_result.get("extract", ""),
            "query": query,
            "title": role_result.get("title", ""),
            "url": role_result.get("url", ""),
        })
        log.info("Ergebnis (Rollen-Frage) in sensor.wikipedia_result geschrieben")
        return

    # 2. Normaler Wikipedia-Artikel
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

    # 3. TTS-taugliche Zusammenfassung (max. 5 Sätze, bereinigt)
    summary = tts_summary(extract)

    log.info("Zusammenfassung (%d Zeichen): %s", len(summary), summary[:100])

    # 4. Ergebnis in HA-Sensor schreiben
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
