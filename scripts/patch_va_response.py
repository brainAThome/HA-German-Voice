#!/usr/bin/env python3
"""
Patcht View Assist entity_listeners.py für Jarvis Speaker.

Fixes:
1. Race Condition: Daten werden ZUERST gesetzt, DANN wird navigiert
2. Title "AI Response" → "Jarvis" (deutsch/personalisiert)
3. Dynamische Font-Size (6 Stufen) für 5.5" Echo Show Display
4. Auch lokal verarbeitete Antworten anzeigen wenn kein Entity betroffen
5. Wetter-Fix: Wenn changed_entities (Wetter etc.) vorhanden aber keine
   lights/switches/todos matchen, trotzdem Info-View anzeigen
6. Revert-Fix: Expliziter 30s Timeout für Info-View Navigation
7. Kurze Bestätigungen (<=6 Wörter) nur Sprache, kein Display

Kann nach View Assist Updates erneut ausgeführt werden.
"""

FILE = "/config/custom_components/view_assist/devices/entity_listeners.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Backup erstellen
with open(FILE + ".bak", "w", encoding="utf-8") as f:
    f.write(content)
print(f"Backup erstellt: {FILE}.bak")

# ============================================================
# PATCH: Kompletter Block von entities/todos bis Info-View
# ============================================================

# Original VA Code (ungepatcht)
OLD_BLOCK = '''                # Process changes to update sensor and navigate view if needed
                if entities:
                    _LOGGER.debug("Entities affected: %s", entities)
                    entities_output = [
                        {
                            "type": "custom:button-card",
                            "entity": entity,
                            "tap_action": {"action": "toggle"},
                            "double_tap_action": {"action": "more-info"},
                        }
                        for entity in entities
                    ]
                    updates["intent_entities"] = entities_output
                    self._update_sensor_entity(updates)
                    if navigation_manager:
                        navigation_manager.browser_navigate(
                            self.config.runtime_data.dashboard.intent
                        )
                elif todos:
                    _LOGGER.debug("Todo lists affected: %s", todos)
                    updates["list"] = todos[0]  # Just use the first todo list
                    self._update_sensor_entity(updates)
                    if navigation_manager:
                        navigation_manager.browser_navigate(
                            self.config.runtime_data.dashboard.list_view
                        )
            # Checks if AI response or if no speech is returned
            elif not processed_locally and speech_text != "*":
                _LOGGER.debug("No entities or todo lists affected")
                word_count = len(speech_text.split())
                message_font_size = ["10vw", "8vw", "6vw", "4vw"][
                    min(word_count // 6, 3)
                ]
                # Navigate first to trigger title clear
                if navigation_manager:
                    navigation_manager.browser_navigate("view-assist/info")
                # Then set the title/message after navigation to prevent clearing
                updates.update(
                    {
                        "title": "AI Response",
                        "message_font_size": message_font_size,
                        "message": speech_text,
                    }
                )
                self._update_sensor_entity(updates)'''

# Gepatchter Code
NEW_BLOCK = '''                # Process changes to update sensor and navigate view if needed
                if entities:
                    _LOGGER.debug("Entities affected: %s", entities)
                    entities_output = [
                        {
                            "type": "custom:button-card",
                            "entity": entity,
                            "tap_action": {"action": "toggle"},
                            "double_tap_action": {"action": "more-info"},
                        }
                        for entity in entities
                    ]
                    updates["intent_entities"] = entities_output
                    self._update_sensor_entity(updates)
                    if navigation_manager:
                        navigation_manager.browser_navigate(
                            self.config.runtime_data.dashboard.intent
                        )
                    return
                elif todos:
                    _LOGGER.debug("Todo lists affected: %s", todos)
                    updates["list"] = todos[0]  # Just use the first todo list
                    self._update_sensor_entity(updates)
                    if navigation_manager:
                        navigation_manager.browser_navigate(
                            self.config.runtime_data.dashboard.list_view
                        )
                    return
            # AI/Conversation Response anzeigen
            # Zeigt sowohl Ollama-Antworten als auch lokale Antworten ohne
            # Entity-Änderungen an (z.B. Wetter-Infos, allgemeine Fragen)
            if speech_text and speech_text != "*":
                word_count = len(speech_text.split())
                # Kurze Bestaetigungen (<=6 Woerter) nur Sprache, kein Display
                if word_count <= 6:
                    _LOGGER.debug("Short confirmation, skip display: '%s'", speech_text)
                    self._update_sensor_entity(updates)
                    return
                _LOGGER.debug("AI/Conversation response display")
                # Font-Size optimiert für kleine Displays (5.5" Echo Show)
                # Dynamische Skalierung: je mehr Wörter, desto kleiner
                if word_count <= 8:
                    message_font_size = "9vw"
                elif word_count <= 16:
                    message_font_size = "7vw"
                elif word_count <= 24:
                    message_font_size = "6vw"
                elif word_count <= 40:
                    message_font_size = "5vw"
                elif word_count <= 60:
                    message_font_size = "4vw"
                else:
                    message_font_size = "3.5vw"
                # ERST Daten setzen, DANN navigieren (verhindert leere Anzeige)
                updates.update(
                    {
                        "title": "Jarvis",
                        "message_font_size": message_font_size,
                        "message": speech_text,
                    }
                )
                self._update_sensor_entity(updates)
                # Navigation NACH dem Setzen der Daten
                if navigation_manager:
                    navigation_manager.browser_navigate("view-assist/info", timeout=30)'''

if OLD_BLOCK in content:
    content = content.replace(OLD_BLOCK, NEW_BLOCK)
    print("PATCH angewendet: Komplett (Race Condition + Font + Wetter + Revert)")
elif "# AI/Conversation response display" in content:
    print("Bereits gepatcht — prüfe Einzelfixes...")
    patched = False

    # Upgrade: 4-Stufen → 6-Stufen Font
    if '["9vw", "7vw", "6vw", "5vw"]' in content:
        OLD_FONT = '''                message_font_size = ["9vw", "7vw", "6vw", "5vw"][
                    min(word_count // 8, 3)
                ]'''
        NEW_FONT = '''                if word_count <= 8:
                    message_font_size = "9vw"
                elif word_count <= 16:
                    message_font_size = "7vw"
                elif word_count <= 24:
                    message_font_size = "6vw"
                elif word_count <= 40:
                    message_font_size = "5vw"
                elif word_count <= 60:
                    message_font_size = "4vw"
                else:
                    message_font_size = "3.5vw"'''
        content = content.replace(OLD_FONT, NEW_FONT)
        print("  → Font-Size auf 6 Stufen aktualisiert")
        patched = True

    # Wetter-Fix: return nach entities/todos + elif→if
    if 'elif speech_text and speech_text != "*":' in content:
        content = content.replace(
            'elif speech_text and speech_text != "*":',
            'if speech_text and speech_text != "*":'
        )
        print("  → elif->if für speech_text (Wetter-Fix)")
        patched = True

    # return nach entities navigate
    old_ent = (
        "                            self.config.runtime_data.dashboard.intent\n"
        "                        )\n"
        "                elif todos:"
    )
    new_ent = (
        "                            self.config.runtime_data.dashboard.intent\n"
        "                        )\n"
        "                    return\n"
        "                elif todos:"
    )
    if old_ent in content:
        content = content.replace(old_ent, new_ent)
        print("  → return nach entities navigate")
        patched = True

    # return nach todos navigate
    old_todo = (
        "                            self.config.runtime_data.dashboard.list_view\n"
        "                        )\n"
        "            # AI/Conversation Response anzeigen"
    )
    new_todo = (
        "                            self.config.runtime_data.dashboard.list_view\n"
        "                        )\n"
        "                    return\n"
        "            # AI/Conversation Response anzeigen"
    )
    if old_todo in content:
        content = content.replace(old_todo, new_todo)
        print("  → return nach todos navigate")
        patched = True

    # Expliziter Timeout
    if 'browser_navigate("view-assist/info")' in content:
        content = content.replace(
            'browser_navigate("view-assist/info")',
            'browser_navigate("view-assist/info", timeout=30)'
        )
        print("  → Expliziter 30s Timeout für Info-View")
        patched = True

    if not patched:
        print("  Alle Fixes bereits vorhanden ✓")
else:
    print("WARNUNG: Code-Struktur hat sich geändert!")
    print("Manuelle Anpassung nötig.")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("\nDone. HA muss neu gestartet werden damit die Änderungen wirksam werden.")
