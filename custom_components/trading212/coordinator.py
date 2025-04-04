"""Trading212 integration coordinator class."""

from __future__ import annotations

from datetime import timedelta
import logging

from pytrading212api.exceptions import (
    Trading212BadApiKey,
    Trading212Error,
    Trading212Limited,
    Trading212TimeOut,
)
from pytrading212api.position import Position

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class Trading212Coordinator(DataUpdateCoordinator):
    """Coordinator is responsible for querying the device at a specified route."""

    def __init__(
        self, hass: HomeAssistant, position: Position, interval, entry: ConfigEntry
    ) -> None:
        """Initialise a custom coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )
        self.position = position
        self.config_entry: ConfigEntry = entry

    async def _async_update_data(self) -> None:
        """Fetch the data from the device."""
        try:
            await self.position.update_data()
        except Trading212BadApiKey as err:
            raise ConfigEntryAuthFailed(
                f"Authentication failed for {self.config_entry.data[CONF_ID]}"
            ) from err
        except (Trading212Limited, Trading212TimeOut, Trading212Error) as err:
            raise UpdateFailed(err) from err
