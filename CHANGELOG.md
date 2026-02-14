# HA-German-Voice - CHANGELOG

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

## [5.0.0] - 2026-02-14

### ⏰🛑 Erinnerungs-Komplettsystem + Universeller Stopp & Löschen

Kompletter Umbau des Erinnerungs- und Wecker-Systems: 3-fach Alarm mit nativem
VA Alarm-Sound und Info-Karte, flexibles Intent-Matching, getrennte Lösch-Befehle
für Erinnerungen und Wecker, universeller Stopp für alle laufenden Alarme.

### Hinzugefügt
- **3-fach Alarm bei Erinnerung**: 3 Runden (TTS-Ansage + 3.5s nativer Alarm-Switch)
  statt einfacher TTS-Ansage
- **VA Info-Karte**: Erinnerungstext wird als native VA Info-Karte auf dem Display
  angezeigt (`/view-assist/info` View) — kein Custom-Dashboard-Hack nötig
- **View-Timeout Management**: `view_timeout` wird auf `"0,0"` gesetzt damit Info-Karte
  sichtbar bleibt, nach Alarm auf `"20,0"` zurückgesetzt
- **Flexible Satzstruktur**: Nachricht vor oder nach Zeitangabe funktioniert jetzt:
  - "Erinnere mich **an Pizza** in 5 Minuten" (Nachricht vor Zeit)
  - "Erinnere mich in 5 Minuten **an Pizza**" (Zeit vor Nachricht)
  - Für alle Zeiteinheiten: Sekunden, Minuten, Stunden
- **Erweiterter Sekunden-Bereich**: 1–120 Sekunden mit allen Zahlwörtern
  (vorher nur 5, 10, 15, 20, 30, 45, 60)
- **DeleteAlles Intent**: "Lösche alles" löscht Erinnerungen UND Wecker
- **Universeller Stopp**: StopReminder und StopWecker führen identische Aktionen aus:
  - Alarm-Switch OFF
  - Wecker-Klingeln OFF
  - Media-Player STOP
  - Erinnerungs-Automationen abbrechen (beendet 3×-Schleife sofort)
  - Wecker-Alarm-Loop-Script stoppen
  - Display aufräumen (view_timeout, message, clock-navigation)
  - Automationen für zukünftige Trigger wieder aktivieren

### Geändert
- **Erinnerungs-Automationen komplett neu**: `erinnerung_timer_abgelaufen` und
  `erinnerung_zeit_abgelaufen` — vollständig mit Python-Script (`yaml.safe_load/dump`)
  8× iteriert und getestet
- **DeleteReminder**: Löscht jetzt NUR Erinnerungen (vorher: alles)
- **DeleteWecker**: Löscht jetzt NUR Wecker (vorher: alles)
- **StopReminder**: Vollständige Aufräum-Logik (vorher: nur `media_player.media_stop`)
- **StopWecker**: Identisch zu StopReminder (universeller Stopp)
- **intent_script.yaml**: Auf Einzeldatei-Modus umgestellt (statt `!include_dir_merge_named`)
- **reminders.yaml**: Sekunden-Liste erweitert, Satzstruktur-Patterns ergänzt,
  DeleteAlles-Intent hinzugefügt

### Behoben
- **Mediakarte bei Erinnerung**: VA Timer Sync erstellte VA-Timer → VA Alarm-Blueprint
  feuerte `sound_alarm` → Mediakarte auf Display. Fix: VA Timer Sync für Erinnerungen
  deaktiviert, nur nativer Alarm-Switch
- **Info-Karte verschwindet zu früh**: `view_timeout` von 20s navigierte automatisch
  zurück zur Uhr. Fix: `view_timeout = "0,0"` während Erinnerung
- **Intent "25 Sekunden" nicht erkannt**: Wert fehlte in der Sekunden-Liste
- **"Erinnerung an test in 10 Sekunden"** matcht nicht: STT liefert Nachricht manchmal
  vor der Zeitangabe. Fix: Patterns mit Nachricht-vor-Zeit für alle Zeiteinheiten

### VA Timer Sync Status
- `va_timer_sync_erinnerung_gestartet` — **DEAKTIVIERT** (verhindert Mediakarte)
- `va_timer_sync_timer_geloscht` — **DEAKTIVIERT**
- `va_timer_sync_wecker_gesetzt` — Aktiv (Wecker separat)

---

## [4.2.0] - 2026-02-12

### 📻 Radio Stream-Fix + Ducking-Bugfix

Umfassender Radio-Stream-Audit: 22+ defekte Sender-URLs repariert,
ExoPlayer-Kompatibilitätsproblem mit HTTPS→HTTP-Redirects gelöst,
und falsches Spotify-Resume beim Radio-Stopp behoben.

### Behoben
- **22+ defekte Radio-Stream-URLs ersetzt**: Alle Sender mit DNS-Fehlern, 404s, SSL-Problemen
  durch funktionierende Streams via radio-browser.info API ersetzt
  - Betroffene Sender u.a.: Bayern1, Bayern3, NDR2, NDR1, NJOY, HR3, Energy, Radio7,
    PlanetRadio, MDRJump, MDRSputnik, JamFM, YouFM, DieNeue1077, Ostseewelle,
    AlsterRadio, HitRadioFFH, SwissJazz, AbsolutRelax
- **FFN: HTTPS→HTTP Redirect behoben**: ExoPlayer verweigert Cross-Protocol-Redirects.
  Fix: Direkte HTTP-URL
- **RadioHamburg: SSL-Fix**: `TLSV1_UNRECOGNIZED_NAME` — ersetzt durch streamonkey.net
- **RadioBremen: DNS-Fix**: DNS nicht auflösbar — ersetzt durch icecast.radiobremen.de
- **Falsches Spotify-Resume beim Radio-Stopp**: Monitor sendete `KEYCODE_MEDIA_PLAY`
  bedingungslos. Fix: Nur wenn `_ducking_was_spotify == True`
- **Genre-Streams repariert**: SwissJazz, AbsolutRelax und weitere Genre-basierte Sender

### Geändert
- **intent_scripts/radio.yaml**: Alle drei Station-Maps mit verifizierten Stream-URLs
- **scripts/spotify_monitor.py**: Ducking-Resume-Logik um `_ducking_was_spotify`-Guard erweitert

## [4.1.0] - 2026-02-11

### 🎛️ Spotify Monitor v3 + Audio-Ducking Fix + Alarm/Wecker

Spotify Track Monitor als ADB-Daemon, Race-Condition-Fix für Audio-Ducking,
TTS-Bereinigung bei Stopp-Befehlen, und neue Wecker/Alarm-Intents.

### Hinzugefügt
- **Spotify Monitor v3**: `scripts/spotify_monitor.py` — All-in-One ADB-Daemon
  - Track Monitor, Keep-Alive, Audio-Ducking, Display-Navigation
  - Boolean-basierte Stopp-Erkennung mit Polling (0.5s Intervall, 15s Max)
  - MEDIA_STOP bei Stopp-Intent → verhindert Spotify Connect Auto-Reconnect
  - PID-File Management, Log-Rotation, Signal-Handler
- **Wecker/Alarm Intents**: `custom_sentences/de/alarm.yaml`
  - Wecker stellen (einmalig + wiederkehrend), löschen, abfragen, Snooze
- **Wecker Alarm-Loop Script**: `scripts/wecker_scripts.yaml`
  - TTS-Ansage + nativer Alarm-Switch + wait_template auf Stopp
- **Spotify Monitor Supervisor**: `scripts/spotify_monitor_supervisor.sh`

### Behoben
- **Race Condition im Audio-Ducking**: Boolean ON VOR ADB-Befehlen
- **Polling-Timeout zu kurz**: RESUME_POLL_MAX von 5s auf 15s erhöht
- **TTS bei Stopp-Befehlen entfernt**: `speech.text: ''` für stumme Ausführung

## [4.0.0] - 2026-02-11

### 🤖 Jarvis Router + Ollama LLM + Radio Player + Display-Steuerung

Intelligenter Conversation Agent mit lokalem Intent-Routing und Ollama-Fallback,
Radio Player mit 60+ Sendern, sowie optimierte Display-Steuerung für View Assist.

### Hinzugefügt
- **Jarvis Router Custom Component**: Lokale Intents → Ollama-Fallback
- **Radio Player**: 60+ deutsche Radiosender, RadioSearch über Radio Browser API
- **Allgemeiner Stopp (Sentence Trigger)**: Priorität über HA-Builtins
- **Wetter-Macros**: Jinja2 Macros für Wetterübersetzungen
- **Display-Optimierung**: `prefer_local_intents: true` — kein AI Response bei lokalen Intents

## [3.1.0] - 2026-02-10

### 🎵 Spotify Sprachsteuerung

Vollständige Spotify-Integration per Sprachbefehl.

### Hinzugefügt
- **Spotify Suche & Wiedergabe**: Songs, Künstler, Playlists, Alben
- **Spotify Steuerung**: Pause, Weiter, Shuffle, Gerätewechsel
- **Spotify Now Playing**: Aktueller Track mit Artist, Titel, Album
- **`spotify_voice.py`**: Python-Skript für Spotify Web API

## [3.0.0] - 2026-02-10

### 🚀 Modulare Architektur + Echo/VACA + TTS-Erinnerungen

### Hinzugefügt
- **Echo/VACA Steuerung**: 22+ Intents für jailbroken Echo Show 5
- **TTS-Erinnerungen**: Sprachansage mit Lautstärke-Boost
- **Entity-basierte Lichtsteuerung**: Alias-Map für STT-Fehlerkorrekturen

## [2.0.0] - 2024

### 🚀 TRUE STATE OF THE ART

Komplett überarbeitete Syntax für Home Assistant 2024+.

### Hinzugefügt
- Entity Slots, Area Slots, Inline Responses
- Dynamische Jinja2-Responses
- Rolladen/Licht/Media Status-Abfragen
