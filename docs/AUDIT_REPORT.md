# 🔍 AUDIT REPORT — ha-german-voice

**Projekt:** Quasselbüchse / ha-german-voice  
**Version:** 4.0.0 (Commit `3924fe9`, Branch `feature/radio`)  
**Datum:** 2025-07-16  
**Umfang:** 32 Dateien, ~400 KB, 5 Python-Skripte, 15 YAML-Dateien, 1 Jinja2-Template, 1 Custom Component  
**HA-Version:** 2026.2.1  
**Server:** 192.168.178.123, Docker `homeassistant`

---

## Inhaltsverzeichnis

1. [Executive Summary](#1-executive-summary)
2. [Methodik](#2-methodik)
3. [Befunde nach Kategorie](#3-befunde-nach-kategorie)
   - 3.1 [KRITISCH (Sofortige Behebung)](#31-kritisch)
   - 3.2 [HOCH (Kurzfristig)](#32-hoch)
   - 3.3 [MITTEL (Planmäßig)](#33-mittel)
   - 3.4 [NIEDRIG (Optimierung)](#34-niedrig)
4. [ISO 27001 — Information Security Audit](#4-iso-27001--information-security-audit)
5. [ISO 25010 — Software Quality Audit](#5-iso-25010--software-quality-audit)
6. [Server-Validierung](#6-server-validierung)
7. [Empfohlene Nächste Schritte](#7-empfohlene-nächste-schritte)
8. [Anhang: Vollständige Befundliste](#8-anhang)

---

## 1. Executive Summary

Das Projekt wurde einer tiefgreifenden Analyse unterzogen, die folgende Bereiche abdeckt:

- **Code-Analyse:** Alle 5 Python-Dateien (973 LOC), syntaktisch und semantisch
- **YAML/Intent-Analyse:** Alle 15 YAML-Dateien, ~136 Intents, Entity-Referenzen, Slot-Mapping
- **Server-Validierung:** HA-Konfiguration, Logs, Entity-Existenz, Pipeline, Shell-Commands
- **ISO 27001:** Informationssicherheits-Management nach 10 relevanten Controls
- **ISO 25010:** Software-Qualitätsbewertung nach allen 8 Charakteristiken

### Gesamtbilanz

| Schweregrad | Anzahl | Status |
|-------------|--------|--------|
| **KRITISCH** | 11 | 🔴 Sofortige Behebung erforderlich |
| **HOCH** | 9 | 🟠 Kurzfristig (< 1 Woche) |
| **MITTEL** | 14 | 🟡 Planmäßig (< 1 Monat) |
| **NIEDRIG** | 12 | 🔵 Optimierung |
| **Gesamt** | **46** | |

### Kritischste Probleme (Top 5)

1. **Hardcoded Secrets in Git** — HA-Token, Spotify Client ID/Secret im Klartext in 2 Python-Dateien, gepusht zu GitHub
2. **YAML Duplicate Keys** — `HassLightSet` 3x, `HassTurnOn`/`HassTurnOff`/`HassOpenCover`/`HassCloseCover` je 2x definiert → Features STILL BROKEN
3. **Spotify `media_stop` nicht unterstützt** — StopReminder und GeneralStop rufen unsupported Services auf → Runtime-Errors
4. **`shell_command.log_conv_raw` fehlt** — In `scripts.yaml` referenziert, nicht in `configuration.yaml` definiert
5. **Slot-Mismatch Cover Intent Scripts** — Sentences übergeben `area`, Intent Scripts erwarten `name` → Jinja-Fehler

---

## 2. Methodik

### Analysierte Dateien

| Kategorie | Dateien | LOC |
|-----------|---------|-----|
| Python Scripts | `radio_search.py`, `spotify_voice.py` | 919 |
| Custom Component | `__init__.py`, `conversation.py`, `config_flow.py` | 165 |
| Custom Sentences (de) | 8 YAML-Dateien | ~2200 |
| Intent Scripts | 7 YAML-Dateien | ~1800 |
| Automations | `general_stop.yaml` | ~45 |
| Templates | `weather_macros.jinja` | ~120 |
| Other | `conversation_logging.yaml`, `erinnerung_scripts.yaml` | ~80 |

### Werkzeuge

- Statische Code-Analyse (Python AST, YAML Parser)
- Server-seitige Validierung (`check_config`, Docker Logs, API-Checks)
- Manuelle Code-Review aller Dateien
- Entity-Existenz-Prüfung via HA REST API
- Pipeline-Konfigurationsanalyse

---

## 3. Befunde nach Kategorie

### 3.1 KRITISCH

#### K-01: Hardcoded HA Long-Lived Access Token
- **Dateien:** `scripts/radio_search.py` (L36), `scripts/spotify_voice.py` (L36)
- **Problem:** Identischer HA-Token im Klartext hardcoded und auf GitHub gepusht
- **Token:** `eyJhbGciOiJIUzI1NiIs...` (Bearer Token, gültig bis 2036)
- **Risiko:** Vollständiger Zugriff auf alle HA-Entities, Services, Konfiguration. Token ist öffentlich auf GitHub einsehbar
- **Fix:** Token in Environment-Variable oder `/config/secrets.yaml` auslagern, bestehenden Token sofort revoken, neuen generieren

#### K-02: Hardcoded Spotify API Credentials
- **Datei:** `scripts/spotify_voice.py` (L47-48)
- **Problem:** `CLIENT_ID` und `CLIENT_SECRET` im Klartext
- **Risiko:** Unbefugter Zugriff auf Spotify-Account, API-Missbrauch
- **Fix:** In Environment oder HA-Secrets auslagern

#### K-03: Vollzugriff auf HA Config Entries Storage
- **Datei:** `scripts/spotify_voice.py` (L38, L161-170)
- **Problem:** Script liest `/config/.storage/core.config_entries` — enthält Tokens/Secrets ALLER Integrationen (Alexa, Ring, etc.)
- **Risiko:** Ein Fehler/Leak in spotify_voice.py exponiert Credentials aller HA-Integrationen
- **Fix:** Nur den Spotify-Token über die HA REST API auslesen, nicht die gesamte Storage-Datei

#### K-04: YAML Duplicate Key — `HassLightSet` (3x definiert)
- **Datei:** `custom_sentences/de/lights.yaml` (L210, L488, L525)
- **Problem:** YAML erlaubt nur einen Wert pro Key. Bei 3x `HassLightSet` gewinnt nur der LETZTE (Farbtemperatur). **Helligkeit** und **Farbsteuerung** sind STILL BROKEN.
- **Auswirkung:** "Stell das Bürolicht auf 50 Prozent" → wird NICHT erkannt. "Mach das Licht rot" → wird NICHT erkannt.
- **Fix:** Alle `HassLightSet`-Blöcke in EINEN Block mit mehreren `data:`-Einträgen zusammenführen

#### K-05: YAML Duplicate Key — `HassTurnOn` (2x definiert)
- **Datei:** `custom_sentences/de/lights.yaml` (L99, L574)
- **Problem:** Erster Block (Entity+Area ON) wird vom zweiten Block (Alle Lichter AN) überschrieben
- **Auswirkung:** "Mach das Bürolicht an" → funktioniert NICHT, nur "Alle Lichter an" funktioniert
- **Fix:** Beide Blöcke unter einem `HassTurnOn` zusammenführen

#### K-06: YAML Duplicate Key — `HassTurnOff` (2x definiert)
- **Datei:** `custom_sentences/de/lights.yaml` (L137, L555)
- **Problem:** Analog zu K-05 — Entity/Area OFF ist tot, nur "Alle Lichter aus" funktioniert
- **Fix:** Zusammenführen

#### K-07: YAML Duplicate Key — `HassOpenCover` (2x definiert)
- **Datei:** `custom_sentences/de/covers.yaml` (L89, L322)
- **Problem:** Entity/Area-spezifisches Öffnen überschrieben durch "Alle Rolladen"-Version
- **Auswirkung:** "Öffne das Schlafzimmer Rollo" → funktioniert NICHT
- **Fix:** Zusammenführen

#### K-08: YAML Duplicate Key — `HassCloseCover` (2x definiert)
- **Datei:** `custom_sentences/de/covers.yaml` (L142, L340)
- **Problem:** Analog zu K-07
- **Fix:** Zusammenführen

#### K-09: Slot-Mismatch Cover Intent Scripts
- **Datei:** `intent_scripts/covers.yaml` — 5 Intent Scripts (`SetSunProtection`, `DisableSunProtection`, `EnableCoverAutomation`, `DisableCoverAutomation`, `GetCoverState`)
- **Problem:** Intent Scripts referenzieren `{{ name }}`, aber custom_sentences übergeben `{area}` (type: area)
- **Auswirkung:** Jinja-Template rendern `name` als leeren String → falsche Entity-IDs, Laufzeitfehler
- **Fix:** In den Intent Scripts `area` statt `name` verwenden, oder area_id() nutzen

#### K-10: Spotify `media_stop`/`media_pause` nicht unterstützt
- **Server-Logs:** `media_player.spotify_sven does not support media_player.media_stop` (~15 Fehler)
- **Betroffene:** `StopReminder` Intent Script, `general_stop_sentence_trigger` Automation
- **Fix:** `media_player.media_play_pause` (toggle) verwenden, oder Spotify Web API `PUT /v1/me/player/pause`

#### K-11: `shell_command.log_conv_raw` fehlt
- **Datei:** Server `scripts.yaml` → `log_conversation_memory` referenziert diesen Shell-Command
- **Problem:** Nicht in `configuration.yaml` definiert
- **Auswirkung:** Conversation Memory Logging schlägt jedes Mal fehl
- **Fix:** Shell-Command definieren oder Script entfernen/deaktivieren

---

### 3.2 HOCH

#### H-01: SSL-Verifikation deaktiviert
- **Datei:** `scripts/radio_search.py` (L63-64)
- **Problem:** `ssl_ctx.check_hostname = False; ssl_ctx.verify_mode = ssl.CERT_NONE`
- **Risiko:** MITM-Angriffe auf Radio Browser API Verbindungen
- **Fix:** Mindestens `certifi` CA-Bundle verwenden, oder Default-SSL-Context beibehalten

#### H-02: Shell Injection via ADB-Kommando
- **Datei:** `scripts/spotify_voice.py` (L376)
- **Problem:** `cmd = f"am start -a android.intent.action.VIEW -d '{uri}'"` — URI wird unsanitized in Shell-Befehl interpoliert
- **Risiko:** Bösartige Spotify-URIs könnten Shell-Befehle auf dem Echo Show ausführen
- **Fix:** `shlex.quote()` für URI-Parameter verwenden

#### H-03: HA-API über Plain HTTP
- **Dateien:** `radio_search.py` (L31), `spotify_voice.py` (L34)
- **Problem:** `http://localhost:8123` — Token wird unverschlüsselt übertragen
- **Bewertung:** Da localhost-only, akzeptables Risiko innerhalb des Docker-Netzwerks. Dennoch empfohlen: HTTPS oder Socket-Verbindung
- **Empfehlung:** In containerinternem Netzwerk tolerierbar, dokumentieren

#### H-04: `sys.exit(0)` bei Fehlern in radio_search.py
- **Datei:** `scripts/radio_search.py` (L265, L272, L280, L296)
- **Problem:** Fehler geben Exit-Code 0 zurück → HA `shell_command` meldet keinen Fehler
- **Auswirkung:** Fehler in RadioSearch sind für HA unsichtbar, kein Retry/Fehlermeldung möglich
- **Fix:** `sys.exit(1)` bei Fehlern verwenden

#### H-05: Orphan Intent Scripts ohne Sentences
- **Dateien:** `intent_scripts/covers.yaml` → `ScheduleCover`, `intent_scripts/weather.yaml` → `GetWeatherForecast`
- **Problem:** Intent Scripts definiert, aber keine korrespondierenden Sentences in custom_sentences
- **Auswirkung:** Dead Code, wird nie aufgerufen
- **Fix:** Sentences erstellen oder Intent Scripts entfernen

#### H-06: StopReminder ultra-breite Patterns
- **Datei:** `custom_sentences/de/reminders.yaml`
- **Problem:** Patterns wie "stopp {name}" / "stop {name}" sind sehr breit und kollidieren mit GeneralStop + Sentence Trigger
- **Auswirkung:** Unvorhersehbare Intent-Auflösung
- **Fix:** Patterns spezifischer machen: "stopp erinnerung {name}" / "erinnerung {name} stoppen"

#### H-07: Orphan-Datei auf Server
- **Datei:** `/homeassistant/scripts/spotify_wrapper.py` (667 Bytes)
- **Problem:** Nicht im Git-Repo, nicht referenziert
- **Fix:** Löschen oder ins Repo aufnehmen

#### H-08: `alarm.yaml` nicht im Repo
- **Server:** `custom_sentences/de/alarm.yaml` + `intent_scripts/alarm.yaml` existieren auf dem Server
- **Problem:** Nicht versioniert → Änderungen gehen bei Neuaufsetzen verloren
- **Fix:** Ins Repo aufnehmen

#### H-09: `spotify_voice.py` Exit-Code 1 in Logs
- **Server-Logs:** `shell_command.spotify_voice` returned code 1
- **Problem:** Mindestens ein Ausführungsfehler aufgezeichnet
- **Fix:** Logging verbessern, Fehlerquelle identifizieren (wahrscheinlich Token-Erneuerung oder Device-Suche)

---

### 3.3 MITTEL

#### M-01: Ungenutzter Import `time` in radio_search.py
- **Datei:** `scripts/radio_search.py` (L22)
- **Fix:** Entfernen

#### M-02: Duplizierter HA-API-Wrapper-Code
- **Dateien:** `radio_search.py` und `spotify_voice.py`
- **Problem:** Beide implementieren eigene HTTP-Helper für die HA-API
- **Fix:** Gemeinsames Modul `ha_utils.py` extrahieren

#### M-03: `weather_macros.jinja` komplett ungenutzt
- **Datei:** `custom_templates/weather_macros.jinja` (~120 LOC)
- **Problem:** Gleiche Logik ist ~40x inline in `intent_scripts/weather.yaml` (85 KB!)
- **Fix:** Template nutzen oder Datei entfernen

#### M-04: `service:` vs `action:` Keyword-Inkonsistenz
- **Dateien:** Gemischte Verwendung von `service:` (deprecated seit HA 2024.x) und `action:` (neues Format)
- **Fix:** Durchgängig `action:` verwenden

#### M-05: Fehlende Logging-Infrastruktur in spotify_voice.py
- **Problem:** Kein Python `logging`-Modul, nur `print()`-Statements mit Prefixes (`ERROR:`, `INFO:`, `OK:`)
- **Fix:** Auf `logging` umstellen wie in radio_search.py

#### M-06: Keine Input-Validierung in spotify_voice.py
- **Problem:** `args.query` wird nicht sanitized, könnte Sonderzeichen enthalten
- **Fix:** Basis-Validierung und Escaping hinzufügen

#### M-07: Conversation.py Return-Typ unvollständig
- **Datei:** `custom_components/jarvis_router/conversation.py` (L106-108)
- **Problem:** Letzter Fehlerfall erstellt `IntentResponse` aber gibt kein `ConversationResult` zurück
- **Fix:** Korrektes `ConversationResult(response=err)` zurückgeben

#### M-08: HA Token-Ablauf nicht validiert
- **Dateien:** Beide Python-Scripts
- **Problem:** Token mit Ablauf 2036 wird nie geprüft. Wenn Token revoked wird, keine sinnvolle Fehlermeldung
- **Fix:** API-Response-Code 401 sauber behandeln

#### M-09: Keine Retry-Logik für HA API Calls
- **Dateien:** `radio_search.py`, `spotify_voice.py`
- **Problem:** Single-Shot HTTP calls, kein Retry bei Timeout/5xx
- **Fix:** Simple Retry mit Backoff implementieren

#### M-10: Duplicate Response Templates
- **Problem:** Identische Jinja-Response-Templates werden in mehreren Intent Scripts kopiert statt zentral verwaltet
- **Fix:** Response-Templates in includes oder gemeinsame Macros auslagern

#### M-11: Hardcoded Entity-IDs überall
- **Problem:** ~50+ Entity-IDs hardcoded in Scripts und Automations
- **Fix:** Zentrale Konfiguration (z.B. `anchors.yaml` oder Python-Config)

#### M-12: Duplicate Sentence Patterns
- **Problem:** Einige Sentence-Patterns erscheinen in leicht variierter Form in mehreren Intent-Dateien
- **Fix:** Review und Deduplizierung

#### M-13: `cover_intent_scripts` verwenden `service:` statt `action:`
- **Datei:** `intent_scripts/covers.yaml`
- **Fix:** Migration auf `action:` Keyword

#### M-14: Comments/Dead Code in lights.yaml
- **Datei:** `custom_sentences/de/lights.yaml` (L516-524)
- **Problem:** Drei aufeinanderfolgende leere Kommentarblöcke "LICHT HELLER (Custom Intent fuer Entity)"
- **Fix:** Bereinigen

---

### 3.4 NIEDRIG

#### N-01: Unused Import `ConfigEntry` in config_flow.py
- **Datei:** `custom_components/jarvis_router/config_flow.py`
- **Fix:** Entfernen

#### N-02: Keine Connection-Pool-Nutzung in Python Scripts
- **Problem:** Jeder API-Call öffnet neue HTTP-Verbindung
- **Fix:** `urllib3` oder `requests.Session()` für Connection Reuse

#### N-03: magic-strings für Pfade und URLs
- **Problem:** Pfade wie `/config/logs/`, `/config/www/radio_logos/` hardcoded an mehreren Stellen
- **Fix:** Konstanten im Config-Bereich definieren (ist teilweise schon gemacht)

#### N-04: VACA Satellite Disconnects
- **Server-Logs:** Periodische Reconnects alle paar Minuten
- **Bewertung:** Netzwerk/Hardware-Issue, nicht code-bedingt
- **Empfehlung:** WiFi-Stabilität prüfen, Keep-Alive-Intervall anpassen

#### N-05: Kein Type-Hinting in Python Scripts
- **Problem:** `radio_search.py` und `spotify_voice.py` ohne Type Annotations
- **Fix:** Type Hints hinzufügen für bessere IDE-Unterstützung und Fehlerprävention

#### N-06: Spotify Device Alias Map hardcoded
- **Datei:** `spotify_voice.py` (L250-268)
- **Problem:** Alias-Map für Geräte ist direkt im Code
- **Fix:** In Konfigurationsdatei auslagern

#### N-07: Kein Graceful Shutdown in ADB-Verbindungen
- **Datei:** `spotify_voice.py` → `adb_wake_spotify()`
- **Problem:** Bei Exception wird `dev.close()` nicht garantiert aufgerufen
- **Fix:** `try/finally` oder Context Manager verwenden

#### N-08: Test-Coverage = 0%
- **Problem:** Keine Unit-Tests, keine Integration-Tests
- **Fix:** Test-Framework einrichten (pytest), mindestens für kritische Funktionen

#### N-09: Keine CI/CD Pipeline
- **Problem:** Kein GitHub Actions Workflow für Linting, Tests, Deployment
- **Fix:** `.github/workflows/ci.yml` einrichten

#### N-10: README.md fehlende Sections
- **Problem:** Setup-Anleitung fehlt für Secrets, SSL, ADB-Keys
- **Fix:** Ergänzen

#### N-11: `_archiv/` Ordner im Repo
- **Problem:** Archivierte Dateien werden mitversioniert
- **Fix:** `.gitignore` ergänzen oder entfernen

#### N-12: `scripts/erinnerung_scripts.yaml` Namenskonvention
- **Problem:** Mischt deutsches Naming mit englischem — sollte konsistent sein
- **Fix:** Einheitliches Naming-Schema definieren

---

## 4. ISO 27001 — Information Security Audit

### Scope

Bewertung der Informationssicherheit des ha-german-voice Projekts gegen relevante Controls aus ISO/IEC 27001:2022 Annex A.

### Ergebnisse nach Control-Domänen

#### A.5 Organisatorische Controls

| Control | Bewertung | Befund |
|---------|-----------|--------|
| A.5.1 Informationssicherheitsrichtlinien | ❌ Nicht vorhanden | Keine Security-Policy dokumentiert |
| A.5.10 Zulässige Nutzung von Informationen | ⚠️ Teilweise | Kein separates Berechtigungskonzept |

#### A.8 Technologische Controls — Asset Management

| Control | Bewertung | Befund |
|---------|-----------|--------|
| A.8.1 User Endpoint Devices | ⚠️ Teilweise | Echo Show 5 via ADB (Port 5555) offen — kein Auth-Logging |
| A.8.9 Configuration Management | ❌ Kritisch | Hardcoded Secrets in versioniertem Code (K-01, K-02) |
| A.8.12 Data Leakage Prevention | ❌ Kritisch | Token & Credentials auf öffentlichem GitHub-Repo |
| A.8.24 Cryptography | ❌ Kritisch | SSL deaktiviert (H-01), Token im Plaintext |

**Bewertung: NON-CONFORMANT**

#### A.8.2-A.8.8 Zugangssteuerung (Access Control)

| Aspekt | Bewertung | Details |
|--------|-----------|---------|
| Authentifizierung | ⚠️ | HA Long-Lived Token (nie rotiert, Ablauf 2036) |
| Autorisierung | ❌ | Token hat ADMIN-Rechte, kein Least-Privilege |
| Token-Management | ❌ | Kein Rotation, kein Revocation-Prozess |
| API-Zugriff | ⚠️ | Localhost-only, aber unverschlüsselt (HTTP) |
| Storage-Zugriff | ❌ | spotify_voice.py liest ALL storage credentials (K-03) |

**Bewertung: NON-CONFORMANT**

#### A.8.25-A.8.28 Software-Sicherheit

| Aspekt | Bewertung | Details |
|--------|-----------|---------|
| Secure Coding | ❌ | Shell Injection (H-02), keine Input-Validierung |
| Dependency Management | ⚠️ | Nur stdlib + adb_shell, kein Dependency-Scanning |
| Code Review | ⚠️ | Kein formaler Review-Prozess, kein PR-Workflow |
| Error Handling | ❌ | Fehler als Exit-Code 0 (H-04), stille Fehlschläge |

**Bewertung: PARTIALLY CONFORMANT**

#### A.8.15-A.8.16 Logging & Monitoring

| Aspekt | Bewertung | Details |
|--------|-----------|---------|
| Audit Logging | ⚠️ | radio_search.py hat File-Logging, spotify_voice.py nur print() |
| Security Event Logging | ❌ | Keine Erkennung von unauthorized access |
| Log Protection | ⚠️ | Logs in /config/logs/, kein Rotation/Retention |

**Bewertung: PARTIALLY CONFORMANT**

### ISO 27001 Gesamtbewertung

```
╔══════════════════════════════════════════════╗
║  ISO 27001 COMPLIANCE SCORE: 18/100         ║
║  Status: NON-CONFORMANT                     ║
║                                              ║
║  Kritische Gaps:                             ║
║  • Secrets im öffentlichen Repository       ║
║  • Kein Token-Rotation-Prozess              ║
║  • Kein Least-Privilege-Prinzip             ║
║  • SSL deaktiviert                           ║
║  • Keine Security-Policy                     ║
╚══════════════════════════════════════════════╝
```

### Sofortmaßnahmen (ISO 27001)

1. **SOFORT:** HA-Token revoken und neu generieren
2. **SOFORT:** GitHub-Repository auf Private setzen ODER Secrets mit `git filter-branch` aus History entfernen
3. **SOFORT:** Spotify Credentials rotieren (neue App in Spotify Developer Dashboard)
4. **Woche 1:** Secrets-Management implementieren (HA secrets.yaml oder Environment Variables)
5. **Woche 2:** SSL-Verifikation aktivieren, Least-Privilege Token erstellen
6. **Monat 1:** Security-Policy dokumentieren, Token-Rotation-Prozess einrichten

---

## 5. ISO 25010 — Software Quality Audit

### Scope

Bewertung der Softwarequalität gegen alle 8 Qualitätscharakteristiken nach ISO/IEC 25010:2023.

### 5.1 Functional Suitability (Funktionale Eignung)

| Sub-Charakteristik | Score | Details |
|---------------------|-------|---------|
| Functional Completeness | 3/5 | 22+ Intents implementiert, alle Kernfunktionen vorhanden. Aber: Orphan intents (H-05), fehlende alarm.yaml im Repo |
| Functional Correctness | 1/5 | **KRITISCH:** 6 YAML Duplicate-Key-Bugs → Helligkeit, Farbe, Entity-On/Off, Cover Entity-Open/Close sind STILL BROKEN. Slot-Mismatches (K-09). media_stop nicht unterstützt (K-10) |
| Functional Appropriateness | 4/5 | Gutes Design: Router-Pattern, Intent-Fallback, Voice-first UX, Display-Integration |

**Score: 2.7/5 — Schwere funktionale Defekte durch YAML-Bugs**

### 5.2 Performance Efficiency (Leistungseffizienz)

| Sub-Charakteristik | Score | Details |
|---------------------|-------|---------|
| Time Behaviour | 3/5 | Radio Browser API: 3-Server-Failover → langsam bei Timeout. Spotify: ADB-Wakeup braucht bis zu 15s |
| Resource Utilization | 4/5 | Nur stdlib, minimaler Memory-Footprint. Aber: Keine Connection-Pools (N-02) |
| Capacity | 4/5 | Skaliert für Single-User gut. weather.yaml mit 85KB ist oversized |

**Score: 3.7/5**

### 5.3 Compatibility (Kompatibilität)

| Sub-Charakteristik | Score | Details |
|---------------------|-------|---------|
| Co-existence | 3/5 | StopReminder/GeneralStop/SentenceTrigger Collision (H-06). SpotifyPause/EchoStumm Overlap |
| Interoperability | 4/5 | Gute Integration: HA API, Spotify Web API, Radio Browser API, ADB, View Assist |

**Score: 3.5/5**

### 5.4 Usability (Benutzerfreundlichkeit)

| Sub-Charakteristik | Score | Details |
|---------------------|-------|---------|
| Appropriateness Recognizability | 4/5 | README vorhanden, CHANGELOG aktuell |
| Learnability | 3/5 | Keine Setup-Anleitung für Secrets/ADB. Hardcoded Config statt Konfigurationsdatei |
| Operability | 4/5 | Shell-Commands, Sentence Triggers — gutes Operations-Design |
| User Error Protection | 2/5 | Stille Fehler (H-04), keine Fehlermeldungen bei YAML-Bugs, kein Health-Check |
| Accessibility | 3/5 | Voice-first ✓, aber keine alternative Steuerung bei STT-Ausfall |

**Score: 3.2/5**

### 5.5 Reliability (Zuverlässigkeit)

| Sub-Charakteristik | Score | Details |
|---------------------|-------|---------|
| Maturity | 2/5 | Keine Tests (N-08), keine CI/CD (N-09), Production-Code mit Debug-Remnants |
| Availability | 3/5 | VACA-Disconnects (N-04), ADB-Wakeup Retry-Logik vorhanden. Aber: Shell-Command-Fehler unsichtbar |
| Fault Tolerance | 2/5 | `sys.exit(0)` bei Fehlern (H-04), fehlende shell_command (K-11), keine Retry-Logik (M-09) |
| Recoverability | 3/5 | HA restart recovert alles. Aber: Keine Healthchecks, keine Auto-Recovery bei Script-Fehlern |

**Score: 2.5/5 — Unzureichende Fehlertoleranz**

### 5.6 Security (Sicherheit)

| Sub-Charakteristik | Score | Details |
|---------------------|-------|---------|
| Confidentiality | 0/5 | **Secrets auf öffentlichem GitHub.** Token + Spotify Creds exposed |
| Integrity | 2/5 | Shell Injection möglich (H-02), keine Input-Validierung |
| Non-repudiation | 1/5 | Kein Audit-Trail, inkonsistentes Logging |
| Accountability | 1/5 | Kein Authentication-Logging, Token hat Admin-Rechte |
| Authenticity | 2/5 | SSL deaktiviert, Man-in-the-Middle möglich |

**Score: 1.2/5 — KRITISCH**

### 5.7 Maintainability (Wartbarkeit)

| Sub-Charakteristik | Score | Details |
|---------------------|-------|---------|
| Modularity | 3/5 | Gute Dateistruktur (sentences/intents getrennt), aber Code-Duplizierung (M-02) |
| Reusability | 2/5 | HA-API-Wrapper dupliziert, weather_macros.jinja ungenutzt (M-03), ~50 hardcoded Entity-IDs |
| Analysability | 3/5 | Gut kommentiert, aber inkonsistentes Logging (print vs logging) |
| Modifiability | 3/5 | YAML-Struktur flexibel, Python clean. Aber: Hardcoded Config, keine Config-Datei |
| Testability | 1/5 | 0% Test-Coverage, keine Mocks, keine Test-Fixtures |

**Score: 2.4/5**

### 5.8 Portability (Portabilität)

| Sub-Charakteristik | Score | Details |
|---------------------|-------|---------|
| Adaptability | 3/5 | Nur stdlib-Dependencies ✓. Aber: Hardcoded IPs, Entity-IDs, Gerätenamen |
| Installability | 2/5 | Keine Setup-Automatisierung, manuelle SCP-Deployment |
| Replaceability | 3/5 | Standard HA-Patterns (intent_scripts, custom_sentences), austauschbar |

**Score: 2.7/5**

### ISO 25010 Gesamtbewertung

```
╔════════════════════════════════════════════════════════════════╗
║  ISO 25010 SOFTWARE QUALITY SCORECARD                         ║
║                                                                ║
║  1. Functional Suitability  ████░░░░░░  2.7/5                 ║
║  2. Performance Efficiency  ███████░░░  3.7/5                 ║
║  3. Compatibility           ███████░░░  3.5/5                 ║
║  4. Usability               ██████░░░░  3.2/5                 ║
║  5. Reliability             █████░░░░░  2.5/5                 ║
║  6. Security                ██░░░░░░░░  1.2/5  ← KRITISCH    ║
║  7. Maintainability         ████░░░░░░  2.4/5                 ║
║  8. Portability             █████░░░░░  2.7/5                 ║
║                                                                ║
║  GESAMTSCORE: 2.7/5 (54%)                                     ║
║  Status: BELOW ACCEPTABLE THRESHOLD (3.0/5 = 60%)             ║
╚════════════════════════════════════════════════════════════════╝
```

---

## 6. Server-Validierung

### HA Configuration Check
- ✅ `check_config` bestanden — keine Konfigurationsfehler

### Entity-Existenz
- ✅ Alle 12 geprüften Entities existieren und sind erreichbar

### Pipeline
- ✅ `conversation.jarvis_router` als Agent konfiguriert
- ✅ `prefer_local_intents: true` gesetzt
- ✅ STT/TTS: Cloud (de-DE, KatjaNeural)

### Shell Commands
- ✅ `spotify_voice`, `spotify_device_transfer`, `radio_search` definiert
- ❌ `log_conv_raw` FEHLT (referenziert in scripts.yaml)

### Custom Components
- ✅ `jarvis_router` installiert und aktiv
- ✅ `vaca`, `view_assist` vorhanden

### Disk Space
- ✅ 34.4 GB frei (42% genutzt)

### Bekannte Runtime-Fehler (Server-Logs)
| Fehler | Häufigkeit | Schwere |
|--------|-----------|---------|
| `media_player.spotify_sven` → `media_stop` not supported | ~15x | KRITISCH |
| `shell_command.spotify_voice` exit code 1 | 1x | HOCH |
| VACA satellite disconnect/reconnect | periodisch | NIEDRIG |

---

## 7. Empfohlene Nächste Schritte

### Phase 1: Notfall-Fixes (SOFORT, < 24h)

| # | Aktion | Aufwand | Befunde |
|---|--------|---------|---------|
| 1 | **HA-Token revoken**, neuen Token generieren, in `/config/secrets.yaml` speichern | 15 min | K-01 |
| 2 | **Spotify App-Credentials rotieren** in Developer Dashboard | 10 min | K-02 |
| 3 | **GitHub Repo auf Private** setzen oder git filter-branch für Secret-Removal | 30 min | K-01, K-02 |
| 4 | **Python Scripts**: Token/Secrets aus Env-Vars oder secrets.yaml lesen | 1h | K-01, K-02, K-03 |

### Phase 2: Funktionale Reparaturen (Woche 1)

| # | Aktion | Aufwand | Befunde |
|---|--------|---------|---------|
| 5 | **lights.yaml:** Alle Duplicate Keys zusammenführen (`HassLightSet`, `HassTurnOn`, `HassTurnOff`) | 1h | K-04, K-05, K-06 |
| 6 | **covers.yaml:** Duplicate Keys zusammenführen (`HassOpenCover`, `HassCloseCover`) | 30 min | K-07, K-08 |
| 7 | **covers.yaml Intent Scripts:** `name` → `area` Slot-Fix, `area_id()` verwenden | 30 min | K-09 |
| 8 | **StopReminder/GeneralStop:** `media_stop` → `media_play_pause` ersetzen | 15 min | K-10 |
| 9 | **`log_conv_raw`:** Shell-Command definieren oder Script deaktivieren | 15 min | K-11 |
| 10 | **radio_search.py:** `sys.exit(0)` → `sys.exit(1)` bei Fehlern | 5 min | H-04 |

### Phase 3: Code-Qualität (Woche 2-3)

| # | Aktion | Aufwand | Befunde |
|---|--------|---------|---------|
| 11 | **SSL-Verifikation** in radio_search.py aktivieren | 15 min | H-01 |
| 12 | **Shell Injection Fix** in spotify_voice.py (shlex.quote) | 10 min | H-02 |
| 13 | **Gemeinsames `ha_utils.py`** Modul für HA API Calls | 2h | M-02 |
| 14 | **spotify_voice.py**: Von print() auf logging umstellen | 30 min | M-05 |
| 15 | **`service:` → `action:`** Migration in allen Intent Scripts | 30 min | M-04 |
| 16 | **conversation.py** Return-Typ Fix | 10 min | M-07 |
| 17 | **Unused imports** entfernen | 5 min | M-01, N-01 |
| 18 | **alarm.yaml** + **spotify_wrapper.py**: Ins Repo / aufräumen | 15 min | H-07, H-08 |

### Phase 4: Architektur-Verbesserungen (Monat 1)

| # | Aktion | Aufwand | Befunde |
|---|--------|---------|---------|
| 19 | **Test-Framework** einrichten (pytest + Fixtures) | 4h | N-08 |
| 20 | **CI/CD Pipeline** (.github/workflows/ci.yml) | 2h | N-09 |
| 21 | **Config-Management**: Entity-IDs, Pfade, Gerätenamen in zentrale Config | 3h | M-11, N-03, N-06 |
| 22 | **weather.yaml Refactoring**: weather_macros.jinja nutzen oder Template-Reuse | 3h | M-03 |
| 23 | **Security Policy** dokumentieren | 1h | ISO 27001 |
| 24 | **Health-Check Script** für automatische Validierung aller Components | 2h | Allgemein |
| 25 | **Retry-Logik** für externe API-Calls | 1h | M-09 |

### Geschätzter Gesamtaufwand

| Phase | Aufwand | Priorität |
|-------|---------|-----------|
| Phase 1: Notfall-Fixes | ~2h | ⛔ SOFORT |
| Phase 2: Funktionale Reparaturen | ~2.5h | 🔴 Diese Woche |
| Phase 3: Code-Qualität | ~4h | 🟠 Nächste 2 Wochen |
| Phase 4: Architektur | ~16h | 🟡 Nächster Monat |
| **Gesamt** | **~24.5h** | |

---

## 8. Anhang

### A. Entity-Referenzen im Projekt

| Entity ID | Verwendet in |
|-----------|-------------|
| `sensor.quasselbuechse` | radio_search.py, spotify_voice.py, intent_scripts/* |
| `media_player.vaca_362812d56_mediaplayer` | radio_search.py, intent_scripts/radio.yaml, echo.yaml |
| `media_player.spotify_sven` | spotify_voice.py, intent_scripts/spotify.yaml |
| `input_boolean.spotify_ducking_active` | radio_search.py, intent_scripts/spotify.yaml |
| `input_text.radio_current_station` | radio_search.py, intent_scripts/radio.yaml |
| `input_text.radio_search_query` | radio_search.py, intent_scripts/radio.yaml |
| `input_text.radio_search_result` | radio_search.py, intent_scripts/radio.yaml |
| `input_text.spotify_query` | spotify_voice.py, intent_scripts/spotify.yaml |
| `input_text.spotify_type` | spotify_voice.py, intent_scripts/spotify.yaml |
| `input_text.spotify_device` | spotify_voice.py, intent_scripts/spotify.yaml |
| `input_text.spotify_last_played` | spotify_voice.py |
| `weather.forecast_home` | intent_scripts/weather.yaml |

### B. Intent-Übersicht

| Intent | Typ | Sentences | Scripts | Status |
|--------|-----|-----------|---------|--------|
| HassTurnOn | HA Built-in + Custom | lights.yaml | — | ❌ Duplicate Key → nur "alle Lichter an" |
| HassTurnOff | HA Built-in + Custom | lights.yaml | — | ❌ Duplicate Key → nur "alle Lichter aus" |
| HassLightSet | HA Built-in + Custom | lights.yaml | — | ❌ Duplicate Key → nur color_temp |
| HassToggle | HA Built-in + Custom | lights.yaml | — | ✅ OK |
| HassOpenCover | HA Built-in + Custom | covers.yaml | — | ❌ Duplicate Key → nur "alle Rolladen" |
| HassCloseCover | HA Built-in + Custom | covers.yaml | — | ❌ Duplicate Key → nur "alle Rolladen" |
| HassStopCover | HA Built-in + Custom | covers.yaml | — | ✅ OK |
| HassSetCoverPosition | HA Built-in + Custom | covers.yaml | — | ✅ OK |
| HassSetCoverTiltPosition | HA Built-in + Custom | covers.yaml | — | ✅ OK |
| LightBrighterArea | Custom | lights.yaml | lights.yaml | ✅ OK |
| LightDarkerArea | Custom | lights.yaml | lights.yaml | ✅ OK |
| LightMaxArea | Custom | lights.yaml | lights.yaml | ✅ OK |
| LightMinArea | Custom | lights.yaml | lights.yaml | ✅ OK |
| LightBrighterEntity | Custom | lights.yaml | lights.yaml | ✅ OK |
| LightDarkerEntity | Custom | lights.yaml | lights.yaml | ✅ OK |
| LightMaxEntity | Custom | lights.yaml | lights.yaml | ✅ OK |
| LightMinEntity | Custom | lights.yaml | lights.yaml | ✅ OK |
| GetLightState | Custom | lights.yaml | — (inline) | ✅ OK |
| SetSunProtection | Custom | covers.yaml | covers.yaml | ⚠️ Slot mismatch |
| DisableSunProtection | Custom | covers.yaml | covers.yaml | ⚠️ Slot mismatch |
| EnableCoverAutomation | Custom | covers.yaml | covers.yaml | ⚠️ Slot mismatch |
| DisableCoverAutomation | Custom | covers.yaml | covers.yaml | ⚠️ Slot mismatch |
| GetCoverState | Custom | covers.yaml | covers.yaml | ⚠️ Slot mismatch |
| SetCoverScene | Custom | covers.yaml | covers.yaml | ✅ OK (nutzt trigger_sentence) |
| ScheduleCover | Custom | — | covers.yaml | ❌ Orphan (kein Sentence) |
| RadioSearch | Custom | radio.yaml | radio.yaml | ✅ OK |
| RadioStop | Custom | radio.yaml | radio.yaml | ✅ OK |
| SpotifySearch | Custom | spotify.yaml | spotify.yaml | ✅ OK |
| SpotifyDevice | Custom | spotify.yaml | spotify.yaml | ✅ OK |
| SpotifyPause | Custom | spotify.yaml | spotify.yaml | ⚠️ Overlap mit EchoStumm |
| SpotifyResume | Custom | spotify.yaml | spotify.yaml | ⚠️ Bare "play" Pattern |
| GeneralStop | Custom | — | — | ✅ Sentence Trigger |
| StopReminder | Custom | reminders.yaml | reminders.yaml | ⚠️ Broad patterns |
| SetReminder | Custom | reminders.yaml | reminders.yaml | ✅ OK |
| GetWeatherForecast | Custom | — (deprecated?) | weather.yaml | ❌ Orphan |

### C. Dateigrößen

| Datei | Größe |
|-------|-------|
| intent_scripts/weather.yaml | 85 KB |
| scripts/spotify_voice.py | 21 KB |
| custom_sentences/de/lights.yaml | 19 KB |
| custom_sentences/de/covers.yaml | 14 KB |
| scripts/radio_search.py | 12 KB |
| intent_scripts/covers.yaml | 8 KB |
| intent_scripts/lights.yaml | 7 KB |
| Alle anderen | < 5 KB |

---

*Report generiert am 2025-07-16 durch automatisierte Code-Analyse + manuelle Review*
*Analysiert: 32 Dateien, ~973 LOC Python, ~4000 LOC YAML, 1 Jinja2-Template*
