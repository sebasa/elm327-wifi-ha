"""Sensores para ELM327 OBD-II WiFi."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OBD_COMMANDS, STATE_CONNECTED
from . import Elm327DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurar sensores ELM327 OBD-II."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Crear sensores para cada comando OBD
    sensors = []
    for sensor_key, sensor_config in OBD_COMMANDS.items():
        sensors.append(
            Elm327Sensor(
                coordinator=coordinator,
                config_entry=config_entry,
                sensor_key=sensor_key,
                sensor_config=sensor_config,
            )
        )
    
    # Agregar sensor de estado de conexión
    sensors.append(
        Elm327ConnectionSensor(
            coordinator=coordinator,
            config_entry=config_entry,
        )
    )
    
    async_add_entities(sensors)


class Elm327Sensor(CoordinatorEntity, SensorEntity):
    """Sensor para datos OBD-II del ELM327."""
    
    def __init__(
        self,
        coordinator: Elm327DataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_key: str,
        sensor_config: Dict[str, Any],
    ) -> None:
        """Inicializar sensor."""
        super().__init__(coordinator)
        
        self._config_entry = config_entry
        self._sensor_key = sensor_key
        self._sensor_config = sensor_config
        self._host = config_entry.data[CONF_HOST]
        self._port = config_entry.data[CONF_PORT]
        
        # Configurar atributos del sensor
        self._attr_name = f"ELM327 {sensor_config['name']}"
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_key}"
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_icon = sensor_config.get("icon")
        
        # Configurar clase de dispositivo basada en el tipo de sensor
        if sensor_key == "vehicle_speed":
            self._attr_device_class = SensorDeviceClass.SPEED
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensor_key in ["fuel_level", "throttle_position"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensor_key in ["engine_rpm", "barometric_pressure"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensor_key == "ambient_temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif sensor_key == "battery_voltage":
            self._attr_device_class = SensorDeviceClass.VOLTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def device_info(self) -> DeviceInfo:
        """Información del dispositivo."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=f"ELM327 OBD-II ({self._host})",
            manufacturer="ELM327",
            model="OBD-II WiFi Adapter",
            sw_version="1.0",
        )
    
    @property
    def native_value(self) -> Optional[float]:
        """Valor nativo del sensor."""
        if self.coordinator.data is None:
            return None
        
        value = self.coordinator.data.get(self._sensor_key)
        if value is not None:
            # Redondear valores según el tipo
            if self._sensor_key == "engine_rpm":
                return round(value)
            elif self._sensor_key in ["throttle_position", "fuel_level"]:
                return round(value, 1)
            elif self._sensor_key == "battery_voltage":
                return round(value, 2)
            else:
                return round(value, 1) if isinstance(value, float) else value
        
        return None
    
    @property
    def available(self) -> bool:
        """Disponibilidad del sensor."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.get("connection_state") == STATE_CONNECTED
        )
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Atributos adicionales del estado."""
        attrs = {}
        if self.coordinator.data:
            attrs["connection_state"] = self.coordinator.data.get("connection_state")
            attrs["host"] = self._host
            attrs["port"] = self._port
            attrs["command"] = self._sensor_config["command"]
        return attrs


class Elm327ConnectionSensor(CoordinatorEntity, SensorEntity):
    """Sensor para el estado de conexión del ELM327."""
    
    def __init__(
        self,
        coordinator: Elm327DataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Inicializar sensor de conexión."""
        super().__init__(coordinator)
        
        self._config_entry = config_entry
        self._host = config_entry.data[CONF_HOST]
        self._port = config_entry.data[CONF_PORT]
        
        self._attr_name = f"ELM327 Connection Status"
        self._attr_unique_id = f"{config_entry.entry_id}_connection"
        self._attr_icon = "mdi:car-connected"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Información del dispositivo."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=f"ELM327 OBD-II ({self._host})",
            manufacturer="ELM327",
            model="OBD-II WiFi Adapter",
            sw_version="1.0",
        )
    
    @property
    def native_value(self) -> str:
        """Estado de la conexión."""
        if self.coordinator.data:
            return self.coordinator.data.get("connection_state", "unknown")
        return "unknown"
    
    @property
    def available(self) -> bool:
        """Disponibilidad del sensor."""
        return self.coordinator.last_update_success
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Atributos adicionales del estado."""
        return {
            "host": self._host,
            "port": self._port,
            "last_update": self.coordinator.last_update_success_time,
        }