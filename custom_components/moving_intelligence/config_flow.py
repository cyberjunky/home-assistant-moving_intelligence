"""Config flow for Moving Intelligence platform."""
import logging

from pymovingintelligence_ha import MovingIntelligence
from pymovingintelligence_ha.utils import InvalidAuthError
import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MovingIntelligenceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Moving Intelligence."""

    async def async_step_user(self, user_input=None):
        """Show form."""
        errors = {}
        if user_input is not None:
            data = await self.async_get_entry_data(user_input, errors)
            if data:
                return await self.async_create_or_update_entry(data=data)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("username"): str, vol.Required("apikey"): str}
            ),
            errors=errors,
        )

    async def async_get_entry_data(self, user_input, errors):
        """Check input."""
        try:
            client = MovingIntelligence(
                username=user_input["username"], apikey=user_input["apikey"]
            )
            await client.get_devices()
            return {"username": user_input["username"], "apikey": user_input["apikey"]}
        except InvalidAuthError:
            errors["base"] = "not_logged_in"
            _LOGGER.error("Not logged in")
        except Exception:
            errors["base"] = "unknown"
            _LOGGER.exception("Unknown error")

    async def async_create_or_update_entry(self, data):
        """Create or update configuration."""
        existing_entry = await self.async_set_unique_id(f"{DOMAIN}:{data['username']}")
        if existing_entry:
            self.hass.config_entries.async_update_entry(existing_entry, data=data)
            await self.hass.config_entries.async_reload(existing_entry.entry_id)
            return self.async_abort(reason="reauth_successful")
        return self.async_create_entry(title=data["username"], data=data)

    async def async_step_reauth(self):
        """Update configuration."""
        return await self.async_step_user()
