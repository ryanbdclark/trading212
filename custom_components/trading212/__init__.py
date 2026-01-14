"""The Trading212 integration."""

from __future__ import annotations

import asyncio
import logging

from pytrading212api.api import Trading212API
from pytrading212api.exceptions import Trading212BadApiKey, Trading212TimeOut
from pytrading212api.position import Position

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_ID, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_SECRET, DOMAIN
from .coordinator import Trading212Coordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Traiding212 from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    trading212_api = Trading212API(
        api_key=entry.data[CONF_API_KEY],
        api_secret=entry.data[CONF_API_SECRET],
        session=async_get_clientsession(hass),
    )

    try:
        positions = await trading212_api.get_positions()

    except Trading212BadApiKey as err:
        _LOGGER.error("API key invalid")
        raise ConfigEntryAuthFailed(f"API key invalid {entry.data[CONF_ID]}") from err

    except Trading212TimeOut as err:
        raise ConfigEntryNotReady(f"Error connecting to {entry.data[CONF_ID]}") from err

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL)
    coordinators = {
        position["ticker"]: Trading212Coordinator(
            hass, Position(trading212_api, position), scan_interval, entry
        )
        for position in positions
    }

    await asyncio.gather(
        *(
            coordinator.async_config_entry_first_refresh()
            for coordinator in list(coordinators.values())
        )
    )

    hass.data[DOMAIN][entry.entry_id] = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
