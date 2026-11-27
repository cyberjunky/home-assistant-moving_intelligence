"""Data update coordinator for the Moving Intelligence integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymovingintelligence_ha import MovingIntelligence
from pymovingintelligence_ha.utils import InvalidAuthError

from .const import CONF_APIKEY, CONF_USERNAME, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type MovingIntelligenceConfigEntry = ConfigEntry[MovingIntelligenceCoordinator]
type VehicleData = dict[str, Any]


def vehicle_key(vehicle: VehicleData) -> str:
    """Return the stable key of a vehicle (its chassis number / VIN)."""
    return str(vehicle.get("chassis_number") or vehicle.get("id"))


class MovingIntelligenceCoordinator(DataUpdateCoordinator[dict[str, VehicleData]]):
    """Poll the Moving Intelligence API for all vehicles of an account."""

    config_entry: MovingIntelligenceConfigEntry

    def __init__(self, hass: HomeAssistant, entry: MovingIntelligenceConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = MovingIntelligence(
            username=entry.data[CONF_USERNAME], apikey=entry.data[CONF_APIKEY]
        )

    async def _async_update_data(self) -> dict[str, VehicleData]:
        """Fetch the latest vehicle data, keyed by chassis number."""
        try:
            devices = await self.client.get_devices()
        except InvalidAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except Exception as err:
            # The library surfaces network errors and malformed/empty API
            # responses as arbitrary exceptions; treat them all as transient.
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err) or type(err).__name__},
            ) from err
        return {vehicle_key(device.data): device.data for device in devices}
