"""Fixtures for Moving Intelligence tests."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.moving_intelligence.const import CONF_APIKEY, CONF_USERNAME, DOMAIN

USERNAME = "user@example.com"
APIKEY = "secret-key"
VIN = "WVWZZZ1KZAW000001"
ENTRY_DATA = {CONF_USERNAME: USERNAME, CONF_APIKEY: APIKEY}


def vehicle_data(**overrides: Any) -> dict[str, Any]:
    """Return a vehicle as produced by pymovingintelligence_ha Device.data."""
    data: dict[str, Any] = {
        "id": 1234,
        "make": "Volkswagen",
        "model": "Golf",
        "license_plate": "AB-123-C",
        "chassis_number": VIN,
        "in_use_date": "2020-01-01 00:00:00",
        "year": 2019,
        "remarks": None,
        "latitude": 52.37,
        "longitude": 4.89,
        "odometer": 54321,
        "speed": 0,
        "start_trip_time": "2026-11-06 08:00:00",
        "start_trip_address": "Street 1, Utrecht, NL",
        "end_trip_time": "2026-11-06 08:45:00",
        "end_trip_address": "Dam 1, Amsterdam, NL",
        "trip_distance": 42.0,
        "last_seen": "2026-11-06 08:45:00",
        "location_alias": "Work",
    }
    data.update(overrides)
    return data


def make_device(**overrides: Any) -> MagicMock:
    """Return a mocked library Device."""
    device = MagicMock()
    device.data = vehicle_data(**overrides)
    return device


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a config entry shaped like those created by every released version."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=USERNAME,
        data=dict(ENTRY_DATA),
        unique_id=f"{DOMAIN}:{USERNAME}",
    )


@pytest.fixture
def mock_client() -> Generator[MagicMock]:
    """Patch the API client used by the coordinator."""
    with patch(
        "custom_components.moving_intelligence.coordinator.MovingIntelligence", autospec=True
    ) as mock_cls:
        client = mock_cls.return_value
        client.get_devices = AsyncMock(return_value=[make_device()])
        yield client


@pytest.fixture
def mock_flow_client() -> Generator[MagicMock]:
    """Patch the API client used by the config flow."""
    with patch(
        "custom_components.moving_intelligence.config_flow.MovingIntelligence", autospec=True
    ) as mock_cls:
        client = mock_cls.return_value
        client.get_devices = AsyncMock(return_value=[make_device()])
        yield client


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Prevent the integration from actually being set up after a flow."""
    with patch(
        "custom_components.moving_intelligence.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup
