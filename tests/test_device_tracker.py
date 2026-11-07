"""Tests for the Moving Intelligence device tracker."""

from unittest.mock import MagicMock

from aiohttp import ClientError
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import STATE_NOT_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed

from custom_components.moving_intelligence.const import DOMAIN, UPDATE_INTERVAL

from .conftest import VIN, make_device

ENTITY_ID = "device_tracker.ab_123_c"


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _tick(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_tracker_state(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Vehicle position, attributes, unique ID and device are exposed."""
    await _setup(hass, mock_config_entry)

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_NOT_HOME
    assert state.attributes["latitude"] == 52.37
    assert state.attributes["longitude"] == 4.89
    assert state.attributes["source_type"] == "gps"
    assert state.attributes["odometer"] == 54321
    assert state.attributes["location_alias"] == "Work"
    assert state.attributes["friendly_name"] == "AB-123-C"

    entity = entity_registry.async_get(ENTITY_ID)
    assert entity is not None
    # Unchanged from earlier releases so existing entities keep their entity ID and history.
    assert entity.unique_id == f"Moving Intelligence {VIN}"
    assert entity.translation_key == "vehicle"

    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, VIN), mock_config_entry.entry_id
    )
    assert device is not None
    assert device.name == "AB-123-C"
    assert device.manufacturer == "Volkswagen"
    assert device.model == "Golf"


async def test_existing_entity_id_is_kept(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """An entity registered by an older version keeps its entity ID."""
    mock_config_entry.add_to_hass(hass)
    entity_registry.async_get_or_create(
        "device_tracker",
        DOMAIN,
        f"Moving Intelligence {VIN}",
        suggested_object_id="ab_123_c_volkswagen_golf",
        config_entry=mock_config_entry,
    )
    await _setup(hass, mock_config_entry)

    assert hass.states.get("device_tracker.ab_123_c_volkswagen_golf") is not None
    assert hass.states.get(ENTITY_ID) is None


async def test_tracker_updates_and_availability(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Polls move the tracker; failures and missing vehicles mark it unavailable."""
    await _setup(hass, mock_config_entry)

    mock_client.get_devices.return_value = [make_device(latitude=51.92, longitude=4.48)]
    await _tick(hass, freezer)
    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.attributes["latitude"] == 51.92

    mock_client.get_devices.side_effect = ClientError("down")
    await _tick(hass, freezer)
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE  # type: ignore[union-attr]

    mock_client.get_devices.side_effect = None
    mock_client.get_devices.return_value = []
    await _tick(hass, freezer)
    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE  # type: ignore[union-attr]

    mock_client.get_devices.return_value = [make_device()]
    await _tick(hass, freezer)
    assert hass.states.get(ENTITY_ID).state == STATE_NOT_HOME  # type: ignore[union-attr]


async def test_no_position_yet(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """A vehicle without trips (library reports 0/0) has an unknown state."""
    mock_client.get_devices.return_value = [make_device(latitude=0, longitude=0)]
    await _setup(hass, mock_config_entry)
    assert hass.states.get(ENTITY_ID).state == STATE_UNKNOWN  # type: ignore[union-attr]


async def test_new_vehicle_added_on_update(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """A vehicle that appears later gets an entity without a reload."""
    await _setup(hass, mock_config_entry)
    assert len(hass.states.async_entity_ids("device_tracker")) == 1

    mock_client.get_devices.return_value = [
        make_device(),
        make_device(id=99, chassis_number="VIN2", license_plate="XY-999-Z"),
    ]
    await _tick(hass, freezer)
    assert len(hass.states.async_entity_ids("device_tracker")) == 2
    assert hass.states.get("device_tracker.xy_999_z") is not None
