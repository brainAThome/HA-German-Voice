# 🇩🇪 HA-German-Voice

**Deutsche Sprachbefehle für Home Assistant** — Modulare Custom Sentences + Intent Scripts für Assist/Voice Pipelines.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Features

### 🌤️ Wetter
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

---

## 📂 Projektstruktur

```
ha-german-voice/
├── custom_sentences/de/     # Sprachbefehle (Sentence-Dateien)
│   ├── covers.yaml          # Rolladen/Jalousien
│   ├── echo.yaml            # Echo/VACA Steuerung
│   ├── lights.yaml          # Lichter
│   ├── media.yaml           # Medien
│   ├── reminders.yaml       # Erinnerungen/Timer
│   ├── spotify.yaml         # Spotify Sprachsteuerung
│   └── weather.yaml         # Wetter
├── intent_scripts/          # Intent Handler (Aktionen + Antworten)
│   ├── covers.yaml          # Rolladen-Szenen
│   ├── echo.yaml            # Echo/VACA Aktionen
│   ├── lights.yaml          # Licht-Aktionen (mit Alias-Map)
│   ├── reminders.yaml       # Timer + Watcher-Script-Aufrufe
│   ├── spotify.yaml         # Spotify Intent-Skripte
│   └── weather.yaml         # Wetter-Abfragen
├── scripts/                 # HA Scripts
│   ├── erinnerung_scripts.yaml
│   └── spotify_voice.py     # Spotify Web API Bridge
├── conversation_logging.yaml # Konversations-Logging Config
├── hacs.json                # HACS-Manifest
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

### 5. Spotify Sprachsteuerung (Optional)

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
| "Spiele Enter Sandman auf Spotify" | Spotify Song suchen + abspielen |
| "Spiele Musik von Rammstein auf Spotify" | Spotify Künstler abspielen |
| "Spiele die Playlist Goa Trance auf Spotify" | Spotify Playlist abspielen |
| "Spotify Pause" / "Spotify weiter" | Spotify Steuerung |
| "Was spielt auf Spotify?" | Aktueller Spotify-Track |
| "Spiele Spotify auf Echo Dot" | Gerätewechsel |

---

## 🏗️ Architektur

### Modulares System

Das Projekt verwendet `!include_dir_merge_named intent_scripts/` statt einer monolithischen Datei:

- **custom_sentences/de/*.yaml** — Sprachmuster (was der User sagen kann)
- **intent_scripts/*.yaml** — Handler (was HA bei Erkennung tut)
- **scripts/*.yaml** — Hintergrund-Scripts (TTS-Watcher für Erinnerungen)

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

| Befehl | Funktion |
|--------|----------|
| "Wie ist das Wetter?" | Aktuelle Wetterbedingungen |
| "Wird es morgen regnen?" | Wettervorhersage |
| "Erinnere mich in 5 Minuten" | Timer starten |
| "Mach das Wohnzimmerlicht an" | Licht einschalten |
| "Dimme auf 50%" | Helligkeit setzen |
| "Was läuft gerade?" | Aktuelle Medienwiedergabe |
| "Rolladen im Schlafzimmer zu" | Rolladen schließen |
| "Sonnenschutz Wohnzimmer" | Sonnenschutz aktivieren |
| "Gute Nacht" | Alle Rolladen schließen |

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
