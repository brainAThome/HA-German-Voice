# HA-German-Voice - CHANGELOG

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

## [4.1.0] - 2026-02-11

### 🎛️ Spotify Monitor v3 + Audio-Ducking Fix + Alarm/Wecker

Spotify Track Monitor als ADB-Daemon, Race-Condition-Fix für Audio-Ducking,
TTS-Bereinigung bei Stopp-Befehlen, und neue Wecker/Alarm-Intents.

### Hinzugefügt
- **Spotify Monitor v3**: `scripts/spotify_monitor.py` — All-in-One ADB-Daemon
  - **Track Monitor**: Erkennt Titelwechsel/Play/Pause via ADB MediaSession → HA Entity-Update
  - **Keep-Alive**: Hält Spotify App permanent am Leben (Doze-Whitelist, 30s Prozess-Check)
  - **Audio-Ducking**: Pausiert Musik bei Spracheingabe via ADB KEYCODE_MEDIA_PAUSE
  - Adaptive Polling: 0.5s während Ducking, 5s im Idle
  - Boolean-basierte Stopp-Erkennung mit Polling (0.5s Intervall, 15s Max)
  - MEDIA_STOP bei Stopp-Intent → verhindert Spotify Connect Auto-Reconnect
  - Display-Navigation: automatisch Music-View bei Wiedergabe, Clock-View bei Stopp
  - PID-File Management, Log-Rotation, Signal-Handler
- **Spotify Monitor Startskript**: `scripts/spotify_monitor_start.sh`
- **Wecker/Alarm Intents**: `custom_sentences/de/alarm.yaml` + `intent_scripts/alarm.yaml`
  - Wecker stellen, löschen, abfragen, Snooze
- **Echo Screen Fix Automation**: `automations/echo_screen_fix.yaml`
  - Setzt Screen-Settings bei HA-Start und navigiert zur Music-View falls Spotify spielt
- **Radio-Logo Download**: `scripts/download_radio_logos.py` — Lädt Senderlogos via Radio Browser API

### Behoben
- **Race Condition im Audio-Ducking**: Boolean ON wird jetzt VOR ADB-Befehlen gesetzt
  - Problem: ADB dauert 1-3s, Stopp-Automation setzte Boolean OFF während dieser Zeit,
    Monitor's verspätetes ON überschrieb das OFF → falsches Resume trotz Stopp-Intent
  - Fix: Boolean ON sofort beim Ducking-Start, vor allen langsamen Operationen
- **Polling-Timeout zu kurz**: RESUME_POLL_MAX von 5s auf 15s erhöht
  - Voice-Pipeline (Wake→STT→NLU→Automation) dauert 7-10s — 5s war zu kurz
- **TTS bei Stopp-Befehlen entfernt**: Keine Sprachausgabe mehr bei "Stopp", "Spotify Pause",
  "Spotify weiter" — `speech.text: ''` für SpotifyPause, SpotifyResume, GeneralStop +
  `set_conversation_response: ''` in der Stopp-Automation

### Geändert
- **Allgemeiner Stopp Automation**: `set_conversation_response: ''` — stumme Ausführung
- **Intent Scripts Spotify**: Alle Stopp/Pause/Resume-Intents ohne TTS-Feedback
- **.gitignore**: Temporäre Debug/Test-Skripte mit hardcoded Tokens ausgeschlossen
- **AUDIT_REPORT**: Token-Fragment entfernt
- **Konfiguration**: ANPASSEN-Kommentare in spotify_monitor.py und spotify_voice.py

## [4.0.0] - 2026-02-11

### 🤖 Jarvis Router + Ollama LLM + Radio Player + Display-Steuerung

Intelligenter Conversation Agent mit lokalem Intent-Routing und Ollama-Fallback,
Radio Player mit 60+ Sendern und Radio Browser API Suche, sowie optimierte Display-Steuerung
für View Assist / VACA Satellite.

### Hinzugefügt
- **Jarvis Router Custom Component**: Conversation Agent, der lokale Intents über
  `conversation.home_assistant` verarbeitet und bei No-Match an `conversation.ollama_conversation` weiterleitet
  - `custom_components/jarvis_router/` — Komplett eigenständige HA-Integration
  - NO_MATCH_PHRASES Detection für automatischen Ollama-Fallback
  - Nahtlose Integration in die HA Assist Pipeline
- **Radio Player**: 60+ deutsche Radiosender per Sprache steuerbar
  - Direktwahl: "Spiele SWR3" / "Spiele Radio Bob" / "Spiele 1Live"
  - RadioSearch: "Suche ChillHop im Radio" — über Radio Browser API
  - `scripts/radio_search.py` — Python-Skript für Radio Browser API
  - Senderlogos auf dem VACA Display mit Fallback-Icon
  - Lautstärke, Stopp, Senderwechsel per Sprache
  - `custom_sentences/de/radio.yaml` — 15+ Radio-Intents
  - `intent_scripts/radio.yaml` — Intent-Skripte mit Display-Navigation
- **Allgemeiner Stopp (Sentence Trigger)**: `automations/general_stop.yaml`
  - "Stopp"/"Stop"/"Aus"/"Schluss"/"Ende" als Einwort-Befehle
  - Sentence Trigger hat Priorität über HA-Builtin `HassMediaPause`
  - Stoppt Spotify + VACA Media Player + navigiert zurück zur Uhr
- **Wetter-Macros**: `custom_templates/weather_macros.jinja`
  - Jinja2 Macros für Wetterübersetzungen, Windrichtungen, Kleidungsempfehlung
- **Radio Default Logo**: `www/radio_logos/radio_default.png` — Fallback für Sender ohne Favicon
- **Display-Optimierung**: `prefer_local_intents: true` in der Pipeline
  - Lokale Intents (Radio, Spotify, Licht etc.) → **kein** AI Response Overlay
  - Ollama-Antworten (Wissensfragen) → AI Response Overlay auf dem Display
  - Radio-View bleibt stabil beim Abspielen, kein Flackern

### Geändert
- **GeneralStop Sentences**: Einwort-Befehle in Sentence Trigger Automation verschoben
  (Priorität über HA-Builtins), "alles stoppen"-Patterns bleiben im Intent
- **RadioSearch**: `logo_key|display_name` Pipe-Format für korrekte Anzeige
- **README**: Komplett überarbeitet mit Jarvis Router, Radio, Ollama, Pipeline-Architektur

## [3.1.0] - 2026-02-10

### 🎵 Spotify Sprachsteuerung

Vollständige Spotify-Integration per Sprachbefehl — Suche, Wiedergabe, Steuerung und Gerätewechsel.

### Hinzugefügt
- **Spotify Suche & Wiedergabe**: Per Sprache Songs, Künstler, Playlists und Alben suchen und abspielen
  - "Spiele Highway to Hell auf Spotify"
  - "Spiele Musik von Rammstein auf Spotify"
  - "Spiele die Playlist Goa Trance auf Spotify"
  - "Spiele das Album Appetite for Destruction auf Spotify"
- **Spotify Steuerung**: Pause, Weiter, Nächstes/Vorheriges Lied, Shuffle
  - "Spotify pause" / "Spotify weiter"
  - "Spotify nächstes Lied" / "Spotify zurück"
  - "Spotify Shuffle an/aus"
- **Spotify Gerätewechsel**: Wiedergabe auf verschiedene Geräte übertragen
  - "Spiele Spotify auf Echo Dot"
  - Unterstützt alle Spotify Connect Geräte
- **Spotify Now Playing**: "Was spielt gerade auf Spotify?" mit Künstler, Titel, Album
- **`spotify_voice.py`**: Python-Skript für Spotify Web API (Suche + Wiedergabe)
  - Automatisches Token-Management (liest aus HA-Storage, auto-refresh)
  - Nur Python-Standardbibliotheken (urllib), keine Pip-Dependencies
  - Geräte-Alias-Map für deutsche Bezeichnungen
- **Neue Dateien**:
  - `custom_sentences/de/spotify.yaml` — 13 Spotify-Intents
  - `intent_scripts/spotify.yaml` — Intent-Skripte für alle Spotify-Befehle
  - `scripts/spotify_voice.py` — Spotify Web API Bridge
- **HA Konfiguration**: `shell_command.spotify_voice`, `shell_command.spotify_device_transfer`
- **HA Helper**: `input_text.spotify_query`, `spotify_type`, `spotify_device`, `spotify_last_played`

## [3.0.0] - 2026-02-10

### 🚀 Modulare Architektur + Echo/VACA + TTS-Erinnerungen

Komplett überarbeitete Architektur mit modularem Intent-System, Echo-Steuerung und funktionierenden Erinnerungen.

### Hinzugefügt
- **Echo/VACA Steuerung**: 22+ neue Intents für jailbroken Echo Show 5
  - Sprachlautstärke, Musiklautstärke, Gesamtlautstärke
  - Bildschirmhelligkeit, Mikrofon
  - Routinen starten, Media-Player Kontrolle
- **TTS-Erinnerungen**: Erinnerungen werden jetzt per Sprachansage durchgegeben
  - `erinnerung_timer_watcher` Script für timer-basierte Erinnerungen
  - `erinnerung_zeit_watcher` Script für uhrzeitbasierte Erinnerungen
  - Automatischer Sprachlautstärke-Boost (+50%) bei Ansage
- **Entity-basierte Lichtsteuerung**: Heller/Dunkler/Max/Min für benannte Lampen
  - Alias-Map für STT-Fehlerkorrekturen (Wadenlicht → Wandlicht)
- **Conversation Logging**: Konversations-Logging Konfiguration
- **Modulares Intent-System**: `intent_scripts/` Verzeichnis mit 5 Moduldateien

### Geändert
- **Architektur**: Von monolithischer `intent_script.yaml` zu `!include_dir_merge_named intent_scripts/`
- **Lichter**: 373+ neue Zeilen für Entity-basierte Steuerung
- **Erinnerungen**: Pattern-Fixes (Hälfte, Prozent, reduzieren)
- **Wetter**: Verbesserte Patterns und Responses
- **Rolladen**: Aktualisierte Sentence-Patterns

### Entfernt
- `intent_script.yaml` (monolithische Datei) — ersetzt durch modulares System

## [2.0.0] - 2024

### 🚀 TRUE STATE OF THE ART

Komplett überarbeitete Syntax für Home Assistant 2024+:

### Hinzugefügt
- **Entity Slots**: `type: entity` mit `domain` für automatisches Matching
- **Area Slots**: `type: area` für raumbasierte Steuerung
- **Inline Responses**: Antworten direkt in Sentence-Dateien
- **Dynamische Responses**: Jinja2-Templates in Responses
- **Rolladen Status-Abfrage**: Dynamische Position- und Status-Anzeige
- **Licht Status-Abfrage**: Helligkeit und Zustand abfragen
- **Media Status-Abfrage**: "Was spielt gerade?" mit Titel/Artist

### Geändert
- **Alle Built-In Intents**: HassTurnOn, HassOpenCover, etc. mit Entity-Slots
- **Responses**: Von intent_script.yaml in Sentence-Dateien verschoben
- **Expansion Rules**: Vereinfacht und konsistent gemacht
- **Minimum Version**: Home Assistant 2024.1+ erforderlich

### Technische Details
- Entity-Slots: `slots: { name: { type: entity, domain: cover } }`
- Area-Slots: `slots: { area: { type: area } }`
- Responses: `response: "OK, {{ slots.name }} wird geöffnet."`
- Template-Responses: `response: >` für komplexe Jinja2

## [1.1.0] - 2024

### Hinzugefügt
- **Rolladen/Jalousie-Befehle**: Öffnen, Schließen, Position, Lamellen
- **Sonnenschutz**: Automatische Beschattung aktivieren/deaktivieren
- **Szenen**: Morgen-Modus, Nacht-Modus, Kino-Modus
- **Rolladen-Automatik**: Automatische Steuerung an/aus
- **Status-Abfrage**: "Ist der Rolladen offen?"

## [1.0.0] - 2024

### Hinzugefügt
- **Wetter-Befehle**: Aktuelle Bedingungen, Vorhersagen, Temperatur, Luftfeuchtigkeit, Wind
- **Erinnerungs-Befehle**: Sekunden, Minuten, Stunden, Uhrzeiten mit optionaler Nachricht
- **Licht-Befehle**: Ein/Aus, Helligkeit, Farben, Farbtemperatur
- **Medien-Befehle**: Play/Pause, Navigation, Lautstärke, Suche
- **State of the Art Syntax**: Expansion Rules, kompakte Alternative-Syntax
- **HACS-Unterstützung**: Einfache Installation über Custom Repository
- **Intent Scripts**: Vollständige Handler für alle custom Intents
- **Deutsche Sprachvarianten**: Umlaute und ß werden korrekt unterstützt

### Technische Details
- Verwendet Home Assistant Sentence Expansion Syntax
- `(a|b|c)` für Alternativen
- `[optional]` für optionale Teile
- `{slot}` für Variablen
- `expansion_rules` für wiederverwendbare Muster
