"""The Mapit Motorcycle Tracker integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .mapit_api import MapitAPI

_LOGGER = logging.getLogger(__name__)

DOMAIN = "mapit_tracker"
PLATFORMS: list[Platform] = [Platform.DEVICE_TRACKER, Platform.SENSOR]

# Polling interval - every 30 seconds
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Mapit Motorcycle Tracker from a config entry."""
    _LOGGER.debug("Setting up Mapit Tracker integration")
    
    # Create API instance
    api = MapitAPI(
        username=entry.data["username"],
        password=entry.data["password"],
        identity_pool_id=entry.data["identity_pool_id"],
        user_pool_id=entry.data["user_pool_id"],
        user_pool_client_id=entry.data["user_pool_client_id"],
        hass=hass,
    )
    
    # Create coordinator for data updates
    coordinator = MapitDataUpdateCoordinator(hass, api)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Mapit Tracker integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


class MapitDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Mapit data."""

    def __init__(self, hass: HomeAssistant, api: MapitAPI) -> None:
        """Initialize."""
        self.api = api
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            return await self.hass.async_add_executor_job(self.api.get_current_status)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
