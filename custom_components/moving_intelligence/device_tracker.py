"""Device tracker for Moving Intelligence platform."""
import logging

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the Moving Intelligence tracker from config entry."""
    trackers = []

    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    for vehicle in coordinator.data:
        tracker = MovingIntelligenceLocationTracker(coordinator, vehicle.data)
        trackers.append(tracker)

    async_add_devices(trackers, True)


class MovingIntelligenceBaseEntity(CoordinatorEntity):
    """Base entity for Moving Intelligence tracker."""
    def __init__(self, coordinator, vehicle) -> None:
        super().__init__(coordinator)
        self._vehicle = vehicle
        self._vin = vehicle["chassis_number"]
        self._plate = vehicle["license_plate"]
        self._model = "{} {}".format(vehicle["make"], vehicle["model"])
        self._name =  "{} {}".format(vehicle["license_plate"], self._model)

        self._attr_name = self._name
        self._attr_unique_id = f"Moving Intelligence {self._vin}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._vin)},
            "name": self._vin,
            "model": self._model,
            "manufacturer": "Moving Intelligence",
        }

    @property
    def vehicle(self):
        return self._vehicle

    @property
    def available(self):
        return True


class MovingIntelligenceLocationTracker(MovingIntelligenceBaseEntity, TrackerEntity):
    """The Moving Intelligence tracker."""
    def __init__(self, coordinator, vehicle) -> None:
        """Initialize the Tracker."""
        super().__init__(coordinator, vehicle)
        self._vin = vehicle["license_plate"]

        self._attr_unique_id = f"Moving Intelligence {self._vin}"
        self._attr_icon = "mdi:car"
        self._attr_extra_state_attributes = vehicle

    @property
    def latitude(self):
        return self.vehicle["latitude"]

    @property
    def longitude(self):
        return self.vehicle["longitude"]

    @property
    def source_type(self):
        return SOURCE_TYPE_GPS

    @property
    def available(self):
        return True
