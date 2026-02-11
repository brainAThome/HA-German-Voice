"""Config flow for Jarvis Router."""
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow

DOMAIN = "jarvis_router"

class JarvisRouterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jarvis Router."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if user_input is not None:
            return self.async_create_entry(title="Jarvis Router", data={})
        return self.async_show_form(step_id="user")

    async def async_step_import(self, import_config=None):
        """Handle import from YAML config."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        return self.async_create_entry(title="Jarvis Router", data={})
