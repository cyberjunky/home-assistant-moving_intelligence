"""Config flow for the Moving Intelligence integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from pymovingintelligence_ha import MovingIntelligence
from pymovingintelligence_ha.utils import InvalidAuthError

try:
    import probatio as vol
except ImportError:  # Home Assistant < 2026.10 ships voluptuous instead
    import voluptuous as vol  # type: ignore[no-redef]

from .const import CONF_APIKEY, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema({vol.Required(CONF_USERNAME): str, vol.Required(CONF_APIKEY): str})
REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_APIKEY): str})


async def _validate(username: str, apikey: str) -> str | None:
    """Try the credentials; return an error key or None on success."""
    client = MovingIntelligence(username=username, apikey=apikey)
    try:
        await client.get_devices()
    except InvalidAuthError:
        return "invalid_auth"
    except (ClientError, TimeoutError):
        return "cannot_connect"
    except Exception:
        _LOGGER.exception("Unexpected error validating Moving Intelligence credentials")
        return "unknown"
    return None


class MovingIntelligenceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Moving Intelligence."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME]
            # Unique ID format predates this flow; keep it so existing entries match.
            await self.async_set_unique_id(f"{DOMAIN}:{username}")
            self._abort_if_unique_id_configured()

            if not (error := await _validate(username, user_input[CONF_APIKEY])):
                return self.async_create_entry(
                    title=username,
                    data={CONF_USERNAME: username, CONF_APIKEY: user_input[CONF_APIKEY]},
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        """Start reauthentication when the API key is rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new API key."""
        entry = self._get_reauth_entry()
        username = entry.data[CONF_USERNAME]
        errors: dict[str, str] = {}
        if user_input is not None:
            apikey = user_input[CONF_APIKEY]
            if not (error := await _validate(username, apikey)):
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_APIKEY: apikey}
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            description_placeholders={"username": username},
            errors=errors,
        )
