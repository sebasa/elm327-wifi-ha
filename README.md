# ELM327 WiFi OBD-II para Home Assistant

Este componente personalizado permite integrar un adaptador ELM327 WiFi con Home Assistant para monitorear datos del vehículo en tiempo real.

## Características

- ✅ **Home Assistant moderno**: requiere Home Assistant 2025.2 o superior (Python 3.13+)
- 🚗 **Múltiples sensores**: RPM, velocidad, temperatura, combustible, etc.
- 📡 **Conexión WiFi**: Comunicación inalámbrica con el adaptador ELM327
- 🔄 **Actualización automática**: Datos actualizados cada 30 segundos (configurable desde *Opciones*)
- 🟢 **Sensor Online**: indica cuando el vehículo está en marcha (la ECU responde)
- 💾 **Último valor conocido**: los sensores nunca quedan en *desconocido*; con el vehículo apagado conservan el último valor (0 si nunca hubo lectura), incluso tras reiniciar Home Assistant
- 📊 **Dashboard integrado**: Tarjetas y gráficos listos para usar
- 📊 **Configuracion GUi**: Configuración completa desde la interfaz web con validacion de conexion exitosa
- 🚨 **Automatizaciones**: Alertas por temperatura alta, combustible bajo, etc.

## Sensores Disponibles

El componente crea los siguientes sensores automáticamente:

| Sensor | Descripción | Unidad | Comando OBD |
|--------|-------------|--------|-------------|
| **Engine RPM** | Revoluciones por minuto del motor | rpm | 010C |
| **Vehicle Speed** | Velocidad del vehículo | km/h | 010D |
| **Throttle Position** | Posición del acelerador | % | 0111 |
| **Fuel Level** | Nivel de combustible | % | 012F |
| **Barometric Pressure** | Presión barométrica | kPa | 0133 |
| **Ambient Temperature** | Temperatura ambiente | °C | 0146 |
| **Battery Voltage** | Voltaje de la batería | V | 0142 |
| **Connection Status** | `connected` / `adapter_only` / `disconnected` | - | - |
| **Online** (binary_sensor) | Encendido cuando el vehículo está en marcha | - | - |

### Comportamiento con el vehículo apagado

- **Online** pasa a *Desconectado* cuando el adaptador no responde o la ECU no entrega datos (contacto apagado).
- **RPM, Velocidad y Posición del acelerador** pasan a `0` (motor apagado).
- **Combustible, Voltaje, Temperatura y Presión** conservan el último valor leído (o `0` si nunca hubo lectura).
- Las entidades nunca quedan *no disponibles* ni *desconocidas*.
## Requisitos

### Hardware
- Adaptador ELM327 WiFi (disponible en tiendas online por ~$10-25 . tested: Vgate iCar 3 WiFi) 
- Vehículo con puerto OBD-II (fabricados después de 1996)
- Home Assistant instalado

En mi caso tuve que modificar el chip ELM327 para dejarlo en modo STA y sin ahorro de bateria. Instrucciones aqui https://github.com/dconlon/icar_odb_wifi

## Instalación

### Opción 1: HACS (Recomendado)
1. Instala HACS si no lo tienes
2. Ve a HACS → Integraciones
3. Menú de tres puntos → Repositorios personalizados
4. Agrega este repositorio como "Integración"
5. Busca "ELM327 OBD-II WiFi" e instala

### Opción 2: Instalación Manual
1. Descarga todos los archivos del componente
2. Copia la carpeta `custom_components/elm327_obd/` de este repositorio a `custom_components/` en tu directorio de configuración de Home Assistant:
   ```
   custom_components/elm327_obd/
   ├── __init__.py
   ├── binary_sensor.py
   ├── config_flow.py
   ├── const.py
   ├── coordinator.py
   ├── elm327_client.py
   ├── entity.py
   ├── manifest.json
   ├── sensor.py
   ├── strings.json
   └── translations/
   ```
3. Reinicia Home Assistant

## Configuración

### 1. Configurar el adaptador ELM327

1. Conectar el adaptador ELM327 al puerto OBD-II del vehículo
2. Conectar tu dispositivo a la red WiFi del ELM327 (generalmente llamada "WiFi_OBDII" o similar)
3. Identificar la IP del adaptador (normalmente `192.168.0.10` o `192.168.4.1`)

### 2. Configurar Home Assistant

## Configuración

1. Ve a **Configuración** → **Dispositivos y servicios**
2. Haz clic en **+ AGREGAR INTEGRACIÓN**
3. Busca "ELM327 OBD-II WiFi"
4. Ingresa la información de tu adaptador:
   - **Dirección IP**: La IP de tu adaptador ELM327 (ej: 192.168.8.204)
   - **Puerto**: Generalmente 35000 (puerto por defecto)

## Uso

### Dashboard básico

Los sensores estarán disponibles automáticamente. Puedes crear tarjetas como:

```yaml
type: entities
title: "Estado del Motor"
entities:
  - binary_sensor.elm327_online
  - sensor.elm327_engine_rpm
  - sensor.elm327_vehicle_speed
  - sensor.elm327_fuel_level
```

### Automatizaciones de ejemplo

**Aviso al arrancar el vehículo:**
```yaml
automation:
  - alias: "Vehículo en marcha"
    triggers:
      - trigger: state
        entity_id: binary_sensor.elm327_online
        to: "on"
    actions:
      - action: notify.mobile_app_tu_telefono
        data:
          message: "🚗 El vehículo se puso en marcha"
```

**Alerta por combustible bajo:**
```yaml
automation:
  - alias: "Combustible Bajo"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.elm327_fuel_level
        below: 15
    conditions:
      - condition: state
        entity_id: binary_sensor.elm327_online
        state: "on"
    actions:
      - action: notify.mobile_app_tu_telefono
        data:
          message: "⛽ Combustible bajo: {{ states('sensor.elm327_fuel_level') }}%"
```

## Solución de Problemas

### Error de conexión

1. **Verificar la IP del adaptador:**
   - Conectar via SSH/Putty al adaptador

2. **Verificar el puerto:**
   - Puerto común: 35000
   - Algunos modelos usan: 23, 80, 8080

3. **Revisar logs de Home Assistant:**
   ```
   Configuración → Sistema → Logs
   ```

### Sensores sin datos

1. **Verificar compatibilidad del vehículo:**
   - Vehículo debe ser OBD-II (1996+)
   - Algunos comandos pueden no estar soportados

2. **Motor encendido:**
   - El vehículo debe estar encendido para obtener datos


### Rendimiento

- **Sensores específicos:** Modificar el código para incluir solo los sensores que necesites

## Personalización

### Agregar nuevos sensores

1. Agregar el PID en `OBD_COMMANDS` en [`const.py`](custom_components/elm327_obd/const.py):
   ```python
   "tu_sensor": "01XX",
   ```
2. Agregar la fórmula de conversión en `Elm327Client._decode` ([`elm327_client.py`](custom_components/elm327_obd/elm327_client.py)).
3. Agregar un `Elm327SensorEntityDescription` en `SENSORS` ([`sensor.py`](custom_components/elm327_obd/sensor.py)) y su nombre en `strings.json` / `translations/*.json`.

## Contribución

¡Las contribuciones son bienvenidas! Por favor:

1. Hacer fork del repositorio
2. Crear una rama para tu feature
3. Commit y push tus cambios
4. Crear un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo LICENSE para más detalles.

## Agradecimientos

- Basado en el proyecto original de [SebasES](https://github.com/SebasES/ELM327-Wifi-OBDII-Adapter-with-Python)
- Comunidad de Home Assistant por la documentación y ejemplos
- Contribuidores y testers del proyecto

## Soporte

Para reportar problemas o solicitar features:
- Crear un issue en GitHub
- Incluir logs de Home Assistant
- Especificar modelo de adaptador ELM327 y vehículo
