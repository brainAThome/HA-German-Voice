#!/usr/bin/env python3
"""
Spotify Track Monitor v3 — ADB MediaSession + Keep-Alive + Ducking
===================================================================
Alles-in-einem-Daemon für Jarvis (Echo Show 5 mit LineageOS):

1. TRACK MONITOR — Erkennt Titelwechsel/Play/Pause via ADB MediaSession
   → HA Entity-Update erzwingen, Display-Navigation

2. KEEP-ALIVE — Hält Spotify App permanent im Hintergrund am Leben
   → Prüft alle 30s ob Spotify-Prozess läuft, startet ihn falls nicht
   → Doze-Whitelist → Android killt ihn nicht
   → VACA bleibt immer im Vordergrund (kein App-Stealing)

3. DUCKING — Pausiert Musik bei Spracheingabe via ADB KeyEvent
   → Pollt assist_satellite State via HA API
   → Bei Spracheingabe: KEYCODE_MEDIA_PAUSE (~100ms statt 2-3s)
   → Bei Ende: KEYCODE_MEDIA_PLAY

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
from datetime import datetime, timezone

# ============================================================================
# KONFIGURATION
# ============================================================================

POLL_INTERVAL = float(os.getenv("SPOTIFY_POLL_INTERVAL", "0.5"))
POLL_INTERVAL_IDLE = float(os.getenv("SPOTIFY_POLL_INTERVAL_IDLE", "1.0"))
ADB_RECONNECT_WAIT = 10    # Sekunden zwischen Reconnect-Versuchen
ADB_TIMEOUT = 8            # ADB-Verbindungs-Timeout

ECHO_HOST = "192.168.178.103"
ECHO_PORT = 5555
ADB_KEY_PATH = "/config/.storage/adbkey"


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

HA_API = "http://localhost:8123/api"
SPOTIFY_ENTITY = os.getenv("SPOTIFY_ENTITY", "media_player.spotify_sven")
SATELLITE_ENTITY = os.getenv("SATELLITE_ENTITY", "assist_satellite.vaca_362812d56")
RADIO_ENTITY = os.getenv("RADIO_ENTITY", "media_player.vaca_362812d56_mediaplayer")
VA_DEVICE = os.getenv("VA_DEVICE", "sensor.quasselbuechse")
VA_MUSIC_PATH = "/view-assist/music"
VA_HOME_PATH = "/view-assist/clock"

# Keep-Alive
KEEPALIVE_INTERVAL = int(os.getenv("SPOTIFY_KEEPALIVE_INTERVAL", "8"))
SPOTIFY_KEEPALIVE_MIN_RESTART_GAP_SECONDS = int(os.getenv("SPOTIFY_KEEPALIVE_MIN_RESTART_GAP_SECONDS", "30"))
SPOTIFY_PACKAGE = "com.spotify.music"
SPOTIFY_KEEPALIVE_ENABLED = env_bool("SPOTIFY_KEEPALIVE_ENABLED", default=True)
SPOTIFY_KEEPALIVE_ONLY_WHEN_ACTIVE = env_bool("SPOTIFY_KEEPALIVE_ONLY_WHEN_ACTIVE", default=False)
JARVIS_SPOTIFY_NAME = os.getenv("JARVIS_SPOTIFY_NAME", "").strip().strip("\"'")
SPOTIFY_VOLUME_SYNC_ENABLED = env_bool("SPOTIFY_VOLUME_SYNC_ENABLED", default=True)
SPOTIFY_VOLUME_SYNC_INTERVAL = float(os.getenv("SPOTIFY_VOLUME_SYNC_INTERVAL", "0.7"))
SPOTIFY_VOLUME_MAX_STEPS = int(os.getenv("SPOTIFY_VOLUME_MAX_STEPS", "15"))
SPOTIFY_VOLUME_SYNC_ONLY_WHEN_PLAYING = env_bool("SPOTIFY_VOLUME_SYNC_ONLY_WHEN_PLAYING", default=True)
SPOTIFY_VOLUME_SYNC_REQUIRE_SOURCE_MATCH = env_bool("SPOTIFY_VOLUME_SYNC_REQUIRE_SOURCE_MATCH", default=True)
SPOTIFY_VOLUME_CACHE_FILE = os.getenv("SPOTIFY_VOLUME_CACHE_FILE", "/config/scripts/.spotify_last_volume")
SPOTIFY_HA_FAST_REFRESH_ENABLED = env_bool("SPOTIFY_HA_FAST_REFRESH_ENABLED", default=True)
SPOTIFY_HA_FAST_REFRESH_INTERVAL = float(os.getenv("SPOTIFY_HA_FAST_REFRESH_INTERVAL", "1.2"))
SPOTIFY_USER_STOP_COOLDOWN_SECONDS = int(os.getenv("SPOTIFY_USER_STOP_COOLDOWN_SECONDS", "900"))
SPOTIFY_USER_STOP_MARKER_FILE = os.getenv("SPOTIFY_USER_STOP_MARKER_FILE", "/config/scripts/.spotify_user_stop_until")
SPOTIFY_ALWAYS_REACHABLE = env_bool("SPOTIFY_ALWAYS_REACHABLE", default=True)
SPOTIFY_STOP_PAUSE_VIA_HA = env_bool("SPOTIFY_STOP_PAUSE_VIA_HA", default=True)
SPOTIFY_DUCKING_CONTROL_VIA_HA = env_bool("SPOTIFY_DUCKING_CONTROL_VIA_HA", default=True)

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
log.propagate = False  # Prevent duplicate messages via root logger

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


def _find_first_entity(states, predicate):
    for item in states:
        entity_id = item.get("entity_id", "")
        attrs = item.get("attributes", {}) or {}
        if predicate(entity_id, attrs):
            return entity_id
    return ""


def autodiscover_entities():
    global SPOTIFY_ENTITY, SATELLITE_ENTITY, RADIO_ENTITY, VA_DEVICE

    if all([
        ha_entity_exists(SPOTIFY_ENTITY),
        ha_entity_exists(SATELLITE_ENTITY),
        ha_entity_exists(VA_DEVICE),
    ]):
        return

    states = ha_list_states()
    if not states:
        log.warning("Auto-Discovery: keine /states-Daten erhalten")
        return

    if not ha_entity_exists(SPOTIFY_ENTITY):
        discovered = _find_first_entity(
            states,
            lambda entity_id, attrs: entity_id.startswith("media_player.spotify"),
        )
        if discovered:
            log.info("Auto-Discovery: SPOTIFY_ENTITY %s -> %s", SPOTIFY_ENTITY, discovered)
            SPOTIFY_ENTITY = discovered

    if not ha_entity_exists(SATELLITE_ENTITY):
        discovered = _find_first_entity(
            states,
            lambda entity_id, attrs: entity_id.startswith("assist_satellite."),
        )
        if discovered:
            log.info("Auto-Discovery: SATELLITE_ENTITY %s -> %s", SATELLITE_ENTITY, discovered)
            SATELLITE_ENTITY = discovered

    if not ha_entity_exists(RADIO_ENTITY):
        discovered = _find_first_entity(
            states,
            lambda entity_id, attrs: entity_id.startswith("media_player.") and "vaca" in entity_id and "mediaplayer" in entity_id,
        )
        if discovered:
            log.info("Auto-Discovery: RADIO_ENTITY %s -> %s", RADIO_ENTITY, discovered)
            RADIO_ENTITY = discovered

    if not ha_entity_exists(VA_DEVICE):
        discovered = _find_first_entity(
            states,
            lambda entity_id, attrs: entity_id.startswith("sensor.") and (
                "quassel" in entity_id.lower() or "vaca" in entity_id.lower() or "display" in entity_id.lower()
            ),
        )
        if discovered:
            log.info("Auto-Discovery: VA_DEVICE %s -> %s", VA_DEVICE, discovered)
            VA_DEVICE = discovered

# ============================================================================
# ADB MediaSession — Kern des Monitors
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
    """Führt ADB Shell-Befehl aus. Thread-safe.
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
        "echo \"$MS\" | awk '"
        "/com\\.spotify\\.music/ {in_sp=1} "
        "in_sp && /state=PlaybackState/ {print; next} "
        "in_sp && /description=/ {print; next} "
        "in_sp && /active=/ {print; next} "
        "in_sp && /^ +package=/ && $0 !~ /com\\.spotify\\.music/ {in_sp=0} "
        "'"
    )

    if not raw or "description=" not in raw:
        return None

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    desc_line = ""
    state_line = ""
    active_line = ""
    for line in lines:
        if "description=" in line:
            desc_line = line
        elif "state=PlaybackState" in line:
            state_line = line
        elif "active=" in line:
            active_line = line

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
        log.info("Display → %s", path)


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

    WICHTIG: Bei HTTP-Fehler wird der LETZTE bekannte State zurückgegeben,
    NICHT 'idle'. Sonst wird bei einem Timeout fälschlich idle erkannt
    und Ducking-Resume ausgelöst.
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


def ha_get_entity(entity_id):
    """Liest ein HA-Entity inkl. attributes."""
    data, status = http_get(
        f"{HA_API}/states/{entity_id}",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        timeout=5,
    )
    if status == 200 and isinstance(data, dict):
        return data
    return None


def _clamp(value, low, high):
    return max(low, min(high, value))


def _source_is_jarvis(source_name):
    source_l = (source_name or "").strip().lower()
    if not source_l:
        return False
    if JARVIS_SPOTIFY_NAME:
        return source_l == JARVIS_SPOTIFY_NAME.lower()
    return ("jarvis" in source_l) or ("echo" in source_l) or ("show" in source_l)


def _save_cached_volume_index(index_value):
    try:
        with open(SPOTIFY_VOLUME_CACHE_FILE, "w", encoding="utf-8") as handle:
            handle.write(str(int(index_value)))
    except Exception:
        pass


def _load_cached_volume_index():
    try:
        with open(SPOTIFY_VOLUME_CACHE_FILE, "r", encoding="utf-8") as handle:
            raw = handle.read().strip()
        if raw == "":
            return None
        return int(raw)
    except Exception:
        return None


def _set_user_stop_cooldown():
    if SPOTIFY_USER_STOP_COOLDOWN_SECONDS <= 0:
        return
    try:
        until_ts = int(time.time() + SPOTIFY_USER_STOP_COOLDOWN_SECONDS)
        with open(SPOTIFY_USER_STOP_MARKER_FILE, "w", encoding="utf-8") as handle:
            handle.write(str(until_ts))
        log.info("Keep-Alive: Nutzer-Stopp erkannt, Cooldown %ds aktiv", SPOTIFY_USER_STOP_COOLDOWN_SECONDS)
    except Exception:
        pass


def _get_user_stop_cooldown_remaining():
    try:
        with open(SPOTIFY_USER_STOP_MARKER_FILE, "r", encoding="utf-8") as handle:
            raw = handle.read().strip()
        if raw == "":
            return 0
        until_ts = int(raw)
        remaining = until_ts - int(time.time())
        return remaining if remaining > 0 else 0
    except Exception:
        return 0


def _clear_user_stop_cooldown():
    try:
        os.remove(SPOTIFY_USER_STOP_MARKER_FILE)
        log.info("Keep-Alive: Nutzer-Stopp-Cooldown aufgehoben")
    except FileNotFoundError:
        pass
    except Exception:
        pass


def sync_volume_from_ha(last_volume_level):
    """Übernimmt HA-Volume (0..1) auf Echo STREAM_MUSIC via ADB cmd media_session."""
    if not SPOTIFY_VOLUME_SYNC_ENABLED:
        return last_volume_level

    state = ha_get_entity(SPOTIFY_ENTITY)
    if not state:
        return last_volume_level

    playback_state = (state.get("state") or "").lower()
    attrs = state.get("attributes", {}) or {}
    source_name = (attrs.get("source") or "").strip()

    if SPOTIFY_VOLUME_SYNC_ONLY_WHEN_PLAYING and playback_state != "playing":
        return last_volume_level

    if SPOTIFY_VOLUME_SYNC_REQUIRE_SOURCE_MATCH and not _source_is_jarvis(source_name):
        return last_volume_level

    raw_level = attrs.get("volume_level")
    if raw_level is None:
        return last_volume_level

    try:
        level = float(raw_level)
    except (TypeError, ValueError):
        return last_volume_level

    level = _clamp(level, 0.0, 1.0)
    if last_volume_level is not None and abs(level - last_volume_level) < 0.01:
        return last_volume_level

    max_steps = SPOTIFY_VOLUME_MAX_STEPS if SPOTIFY_VOLUME_MAX_STEPS > 0 else 15
    target_index = int(round(level * max_steps))
    target_index = _clamp(target_index, 0, max_steps)

    adb_shell(
        f"cmd media_session volume --stream 3 --set {target_index}",
        timeout_s=3,
    )
    _save_cached_volume_index(target_index)
    log.info("Volume-Sync: HA %.2f -> Echo index %d/%d", level, target_index, max_steps)
    return level

# ============================================================================
# KEEP-ALIVE: Spotify App permanent im Hintergrund
# ============================================================================

_keepalive_initialized = False
_last_keepalive_launch_ts = 0.0


def keepalive_init():
    """Einmaliges Setup: Doze-Whitelist + Spotify im Hintergrund starten."""
    global _keepalive_initialized
    if not SPOTIFY_KEEPALIVE_ENABLED:
        return
    if _keepalive_initialized:
        return

    # Spotify in Doze-Whitelist → Android killt es nicht im Deep Sleep
    result = adb_shell(
        f"dumpsys deviceidle whitelist +{SPOTIFY_PACKAGE} 2>/dev/null; "
        f"cmd appops set {SPOTIFY_PACKAGE} RUN_IN_BACKGROUND allow 2>/dev/null; "
        f"cmd appops set {SPOTIFY_PACKAGE} RUN_ANY_IN_BACKGROUND allow 2>/dev/null",
        timeout_s=10,
    )
    if result is not None:
        log.info("Keep-Alive: Spotify in Doze-Whitelist + Background-Erlaubnis gesetzt")
        cached_volume = _load_cached_volume_index()
        if cached_volume is not None:
            adb_shell(
                f"cmd media_session volume --stream 3 --set {cached_volume}",
                timeout_s=3,
            )
            log.info("Volume-Restore: Echo index %d aus Cache gesetzt", cached_volume)
        _keepalive_initialized = True

def _keepalive_should_run_now():
    if not SPOTIFY_KEEPALIVE_ONLY_WHEN_ACTIVE:
        return True

    data, status = http_get(
        f"{HA_API}/states/{SPOTIFY_ENTITY}",
        headers={"Authorization": f"Bearer {HA_TOKEN}"},
        timeout=5,
    )
    if status != 200:
        return False

    state = (data.get("state") or "").lower()
    attrs = data.get("attributes", {}) or {}
    source = (attrs.get("source") or "").strip()

    if state != "playing":
        return False

    position_updated_at = attrs.get("media_position_updated_at")
    if position_updated_at:
        try:
            ts = datetime.fromisoformat(position_updated_at.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            if age > (KEEPALIVE_INTERVAL + 20):
                return False
        except Exception:
            pass

    if not source:
        return False

    src_l = source.lower()
    if JARVIS_SPOTIFY_NAME:
        return src_l == JARVIS_SPOTIFY_NAME.lower()

    return ("echo" in src_l) or ("show" in src_l)


def keepalive_check(force=False):
    """Prüft ob Spotify läuft. Falls nicht: im Hintergrund starten.

    Startet Spotify und bringt sofort VACA wieder in den Vordergrund.
    """
    if not SPOTIFY_KEEPALIVE_ENABLED:
        return True

    if not force and not _keepalive_should_run_now():
        return True

    result = adb_shell(f"pidof {SPOTIFY_PACKAGE}", timeout_s=3)
    if result and result.strip():
        return True  # Spotify läuft

    cooldown_remaining = _get_user_stop_cooldown_remaining()
    if cooldown_remaining > 0 and not SPOTIFY_ALWAYS_REACHABLE:
        log.info("Keep-Alive: Nutzer-Stopp-Cooldown aktiv (%ds verbleibend), kein Auto-Restart", cooldown_remaining)
        return True

    if cooldown_remaining > 0 and SPOTIFY_ALWAYS_REACHABLE:
        log.info("Keep-Alive: Nutzer-Stopp-Cooldown aktiv (%ds), starte nur App für Connect-Erreichbarkeit", cooldown_remaining)

    global _last_keepalive_launch_ts

    now_mono = time.monotonic()
    if SPOTIFY_KEEPALIVE_MIN_RESTART_GAP_SECONDS > 0:
        since_last = now_mono - _last_keepalive_launch_ts
        if _last_keepalive_launch_ts > 0 and since_last < SPOTIFY_KEEPALIVE_MIN_RESTART_GAP_SECONDS:
            wait_left = int(SPOTIFY_KEEPALIVE_MIN_RESTART_GAP_SECONDS - since_last)
            log.info("Keep-Alive: Restart-Backoff aktiv (%ds), überspringe Neustart", wait_left)
            return False

    log.warning("Keep-Alive: Spotify-Prozess nicht gefunden, starte...")
    _last_keepalive_launch_ts = now_mono

    # Spotify starten — monkey ist der zuverlässigste Weg
    adb_shell(
        f"monkey -p {SPOTIFY_PACKAGE} -c android.intent.category.LAUNCHER 1 2>/dev/null",
        timeout_s=10,
    )
    # Warte kurz, dann VACA sofort wieder in den Vordergrund
    time.sleep(2)
    adb_shell(
        "am start -n com.msp1974.vacompanion/.MainActivity "
        "-a android.intent.action.MAIN",
        timeout_s=5,
    )
    time.sleep(0.3)
    adb_shell("settings put system screen_off_timeout 86400000", timeout_s=5)

    # Prüfen ob es jetzt läuft
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
    - WIR setzen input_boolean → ON beim Ducking-Start
    - Stopp-Automation setzt input_boolean → OFF als ERSTE Aktion
    - Nach 3s Wartezeit: ON = normales Ducking → Resume,
                          OFF = Stopp-Intent → kein Resume
    """
    global _ducking_active, _last_satellite_state
    global _ducking_was_spotify, _ducking_was_radio

    sat_state = ha_get_satellite_state()

    # Satellite hat sich nicht geändert → nichts zu tun
    if sat_state == _last_satellite_state:
        return
    old_state = _last_satellite_state
    _last_satellite_state = sat_state

    # === PAUSE: Satellite verlässt idle → Spracheingabe beginnt ===
    if old_state == "idle" and sat_state != "idle":
        # Was läuft gerade? Spotify (ADB) und/oder Radio (HA)
        _ducking_was_spotify = (current_spotify_state == STATE_PLAYING)
        radio_state = ha_get_entity_state(RADIO_ENTITY)
        _ducking_was_radio = (radio_state == "playing")

        if _ducking_was_spotify or _ducking_was_radio:
            sources = []
            if _ducking_was_spotify:
                sources.append("Spotify")
            if _ducking_was_radio:
                sources.append("Radio")
            log.info("🔇 Ducking: Satellite=%s, pausiere %s",
                     sat_state, "+".join(sources))
            _ducking_active = True

            # WICHTIG: Boolean ON ZUERST setzen, BEVOR ADB/Radio!
            # Race-Condition-Fix: ADB dauert 1-3s. Wenn die Stopp-Automation
            # Boolean OFF setzt BEVOR unser ON ankommt, überschreiben wir
            # das OFF und der Monitor denkt "kein Stopp" → falsches Resume.
            http_post(
                f"{HA_API}/services/input_boolean/turn_on",
                headers={"Authorization": f"Bearer {HA_TOKEN}"},
                json_data={"entity_id": "input_boolean.spotify_ducking_active"},
            )

            # Spotify pausieren (prefer HA service to avoid MEDIA_BUTTON ANR)
            if _ducking_was_spotify and SPOTIFY_DUCKING_CONTROL_VIA_HA:
                http_post(
                    f"{HA_API}/services/media_player/media_pause",
                    headers={"Authorization": f"Bearer {HA_TOKEN}"},
                    json_data={"entity_id": SPOTIFY_ENTITY},
                )
            else:
                adb_shell("input keyevent KEYCODE_MEDIA_PAUSE", timeout_s=3)

            # Radio zusätzlich via HA pausieren (falls nicht via ADB)
            if _ducking_was_radio:
                http_post(
                    f"{HA_API}/services/media_player/media_pause",
                    headers={"Authorization": f"Bearer {HA_TOKEN}"},
                    json_data={"entity_id": RADIO_ENTITY},
                )
        return

    # === RESUME: Satellite kommt zurück zu idle ===
    if sat_state == "idle" and _ducking_active:
        # POLLING-ANSATZ: Prüfe Boolean alle 0.5s für max 15s.
        #
        # WARUM POLLING statt einmaligem Wait?
        # Die Stopp-Automation läuft als Sentence-Trigger in der Pipeline.
        # Je nach HA-Last kann sie VOR oder NACH satellite→idle fertig sein.
        # Mit Polling erkennen wir den Boolean-Wechsel sofort wenn er kommt,
        # statt blind 3s zu warten und dann zu spät oder zu früh zu prüfen.
        #
        # Ablauf:
        # - Alle 0.5s: Boolean prüfen + Satellite-State prüfen
        # - Boolean OFF → Stopp-Intent erkannt → sofort KEIN Resume
        # - Boolean ON nach 15s → normales Ducking → Resume
        # - Satellite nicht mehr idle → abbrechen, nächsten Übergang abwarten
        RESUME_POLL_INTERVAL = 0.5
        RESUME_POLL_MAX = 15.0  # Sekunden (genug für langsame Pipelines)
        elapsed = 0.0
        stop_detected = False

        while elapsed < RESUME_POLL_MAX:
            time.sleep(RESUME_POLL_INTERVAL)
            elapsed += RESUME_POLL_INTERVAL

            # Satellite immer noch idle?
            sat_recheck = ha_get_satellite_state()
            if sat_recheck != "idle":
                log.info("🔇 Ducking: Satellite=%s während Wartezeit → warte weiter",
                         sat_recheck)
                _last_satellite_state = sat_recheck
                return  # Nächster idle-Übergang wird erneut geprüft

            # Boolean prüfen
            bool_data, bool_status = http_get(
                f"{HA_API}/states/input_boolean.spotify_ducking_active",
                headers={"Authorization": f"Bearer {HA_TOKEN}"},
            )
            ducking_bool = bool_data.get("state", "unknown") if bool_status == 200 else "unknown"

            if ducking_bool != "on":
                # OFF → Stopp-Intent erkannt!
                stop_detected = True
                log.info("🔇 Ducking: Boolean='%s' nach %.1fs → Stopp erkannt → KEIN Resume",
                         ducking_bool, elapsed)
                log.info("🔇 Ducking: Pipeline-Dauer bis Boolean OFF: %.1fs", elapsed)
                _set_user_stop_cooldown()
                # Automation hat bereits media_pause gesendet → hier NICHT
                # nochmal senden, um doppelte Befehle zu vermeiden.
                log.info("🔇 Ducking: Stopp-Automation hat pausiert, kein erneuter Pause-Befehl nötig")
                break

        if not stop_detected:
            # Boolean war die ganze Zeit ON → normales Ducking → Resume
            sources = "+".join(filter(None, [
                "Spotify" if _ducking_was_spotify else "",
                "Radio" if _ducking_was_radio else "",
            ]))
            log.info("🔊 Ducking Ende: Resume nach %.1fs (%s) — Boolean blieb ON",
                     elapsed, sources)
            if _ducking_was_spotify:
                if SPOTIFY_DUCKING_CONTROL_VIA_HA:
                    http_post(
                        f"{HA_API}/services/media_player/media_play",
                        headers={"Authorization": f"Bearer {HA_TOKEN}"},
                        json_data={"entity_id": SPOTIFY_ENTITY},
                    )
                else:
                    adb_shell("input keyevent KEYCODE_MEDIA_PLAY", timeout_s=3)
            if _ducking_was_radio:
                http_post(
                    f"{HA_API}/services/media_player/media_play",
                    headers={"Authorization": f"Bearer {HA_TOKEN}"},
                    json_data={"entity_id": RADIO_ENTITY},
                )

        # Aufräumen
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
            log.info("Alte Instanz (PID %d) SIGTERM gesendet", old_pid)
            time.sleep(2)
            # Prüfen ob noch am Leben → SIGKILL
            try:
                os.kill(old_pid, 0)  # Existenz prüfen
                os.kill(old_pid, signal.SIGKILL)
                log.warning("Alte Instanz (PID %d) SIGKILL gesendet", old_pid)
                time.sleep(1)
            except ProcessLookupError:
                pass  # Bereits beendet
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
    if SPOTIFY_KEEPALIVE_ENABLED:
        log.info("Keep-Alive: aktiv (Intervall %ds)", KEEPALIVE_INTERVAL)
    else:
        log.info("Keep-Alive: deaktiviert (HA-only Modus)")
    log.info("=" * 50)

    autodiscover_entities()
    log.info("Entities: spotify=%s satellite=%s radio=%s display=%s",
             SPOTIFY_ENTITY, SATELLITE_ENTITY, RADIO_ENTITY, VA_DEVICE)

    # State-Tracking
    last_description = None
    last_state = None
    last_active_item = None
    consecutive_errors = 0
    consecutive_none = 0          # Session-Flicker-Debounce
    SESSION_NONE_THRESHOLD = 3    # N aufeinanderfolgende None-Polls nötig
    display_on_music = False
    last_keepalive_check = 0
    last_volume_sync_check = 0.0
    last_ha_volume_level = None
    last_fast_refresh_check = 0.0

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
                autodiscover_entities()
                # Einmaliges Setup bei erster Verbindung
                keepalive_init()

            # ============================================================
            # Keep-Alive Check (alle 30s)
            # ============================================================
            now = time.monotonic()
            if SPOTIFY_KEEPALIVE_ENABLED and now - last_keepalive_check > KEEPALIVE_INTERVAL:
                keepalive_check()
                last_keepalive_check = now

            if SPOTIFY_VOLUME_SYNC_ENABLED and now - last_volume_sync_check > SPOTIFY_VOLUME_SYNC_INTERVAL:
                last_ha_volume_level = sync_volume_from_ha(last_ha_volume_level)
                last_volume_sync_check = now

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
            # FALL 1: Kein Spotify aktiv (mit Flicker-Debounce)
            # ============================================================
            if current is None:
                consecutive_none += 1
                if consecutive_none < SESSION_NONE_THRESHOLD:
                    # Noch nicht sicher ob wirklich weg → kurzer Poll
                    time.sleep(POLL_INTERVAL)
                    continue
                # Sicher: Session ist wirklich weg
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
            consecutive_none = 0  # Session da → Flicker-Zähler zurücksetzen

            if (
                SPOTIFY_HA_FAST_REFRESH_ENABLED
                and state == STATE_PLAYING
                and now - last_fast_refresh_check > SPOTIFY_HA_FAST_REFRESH_INTERVAL
            ):
                if _get_user_stop_cooldown_remaining() > 0:
                    _clear_user_stop_cooldown()
                ha_update_entity()
                last_fast_refresh_check = now

            # ============================================================
            # FALL 2: Titelwechsel erkannt!
            # ============================================================
            if active_item >= 0 and last_active_item is not None:
                title_changed = active_item != last_active_item
            else:
                title_changed = description != last_description

            if title_changed:
                if last_description is not None:
                    log.info("▶ Titelwechsel: %s — %s", artist, title)
                else:
                    log.info("▶ Erster Titel: %s — %s", artist, title)

                # 1) HA Entity sofort aktualisieren
                #    (Während Ducking auch OK — wir nutzen den input_boolean
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
                        log.debug("State-Wechsel während Ducking: %s → %s",
                                  STATE_NAMES.get(last_state, "?"),
                                  STATE_NAMES.get(state, "?"))
                    elif state == STATE_PLAYING:
                        log.info("▶ Wiedergabe fortgesetzt: %s — %s", artist, title)
                        ha_update_entity()
                        ha_navigate(VA_MUSIC_PATH, revert_timeout=3600)
                        display_on_music = True
                    elif state == STATE_PAUSED:
                        log.info("⏸ Pausiert: %s — %s", artist, title)
                        ha_update_entity()
                        if display_on_music:
                            ha_navigate(VA_HOME_PATH)
                            display_on_music = False
                    elif state == STATE_STOPPED:
                        log.info("⏹ Gestoppt")
                        ha_update_entity()
                        if display_on_music:
                            ha_navigate(VA_HOME_PATH)
                            display_on_music = False

                last_state = state

            # Adaptive Polling — SCHNELL während Ducking!
            if _ducking_active:
                time.sleep(POLL_INTERVAL)       # 0.5s — muss satellite→idle schnell erkennen
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
