# HA-German-Voice - CHANGELOG

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

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
