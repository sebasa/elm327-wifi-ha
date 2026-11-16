"""Entidad base para ELM327 OBD-II WiFi."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import Elm327DataUpdateCoordinator


class Elm327Entity(CoordinatorEntity[Elm327DataUpdateCoordinator]):
    """Entidad base: siempre disponible, ligada al dispositivo ELM327."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: Elm327DataUpdateCoordinator, key: str) -> None:
        """Inicializar entidad."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ELM327",
            manufacturer="ELM327",
            model="OBD-II WiFi Adapter",
            serial_number=f"{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}",
        )

    @property
    def available(self) -> bool:
        """Las entidades nunca quedan 'no disponibles': conservan el último valor."""
        return True
