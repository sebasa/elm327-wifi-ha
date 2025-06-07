"""Componente ELM327 OBD-II WiFi para Home Assistant."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_TIMEOUT, DEFAULT_UPDATE_INTERVAL
from .elm327_client import Elm327Client

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurar ELM327 OBD-II desde una entrada de configuración.""" 
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    
    # Crear cliente ELM327
    client = Elm327Client(host, port, DEFAULT_TIMEOUT)
    
    # Crear coordinador de datos
    coordinator = Elm327DataUpdateCoordinator(hass, client)
    
    # Actualizar datos iniciales
    await coordinator.async_config_entry_first_refresh()
    
    # Guardar coordinador en hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Configurar plataformas
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Descargar entrada de configuración."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.async_disconnect()
    
    return unload_ok


class Elm327DataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinador para actualizar datos del ELM327."""
    
    def __init__(self, hass: HomeAssistant, client: Elm327Client) -> None:
        """Inicializar coordinador."""
        self.client = client
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
    
    async def _async_update_data(self):
        """Obtener datos del ELM327."""
        try:
            return await self.client.async_get_all_data()
        except Exception as err:
            raise UpdateFailed(f"Error comunicándose con ELM327: {err}") from err