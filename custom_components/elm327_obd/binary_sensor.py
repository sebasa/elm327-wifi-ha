"""Sensores binarios para ELM327 OBD-II WiFi."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import KEY_ONLINE
from .coordinator import Elm327ConfigEntry, Elm327DataUpdateCoordinator
from .entity import Elm327Entity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Elm327ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Configurar sensores binarios."""
    async_add_entities([Elm327OnlineSensor(entry.runtime_data)])


class Elm327OnlineSensor(Elm327Entity, BinarySensorEntity):
    """Encendido cuando el adaptador responde y la ECU del vehículo entrega datos.

    Es decir: el vehículo está en marcha / con contacto.
    """

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: Elm327DataUpdateCoordinator) -> None:
        """Inicializar sensor."""
        super().__init__(coordinator, KEY_ONLINE)

    @property
    def is_on(self) -> bool:
        """Vehículo online."""
        return bool((self.coordinator.data or {}).get(KEY_ONLINE))
