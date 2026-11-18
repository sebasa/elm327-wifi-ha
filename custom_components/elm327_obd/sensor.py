"""Sensores para ELM327 OBD-II WiFi."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONNECTION_STATES, KEY_CONNECTION_STATE, KEY_ONLINE, STATE_DISCONNECTED
from .coordinator import Elm327ConfigEntry, Elm327DataUpdateCoordinator
from .entity import Elm327Entity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class Elm327SensorEntityDescription(SensorEntityDescription):
    """Descripción de un sensor OBD-II."""

    # Si es True, el valor pasa a 0 cuando el vehículo está apagado/offline
    # (un motor apagado tiene 0 rpm, 0 km/h y 0 % de acelerador).
    zero_when_offline: bool = False


SENSORS: tuple[Elm327SensorEntityDescription, ...] = (
    Elm327SensorEntityDescription(
        key="engine_rpm",
        translation_key="engine_rpm",
        native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        zero_when_offline=True,
    ),
    Elm327SensorEntityDescription(
        key="vehicle_speed",
        translation_key="vehicle_speed",
        device_class=SensorDeviceClass.SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        zero_when_offline=True,
    ),
    Elm327SensorEntityDescription(
        key="throttle_position",
        translation_key="throttle_position",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        zero_when_offline=True,
    ),
    Elm327SensorEntityDescription(
        key="fuel_level",
        translation_key="fuel_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    Elm327SensorEntityDescription(
        key="barometric_pressure",
        translation_key="barometric_pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.KPA,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    Elm327SensorEntityDescription(
        key="ambient_temperature",
        translation_key="ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    Elm327SensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Elm327ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Configurar sensores ELM327 OBD-II."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        Elm327Sensor(coordinator, description) for description in SENSORS
    ]
    entities.append(Elm327ConnectionSensor(coordinator))
    async_add_entities(entities)


class Elm327Sensor(Elm327Entity, RestoreSensor):
    """Sensor OBD-II que conserva el último valor conocido (0 por defecto)."""

    entity_description: Elm327SensorEntityDescription

    def __init__(
        self,
        coordinator: Elm327DataUpdateCoordinator,
        description: Elm327SensorEntityDescription,
    ) -> None:
        """Inicializar sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_native_value = 0

    async def async_added_to_hass(self) -> None:
        """Restaurar el último valor tras un reinicio de Home Assistant."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None and isinstance(
            last.native_value, (int, float)
        ):
            self._attr_native_value = last.native_value
        self._update_from_coordinator()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Actualizar con los nuevos datos del coordinador."""
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    @callback
    def _update_from_coordinator(self) -> None:
        data = self.coordinator.data or {}
        value = data.get(self.entity_description.key)
        if value is not None:
            self._attr_native_value = value
        elif self.entity_description.zero_when_offline and not data.get(KEY_ONLINE):
            self._attr_native_value = 0


class Elm327ConnectionSensor(Elm327Entity, SensorEntity):
    """Estado de conexión: connected / adapter_only / disconnected."""

    _attr_translation_key = "connection_state"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = CONNECTION_STATES
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: Elm327DataUpdateCoordinator) -> None:
        """Inicializar sensor de conexión."""
        super().__init__(coordinator, "connection")

    @property
    def native_value(self) -> str:
        """Estado de la conexión."""
        return (self.coordinator.data or {}).get(KEY_CONNECTION_STATE, STATE_DISCONNECTED)
