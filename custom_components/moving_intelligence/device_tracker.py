"""Support for Moving Intelligence Platform."""
import logging

from pymovingintelligence_ha import MovingIntelligence

import requests
import voluptuous as vol
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker import (
    PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
)
from homeassistant.const import CONF_API_KEY, CONF_INCLUDE, CONF_USERNAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_utc_time_change

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PARENT_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_INCLUDE, default=[]): vol.All(cv.ensure_list, [cv.string]),
    }
)


def setup_scanner(hass, config: dict, see, discovery_info=None):
    """Set up the DeviceScanner."""
    scanner = MovingIntelligenceTracker(config, see)
    scanner.setup(hass)

    return True


class MovingIntelligenceTracker(TrackerEntity):
    """Define a scanner for the MovingIntelligence platform."""

    def __init__(self, config, see):
        """Initialize MovingIntellgienceScanner."""
        self._include = config.get(CONF_INCLUDE)
        self._see = see

        self._api = MovingIntelligence(
            username=config.get(CONF_USERNAME),
            apikey=config.get(CONF_API_KEY),
        )


    def setup(self, hass):
        """Set up a timer and start gathering devices."""
        self._refresh()
        track_utc_time_change(
            hass, lambda now: self._refresh(), second=range(0, 60, 30)
        )


    def _refresh(self) -> None:
        """Refresh device information from the MovingIntelligence platform."""
        try:
            devices = self._api.get_devices()

            for device in devices:
                if not self._include or device.license_plate in self._include:

                    self._see(
                        dev_id=device.plate_as_id,
                        gps=(device.latitude, device.longitude),
                        attributes=device.state_attributes,
                        icon="mdi:car",
                    )
        except requests.exceptions.ConnectionError:
            _LOGGER.error("ConnectionError: Could not connect to MovingIntelligence")
