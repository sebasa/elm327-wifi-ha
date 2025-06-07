"""Cliente para comunicación con ELM327 OBD-II WiFi."""
import asyncio
import logging
import socket
from typing import Dict, Optional, Any

from .const import OBD_COMMANDS, STATE_CONNECTED, STATE_DISCONNECTED, STATE_ERROR

_LOGGER = logging.getLogger(__name__)


class Elm327Client:
    """Cliente para comunicar con ELM327 OBD-II WiFi."""
    
    def __init__(self, host: str, port: int, timeout: int = 5) -> None:
        """Inicializar cliente."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None
        self._connected = False
        self._initialized = False
    
    async def async_connect(self) -> bool:
        """Conectar al ELM327."""
        try:
            _LOGGER.debug(f"Conectando a ELM327 en {self.host}:{self.port}")
            
            # Crear socket de forma asíncrona
            loop = asyncio.get_event_loop()
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(self.timeout)
            
            await loop.run_in_executor(
                None, self._sock.connect, (self.host, self.port)
            )
            
            self._connected = True
            _LOGGER.info(f"Conectado exitosamente a ELM327 en {self.host}:{self.port}")
            
            return True
            
        except Exception as e:
            _LOGGER.error(f"Error conectando a ELM327: {e}")
            self._connected = False
            if self._sock:
                self._sock.close()
                self._sock = None
            return False
    
    async def async_disconnect(self) -> None:
        """Desconectar del ELM327."""
        if self._sock:
            self._sock.close()
            self._sock = None
        self._connected = False
        self._initialized = False
        _LOGGER.debug("Desconectado del ELM327")
    
    async def async_send_command(self, command: str) -> Optional[str]:
        """Enviar comando al ELM327 y recibir respuesta."""
        if not self._connected or not self._sock:
            if not await self.async_connect():
                return None
        
        try:
            loop = asyncio.get_event_loop()
            
            # Enviar comando
            full_command = f"{command}\r"
            await loop.run_in_executor(
                None, self._sock.send, full_command.encode()
            )
            
            # Recibir respuesta
            response = ""
            while True:
                data = await loop.run_in_executor(
                    None, self._sock.recv, 1024
                )
                response += data.decode().strip()
                if ">" in response:  # Prompt del ELM327
                    break
            
            return response.replace(">", "").strip()
            
        except Exception as e:
            _LOGGER.error(f"Error enviando comando {command}: {e}")
            self._connected = False
            return None
    
    async def async_initialize(self) -> bool:
        """Inicializar ELM327."""
        if self._initialized:
            return True
            
        _LOGGER.debug("Inicializando ELM327...")
        
        init_commands = [
            ("ATZ", "Reset"),
            ("ATE0", "Echo Off"),
            ("ATL0", "Line feeds Off"),
            ("ATS0", "Spaces Off"),
            ("ATH1", "Headers On")
        ]
        
        for cmd, desc in init_commands:
            response = await self.async_send_command(cmd)
            if response:
                _LOGGER.debug(f"Inicialización {desc}: {response}")
            else:
                _LOGGER.warning(f"Sin respuesta para {desc}")
            
            # Pequeña pausa entre comandos
            await asyncio.sleep(0.5)
        
        self._initialized = True
        return True
    
    def _parse_obd_response(self, command_code: str, response: str) -> Optional[float]:
        """Parsear respuesta OBD-II."""
        if not response or "NO DATA" in response or "ERROR" in response:
            return None
        
        try:
            # Limpiar respuesta y obtener bytes de datos
            hex_data = response.replace(" ", "")
            # Saltar header (primeros 4 caracteres + 4 del PID)
            data_bytes = hex_data[8:] if len(hex_data) > 8 else hex_data[4:]
            
            if command_code == "010C":  # Engine RPM
                if len(data_bytes) >= 4:
                    a = int(data_bytes[0:2], 16)
                    b = int(data_bytes[2:4], 16)
                    return ((a * 256) + b) / 4
                    
            elif command_code == "010D":  # Vehicle Speed
                if len(data_bytes) >= 2:
                    return int(data_bytes[0:2], 16)
                    
            elif command_code == "0111":  # Throttle Position
                if len(data_bytes) >= 2:
                    return int(data_bytes[0:2], 16) * 100 / 255
                    
            elif command_code == "012F":  # Fuel Level
                if len(data_bytes) >= 2:
                    return int(data_bytes[0:2], 16) * 100 / 255
                    
            elif command_code == "0133":  # Barometric Pressure
                if len(data_bytes) >= 2:
                    return int(data_bytes[0:2], 16)
                    
            elif command_code == "0146":  # Ambient Temperature
                if len(data_bytes) >= 2:
                    return int(data_bytes[0:2], 16) - 40
                    
            elif command_code == "0142":  # Battery Voltage
                if len(data_bytes) >= 4:
                    a = int(data_bytes[0:2], 16)
                    b = int(data_bytes[2:4], 16)
                    return ((a * 256) + b) / 1000
                    
        except Exception as e:
            _LOGGER.warning(f"Error parseando comando {command_code}: {e}")
            
        return None
    
    async def async_get_all_data(self) -> Dict[str, Any]:
        """Obtener todos los datos OBD-II."""
        if not await self.async_initialize():
            return {"connection_state": STATE_ERROR}
        
        data = {"connection_state": STATE_CONNECTED}
        
        for sensor_key, sensor_config in OBD_COMMANDS.items():
            command = sensor_config["command"]
            response = await self.async_send_command(command)
            
            if response:
                value = self._parse_obd_response(command, response)
                data[sensor_key] = value
                _LOGGER.debug(f"{sensor_key}: {value}")
            else:
                data[sensor_key] = None
                _LOGGER.debug(f"{sensor_key}: Sin datos")
            
            # Pequeña pausa entre comandos
            await asyncio.sleep(0.1)
        
        return data