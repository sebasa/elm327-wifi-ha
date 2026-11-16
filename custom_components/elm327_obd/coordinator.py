"""Coordinador de datos para ELM327 OBD-II WiFi."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN
from .elm327_client import Elm327Client

_LOGGER = logging.getLogger(__name__)

type Elm327ConfigEntry = ConfigEntry[Elm327DataUpdateCoordinator]


class Elm327DataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinador que consulta periódicamente el ELM327.

    No lanza UpdateFailed cuando el vehículo está apagado o fuera de alcance:
    así las entidades siguen disponibles y conservan el último valor conocido.
    """

    config_entry: Elm327ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: Elm327ConfigEntry, client: Elm327Client
    ) -> None:
        """Inicializar coordinador."""
        self.client = client
        interval = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Obtener datos del ELM327."""
        return await self.client.async_get_all_data()
