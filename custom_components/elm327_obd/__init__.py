"""Componente ELM327 OBD-II WiFi para Home Assistant."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import DEFAULT_TIMEOUT
from .coordinator import Elm327ConfigEntry, Elm327DataUpdateCoordinator
from .elm327_client import Elm327Client

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: Elm327ConfigEntry) -> bool:
    """Configurar ELM327 OBD-II desde una entrada de configuración."""
    client = Elm327Client(entry.data[CONF_HOST], entry.data[CONF_PORT], DEFAULT_TIMEOUT)
    coordinator = Elm327DataUpdateCoordinator(hass, entry, client)

    # No falla si el vehículo está apagado: el coordinador devuelve estado offline.
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Elm327ConfigEntry) -> bool:
    """Descargar entrada de configuración."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.client.async_disconnect()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: Elm327ConfigEntry) -> None:
    """Recargar al cambiar opciones."""
    await hass.config_entries.async_reload(entry.entry_id)
