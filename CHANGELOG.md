# HA-German-Voice - CHANGELOG

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

## [3.2.0] - 2026-02-11

### 🔇 Audio Ducking + 🌤️ Wetterkarte + 🏠 Startseite

Spotify-Ducking bei Sprachbefehlen, automatische Wetterkarten-Anzeige und Navigation zur Startseite.

### Hinzugefügt
- **Audio Ducking**: Spotify pausiert automatisch bei Sprachbefehlen und setzt danach fort
  - `input_boolean.spotify_ducking_active` verhindert Resume nach bewusstem Stopp
  - Alle Stop/Pause/Play-Intents setzen das Ducking-Flag korrekt
  - Automations: `spotify_audio_ducking_down` + `spotify_audio_ducking_up`
- **Wetterkarte auf Display**: Bei allen 40 Wetter-Intents wird die Wetterkarte 30s lang angezeigt
  - `view_assist.navigate` mit `revert_timeout: 30` zu `/view-assist/weather`
  - Danach automatische Rückkehr zur Uhr
- **ShowStartseite Intent**: Neuer Befehl zur Navigation auf die Startseite/Uhr
  - "Startseite" / "Startbildschirm" / "Zeig die Startseite" / "Zurück zur Uhr"
- **Spotify Display-Navigation**: Automatischer Wechsel zwischen Musik-Karte und Uhr
  - `spotify_nav_uhr`: Bei Stop/Pause → Uhr anzeigen (auch von PC/Phone)
  - `spotify_nav_musik`: Bei Play → Musik-Karte anzeigen

### Geändert
- **Spotify Intents**: Alle Play/Pause/Stop-Intents enthalten jetzt `input_boolean.turn_off spotify_ducking_active` als erste Aktion
- **Audio Ducking Ansatz**: Von Volume-Ducking (verursachte Verzerrungen) zu Pause/Resume gewechselt

### Entfernt
- `input_number.spotify_volume_before_ducking` (nicht mehr benötigt nach Wechsel zu Pause/Resume)

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
