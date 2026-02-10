# HA-German-Voice - CHANGELOG

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

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
