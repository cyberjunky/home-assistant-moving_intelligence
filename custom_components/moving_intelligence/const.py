"""Constants for the Moving Intelligence integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "moving_intelligence"

# Config entry data keys; kept as-is so existing entries stay compatible.
CONF_USERNAME: Final = "username"
CONF_APIKEY: Final = "apikey"

UPDATE_INTERVAL: Final = timedelta(minutes=1)
