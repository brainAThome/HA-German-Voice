# 🇩🇪 HA-German-Voice

**Deutsche Sprachbefehle für Home Assistant** — Custom Sentences + Intent Scripts für Assist/Voice Pipelines mit View Assist (VACA) Display-Integration.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.7+-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Features

### 🤖 Jarvis Router (Custom Conversation Agent)
- **Intelligentes Routing**: Lokale Intents → Home Assistant Default Agent, Fallback → Ollama LLM
- **Nahtlose Integration**: Alle Sprachbefehle werden zuerst lokal verarbeitet, nur unbekannte Fragen gehen an Ollama
- **Keine Doppelverarbeitung**: `prefer_local_intents: true` in der Pipeline sorgt dafür, dass lokale Intents **nicht** zusätzlich ans LLM gehen
- **Display-Steuerung**: Lokale Intents → kein AI Response Overlay, Ollama-Antworten → AI Response auf dem Display

### ⏰ Erinnerungen (mit Alarm-Sound + Info-Karte + Lautstärke-Boost)
- **Sekunden/Minuten/Stunden**: "Erinnere mich in 30 Sekunden an die Pizza"
- **Uhrzeiten**: "Erinnere mich um 14 Uhr an den Termin"
- **Flexible Satzstruktur**: Nachricht vor oder nach der Zeitangabe — "Erinnere mich an Pizza in 5 Minuten" oder "Erinnere mich in 5 Minuten an Pizza"
- **3-fach Alarm**: Bei Ablauf wird die Erinnerung 3× angesagt + nativer Alarm-Sound (3.5s)
- **Info-Karte**: Erinnerungstext wird auf dem VACA Display als native VA Info-Karte angezeigt
- **Lautstärke-Boost**: Sprachlautstärke wird für die Ansage um 50% erhöht, danach zurückgesetzt
- **Display-Timeout deaktiviert**: `view_timeout` wird während der Erinnerung auf `0,0` gesetzt, damit die Info-Karte sichtbar bleibt
- **Abfragen**: "Welche Erinnerungen habe ich?" / "Welche Timer laufen?"
- **Gezielt löschen**: "Lösche alle Erinnerungen" (nur Erinnerungen) / "Lösche alle Wecker" (nur Wecker) / "Lösche alles" (beides)
- **Stopp**: "Stopp" / "Halt" bricht einen laufenden Alarm sofort ab (Erinnerung oder Wecker)
- **Erweiterter Sekunden-Bereich**: 1–120 Sekunden inkl. aller Zahlwörter

### ⏰ Wecker/Alarm
- **Wecker stellen**: "Stelle den Wecker auf 7 Uhr 30" / "Weck mich um 6:30"
- **Wiederkehrend**: "Wecker werktags um 6 Uhr" / "Wecker jeden Tag um 7"
- **Wecker löschen**: "Lösche den Wecker" / "Wecker aus" (nur Wecker)
- **Wecker abfragen**: "Wann klingelt der Wecker?" / "Welche Wecker habe ich?"
- **Snooze**: "Schlummern" / "Noch 10 Minuten" / "Snooze"
- **Alarm-Loop**: Nativer VA Alarm-Switch mit TTS-Ansage, automatischer Stopp nach 5 Min oder per Sprachbefehl

### 🛑 Universeller Stopp & Löschen
- **Stopp**: "Stopp" / "Halt" / "Es reicht" / "Sei still" — bricht laufenden Alarm ab (Erinnerung ODER Wecker), stoppt Alarm-Switch, beendet Alarm-Loop, räumt Display auf
- **Löschen getrennt**: "Lösche alle Erinnerungen" → nur Erinnerungen | "Lösche alle Wecker" → nur Wecker | "Lösche alles" → beides
- **Aufräumen**: Display-Navigation zurück zur Uhr, `view_timeout` zurückgesetzt, Nachricht gelöscht

### 📻 Radio Player (60+ Sender)
- **Direktwahl**: "Spiele SWR3" / "Spiele Radio Bob" / "Spiele 1Live"
- **Radiosuche**: "Suche ChillHop im Radio" — sucht über Radio Browser API
- **60+ deutsche Sender**: Alle großen ARD-Sender, private Sender, Spezialsender
- **Display-Anzeige**: Sendername + Logo auf dem VACA Display
- **Steuerung**: Lautstärke, Stopp, Senderwechsel per Sprache

### 🌤️ Wetter (mit Jinja2 Macros)
- **Aktuelles Wetter**: "Wie ist das Wetter?" / "Wie warm ist es draußen?"
- **Vorhersagen**: "Wie wird das Wetter morgen?" / "Regnet es am Wochenende?"
- **Spezifische Werte**: Luftfeuchtigkeit, Wind, Niederschlag, Luftdruck, Nebel, Schnee, Gewitter
- **Zeitbereiche**: "Wetter heute Nachmittag" / "Wie wird der Abend?"
- **Vergleiche**: "Wie wird das Wetter morgen im Vergleich zu heute?"
- **Empfehlungen**: "Was soll ich anziehen?" / "Kann ich draußen Sport machen?"
- **Sonnenauf-/untergang**: "Wann geht die Sonne auf/unter?"

### 💡 Lichter
- **Ein/Aus**: "Mach das Licht im Wohnzimmer an"
- **Helligkeit**: "Dimme die Lampe auf 50 Prozent" / "Heller" / "Dunkler"
- **Farben**: "Mach das Schlafzimmer rot" / "Blaues Licht"
- **Farbtemperatur**: "Warmes Licht im Büro"
- **Entity-basiert**: "Wandlicht heller" / "Bürolicht auf Maximum"
- **Area-basiert**: "Licht im Bad an" (automatisches Area-Matching)
- **Alias-Support**: STT-Fehler wie "Wadenlicht" → Wandlicht werden erkannt

### 🔊 Echo/VACA Steuerung (VACA Companion)
- **Sprachlautstärke**: "Sprachlautstärke auf 8" / "Sprachlautstärke lauter"
- **Musiklautstärke**: "Musiklautstärke auf 5" / "Musiklautstärke leiser"
- **Gesamtlautstärke**: "Lautstärke auf 7" / "Lauter" / "Leiser"
- **Bildschirm**: "Bildschirm auf 80%" / "Heller" / "Dunkler"
- **Mikrofon**: "Mikrofon auf 10" / "Mikrofon lauter"
- **Media-Player**: "Pause" / "Weiter" / "Nächstes Lied" / "Stopp"

### 🪟 Rolladen/Jalousien
- **Öffnen/Schließen**: "Wohnzimmerrollo auf" / "Rolladen runter"
- **Area-basiert**: "Rolladen im Wohnzimmer auf"
- **Position**: "Rolladen auf 50 Prozent"
- **Szenen**: "Guten Morgen" / "Kino Modus" / "Gute Nacht"
- **Sonnenschutz**: "Sonnenschutz Wohnzimmer an/aus"
- **Automatik**: "Rolladen-Automatik Schlafzimmer an/aus"

### 🎵 Spotify Sprachsteuerung
- **Song suchen + abspielen**: "Spiele Highway to Hell auf Spotify"
- **Künstler abspielen**: "Spiele Musik von Rammstein auf Spotify"
- **Playlist abspielen**: "Spiele die Playlist Goa Trance auf Spotify"
- **Album abspielen**: "Spiele das Album Appetite for Destruction auf Spotify"
- **Steuerung**: Pause, Weiter, Zurück, Shuffle, Gerätewechsel
- **Now Playing**: "Was spielt gerade auf Spotify?" mit Artist, Titel, Album
- **Spotify Web API**: Direkte Suche über die Spotify API — kein Spotcast nötig

### 🎛️ Spotify Monitor (HA API + ADB Fallback)
- **Track Monitor**: Erkennt Titelwechsel/Play/Pause → HA Entity-Update
- **Keep-Alive**: Hält Spotify App permanent im Hintergrund am Leben (Doze-Whitelist, 30s Prozess-Check)
- **Audio-Ducking**: Pausiert Musik automatisch bei Sprachbefehlen
  - **Primär via HA API** (`SPOTIFY_DUCKING_CONTROL_VIA_HA=True`) — `media_player.media_pause/play`
  - **ADB Fallback**: Optional via ADB KeyEvent wenn HA API deaktiviert
  - Race-Condition-sicher: Boolean ON vor Befehlen, Polling mit 15s Timeout
- **Stopp via HA API** (`SPOTIFY_STOP_PAUSE_VIA_HA=True`) — kein Spotify Connect Auto-Reconnect
- **Display-Navigation**: Automatisch Music-View bei Wiedergabe, Clock-View bei Stopp

### 🎵 Medien
- **Wiedergabe**: "Spiele Musik ab" / "Pause" / "Weiter"
- **Lautstärke**: "Lauter" / "Lautstärke auf 50%"
- **Shuffle/Repeat**: "Shuffle an" / "Wiederholen"

---

## 📂 Projektstruktur

```
ha-german-voice/
├── automations/                    # Sentence Trigger Automations
│   ├── general_stop.yaml           # Stopp-Automation (kontextabhängig: Spotify/Radio/Default)
│   ├── wecker_trigger.yaml         # Wecker Zeit-Trigger Automation
│   └── echo_screen_fix.yaml        # Echo Display Fix
├── custom_components/              # Custom Components
│   └── jarvis_router/              # Conversation Agent Router
│       ├── __init__.py
│       ├── config_flow.py
│       ├── conversation.py         # Lokale Intents → Ollama Fallback
│       ├── manifest.json
│       └── strings.json
├── custom_sentences/de/            # Sprachbefehle (Sentence-Dateien)
│   ├── alarm.yaml                  # Wecker/Alarm (7 Intents)
│   ├── covers.yaml                 # Rolladen/Jalousien (10 Intents)
│   ├── echo.yaml                   # Echo/VACA Steuerung (22 Intents)
│   ├── lights.yaml                 # Lichter (9 Intents)
│   ├── media.yaml                  # Medien (10 Intents)
│   ├── radio.yaml                  # Radio (9 Intents, 60+ Sender)
│   ├── reminders.yaml              # Erinnerungen/Timer (14 Intents)
│   ├── spotify.yaml                # Spotify (13 Intents)
│   └── weather.yaml                # Wetter (30 Intents)
├── custom_templates/               # Jinja2 Macros
│   └── weather_macros.jinja        # Wetter-Übersetzungen, Prognosen
├── scripts/                        # Python-Skripte & YAML
│   ├── erinnerung_scripts.yaml     # Erinnerungs-Watcher Scripts
│   ├── wecker_scripts.yaml         # Wecker Alarm-Loop Script
│   ├── radio_search.py             # Radio Browser API Suche
│   ├── spotify_monitor.py          # Spotify Monitor (HA API + ADB Fallback)
│   ├── spotify_monitor_start.sh    # Startskript für Monitor
│   ├── spotify_monitor_supervisor.sh # Supervisor mit auto-restart
│   ├── spotify_voice.py            # Spotify Web API Bridge
│   ├── spotify.env.example         # Beispiel-Konfiguration für Monitor
│   └── download_radio_logos.py     # Radio-Logos herunterladen
├── www/                            # Web Assets
│   └── radio_logos/                # Senderlogos (PNG)
│       └── radio_default.png       # Fallback-Logo
├── docs/                           # Dokumentation
├── intent_script.yaml              # Alle Intent Scripts (124 Intents)
├── conversation_logging.yaml       # Konversations-Logging
├── hacs.json                       # HACS Konfiguration
├── CHANGELOG.md
├── LICENSE
└── README.md
```

---

## 📊 Intent-Übersicht

| Modul | Datei | Intents | Beschreibung |
|-------|-------|---------|-------------|
| Wetter | `weather.yaml` | 30 | Temperatur, Regen, Wind, Schnee, Nebel, Sturm, UV, Kleidung, Outdoor |
| Erinnerungen | `reminders.yaml` | 14 | Sekunden/Minuten/Stunden/Uhrzeit, mit/ohne Nachricht, Abfrage, Löschen, Stopp, Löschen-Alles |
| Echo/VACA | `echo.yaml` | 22 | Sprach-/Musik-/Gesamtlautstärke, Bildschirm, Mikrofon, Media |
| Spotify | `spotify.yaml` | 13 | Suche, Wiedergabe, Steuerung, Gerätewechsel, GeneralStop |
| Rolladen | `covers.yaml` | 10 | Öffnen, Schließen, Position, Szenen, Sonnenschutz, Automatik |
| Lichter | `lights.yaml` | 9 | Ein/Aus, Helligkeit, Farbe, Entity/Area-basiert, Alias-Map |
| Radio | `radio.yaml` | 9 | Direktwahl, Suche, Lautstärke, Now Playing, Senderliste |
| Medien | `media.yaml` | 10 | Play, Pause, Stop, Lautstärke, Shuffle, Repeat |
| Wecker | `alarm.yaml` | 7 | Stellen, Wiederkehrend, Stopp, Snooze, Abfrage, Löschen |
| **Gesamt** | | **124** | |

---

## 📦 Installation

### HACS (Empfohlen)

1. Öffne HACS → **Integrations** → ⋮ → **Custom repositories**
2. Repository: `https://github.com/brainAThome/HA-German-Voice` / Category: **Integration**
3. Suche nach "German Voice" und installiere
4. **Neustart** von Home Assistant

### Manuelle Installation

1. Repository herunterladen/klonen
2. Dateien kopieren:

```bash
# Sprachbefehle
cp -r custom_sentences/de/*.yaml /config/custom_sentences/de/

# Intent Scripts
cp intent_script.yaml /config/intent_script.yaml
```

---

## ⚙️ Konfiguration

### 1. configuration.yaml

```yaml
# Intent Scripts
intent_script: !include intent_script.yaml
```

### 2. Erinnerungs-Helper

```yaml
timer:
  erinnerung_1:
    name: Erinnerung 1
    duration: "00:05:00"
  erinnerung_2:
    name: Erinnerung 2
    duration: "00:05:00"
  erinnerung_3:
    name: Erinnerung 3
    duration: "00:05:00"

input_text:
  erinnerung_1_nachricht:
    name: Erinnerung 1 Nachricht
    max: 255
    initial: ""
  erinnerung_2_nachricht:
    name: Erinnerung 2 Nachricht
    max: 255
    initial: ""
  erinnerung_3_nachricht:
    name: Erinnerung 3 Nachricht
    max: 255
    initial: ""

input_datetime:
  erinnerung_1_zeit:
    name: Erinnerung 1 Zeit
    has_date: true
    has_time: true
  erinnerung_2_zeit:
    name: Erinnerung 2 Zeit
    has_date: true
    has_time: true
  erinnerung_3_zeit:
    name: Erinnerung 3 Zeit
    has_date: true
    has_time: true

input_boolean:
  erinnerung_1_aktiv:
    name: Erinnerung 1 Aktiv
    initial: false
  erinnerung_2_aktiv:
    name: Erinnerung 2 Aktiv
    initial: false
  erinnerung_3_aktiv:
    name: Erinnerung 3 Aktiv
    initial: false
```

### 3. Wecker-Helper

```yaml
input_datetime:
  wecker_1_zeit:
    name: Wecker 1 Zeit
    has_time: true
  wecker_2_zeit:
    name: Wecker 2 Zeit
    has_time: true

input_boolean:
  wecker_1_aktiv:
    name: Wecker 1 Aktiv
    initial: false
  wecker_2_aktiv:
    name: Wecker 2 Aktiv
    initial: false
  wecker_1_wiederkehrend:
    name: Wecker 1 Wiederkehrend
    initial: false
  wecker_2_wiederkehrend:
    name: Wecker 2 Wiederkehrend
    initial: false
  wecker_klingelt:
    name: Wecker Klingelt
    initial: false

input_text:
  wecker_1_tage:
    name: Wecker 1 Tage
    max: 255
    initial: ""
  wecker_2_tage:
    name: Wecker 2 Tage
    max: 255
    initial: ""
  wecker_aktiver_slot:
    name: Wecker Aktiver Slot
    max: 5
    initial: ""

timer:
  wecker_snooze:
    name: Wecker Snooze
    duration: "00:10:00"
```

### 4. Erinnerungs-Automationen

Die Erinnerungs-Automationen (`Erinnerung: Timer abgelaufen` und `Erinnerung: Uhrzeit erreicht`) werden als HA-Automationen angelegt. Sie beinhalten:

- **Bildschirm aufwecken**
- **View-Timeout deaktivieren** (`0,0`) damit Info-Karte sichtbar bleibt
- **Erinnerungstext als Message** auf dem VA Sensor setzen
- **Navigation zur Info-Karte** (`/view-assist/info`)
- **Lautstärke-Boost** (+50%, max 10)
- **3× Ansage + Alarm** (TTS "Erinnerung: ..." + 3.5s nativer Alarm-Switch)
- **Aufräumen**: Message löschen, View-Timeout zurücksetzen (`20,0`), Navigation zur Uhr

> ⚠️ **ANPASSEN**: Entity-IDs für deinen VACA Satellite, Alarm-Switch und Sprachlautstärke

> 📝 **Hinweis**: Alle mitgelieferten Dateien (`erinnerung_scripts.yaml`, `wecker_scripts.yaml`, `general_stop.yaml`, `spotify_monitor.py`) enthalten Beispiel-Entity-IDs (`vaca_362812d56`, `sensor.quasselbuechse`). Suche in jeder Datei nach `ANPASSEN` und ersetze die Entity-IDs durch deine eigenen VACA-Entities.

### 5. Wecker-Automationen & Script

Die Wecker-Automationen (`Wecker: Zeit-Trigger` und `Wecker: Snooze Retrigger`) triggern das `wecker_alarm_loop` Script:

- **TTS-Ansage** "Wecker! Aufstehen!"
- **Alarm-Switch aktivieren** (nativer VA Alarm-Sound)
- **Wartet auf Stopp** (`input_boolean.wecker_klingelt` → off) oder 5 Min Timeout
- **Einmal-Wecker deaktivieren** nach Stopp (wiederkehrende bleiben aktiv)

### 6. Jarvis Router (Ollama LLM Fallback)

```bash
cp -r custom_components/jarvis_router/ /config/custom_components/jarvis_router/
```

Pipeline konfigurieren:
1. Settings → Voice Assistants → Pipeline → Conversation Agent: **Jarvis Router**
2. `prefer_local_intents: true` aktivieren

### 7. Radio Player (Optional)

```bash
cp scripts/radio_search.py /config/scripts/
cp -r www/radio_logos/ /config/www/radio_logos/
```

```yaml
shell_command:
  radio_search: "python3 /config/scripts/radio_search.py '{{ states('input_text.radio_search_query') }}'"
```

### 8. Spotify (Optional)

```bash
cp scripts/spotify_voice.py /config/scripts/
cp scripts/spotify_monitor.py /config/scripts/
cp scripts/spotify_monitor_start.sh /config/scripts/
cp scripts/spotify_monitor_supervisor.sh /config/scripts/
```

> ⚠️ **ANPASSEN** in `spotify_voice.py`: `HA_TOKEN`, `CLIENT_ID`/`CLIENT_SECRET`, `SPOTIFY_ENTITY`, Geräte-Aliase

---

## 🗣️ Beispiele

| Befehl | Funktion |
|--------|----------|
| "Wie ist das Wetter?" | Aktuelle Wetterbedingungen |
| "Wird es morgen regnen?" | Wettervorhersage |
| "Erinnere mich in 5 Minuten ans Essen" | Timer + 3× Alarm bei Ablauf |
| "Erinnere mich an Pizza in 30 Sekunden" | Nachricht vor Zeitangabe |
| "Erinnere mich um 14 Uhr an den Termin" | Zeitbasierte Erinnerung |
| "Welche Erinnerungen habe ich?" | Aktive Timer abfragen |
| "Lösche alle Erinnerungen" | Nur Erinnerungen löschen |
| "Lösche alle Wecker" | Nur Wecker löschen |
| "Lösche alles" | Erinnerungen + Wecker löschen |
| "Stopp" | Laufenden Alarm sofort abbrechen |
| "Wecker auf 7 Uhr 30" | Einmal-Wecker stellen |
| "Wecker werktags um 6 Uhr" | Wiederkehrender Wecker |
| "Schlummern" / "Noch 5 Minuten" | Snooze |
| "Mach das Wohnzimmerlicht an" | Licht einschalten |
| "Wandlicht auf 50 Prozent" | Entity-basierte Helligkeit |
| "Sprachlautstärke auf 8" | Echo Sprachlautstärke |
| "Rolladen im Schlafzimmer zu" | Rolladen schließen |
| "Spiele SWR3" | Radio starten |
| "Suche ChillHop im Radio" | Radio Browser API Suche |
| "Spiele Enter Sandman auf Spotify" | Spotify Song abspielen |
| "Was spielt auf Spotify?" | Aktueller Track |
| "Was ist die Hauptstadt von Frankreich?" | Ollama LLM Fallback |

---

## 🏗️ Architektur

### Sprachverarbeitungs-Pipeline

```
User spricht → STT (Cloud) → Assist Pipeline
  │
  ├─ prefer_local_intents: true
  │   └─ Custom Sentences matchen? → Intent Script → processed_locally=true
  │       → Kein AI Response Overlay auf Display
  │
  ├─ Sentence Trigger matchen? → Automation → processed_locally=true
  │   └─ z.B. "stopp" → general_stop_sentence_trigger
  │
  └─ Kein Match → Jarvis Router
      ├─ conversation.home_assistant (Default Agent)
      │   └─ Versuch lokale Verarbeitung
      └─ Fallback → conversation.ollama_conversation
          └─ LLM-Antwort → AI Response Overlay auf Display
```

### Erinnerungs-Ablauf

```
User: "Erinnere mich in 5 Minuten an Pizza"
  → Intent: SetReminderMinutes (message = "Pizza", minutes = 5)
  → Action: timer.start (300s) + input_text.set_value ("Pizza")
  → Response: "Alles klar, in 5 Minuten erinnere ich dich: Pizza."

  ... 5 Minuten später ...

  → Automation: "Erinnerung: Timer abgelaufen"
  → Bildschirm aufwecken
  → view_timeout = "0,0" (Display bleibt stehen)
  → message = "Erinnerung: Pizza" auf VA Sensor
  → Navigation → /view-assist/info (Info-Karte zeigt Text)
  → Lautstärke +50%
  → 3× Runde:
      ├─ TTS: "Erinnerung: Pizza"
      └─ Alarm-Switch ON → 3.5s → Alarm-Switch OFF
  → Aufräumen: message löschen, view_timeout = "20,0", → /view-assist/clock
  → Lautstärke zurücksetzen
```

### Stopp/Löschen-Logik

```
"Stopp" / "Halt" / "Sei still" / "Es reicht" / ...
  ├─ Sentence Trigger → general_stop_sentence_trigger
  │   ├─ Wecker-Klingeln OFF (immer)
  │   └─ choose (kontextabhängig):
  │       ├─ Spotify playing → Ducking OFF + Spotify pausieren + Clock
  │       ├─ Radio playing  → Radio pausieren + Clock
  │       └─ Default        → Alles stoppen (Spotify, Radio, Media, Clock)
  │
  ├─ StopReminder / StopWecker (Intent Scripts, identische Aktionen):
  │   → Alarm-Switch OFF, Wecker-Klingeln OFF, Media STOP
  │   → Erinnerungs-Automationen abbrechen + neu aktivieren
  │   → Wecker-Alarm-Loop-Script stoppen
  │   → Display aufräumen (view_timeout, message, → Clock)

"Lösche alle Erinnerungen"
  → DeleteReminder: Stopp + Timer cancel + Erinnerungen deaktivieren

"Lösche alle Wecker"
  → DeleteWecker: Stopp + Wecker deaktivieren

"Lösche alles"
  → DeleteAlles: Stopp + alles deaktivieren
```

---

## 🔧 Voraussetzungen

- **Home Assistant 2023.7+** (für Entity/Area Slots)
- Wetter-Integration (z.B. Met.no)
- Assist/Voice Pipeline aktiviert
- Für Echo-Steuerung: VACA Companion Integration (Echo Show 5 o.Ä. mit LineageOS)
- Für Info-Karte: View Assist mit `/view-assist/info` View
- Für LLM-Fallback: Ollama Server + Ollama Conversation Integration
- Für Radio: Radio Browser API (über `radio_search.py`)
- Für Spotify: Spotify Premium + Application Credentials

---

## 🤝 Mitwirken

Beiträge sind willkommen!

1. Fork dieses Repository
2. Feature-Branch erstellen (`git checkout -b feature/NeuerBefehl`)
3. Änderungen committen (`git commit -m 'Add: Neuer Befehl'`)
4. Push und Pull Request öffnen

---

## 📄 Lizenz

MIT License — siehe [LICENSE](LICENSE) für Details.

---

**Made with ❤️ for the German-speaking Home Assistant Community**
