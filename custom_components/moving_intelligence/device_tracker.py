"""Device tracker platform for the Moving Intelligence integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    MovingIntelligenceConfigEntry,
    MovingIntelligenceCoordinator,
    VehicleData,
)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MovingIntelligenceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Moving Intelligence trackers from a config entry."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    def _add_new_vehicles() -> None:
        new = set(coordinator.data) - known
        known.update(new)
        async_add_entities(MovingIntelligenceTracker(coordinator, key) for key in new)

    _add_new_vehicles()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_vehicles))


class MovingIntelligenceTracker(CoordinatorEntity[MovingIntelligenceCoordinator], TrackerEntity):
    """A vehicle tracked by Moving Intelligence."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "vehicle"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: MovingIntelligenceCoordinator, key: str) -> None:
        """Initialize the tracker."""
        super().__init__(coordinator)
        self._key = key
        vehicle = coordinator.data[key]
        # key is the chassis number (VIN). Unique ID format predates this version;
        # keep it so entity IDs and history survive.
        self._attr_unique_id = f"Moving Intelligence {key}"
        # BaseTrackerEntity types _attr_device_info as None; vehicles do get a device.
        self._attr_device_info = DeviceInfo(  # type: ignore[assignment]
            identifiers={(DOMAIN, key)},
            name=vehicle["license_plate"],
            manufacturer=vehicle["make"],
            model=vehicle["model"],
            serial_number=vehicle["chassis_number"],
        )

    @property
    def _vehicle(self) -> VehicleData | None:
        return self.coordinator.data.get(self._key)

    @property
    def available(self) -> bool:
        """Return True if the last poll succeeded and still reported this vehicle."""
        return super().available and self._vehicle is not None

    @property
    def latitude(self) -> float | None:
        """Return the latitude, or None when no position is known yet."""
        return self._position[0]

    @property
    def longitude(self) -> float | None:
        """Return the longitude, or None when no position is known yet."""
        return self._position[1]

    @property
    def _position(self) -> tuple[float | None, float | None]:
        vehicle = self._vehicle or {}
        lat, lon = vehicle.get("latitude"), vehicle.get("longitude")
        # The library reports 0/0 when the vehicle has no trips this month.
        if not lat and not lon:
            return None, None
        return lat, lon

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return all vehicle data reported by the API."""
        return self._vehicle
