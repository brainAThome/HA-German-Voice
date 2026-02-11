# 🇩🇪 HA-German-Voice

**Deutsche Sprachbefehle für Home Assistant** — Modulare Custom Sentences + Intent Scripts für Assist/Voice Pipelines.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Features

### 🤖 Jarvis Router (Custom Conversation Agent)
- **Intelligentes Routing**: Lokale Intents → Home Assistant Default Agent, Fallback → Ollama LLM
- **Nahtlose Integration**: Alle Sprachbefehle werden zuerst lokal verarbeitet, nur unbekannte Fragen gehen an Ollama
- **Keine Doppelverarbeitung**: `prefer_local_intents: true` in der Pipeline sorgt dafür, dass lokale Intents **nicht** zusätzlich ans LLM gehen
- **Display-Steuerung**: Lokale Intents → kein AI Response Overlay, Ollama-Antworten → AI Response auf dem Display

### 📻 Radio Player (60+ Sender)
- **Direktwahl**: "Spiele SWR3" / "Spiele Radio Bob" / "Spiele 1Live"
- **Radiosuche**: "Suche ChillHop im Radio" — sucht über Radio Browser API
- **60+ deutsche Sender**: Alle großen ARD-Sender, private Sender, Spezialsender
- **Display-Anzeige**: Sendername + Logo auf dem VACA Display
- **Steuerung**: Lautstärke, Stopp, Senderwechsel per Sprache

### 🌤️ Wetter (mit Jinja2 Macros)
- **Aktuelles Wetter**: "Wie ist das Wetter?" / "Wie warm ist es draußen?"
- **Vorhersagen**: "Wie wird das Wetter morgen?" / "Regnet es am Wochenende?"
- **Spezifische Werte**: "Was ist die Luftfeuchtigkeit?" / "Wie stark ist der Wind?"
- **Zeitbereiche**: "Wetter heute Nachmittag" / "Wie wird der Abend?"

### ⏰ Erinnerungen (mit TTS-Ansage + Lautstärke-Boost)
- **Sekunden/Minuten/Stunden**: "Erinnere mich in 30 Sekunden an die Pizza"
- **Uhrzeiten**: "Erinnere mich um 14 Uhr an den Termin"
- **TTS-Ansage**: Bei Ablauf wird die Erinnerung per Sprachansage durchgegeben
- **Lautstärke-Boost**: Sprachlautstärke wird für die Ansage um 50% erhöht, danach zurückgesetzt
- **Abfragen/Löschen**: "Welche Erinnerungen habe ich?" / "Lösche alle Timer"

### 💡 Lichter
- **Ein/Aus**: "Mach das Licht im Wohnzimmer an"
- **Helligkeit**: "Dimme die Lampe auf 50 Prozent" / "Heller" / "Dunkler"
- **Farben**: "Mach das Schlafzimmer rot" / "Blaues Licht"
- **Farbtemperatur**: "Warmes Licht im Büro"
- **Entity-basiert**: "Wandlicht heller" / "Bürolicht auf Maximum"
- **Area-basiert**: "Licht im Bad an" (automatisches Area-Matching)
- **Alias-Support**: STT-Fehler wie "Wadenlicht" → Wandlicht werden erkannt

### 🔊 Echo/VACA Steuerung (Jailbroken Echo Show 5)
- **Sprachlautstärke**: "Sprachlautstärke auf 8" / "Sprachlautstärke lauter"
- **Musiklautstärke**: "Musiklautstärke auf 5" / "Musiklautstärke leiser"
- **Gesamtlautstärke**: "Lautstärke auf 7" / "Lauter" / "Leiser"
- **Bildschirm**: "Bildschirm auf 80%" / "Heller" / "Dunkler"
- **Mikrofon**: "Mikrofon auf 10" / "Mikrofon lauter"
- **Routinen**: "Starte Guten Morgen" / "Routine Feierabend"
- **Media-Player**: "Pause" / "Weiter" / "Nächstes Lied" / "Stopp"

### 🪟 Rolladen/Jalousien
- **Öffnen/Schließen**: "Wohnzimmerrollo auf" / "Rolladen runter"
- **Area-basiert**: "Rolladen im Wohnzimmer auf"
- **Position**: "Rolladen auf 50 Prozent"
- **Szenen**: "Guten Morgen" / "Kino Modus" / "Gute Nacht"

### 🎵 Medien
- **Wiedergabe**: "Spiele Musik ab" / "Pause" / "Weiter"
- **Lautstärke**: "Lauter" / "Lautstärke auf 50%"

### 🎵 Spotify Sprachsteuerung
- **Song suchen + abspielen**: "Spiele Highway to Hell auf Spotify"
- **Künstler abspielen**: "Spiele Musik von Rammstein auf Spotify"
- **Playlist abspielen**: "Spiele die Playlist Goa Trance auf Spotify"
- **Album abspielen**: "Spiele das Album Appetite for Destruction auf Spotify"
- **Pause/Weiter**: "Spotify Pause" / "Spotify weiter"
- **Nächstes/Vorheriges**: "Spotify nächstes Lied" / "Spotify zurück"
- **Shuffle**: "Spotify Shuffle an" / "Spotify Shuffle aus"
- **Gerätewechsel**: "Spiele Spotify auf Echo Dot" / "Spotify auf HAL"
- **Was spielt?**: "Was spielt gerade auf Spotify?" mit Artist, Titel, Album
- **Spotify Web API**: Direkte Suche über die Spotify API — kein Spotcast nötig

### 🛑 Allgemeiner Stopp (Sentence Trigger)
- **Einwort-Befehle**: "Stopp" / "Stop" / "Aus" / "Schluss" / "Ende"
- **Mehwort**: "Halt an" / "Es reicht" / "Sei still" / "Jetzt Ruhe"
- **Priorität**: Sentence Trigger hat Vorrang vor HA-Builtins
- **Navigation**: Display geht automatisch zurück zur Uhr

---

## 📂 Projektstruktur

```
ha-german-voice/
├── automations/             # Sentence Trigger Automations
│   └── general_stop.yaml    # Stopp-Automation (Priorität über HA-Builtins)
├── custom_components/       # Custom Components
│   └── jarvis_router/       # Conversation Agent Router
│       ├── __init__.py
│       ├── config_flow.py
│       ├── conversation.py  # Lokale Intents → Ollama Fallback
│       ├── manifest.json
│       └── strings.json
├── custom_sentences/de/     # Sprachbefehle (Sentence-Dateien)
│   ├── covers.yaml          # Rolladen/Jalousien
│   ├── echo.yaml            # Echo/VACA Steuerung
│   ├── lights.yaml          # Lichter
│   ├── media.yaml           # Medien
│   ├── radio.yaml           # Radio (60+ Sender + Suche)
│   ├── reminders.yaml       # Erinnerungen/Timer
│   ├── spotify.yaml         # Spotify + GeneralStop
│   └── weather.yaml         # Wetter
├── custom_templates/        # Jinja2 Macros
│   └── weather_macros.jinja # Wetter-Übersetzungen, Prognosen
├── intent_scripts/          # Intent Handler (Aktionen + Antworten)
│   ├── covers.yaml          # Rolladen-Szenen
│   ├── echo.yaml            # Echo/VACA + ShowStartseite
│   ├── lights.yaml          # Licht-Aktionen (mit Alias-Map)
│   ├── radio.yaml           # Radio Player + Suche + Steuerung
│   ├── reminders.yaml       # Timer + Watcher-Script-Aufrufe
│   ├── spotify.yaml         # Spotify Intent-Skripte + GeneralStop
│   └── weather.yaml         # Wetter-Abfragen
├── scripts/                 # Python-Skripte
│   ├── erinnerung_scripts.yaml
│   ├── radio_search.py      # Radio Browser API Suche
│   └── spotify_voice.py     # Spotify Web API Bridge
├── www/                     # Web Assets
│   └── radio_logos/         # Senderlogos (PNG)
│       └── radio_default.png # Fallback-Logo
├── conversation_logging.yaml
├── hacs.json
└── README.md
```

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

# Intent Scripts (modulares System)
mkdir -p /config/intent_scripts/
cp intent_scripts/*.yaml /config/intent_scripts/
```

---

## ⚙️ Konfiguration

### 1. configuration.yaml

```yaml
# Intent Scripts - Modulares System (NICHT !include intent_script.yaml)
intent_script: !include_dir_merge_named intent_scripts/
```

### 2. Erinnerungs-Helper

Folgendes in `configuration.yaml` hinzufügen:

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

### 3. Erinnerungs-Scripts (TTS-Ansage)

Damit Erinnerungen **per Sprache angesagt** werden (mit Lautstärke-Boost), kopiere den Inhalt von `scripts/erinnerung_scripts.yaml` in deine `/config/scripts.yaml`.

> ⚠️ **WICHTIG**: Passe die Entity-IDs an dein Setup an! Suche nach `ANPASSEN` in der Datei:
> - `assist_satellite.vaca_362812d56` → Dein Assist Satellite
> - `number.vaca_362812d56_sprachlautstarke` → Deine Sprachlautstärke-Entity

### 4. Echo/VACA Steuerung (Optional)

Die Echo/VACA-Intents in `echo.yaml` steuern einen jailbroken Echo Show 5 über VACA.
Voraussetzung: [VACA Integration](https://github.com/) mit Assist Satellite.

Die Entity-IDs in `intent_scripts/echo.yaml` müssen an dein Gerät angepasst werden.

### 5. Jarvis Router (Ollama LLM Fallback)

Der Jarvis Router ist ein Custom Conversation Agent, der lokale Intents und Ollama LLM kombiniert:

#### a) Custom Component kopieren

```bash
cp -r custom_components/jarvis_router/ /config/custom_components/jarvis_router/
```

#### b) configuration.yaml

```yaml
jarvis_router:
```

#### c) Ollama einrichten

1. [Ollama](https://ollama.ai/) auf einem Server installieren
2. Ollama Conversation Integration in HA einrichten (Settings → Integrations → Ollama)
3. Jarvis Router Integration hinzufügen (Settings → Integrations → Jarvis Router)

#### d) Pipeline konfigurieren

1. Settings → Voice Assistants → Pipeline bearbeiten
2. Conversation Agent: **Jarvis Router** auswählen
3. `prefer_local_intents: true` aktivieren (Settings → Voice Assistants → Pipeline → Details)

> **Hinweis**: `prefer_local_intents` sorgt dafür, dass lokale Intents (Radio, Spotify, Licht etc.)
> **vor** dem LLM verarbeitet werden. Nur unbekannte Fragen gehen an Ollama.
> Außerdem wird bei lokalen Intents **kein** AI Response Overlay auf dem Display angezeigt.

### 6. Radio Player (Optional)

#### a) Python-Script + Logos kopieren

```bash
cp scripts/radio_search.py /config/scripts/
cp -r www/radio_logos/ /config/www/radio_logos/
```

#### b) Shell Commands + Helper in `configuration.yaml`

```yaml
shell_command:
  radio_search: "python3 /config/scripts/radio_search.py '{{ states('input_text.radio_search_query') }}'"

input_text:
  radio_current_station:
    name: Aktueller Radiosender
    max: 255
    initial: ""
  radio_search_query:
    name: Radio Suchanfrage
    max: 255
    initial: ""
```

### 7. Allgemeiner Stopp (Sentence Trigger Automation)

Die Datei `automations/general_stop.yaml` enthält eine Sentence Trigger Automation,
die bei "Stopp", "Stop", "Aus" etc. alle Medienwiedergabe stoppt und zum Clock-Display navigiert.

```yaml
# In automations.yaml einfügen (Entity-IDs anpassen!)
```

> ⚠️ **ANPASSEN**: `media_player.spotify_sven`, `media_player.vaca_*`, `sensor.quasselbuechse`

### 8. Wetter-Macros (Optional)

```bash
cp custom_templates/weather_macros.jinja /config/custom_templates/
```

Die Macros werden von den Wetter-Intents referenziert und übersetzen Wetterbedingungen,
Windrichtungen und Kleidungsempfehlungen ins Deutsche.

### 9. Spotify Sprachsteuerung (Optional)

Voraussetzungen:
- **Spotify Integration** in HA eingerichtet (mit Application Credentials)
- **Spotify Premium** Konto (für Playback-Steuerung)

#### a) Python-Script kopieren

```bash
cp scripts/spotify_voice.py /config/scripts/
```

> ⚠️ **ANPASSEN** in `spotify_voice.py`:
> - `HA_TOKEN` — Dein Long-Lived Access Token
> - `CLIENT_ID` / `CLIENT_SECRET` — Deine Spotify App Credentials
> - `SPOTIFY_ENTITY` — Dein Spotify Media Player Entity
> - Geräte-Aliase in `find_device()` — Deine Spotify Connect Geräte

#### b) Shell Commands + Helper in `configuration.yaml`

```yaml
shell_command:
  spotify_voice: "python3 /config/scripts/spotify_voice.py --action search_play --query '{{ states('input_text.spotify_query') }}' --type '{{ states('input_text.spotify_type') }}' --device '{{ states('input_text.spotify_device') }}'"
  spotify_device_transfer: "python3 /config/scripts/spotify_voice.py --action device --device '{{ states('input_text.spotify_device') }}'"

input_text:
  spotify_query:
    name: Spotify Suchanfrage
    max: 255
    initial: ""
  spotify_type:
    name: Spotify Suchtyp
    max: 20
    initial: "track"
  spotify_device:
    name: Spotify Zielgerät
    max: 100
    initial: ""
  spotify_last_played:
    name: Spotify Zuletzt Gespielt
    max: 255
    initial: ""
```

---

## 🗣️ Beispiele

| Befehl | Funktion |
|--------|----------|
| "Wie ist das Wetter?" | Aktuelle Wetterbedingungen |
| "Wird es morgen regnen?" | Wettervorhersage |
| "Erinnere mich in 5 Minuten ans Essen" | Timer + TTS bei Ablauf |
| "Erinnere mich um 14 Uhr an den Termin" | Zeitbasierte Erinnerung |
| "Mach das Wohnzimmerlicht an" | Licht einschalten |
| "Wandlicht auf 50 Prozent" | Entity-basierte Helligkeit |
| "Sprachlautstärke auf 8" | Echo Sprachlautstärke |
| "Lauter" / "Leiser" | Gesamtlautstärke |
| "Rolladen im Schlafzimmer zu" | Rolladen schließen |
| "Starte Guten Morgen" | Echo Routine starten |
| "Welche Erinnerungen habe ich?" | Aktive Timer abfragen |
| "Spiele SWR3" | Radio starten (Direktwahl) |
| "Suche ChillHop im Radio" | Radio Browser API Suche |
| "Radio lauter" / "Radio leiser" | Radio-Lautstärke |
| "Stopp" / "Aus" / "Ende" | Alles stoppen + zurück zur Uhr |
| "Spiele Enter Sandman auf Spotify" | Spotify Song suchen + abspielen |
| "Spiele Musik von Rammstein auf Spotify" | Spotify Künstler abspielen |
| "Spiele die Playlist Goa Trance auf Spotify" | Spotify Playlist abspielen |
| "Spotify Pause" / "Spotify weiter" | Spotify Steuerung |
| "Was spielt auf Spotify?" | Aktueller Spotify-Track |
| "Spiele Spotify auf Echo Dot" | Gerätewechsel |
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
          └─ LLM-Antwort → processed_locally=false
              → AI Response Overlay auf Display
```

### Modulares System

Das Projekt verwendet `!include_dir_merge_named intent_scripts/` statt einer monolithischen Datei:

- **custom_sentences/de/*.yaml** — Sprachmuster (was der User sagen kann)
- **intent_scripts/*.yaml** — Handler (was HA bei Erkennung tut)
- **custom_components/jarvis_router/** — Conversation Agent Router (lokal → Ollama)
- **custom_templates/*.jinja** — Wiederverwendbare Jinja2 Macros
- **automations/** — Sentence Trigger (Priorität über Built-ins)
- **scripts/*.py** — Python-Skripte (Spotify API, Radio Browser API)

### Erinnerungs-Ablauf

```
User: "Erinnere mich in 5 Minuten an Pizza"
  → Intent: SetReminderMinutes
  → Action: timer.start + input_text.set_value
  → Action: script.turn_on (erinnerung_timer_watcher)
    → Watcher wartet auf timer.finished
    → Sprachlautstärke +50% (max 10)
    → TTS: "Erinnerung: Pizza"
    → Sprachlautstärke zurücksetzen
    → Nachricht aufräumen
```

### Alias-Map (Lichter)

STT erkennt Eigennamen oft falsch. Die `alias_map` in `intent_scripts/lights.yaml` korrigiert dies:

```yaml
# "Wadenlicht" → light.wandlicht
# "Bürolicht" → light.buro
alias_map:
  wadenlicht: light.h61a2_d4ea
  wandlampe: light.h61a2_d4ea
  bürolicht: light.buro
```

---

## 🔧 Voraussetzungen

- **Home Assistant 2024.1+** (für Entity/Area Slots)
- Wetter-Integration (z.B. Met.no)
- Assist/Voice Pipeline aktiviert
- Für Echo-Steuerung: VACA Integration mit jailbroken Echo Show 5
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
