#!/usr/bin/env python3
"""
Spotify Track Monitor v3 ÔÇö ADB MediaSession + Keep-Alive + Ducking
===================================================================
Alles-in-einem-Daemon f├╝r Jarvis (Echo Show 5 mit LineageOS):

1. TRACK MONITOR ÔÇö Erkennt Titelwechsel/Play/Pause via ADB MediaSession
   ÔåÆ HA Entity-Update erzwingen, Display-Navigation

2. KEEP-ALIVE ÔÇö H├ñlt Spotify App permanent im Hintergrund am Leben
   ÔåÆ Pr├╝ft alle 30s ob Spotify-Prozess l├ñuft, startet ihn falls nicht
   ÔåÆ Doze-Whitelist ÔåÆ Android killt ihn nicht
   ÔåÆ VACA bleibt immer im Vordergrund (kein App-Stealing)

3. DUCKING ÔÇö Pausiert Musik bei Spracheingabe via ADB KeyEvent
   ÔåÆ Pollt assist_satellite State via HA API
   ÔåÆ Bei Spracheingabe: KEYCODE_MEDIA_PAUSE (~100ms statt 2-3s)
   ÔåÆ Bei Ende: KEYCODE_MEDIA_PLAY

Start:
  python3 /config/scripts/spotify_monitor.py &
"""

import json
import os
import re
import sys
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
import signal
import threading

# ============================================================================
# KONFIGURATION
# ============================================================================
# KONFIGURATION — ANPASSEN an eigenes Setup!
# ============================================================================

POLL_INTERVAL = 0.5        # Sekunden zwischen Polls (ADB ist schnell genug!)
POLL_INTERVAL_IDLE = 5     # Sekunden wenn Spotify idle/pausiert
ADB_RECONNECT_WAIT = 10    # Sekunden zwischen Reconnect-Versuchen
ADB_TIMEOUT = 8            # ADB-Verbindungs-Timeout

# ANPASSEN: IP-Adresse deines Echo Show / Android-Geräts
ECHO_HOST = "192.168.178.103"
ECHO_PORT = 5555
ADB_KEY_PATH = "/config/.storage/adbkey"

HA_API = "http://localhost:8123/api"
# ANPASSEN: Deine Entity-IDs
SPOTIFY_ENTITY = "media_player.spotify_sven"
SATELLITE_ENTITY = "assist_satellite.vaca_362812d56"
RADIO_ENTITY = "media_player.vaca_362812d56_mediaplayer"
VA_DEVICE = "sensor.quasselbuechse"
VA_MUSIC_PATH = "/view-assist/music"
VA_HOME_PATH = "/view-assist/clock"

# Keep-Alive
KEEPALIVE_INTERVAL = 30    # Sekunden zwischen Prozess-Checks
SPOTIFY_PACKAGE = "com.spotify.music"

LOG_DIR = "/config/logs"
LOG_FILE = os.path.join(LOG_DIR, "spotify_monitor.log")
PID_FILE = "/config/scripts/.spotify_monitor.pid"

# PlaybackState-Konstanten (Android MediaSession)
STATE_NONE = 0
STATE_STOPPED = 1
STATE_PAUSED = 2
STATE_PLAYING = 3
STATE_BUFFERING = 6
STATE_NAMES = {0: "NONE", 1: "STOPPED", 2: "PAUSED", 3: "PLAYING", 6: "BUFFERING"}

# ============================================================================
# LOGGING
# ============================================================================

os.makedirs(LOG_DIR, exist_ok=True)

log = logging.getLogger("spotify_monitor")
log.setLevel(logging.INFO)

from logging.handlers import RotatingFileHandler
fh = RotatingFileHandler(LOG_FILE, maxBytes=500_000, backupCount=1)
fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
log.addHandler(fh)

sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
sh.setLevel(logging.WARNING)
log.addHandler(sh)

# ============================================================================
# HA TOKEN
# ============================================================================

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secrets_config import HA_TOKEN

# ============================================================================
# HTTP HELPERS
# ============================================================================

def http_post(url, headers=None, json_data=None, timeout=8):
    body = json.dumps(json_data).encode("utf-8") if json_data else None
    headers = headers or {}
    if json_data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return (json.loads(raw) if raw else {}), resp.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return {"error": raw}, e.code
    except Exception as e:
        return {"error": str(e)}, 0


def http_get(url, headers=None, timeout=5):
    req = urllib.request.Request(url, method="GET")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.status
    except Exception:
        return {}, 0

# ============================================================================
# ADB MediaSession ÔÇö Kern des Monitors
# ============================================================================

_adb_device = None
_adb_lock = threading.Lock()
_RE_DESCRIPTION = re.compile(r"description=(.+)")
_RE_STATE = re.compile(r"state=PlaybackState\s*\{state=(\d+)")
_RE_ACTIVE_ITEM = re.compile(r"active item id=(\d+)")


def adb_connect():
    """Stellt ADB-Verbindung zum Echo Show her."""
    global _adb_device
    try:
        from adb_shell.adb_device import AdbDeviceTcp
        from adb_shell.auth.sign_pythonrsa import PythonRSASigner

        with open(ADB_KEY_PATH) as f:
            priv = f.read()
        with open(ADB_KEY_PATH + ".pub") as f:
            pub = f.read()
        signer = PythonRSASigner(pub, priv)

        dev = AdbDeviceTcp(ECHO_HOST, ECHO_PORT, default_transport_timeout_s=ADB_TIMEOUT)
        dev.connect(rsa_keys=[signer], auth_timeout_s=ADB_TIMEOUT)
        _adb_device = dev
        log.info("ADB verbunden: %s:%d", ECHO_HOST, ECHO_PORT)
        return True
    except Exception as e:
        _adb_device = None
        log.error("ADB-Verbindung fehlgeschlagen: %s", e)
        return False


def adb_disconnect():
    """ADB-Verbindung trennen."""
    global _adb_device
    if _adb_device:
        try:
            _adb_device.close()
        except Exception:
            pass
        _adb_device = None


def adb_shell(cmd, timeout_s=5):
    """F├╝hrt ADB Shell-Befehl aus. Thread-safe.
    Returns: str oder None bei Fehler (setzt _adb_device = None)."""
    global _adb_device
    with _adb_lock:
        if not _adb_device:
            return None
        try:
            return _adb_device.shell(cmd, timeout_s=timeout_s)
        except Exception as e:
            log.warning("ADB Shell-Fehler: %s", e)
            _adb_device = None
            return None


def adb_get_media_session():
    """Liest Spotify MediaSession vom Echo Show.

    Returns dict mit title, artist, album, state, active_item_id, description
    oder None wenn kein Spotify aktiv / Fehler.
    """
    raw = adb_shell(
        "MS=$(dumpsys media_session 2>/dev/null); "
        "echo \"$MS\" | grep 'description=' | tail -1; "
        "echo '---SEP---'; "
        "echo \"$MS\" | grep 'state=PlaybackState' | head -1; "
        "echo '---SEP---'; "
        "echo \"$MS\" | grep 'active=' | tail -1"
    )

    if not raw or "description=" not in raw:
        return None

    parts = raw.split("---SEP---")
    desc_line = parts[0].strip() if len(parts) > 0 else ""
    state_line = parts[1].strip() if len(parts) > 1 else ""
    active_line = parts[2].strip() if len(parts) > 2 else ""

    desc_match = _RE_DESCRIPTION.search(desc_line)
    if not desc_match:
        return None

    description = desc_match.group(1).strip()
    desc_parts = [p.strip() for p in description.split(",", 2)]
    title = desc_parts[0] if len(desc_parts) >= 1 else "?"
    artist = desc_parts[1] if len(desc_parts) >= 2 else ""
    album = desc_parts[2] if len(desc_parts) >= 3 else ""
    if album and " / " in album:
        album = album.rsplit(" / ", 1)[0].strip()

    state = STATE_NONE
    state_match = _RE_STATE.search(state_line)
    if state_match:
        state = int(state_match.group(1))

    active_item_id = -1
    item_match = _RE_ACTIVE_ITEM.search(state_line)
    if item_match:
        active_item_id = int(item_match.group(1))

    is_active = "active=true" in active_line
    if not is_active:
        return None

    return {
        "title": title,
        "artist": artist,
        "album": album,
        "state": state,
        "active_item_id": active_item_id,
        "description": description,
    }

# ============================================================================
# HOME ASSISTANT ACTIONS
# ============================================================================

def ha_update_entity():
    """Erzwingt sofortiges Entity-Update in HA."""
    _, status = http_post(
        f"{HA_API}/services/homeassistant/update_entity",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data={"entity_id": SPOTIFY_ENTITY},
    )
    if status == 200:
        log.debug("Entity update erzwungen")
    else:
        log.warning("Entity update fehlgeschlagen: %s", status)


def ha_navigate(path, revert_timeout=None):
    """Navigiert Jarvis-Display."""
    data = {"device": VA_DEVICE, "path": path}
    if revert_timeout is not None:
        data["revert_timeout"] = revert_timeout
    _, status = http_post(
        f"{HA_API}/services/view_assist/navigate",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data=data,
    )
    if status == 200:
        log.info("Display ÔåÆ %s", path)


def ha_set_input_text(entity_id, value):
    """Setzt einen input_text in HA."""
    http_post(
        f"{HA_API}/services/input_text/set_value",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        json_data={"entity_id": entity_id, "value": str(value)[:255]},
    )


# Letzter bekannter Satellite-State (Fallback bei HTTP-Fehler)
_last_known_satellite = "idle"


def ha_get_satellite_state():
    """Liest den State des VACA Assist-Satellite.

    WICHTIG: Bei HTTP-Fehler wird der LETZTE bekannte State zur├╝ckgegeben,
    NICHT 'idle'. Sonst wird bei einem Timeout f├ñlschlich idle erkannt
    und Ducking-Resume ausgel├Âst.
    """
    global _last_known_satellite
    data, status = http_get(
        f"{HA_API}/states/{SATELLITE_ENTITY}",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
    )
    if status == 200:
        state = data.get("state", "idle")
        _last_known_satellite = state
        return state
    log.debug("Satellite-State nicht lesbar (Status %s), nutze letzten: %s",
             status, _last_known_satellite)
    return _last_known_satellite


def ha_get_entity_state(entity_id):
    """Liest den State eines beliebigen HA-Entity."""
    data, status = http_get(
        f"{HA_API}/states/{entity_id}",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
    )
    if status == 200:
        return data.get("state", "")
    return ""

# ============================================================================
# KEEP-ALIVE: Spotify App permanent im Hintergrund
# ============================================================================

_keepalive_initialized = False


def keepalive_init():
    """Einmaliges Setup: Doze-Whitelist + Spotify im Hintergrund starten."""
    global _keepalive_initialized
    if _keepalive_initialized:
        return

    # Spotify in Doze-Whitelist ÔåÆ Android killt es nicht im Deep Sleep
    result = adb_shell(
        f"dumpsys deviceidle whitelist +{SPOTIFY_PACKAGE} 2>/dev/null; "
        f"cmd appops set {SPOTIFY_PACKAGE} RUN_IN_BACKGROUND allow 2>/dev/null; "
        f"cmd appops set {SPOTIFY_PACKAGE} RUN_ANY_IN_BACKGROUND allow 2>/dev/null",
        timeout_s=10,
    )
    if result is not None:
        log.info("Keep-Alive: Spotify in Doze-Whitelist + Background-Erlaubnis gesetzt")
        _keepalive_initialized = True

    # Initiales Keep-Alive: Sicherstellen dass Spotify l├ñuft
    keepalive_check()


def keepalive_check():
    """Pr├╝ft ob Spotify l├ñuft. Falls nicht: im Hintergrund starten.

    Startet Spotify und bringt sofort VACA wieder in den Vordergrund.
    """
    result = adb_shell(f"pidof {SPOTIFY_PACKAGE}", timeout_s=3)
    if result and result.strip():
        return True  # Spotify l├ñuft

    log.warning("Keep-Alive: Spotify-Prozess nicht gefunden, starte...")

    # Spotify starten ÔÇö monkey ist der zuverl├ñssigste Weg
    adb_shell(
        f"monkey -p {SPOTIFY_PACKAGE} -c android.intent.category.LAUNCHER 1 2>/dev/null",
        timeout_s=10,
    )
    # Warte kurz, dann VACA sofort wieder in den Vordergrund
    time.sleep(2)
    adb_shell(
        "am start -n com.msp1974.vacompanion/.MainActivity "
        "-a android.intent.action.MAIN "
        "-c android.intent.category.HOME",
        timeout_s=5,
    )
    time.sleep(0.3)
    adb_shell("settings put system screen_off_timeout 86400000", timeout_s=5)

    # Pr├╝fen ob es jetzt l├ñuft
    result = adb_shell(f"pidof {SPOTIFY_PACKAGE}", timeout_s=3)
    if result and result.strip():
        log.info("Keep-Alive: Spotify gestartet (PID: %s)", result.strip())
        return True
    else:
        log.error("Keep-Alive: Spotify konnte nicht gestartet werden")
        return False

# ============================================================================
# DUCKING: Musik pausieren bei Spracheingabe
# ============================================================================

_ducking_active = False
_last_satellite_state = "idle"
_ducking_was_spotify = False
_ducking_was_radio = False


def ducking_check(current_spotify_state):
    """Pausiert ALLES (Spotify + Radio) bei Spracheingabe.

    PAUSE:  ADB KEYCODE_MEDIA_PAUSE (pausiert AudioFocus-Halter, ~100ms)
            + HA media_player.media_pause auf Radio (Backup)
    RESUME: Nur wenn kein Stopp-Intent erkannt wurde.
            3s Wartezeit + Satellite-Recheck + Boolean-Check.

    Boolean-Logik:
    - WIR setzen input_boolean ÔåÆ ON beim Ducking-Start
    - Stopp-Automation setzt input_boolean ÔåÆ OFF als ERSTE Aktion
    - Nach 3s Wartezeit: ON = normales Ducking ÔåÆ Resume,
                          OFF = Stopp-Intent ÔåÆ kein Resume
    """
    global _ducking_active, _last_satellite_state
    global _ducking_was_spotify, _ducking_was_radio

    sat_state = ha_get_satellite_state()

    # Satellite hat sich nicht ge├ñndert ÔåÆ nichts zu tun
    if sat_state == _last_satellite_state:
        return
    old_state = _last_satellite_state
    _last_satellite_state = sat_state

    # === PAUSE: Satellite verl├ñsst idle ÔåÆ Spracheingabe beginnt ===
    if old_state == "idle" and sat_state != "idle":
        # Was l├ñuft gerade? Spotify (ADB) und/oder Radio (HA)
        _ducking_was_spotify = (current_spotify_state == STATE_PLAYING)
        radio_state = ha_get_entity_state(RADIO_ENTITY)
        _ducking_was_radio = (radio_state == "playing")

        if _ducking_was_spotify or _ducking_was_radio:
            sources = []
            if _ducking_was_spotify:
                sources.append("Spotify")
            if _ducking_was_radio:
                sources.append("Radio")
            log.info("­ƒöç Ducking: Satellite=%s, pausiere %s",
                     sat_state, "+".join(sources))
            _ducking_active = True

            # WICHTIG: Boolean ON ZUERST setzen, BEVOR ADB/Radio!
            # Race-Condition-Fix: ADB dauert 1-3s. Wenn die Stopp-Automation
            # Boolean OFF setzt BEVOR unser ON ankommt, ├╝berschreiben wir
            # das OFF und der Monitor denkt "kein Stopp" ÔåÆ falsches Resume.
            http_post(
                f"{HA_API}/services/input_boolean/turn_on",
                headers={"Authorization": f"Bearer {HA_TOKEN}"},
                json_data={"entity_id": "input_boolean.spotify_ducking_active"},
            )

            # ADB pausiert den aktuellen AudioFocus-Halter
            adb_shell("input keyevent KEYCODE_MEDIA_PAUSE", timeout_s=3)

            # Radio zus├ñtzlich via HA pausieren (falls nicht via ADB)
            if _ducking_was_radio:
                http_post(
                    f"{HA_API}/services/media_player/media_pause",
                    headers={"Authorization": f"Bearer {HA_TOKEN}"},
                    json_data={"entity_id": RADIO_ENTITY},
                )
        return

    # === RESUME: Satellite kommt zur├╝ck zu idle ===
    if sat_state == "idle" and _ducking_active:
        # POLLING-ANSATZ: Pr├╝fe Boolean alle 0.5s f├╝r max 15s.
        #
        # WARUM POLLING statt einmaligem Wait?
        # Die Stopp-Automation l├ñuft als Sentence-Trigger in der Pipeline.
        # Je nach HA-Last kann sie VOR oder NACH satelliteÔåÆidle fertig sein.
        # Mit Polling erkennen wir den Boolean-Wechsel sofort wenn er kommt,
        # statt blind 3s zu warten und dann zu sp├ñt oder zu fr├╝h zu pr├╝fen.
        #
        # Ablauf:
        # - Alle 0.5s: Boolean pr├╝fen + Satellite-State pr├╝fen
        # - Boolean OFF ÔåÆ Stopp-Intent erkannt ÔåÆ sofort KEIN Resume
        # - Boolean ON nach 15s ÔåÆ normales Ducking ÔåÆ Resume
        # - Satellite nicht mehr idle ÔåÆ abbrechen, n├ñchsten ├£bergang abwarten
        RESUME_POLL_INTERVAL = 0.5
        RESUME_POLL_MAX = 15.0  # Sekunden (genug f├╝r langsame Pipelines)
        elapsed = 0.0
        stop_detected = False

        while elapsed < RESUME_POLL_MAX:
            time.sleep(RESUME_POLL_INTERVAL)
            elapsed += RESUME_POLL_INTERVAL

            # Satellite immer noch idle?
            sat_recheck = ha_get_satellite_state()
            if sat_recheck != "idle":
                log.info("­ƒöç Ducking: Satellite=%s w├ñhrend Wartezeit ÔåÆ warte weiter",
                         sat_recheck)
                _last_satellite_state = sat_recheck
                return  # N├ñchster idle-├£bergang wird erneut gepr├╝ft

            # Boolean pr├╝fen
            bool_data, bool_status = http_get(
                f"{HA_API}/states/input_boolean.spotify_ducking_active",
                headers={"Authorization": f"Bearer {HA_TOKEN}"},
            )
            ducking_bool = bool_data.get("state", "unknown") if bool_status == 200 else "unknown"

            if ducking_bool != "on":
                # OFF ÔåÆ Stopp-Intent erkannt!
                stop_detected = True
                log.info("­ƒöç Ducking: Boolean='%s' nach %.1fs ÔåÆ Stopp erkannt ÔåÆ KEIN Resume",
                         ducking_bool, elapsed)
                log.info("­ƒöç Ducking: Pipeline-Dauer bis Boolean OFF: %.1fs", elapsed)
                # MEDIA_STOP senden damit Spotify WIRKLICH stoppt
                if _ducking_was_spotify:
                    adb_shell("input keyevent KEYCODE_MEDIA_STOP", timeout_s=3)
                    log.info("­ƒöç Ducking: MEDIA_STOP gesendet ÔåÆ Spotify gestoppt")
                break

        if not stop_detected:
            # Boolean war die ganze Zeit ON ÔåÆ normales Ducking ÔåÆ Resume
            sources = "+".join(filter(None, [
                "Spotify" if _ducking_was_spotify else "",
                "Radio" if _ducking_was_radio else "",
            ]))
            log.info("­ƒöè Ducking Ende: Resume nach %.1fs (%s) ÔÇö Boolean blieb ON",
                     elapsed, sources)
            adb_shell("input keyevent KEYCODE_MEDIA_PLAY", timeout_s=3)
            if _ducking_was_radio:
                http_post(
                    f"{HA_API}/services/media_player/media_play",
                    headers={"Authorization": f"Bearer {HA_TOKEN}"},
                    json_data={"entity_id": RADIO_ENTITY},
                )

        # Aufr├ñumen
        _ducking_active = False
        _ducking_was_spotify = False
        _ducking_was_radio = False
        http_post(
            f"{HA_API}/services/input_boolean/turn_off",
            headers={"Authorization": f"Bearer {HA_TOKEN}"},
            json_data={"entity_id": "input_boolean.spotify_ducking_active"},
        )

# ============================================================================
# PID FILE
# ============================================================================

def write_pid():
    try:
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def kill_old_instance():
    try:
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())
        if old_pid != os.getpid():
            os.kill(old_pid, signal.SIGTERM)
            log.info("Alte Instanz (PID %d) beendet", old_pid)
            time.sleep(1)
    except (FileNotFoundError, ValueError, ProcessLookupError, PermissionError):
        pass


def cleanup_pid(*_):
    adb_disconnect()
    try:
        os.remove(PID_FILE)
    except Exception:
        pass
    sys.exit(0)

# ============================================================================
# HAUPTSCHLEIFE
# ============================================================================

def main():
    kill_old_instance()
    write_pid()
    signal.signal(signal.SIGTERM, cleanup_pid)
    signal.signal(signal.SIGINT, cleanup_pid)

    log.info("=" * 50)
    log.info("Spotify Monitor v3 gestartet (PID %d)", os.getpid())
    log.info("Modus: ADB MediaSession + Keep-Alive + Ducking")
    log.info("Echo Show: %s:%d", ECHO_HOST, ECHO_PORT)
    log.info("Poll: %.1fs aktiv, %ds idle", POLL_INTERVAL, POLL_INTERVAL_IDLE)
    log.info("Keep-Alive: alle %ds", KEEPALIVE_INTERVAL)
    log.info("=" * 50)

    # State-Tracking
    last_description = None
    last_state = None
    last_active_item = None
    consecutive_errors = 0
    display_on_music = False
    last_keepalive_check = 0

    while True:
        try:
            # ============================================================
            # ADB-Verbindung sicherstellen
            # ============================================================
            if not _adb_device:
                if not adb_connect():
                    consecutive_errors += 1
                    wait = min(ADB_RECONNECT_WAIT * consecutive_errors, 120)
                    log.warning("ADB Reconnect in %ds...", wait)
                    time.sleep(wait)
                    continue
                consecutive_errors = 0
                # Einmaliges Setup bei erster Verbindung
                keepalive_init()

            # ============================================================
            # Keep-Alive Check (alle 30s)
            # ============================================================
            now = time.monotonic()
            if now - last_keepalive_check > KEEPALIVE_INTERVAL:
                keepalive_check()
                last_keepalive_check = now

            # ============================================================
            # MediaSession auslesen (~94ms)
            # ============================================================
            current = adb_get_media_session()

            # ============================================================
            # Ducking Check (bei jedem Poll!)
            # ============================================================
            current_state = current["state"] if current else STATE_NONE
            ducking_check(current_state)

            # ============================================================
            # FALL 1: Kein Spotify aktiv
            # ============================================================
            if current is None:
                if last_state is not None and last_state == STATE_PLAYING:
                    log.info("Spotify gestoppt (keine aktive Session)")
                    ha_update_entity()
                    if display_on_music:
                        ha_navigate(VA_HOME_PATH)
                        display_on_music = False

                last_description = None
                last_state = None
                last_active_item = None
                time.sleep(POLL_INTERVAL_IDLE)
                continue

            title = current["title"]
            artist = current["artist"]
            state = current["state"]
            description = current["description"]
            active_item = current["active_item_id"]
            consecutive_errors = 0

            # ============================================================
            # FALL 2: Titelwechsel erkannt!
            # ============================================================
            if active_item >= 0 and last_active_item is not None:
                title_changed = active_item != last_active_item
            else:
                title_changed = description != last_description

            if title_changed:
                if last_description is not None:
                    log.info("ÔûÂ Titelwechsel: %s ÔÇö %s", artist, title)
                else:
                    log.info("ÔûÂ Erster Titel: %s ÔÇö %s", artist, title)

                # 1) HA Entity sofort aktualisieren
                #    (W├ñhrend Ducking auch OK ÔÇö wir nutzen den input_boolean
                #    als Signal, nicht den HA Spotify State)
                ha_update_entity()

                # 2) last_played Input-Text updaten
                display_text = f"{artist} - {title}" if artist else title
                ha_set_input_text("input_text.spotify_last_played", display_text)

                # 3) Display auf Music-View (nicht wenn Ducking aktiv)
                if state == STATE_PLAYING and not _ducking_active:
                    ha_navigate(VA_MUSIC_PATH, revert_timeout=3600)
                    display_on_music = True

                last_description = description
                last_active_item = active_item

            # ============================================================
            # FALL 3: Play/Pause Toggle
            # ============================================================
            if state != last_state:
                if last_state is not None:
                    # Bei Ducking: State-Wechsel nicht navigieren
                    if _ducking_active:
                        log.debug("State-Wechsel w├ñhrend Ducking: %s ÔåÆ %s",
                                  STATE_NAMES.get(last_state, "?"),
                                  STATE_NAMES.get(state, "?"))
                    elif state == STATE_PLAYING:
                        log.info("ÔûÂ Wiedergabe fortgesetzt: %s ÔÇö %s", artist, title)
                        ha_update_entity()
                        ha_navigate(VA_MUSIC_PATH, revert_timeout=3600)
                        display_on_music = True
                    elif state == STATE_PAUSED:
                        log.info("ÔÅ© Pausiert: %s ÔÇö %s", artist, title)
                        ha_update_entity()
                        if display_on_music:
                            ha_navigate(VA_HOME_PATH)
                            display_on_music = False
                    elif state == STATE_STOPPED:
                        log.info("ÔÅ╣ Gestoppt")
                        ha_update_entity()
                        if display_on_music:
                            ha_navigate(VA_HOME_PATH)
                            display_on_music = False

                last_state = state

            # Adaptive Polling ÔÇö SCHNELL w├ñhrend Ducking!
            if _ducking_active:
                time.sleep(POLL_INTERVAL)       # 0.5s ÔÇö muss satelliteÔåÆidle schnell erkennen
            elif state == STATE_PLAYING:
                time.sleep(POLL_INTERVAL)
            else:
                time.sleep(POLL_INTERVAL_IDLE)

        except KeyboardInterrupt:
            break
        except Exception as e:
            consecutive_errors += 1
            log.error("Fehler (#%d): %s", consecutive_errors, e)
            adb_disconnect()
            wait = min(10 * consecutive_errors, 120)
            time.sleep(wait)

    cleanup_pid()


if __name__ == "__main__":
    main()
