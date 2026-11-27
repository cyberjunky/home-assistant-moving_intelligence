"""Tests for Moving Intelligence setup and unload."""

from unittest.mock import MagicMock

import pytest
from aiohttp import ClientError
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant
from pymovingintelligence_ha.utils import InvalidAuthError
from pytest_homeassistant.common import MockConfigEntry

from custom_components.moving_intelligence.const import CONF_APIKEY, CONF_USERNAME


async def test_setup_and_unload(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """The integration loads through HA, creates entities and unloads cleanly."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert mock_config_entry.runtime_data.data
    assert len(hass.states.async_entity_ids("device_tracker")) == 1

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_client_uses_entry_credentials(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """The client is built from the stored username/API key."""
    from custom_components.moving_intelligence import coordinator

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator.MovingIntelligence.assert_called_once_with(  # type: ignore[attr-defined]
        username=mock_config_entry.data[CONF_USERNAME],
        apikey=mock_config_entry.data[CONF_APIKEY],
    )


@pytest.mark.parametrize("side_effect", [ClientError("down"), TimeoutError(), TypeError("None")])
async def test_setup_retry_on_connection_error(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    side_effect: Exception,
) -> None:
    """Transient API errors put the entry in setup-retry."""
    mock_client.get_devices.side_effect = side_effect
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_setup_auth_failure_starts_reauth(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """Rejected credentials fail setup and start a reauth flow."""
    mock_client.get_devices.side_effect = InvalidAuthError("bad")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH
    assert flows[0]["context"]["entry_id"] == mock_config_entry.entry_id
