"""Constantes para el componente ELM327 OBD-II WiFi."""

DOMAIN = "elm327_obd"

# Configuración por defecto
DEFAULT_PORT = 35000
DEFAULT_TIMEOUT = 5
DEFAULT_UPDATE_INTERVAL = 30  # segundos

# Comandos OBD-II soportados
OBD_COMMANDS = {
    "engine_rpm": {
        "name": "Engine RPM",
        "command": "010C",
        "unit": "rpm",
        "icon": "mdi:engine"
    },
    "vehicle_speed": {
        "name": "Vehicle Speed", 
        "command": "010D",
        "unit": "km/h",
        "icon": "mdi:speedometer"
    },
    "throttle_position": {
        "name": "Throttle Position",
        "command": "0111", 
        "unit": "%",
        "icon": "mdi:gas-cylinder"
    },
    "fuel_level": {
        "name": "Fuel Level",
        "command": "012F",
        "unit": "%",
        "icon": "mdi:fuel"
    },
    "barometric_pressure": {
        "name": "Barometric Pressure",
        "command": "0133",
        "unit": "kPa",
        "icon": "mdi:gauge"
    },
    "ambient_temperature": {
        "name": "Ambient Temperature",
        "command": "0146",
        "unit": "°C",
        "icon": "mdi:thermometer"
    },
    "battery_voltage": {
        "name": "Battery Voltage",
        "command": "0142",
        "unit": "V",
        "icon": "mdi:car-battery"
    }
}

# Estados de conexión
STATE_CONNECTED = "connected"
STATE_DISCONNECTED = "disconnected"
STATE_ERROR = "error"