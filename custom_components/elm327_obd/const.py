"""Constantes para el componente ELM327 OBD-II WiFi."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "elm327_obd"

# Configuración por defecto
DEFAULT_PORT: Final = 35000
DEFAULT_TIMEOUT: Final = 5
DEFAULT_UPDATE_INTERVAL: Final = 30  # segundos
MIN_UPDATE_INTERVAL: Final = 5
MAX_UPDATE_INTERVAL: Final = 3600

CONF_UPDATE_INTERVAL: Final = "update_interval"

# Comandos OBD-II (modo 01) soportados: clave del sensor -> PID
OBD_COMMANDS: Final[dict[str, str]] = {
    "engine_rpm": "010C",
    "vehicle_speed": "010D",
    "throttle_position": "0111",
    "fuel_level": "012F",
    "barometric_pressure": "0133",
    "ambient_temperature": "0146",
}

# Voltaje de batería: se lee con ATRV (directo del adaptador, funciona con el
# vehículo apagado). El PID 0142 queda como respaldo si ATRV no está soportado.
KEY_BATTERY_VOLTAGE: Final = "battery_voltage"
BATTERY_VOLTAGE_PID: Final = "0142"

# Claves especiales en los datos del coordinador
KEY_CONNECTION_STATE: Final = "connection_state"
KEY_ONLINE: Final = "online"

# Estados de conexión
STATE_CONNECTED: Final = "connected"  # Adaptador + ECU respondiendo (vehículo en marcha)
STATE_ADAPTER_ONLY: Final = "adapter_only"  # Adaptador accesible, ECU sin respuesta
STATE_DISCONNECTED: Final = "disconnected"  # Adaptador inaccesible
CONNECTION_STATES: Final = [STATE_CONNECTED, STATE_ADAPTER_ONLY, STATE_DISCONNECTED]
