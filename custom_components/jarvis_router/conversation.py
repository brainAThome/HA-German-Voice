"""Conversation entity for Jarvis Router."""
import logging

from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationInput,
    ConversationResult,
    async_converse,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

NO_MATCH_PHRASES = [
    "das habe ich nicht verstanden",
    "existiert nicht",
    "kein bereich",
    "nicht gefunden",
    "konnte nicht",
    "nicht vorhanden",
    "tut mir leid",
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jarvis Router conversation entity."""
    async_add_entities([JarvisRouterEntity(config_entry)])
    _LOGGER.info("Jarvis Router conversation entity created")


class JarvisRouterEntity(ConversationEntity):
    """Conversation entity that routes between local intents and Ollama."""

    _attr_has_entity_name = True
    _attr_name = "Jarvis Router"

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry
        self._attr_unique_id = config_entry.entry_id

    @property
    def supported_languages(self) -> list[str]:
        return ["de"]

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Route: try local intents first, fallback to Ollama."""
        text = user_input.text
        _LOGGER.debug("Router received: %s", text)

        # Step 1: Try HA local intents (custom_sentences + built-in)
        try:
            local_result = await async_converse(
                hass=self.hass,
                text=text,
                conversation_id=user_input.conversation_id,
                context=user_input.context,
                language=user_input.language or "de",
                agent_id="conversation.home_assistant",
            )

            response = local_result.response
            if response.response_type.value != "error":
                _LOGGER.debug("Local intent matched: %s", response.response_type)
                return local_result

            # Extract speech
            speech = ""
            if response.speech:
                speech = response.speech.get("plain", {}).get("speech", "")

            is_no_match = any(p in speech.lower() for p in NO_MATCH_PHRASES)
            if not is_no_match:
                _LOGGER.debug("Local intent error (keeping): %s", speech)
                return local_result

            _LOGGER.debug("No match, routing to Ollama: %s", speech[:80])

        except Exception as ex:
            _LOGGER.warning("Local intent failed: %s", ex)

        # Step 2: Fallback to Ollama
        try:
            _LOGGER.debug("Ollama fallback for: %s", text)
            ollama_result = await async_converse(
                hass=self.hass,
                text=text,
                conversation_id=None,
                context=user_input.context,
                language=user_input.language or "de",
                agent_id="conversation.ollama_conversation",
            )
            _LOGGER.debug("Ollama responded")
            return ollama_result

        except Exception as ex:
            _LOGGER.error("Ollama fallback failed: %s", ex)
            from homeassistant.helpers.intent import IntentResponse, IntentResponseType
            err = IntentResponse(language=user_input.language or "de")
            err.response_type = IntentResponseType.ERROR
            err.async_set_speech("Entschuldigung, ich konnte keine Antwort finden.")
            return ConversationResult(response=err, conversation_id=user_input.conversation_id)
