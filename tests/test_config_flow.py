"""Tests for the Moving Intelligence config flow."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pymovingintelligence_ha.utils import InvalidAuthError
from pytest_homeassistant.common import MockConfigEntry

from custom_components.moving_intelligence.const import CONF_APIKEY, CONF_USERNAME, DOMAIN

from .conftest import ENTRY_DATA, USERNAME


async def test_user_flow_success(
    hass: HomeAssistant, mock_flow_client: MagicMock, mock_setup_entry: AsyncMock
) -> None:
    """A valid username and API key create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], dict(ENTRY_DATA))
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == USERNAME
    assert result["data"] == ENTRY_DATA
    assert result["result"].unique_id == f"{DOMAIN}:{USERNAME}"
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (InvalidAuthError("bad"), "invalid_auth"),
        (ClientError("down"), "cannot_connect"),
        (TimeoutError(), "cannot_connect"),
        (TypeError("boom"), "unknown"),
    ],
)
async def test_user_flow_errors_and_recovery(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
    mock_setup_entry: AsyncMock,
    side_effect: Exception,
    error: str,
) -> None:
    """Errors are shown on the form and the user can retry."""
    mock_flow_client.get_devices.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=dict(ENTRY_DATA)
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_flow_client.get_devices.side_effect = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], dict(ENTRY_DATA))
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_duplicate_aborts(
    hass: HomeAssistant, mock_flow_client: MagicMock, mock_config_entry: MockConfigEntry
) -> None:
    """Adding the same username twice aborts."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=dict(ENTRY_DATA)
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_flow_client.get_devices.assert_not_called()


async def test_reauth_flow(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Reauth asks for a new API key, shows errors, then updates the entry."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["description_placeholders"]["username"] == USERNAME

    mock_flow_client.get_devices.side_effect = InvalidAuthError("bad")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_APIKEY: "still-wrong"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    mock_flow_client.get_devices.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_APIKEY: "new-key"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data == {CONF_USERNAME: USERNAME, CONF_APIKEY: "new-key"}
