# 🇩🇪 HA-German-Voice

**Deutsche Sprachbefehle für Home Assistant** - State of the Art Custom Sentences für Assist/Voice Pipelines.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-blue.svg)](https://www.home-assistant.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 State of the Art Features

Dieses Paket nutzt die **neuesten Home Assistant Intent-Features**:

- ✅ **Entity Slots** mit `type: entity` und `domain` für automatisches Matching
- ✅ **Area Slots** mit `type: area` für raumbasierte Steuerung
- ✅ **Responses direkt in Sentences** - keine separaten Dateien nötig
- ✅ **Expansion Rules** für natürliche Sprachvarianten
- ✅ **Built-In Intents** (HassTurnOn, HassOpenCover, etc.) werden automatisch erkannt

---

## ✨ Features

### 🌤️ Wetter
- **Aktuelles Wetter**: "Wie ist das Wetter?" / "Wie warm ist es draußen?"
- **Vorhersagen**: "Wie wird das Wetter morgen?" / "Regnet es am Wochenende?"
- **Spezifische Werte**: "Was ist die Luftfeuchtigkeit?" / "Wie stark ist der Wind?"
- **Zeitbereiche**: "Wetter heute Nachmittag" / "Wie wird der Abend?"

### ⏰ Erinnerungen  
- **Sekunden**: "Erinnere mich in 30 Sekunden"
- **Minuten**: "In 5 Minuten ans Essen erinnern"
- **Stunden**: "Erinnerung in 2 Stunden"
- **Uhrzeiten**: "Erinnere mich um 14 Uhr an den Termin"
- **Abfragen**: "Welche Erinnerungen habe ich?" / "Löschen aller Timer"

### 💡 Lichter
- **Ein/Aus**: "Mach das Licht im Wohnzimmer an" / "Licht in Küche aus"
- **Helligkeit**: "Dimme die Lampe auf 50 Prozent"
- **Farben**: "Mach das Schlafzimmer rot" / "Blaues Licht in Küche"
- **Farbtemperatur**: "Warmes Licht im Büro"
- **Raum-basiert**: "Heller im Wohnzimmer" (mit Area-Matching)

### 🎵 Medien
- **Wiedergabe**: "Spiele Musik ab" / "Pause"
- **Navigation**: "Nächster Titel" / "Zurück"
- **Lautstärke**: "Lauter" / "Lautstärke auf 50%"
- **Status**: "Was spielt gerade?" (mit dynamischer Antwort)

### 🪟 Rolladen/Jalousien
- **Öffnen/Schließen**: "Wohnzimmerrollo auf" / "Rolladen im Schlafzimmer runter"
- **Area-basiert**: "Rolladen im Wohnzimmer auf" (automatisches Matching)
- **Position**: "Rolladen auf 50 Prozent"
- **Lamellen**: "Lamellen auf halb"
- **Sonnenschutz**: "Sonnenschutz aktivieren im Büro"
- **Szenen**: "Guten Morgen" / "Kino Modus" / "Gute Nacht"
- **Status**: "Wie steht das Wohnzimmerrollo?" (mit dynamischer Antwort)

---

## 📦 Installation

### HACS (Empfohlen)

1. Öffne HACS in Home Assistant
2. Gehe zu **Integrations** → ⋮ (drei Punkte) → **Custom repositories**
3. Füge hinzu:
   - Repository: `https://github.com/brainAThome/HA-German-Voice`
   - Category: **Integration**
4. Suche nach "German Voice" und installiere
5. **Neustart** von Home Assistant

### Manuelle Installation

1. Lade dieses Repository herunter
2. Kopiere den Inhalt von `custom_sentences/de/` nach:
   ```
   config/custom_sentences/de/
   ```
3. Kopiere `intent_script.yaml` und füge es zu deiner config hinzu
4. **Neustart** von Home Assistant

---

## ⚙️ Konfiguration

### Voraussetzungen

- **Home Assistant 2024.1 oder neuer** (für Entity/Area Slots)
- Eine Wetter-Integration (z.B. Met.no, oder weather.forecast_home)
- Assist/Voice Pipeline aktiviert

### Optionale Erweiterungen

#### Intent Script (für Custom Intents)

Nur nötig für Wetter, Erinnerungen und Custom Cover Szenen:

```yaml
# configuration.yaml
intent_script: !include intent_script.yaml
```

#### Erinnerungen (Timer)

Füge folgendes zu deiner `configuration.yaml` hinzu:
    max: 255
  erinnerung_2_nachricht:
    name: "Erinnerung 2 Nachricht"
    max: 255
  erinnerung_3_nachricht:
    name: "Erinnerung 3 Nachricht"
    max: 255

input_datetime:
  erinnerung_1_zeit:
    name: "Erinnerung 1 Uhrzeit"
    has_date: true
    has_time: true
  erinnerung_2_zeit:
    name: "Erinnerung 2 Uhrzeit"
    has_date: true
    has_time: true
  erinnerung_3_zeit:
    name: "Erinnerung 3 Uhrzeit"
    has_date: true
    has_time: true

input_boolean:
  erinnerung_1_aktiv:
    name: "Erinnerung 1 aktiv"
  erinnerung_2_aktiv:
    name: "Erinnerung 2 aktiv"
  erinnerung_3_aktiv:
    name: "Erinnerung 3 aktiv"
```

#### Intent Scripts

Für erweiterte Funktionen (Erinnerungs-Handler, Wetterantworten) kopiere `intent_script.yaml` in deine Konfiguration und füge ein:

```yaml
intent_script: !include intent_script.yaml
```

---

## 🗣️ Beispiele

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

## 🔧 Syntax-Referenz

Dieses Projekt verwendet die **State of the Art** Home Assistant Expansion Syntax:

```yaml
sentences:
  # (a|b|c) = Alternativen - EINE muss verwendet werden
  - "(wie|was) ist (das|die) wetter"
  
  # [optional] = Optional - kann weggelassen werden  
  - "wie [warm] ist [es] [draußen]"
  
  # {slot} = Variable - wird vom User gefüllt
  - "erinnere mich in {minutes} minuten"
  
# expansion_rules für wiederverwendbare Muster
expansion_rules:
  polite: "[bitte|kannst du|könntest du]"
```

---

## 🤝 Mitwirken

Beiträge sind willkommen! 

1. Fork dieses Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/NeuerBefehl`)
3. Committe deine Änderungen (`git commit -m 'Add: Neuer Befehl'`)
4. Push zum Branch (`git push origin feature/NeuerBefehl`)
5. Öffne einen Pull Request

---

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

---

## 🙏 Danksagungen

- [Home Assistant](https://www.home-assistant.io/) Team
- [HACS](https://hacs.xyz/) Community
- Alle Mitwirkenden

---

**Made with ❤️ for the German-speaking Home Assistant Community**
